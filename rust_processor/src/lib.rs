use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use duckdb::{Connection, Result as DuckDBResult, params};
use rayon::prelude::*;
use std::sync::{Arc, Mutex};
use indicatif::{ProgressBar, ProgressStyle};

#[derive(Debug, Clone)]
struct TickData {
    tick: i32,
    round_num: i32,
    seconds: f64,
    clock_time: String,
    t_score: i32,
    ct_score: i32,
    steam_id: i64,
    name: String,
    team: String,
    side: String,
    is_alive: bool,
    hp: i32,
    armor: i32,
    x: f64,
    y: f64,
    z: f64,
    view_x: f64,
    view_y: f64,
    active_weapon: String,
    demo_filename: String,
    map_name: String,
}

impl TickData {
    fn from_py_dict(dict: &PyDict, demo_filename: &str, map_name: &str) -> PyResult<Self> {
        Ok(TickData {
            tick: dict.get_item("tick")?.unwrap_or_default().extract().unwrap_or(0),
            round_num: dict.get_item("roundNum")?.unwrap_or_default().extract().unwrap_or(0),
            seconds: dict.get_item("seconds")?.unwrap_or_default().extract().unwrap_or(0.0),
            clock_time: dict.get_item("clockTime")?.unwrap_or_default().extract().unwrap_or_else(|_| String::new()),
            t_score: dict.get_item("tScore")?.unwrap_or_default().extract().unwrap_or(0),
            ct_score: dict.get_item("ctScore")?.unwrap_or_default().extract().unwrap_or(0),
            steam_id: dict.get_item("steamID")?.unwrap_or_default().extract().unwrap_or(0),
            name: dict.get_item("name")?.unwrap_or_default().extract().unwrap_or_else(|_| String::new()),
            team: dict.get_item("team")?.unwrap_or_default().extract().unwrap_or_else(|_| String::new()),
            side: dict.get_item("side")?.unwrap_or_default().extract().unwrap_or_else(|_| String::new()),
            is_alive: dict.get_item("isAlive")?.unwrap_or_default().extract().unwrap_or(true),
            hp: dict.get_item("hp")?.unwrap_or_default().extract().unwrap_or(100),
            armor: dict.get_item("armor")?.unwrap_or_default().extract().unwrap_or(0),
            x: dict.get_item("x")?.unwrap_or_default().extract().unwrap_or(0.0),
            y: dict.get_item("y")?.unwrap_or_default().extract().unwrap_or(0.0),
            z: dict.get_item("z")?.unwrap_or_default().extract().unwrap_or(0.0),
            view_x: dict.get_item("viewX")?.unwrap_or_default().extract().unwrap_or(0.0),
            view_y: dict.get_item("viewY")?.unwrap_or_default().extract().unwrap_or(0.0),
            active_weapon: dict.get_item("activeWeapon")?.unwrap_or_default().extract().unwrap_or_else(|_| String::new()),
            demo_filename: demo_filename.to_string(),
            map_name: map_name.to_string(),
        })
    }
}

#[pyfunction]
fn insert_ticks_bulk(
    db_path: String,
    ticks_data: &PyList,
    demo_filename: String,
    map_name: String,
) -> PyResult<i32> {
    // Convert Python data to Rust structs
    let tick_records: Result<Vec<_>, _> = ticks_data
        .iter()
        .map(|item| {
            let dict = item.downcast::<PyDict>()?;
            TickData::from_py_dict(dict, &demo_filename, &map_name)
        })
        .collect();

    let tick_records = tick_records?;
    let total_ticks = tick_records.len();

    println!("🦀 Rust processor: inserting {} ticks", total_ticks);

    // Connect to DuckDB
    let conn = Connection::open(&db_path).map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to connect to DuckDB: {}", e))
    })?;

    // Prepare the insert statement
    let mut stmt = conn.prepare("
        INSERT INTO demo_ticks (
            tick, round_num, seconds, clock_time, t_score, ct_score,
            steam_id, name, team, side, is_alive, hp, armor,
            x, y, z, view_x, view_y, active_weapon, demo_filename, map_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ").map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to prepare statement: {}", e))
    })?;

    // Begin transaction
    conn.execute_batch("BEGIN TRANSACTION").map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to begin transaction: {}", e))
    })?;

    // Create progress bar
    let pb = ProgressBar::new(total_ticks as u64);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("[{elapsed_precise}] {bar:40.cyan/blue} {pos:>7}/{len:7} {msg}")
            .unwrap()
            .progress_chars("##-"),
    );

    // Batch insert - process in chunks for better memory management
    const BATCH_SIZE: usize = 10000;
    let mut inserted = 0;

    for chunk in tick_records.chunks(BATCH_SIZE) {
        for tick in chunk {
            stmt.execute(params![
                tick.tick,
                tick.round_num,
                tick.seconds,
                tick.clock_time,
                tick.t_score,
                tick.ct_score,
                tick.steam_id,
                tick.name,
                tick.team,
                tick.side,
                tick.is_alive,
                tick.hp,
                tick.armor,
                tick.x,
                tick.y,
                tick.z,
                tick.view_x,
                tick.view_y,
                tick.active_weapon,
                tick.demo_filename,
                tick.map_name,
            ]).map_err(|e| {
                pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to insert tick: {}", e))
            })?;
            
            inserted += 1;
            pb.set_position(inserted as u64);
        }
    }

    // Commit transaction
    conn.execute_batch("COMMIT").map_err(|e| {
        pyo3::exceptions::PyRuntimeError::new_err(format!("Failed to commit transaction: {}", e))
    })?;

    pb.finish_with_message("✅ Complete");
    println!("🦀 Rust processor: successfully inserted {} ticks", inserted);

    Ok(inserted as i32)
}

#[pymodule]
fn demo_processor(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(insert_ticks_bulk, m)?)?;
    Ok(())
}
