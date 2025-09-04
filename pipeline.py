import os
import pandas as pd
from demoparser2 import DemoParser
from pathlib import Path
import logging
import time
from typing import Optional, List, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed

try:
    import typer  # Optional CLI
except Exception:  # pragma: no cover
    typer = None

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_datatypes(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Optimize DataFrame data types for better storage and performance."""
    if df.empty:
        return df
    
    try:
        # Optimize based on data type
        if data_type == 'player_ticks':
            # Optimize coordinates to int32 (strategic analysis doesn't need float64 precision)
            for col in ['X', 'Y', 'Z']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int32')
            
            # Optimize health and armor to int8 (0-100 range)
            for col in ['m_iHealth', 'm_ArmorValue']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int8')
            
            # Optimize team numbers to int8
            if 'm_iTeamNum' in df.columns:
                df['m_iTeamNum'] = pd.to_numeric(df['m_iTeamNum'], errors='coerce').fillna(0).astype('int8')
            
            # Optimize angles to float32
            for col in ['m_angEyeAngles[0]', 'm_angEyeAngles[1]']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float32')
                    
            # Convert player names to category for repeated strings
            if 'name' in df.columns:
                df['name'] = df['name'].astype('category')
                
        elif data_type == 'grenades':
            # Optimize grenade coordinates
            for col in ['x', 'y', 'z']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int32')
            
            # Convert categorical columns
            for col in ['name', 'grenade_type']:
                if col in df.columns:
                    df[col] = df[col].astype('category')
                    
        elif data_type == 'player_info':
            # Convert categorical columns (support both steamid and steam_id)
            for col in ['name', 'steamid', 'steam_id']:
                if col in df.columns:
                    df[col] = df[col].astype('category')
                    
        # Normalize common column names
        if 'steam_id' in df.columns and 'steamid' not in df.columns:
            df.rename(columns={'steam_id': 'steamid'}, inplace=True)

        # Convert tick to int32 for all data types
        if 'tick' in df.columns:
            df['tick'] = pd.to_numeric(df['tick'], errors='coerce').fillna(0).astype('int32')
            
        logger.debug(f"Optimized {data_type} datatypes: {df.memory_usage(deep=True).sum() / 1024**2:.2f}MB")
        
    except Exception as e:
        logger.warning(f"Failed to optimize datatypes for {data_type}: {str(e)}")
        
    return df


def _safe_write_parquet(df: pd.DataFrame, output_file: Path) -> None:
    """Write to a temp file and move into place atomically; prefer pyarrow."""
    tmp_path = output_file.with_suffix(output_file.suffix + '.tmp')
    try:
        df.to_parquet(
            tmp_path,
            index=False,
            compression='snappy',
            engine='pyarrow',
            use_dictionary=True,
        )
    except Exception as e:
        logger.warning(f"  PyArrow write failed ({e}); retrying with fastparquet if available")
        df.to_parquet(
            tmp_path,
            index=False,
            compression='snappy',
            engine='fastparquet'
        )
    # Atomic replace
    tmp_path.replace(output_file)


def _process_single_demo(demo_file: Path, parquet_folder: Path, common_events: List[str], player_props: List[str], tick_sample_mod: Optional[int]) -> Dict[str, int]:
    """Process a single demo file; returns per-type row counts."""
    demo_rows: Dict[str, int] = {}
    demo_start_time = time.time()
    demo_name = demo_file.stem

    logger.info(f"Processing {demo_file.name}...")

    parser = DemoParser(str(demo_file))
    available_events = parser.list_game_events()
    events_to_parse = [event for event in common_events if event in available_events]

    data_to_parse = {
        'grenades': lambda: parser.parse_grenades(),
        'player_info': lambda: parser.parse_player_info(),
        'item_drops': lambda: parser.parse_item_drops(),
        'skins': lambda: parser.parse_skins(),
    }

    if player_props:
        data_to_parse['player_ticks'] = lambda: parser.parse_ticks(player_props)

    for event in events_to_parse:
        data_to_parse[f'event_{event}'] = lambda e=event: parser.parse_events([e])

    demo_output_folder = parquet_folder / demo_name
    demo_output_folder.mkdir(exist_ok=True)

    for data_type, parse_method in data_to_parse.items():
        try:
            parse_start_time = time.time()
            logger.info(f"  Parsing {data_type}...")
            data = parse_method()

            if isinstance(data, list) and len(data) > 0:
                data = pd.concat(data, ignore_index=True)
            elif isinstance(data, list) and len(data) == 0:
                data = pd.DataFrame()

            if data is not None and not data.empty:
                # Optimize dtypes
                data = optimize_datatypes(data, data_type)

                # Optional sampling for player_ticks
                if data_type == 'player_ticks' and tick_sample_mod and 'tick' in data.columns:
                    before = len(data)
                    data = data[data['tick'] % tick_sample_mod == 0]
                    after = len(data)
                    logger.info(f"  Applied tick sampling mod {tick_sample_mod}: {before:,} -> {after:,} rows")

                output_file = demo_output_folder / f"{data_type}.parquet"

                write_start = time.time()
                _safe_write_parquet(data, output_file)
                write_time = time.time() - write_start

                rows_count = len(data)
                demo_rows[data_type] = rows_count
                parse_time = time.time() - parse_start_time

                logger.info(
                    f"  Saved {data_type} to {output_file} ({rows_count:,} rows, parse {parse_time:.1f}s, write {write_time:.1f}s)"
                )
            else:
                logger.warning(f"  No data found for {data_type}")

        except Exception as e:
            logger.error(f"  Error parsing {data_type}: {str(e)}")
            continue

    demo_time = time.time() - demo_start_time
    logger.info(f"Successfully processed {demo_file.name} ({sum(demo_rows.values()):,} total rows, {demo_time:.1f}s)")
    return demo_rows

def parse_demo_files(
    demos_path: str = "demos",
    parquet_path: str = "parquet",
    events: Optional[List[str]] = None,
    tick_sample_mod: Optional[int] = None,
    workers: Optional[int] = None,
) -> Dict[str, Dict[str, int]]:
    """Parse demo files and save optimized parquet files.

    Returns a mapping: demo_name -> {data_type: rows}.
    """
    start_time = time.time()

    demos_folder = Path(demos_path)
    parquet_folder = Path(parquet_path)
    parquet_folder.mkdir(exist_ok=True)

    demo_files = list(demos_folder.glob("*.dem"))
    if not demo_files:
        logger.warning("No demo files found in the demos folder")
        return {}

    logger.info(f"Found {len(demo_files)} demo files to process")

    default_events = ['player_death', 'round_start', 'round_end', 'bomb_planted', 'bomb_defused', 'bomb_exploded', 'weapon_fire', 'player_hurt']
    env_events = os.getenv('SF_EVENTS')
    common_events = events or ([e.strip() for e in env_events.split(',')] if env_events else default_events)

    # Player properties
    player_props = [
        'X', 'Y', 'Z',
        'm_iHealth', 'm_ArmorValue',
        'm_iTeamNum',
        'm_bIsAlive',
        'm_angEyeAngles[0]', 'm_angEyeAngles[1]',
        'm_hActiveWeapon'
    ]

    # Determine sampling
    if tick_sample_mod is None:
        sample_mod_env = os.getenv('SF_TICK_SAMPLE')
        if sample_mod_env:
            try:
                tick_sample_mod = int(sample_mod_env)
                if tick_sample_mod <= 0:
                    tick_sample_mod = None
            except ValueError:
                tick_sample_mod = None
                logger.warning("Invalid SF_TICK_SAMPLE value; ignoring")

    results: Dict[str, Dict[str, int]] = {}

    # Parallel processing per demo
    if workers is None:
        env_workers = os.getenv('SF_WORKERS')
        if env_workers:
            try:
                workers = int(env_workers)
            except ValueError:
                workers = None
        if workers is None:
            workers = max(1, (os.cpu_count() or 2) - 1)

    if workers > 1 and len(demo_files) > 1:
        logger.info(f"Using parallel processing with {workers} workers")
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_process_single_demo, df, parquet_folder, common_events, player_props, tick_sample_mod): df
                for df in demo_files
            }
            for future in as_completed(futures):
                demo_file = futures[future]
                try:
                    demo_rows = future.result()
                    results[demo_file.stem] = demo_rows
                except Exception as e:
                    logger.error(f"Error in worker for {demo_file.name}: {e}")
    else:
        logger.info("Processing demos sequentially")
        for demo_file in demo_files:
            demo_rows = _process_single_demo(demo_file, parquet_folder, common_events, player_props, tick_sample_mod)
            results[demo_file.stem] = demo_rows

    total_rows = sum(sum(v.values()) for v in results.values())
    total_time = time.time() - start_time
    logger.info(f"Demo parsing completed! ({total_rows:,} total rows processed in {total_time:.1f}s)")
    return results

def main():
    """Main function / CLI entrypoint for the demo parsing pipeline."""
    logger.info("Starting demo parsing pipeline...")

    if typer is None:
        # Fallback: env-driven execution
        parse_demo_files()
        return

    app = typer.Typer(add_completion=False, no_args_is_help=False)

    def _run_impl(
        demos: str = typer.Option("demos", help="Path to demos directory"),
        out: str = typer.Option("parquet", help="Output parquet directory"),
        events: Optional[str] = typer.Option(None, help="Comma-separated list of events to parse"),
        tick_sample: Optional[int] = typer.Option(None, help="Modulo for tick sampling (e.g., 64)"),
        workers: Optional[int] = typer.Option(None, help="Number of parallel workers"),
        log_level: str = typer.Option("INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR"),
    ):
        logging.getLogger().setLevel(getattr(logging, log_level.upper(), logging.INFO))
        events_list = [e.strip() for e in events.split(',')] if events else None
        parse_demo_files(demos_path=demos, parquet_path=out, events=events_list, tick_sample_mod=tick_sample, workers=workers)

    @app.command(name="run", help="Parse CS:GO demos into optimized parquet datasets")
    def run(
        demos: str = typer.Option("demos", help="Path to demos directory"),
        out: str = typer.Option("parquet", help="Output parquet directory"),
        events: Optional[str] = typer.Option(None, help="Comma-separated list of events to parse"),
        tick_sample: Optional[int] = typer.Option(None, help="Modulo for tick sampling (e.g., 64)"),
        workers: Optional[int] = typer.Option(None, help="Number of parallel workers"),
        log_level: str = typer.Option("INFO", help="Logging level: DEBUG, INFO, WARNING, ERROR"),
    ):
        _run_impl(demos, out, events, tick_sample, workers, log_level)

    @app.callback()
    def _default(ctx: typer.Context):
        # If no subcommand provided, run with defaults
        if ctx.invoked_subcommand is None:
            _run_impl("demos", "parquet", None, None, None, "INFO")

    app()

if __name__ == "__main__":
    main()
