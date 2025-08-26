import string
import polars as pl
import awpy
from awpy.plot import plot, PLOT_SETTINGS
from awpy import Demo
from awpy.stats import adr
from awpy.plot import gif
from tqdm import tqdm
import duckdb
import os
from database.schema import DatabaseManager
from datetime import datetime
import hashlib
import json
import csv
import tempfile
import time

def get_map_name_from_demo(demo_obj, file_path: str) -> str:
    """Extract map name from demo with fallbacks"""
    # Try to get from demo header first
    try:
        if hasattr(demo_obj, 'header') and demo_obj.header:
            if hasattr(demo_obj.header, 'map_name'):
                return demo_obj.header.map_name
            elif 'map' in demo_obj.header:
                return demo_obj.header['map']
    except:
        pass
    
    # Fallback to filename parsing
    filename = os.path.basename(file_path).lower()
    if "mirage" in filename:
        return "de_mirage"
    elif "dust2" in filename:
        return "de_dust2"
    elif "inferno" in filename:
        return "de_inferno"
    elif "cache" in filename:
        return "de_cache"
    elif "overpass" in filename:
        return "de_overpass"
    elif "nuke" in filename:
        return "de_nuke"
    elif "train" in filename:
        return "de_train"
    elif "vertigo" in filename:
        return "de_vertigo"
    elif "ancient" in filename:
        return "de_ancient"
    elif "anubis" in filename:
        return "de_anubis"
    else:
        return "unknown"

def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of the demo file"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return ""

def insert_demo_metadata(db_manager: DatabaseManager, demo_obj, file_path: str):
    """Insert demo metadata into the database"""
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    file_hash = calculate_file_hash(file_path)
    map_name = get_map_name_from_demo(demo_obj, file_path)
    
    # Calculate totals
    total_ticks = len(demo_obj.ticks) if demo_obj.ticks is not None and not demo_obj.ticks.is_empty() else 0
    total_rounds = len(demo_obj.rounds) if demo_obj.rounds is not None and not demo_obj.rounds.is_empty() else 0
    
    # Try to get team info from rounds
    team1_name = team2_name = ""
    team1_score = team2_score = 0
    if demo_obj.rounds is not None and not demo_obj.rounds.is_empty() and len(demo_obj.rounds) > 0:
        last_round = demo_obj.rounds.tail(1)
        if len(last_round) > 0:
            try:
                team1_score = int(last_round['ct_score'].iloc[0]) if 'ct_score' in last_round.columns else 0
                team2_score = int(last_round['t_score'].iloc[0]) if 't_score' in last_round.columns else 0
            except:
                pass
    
    # Insert metadata
    db_manager.connection.execute("""
        INSERT INTO demo_metadata (
            filename, file_path, file_size_bytes, file_hash, map_name,
            total_rounds, total_ticks, team1_score, team2_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (filename) DO UPDATE SET
            file_path = excluded.file_path,
            file_size_bytes = excluded.file_size_bytes,
            file_hash = excluded.file_hash,
            map_name = excluded.map_name,
            total_rounds = excluded.total_rounds,
            total_ticks = excluded.total_ticks,
            team1_score = excluded.team1_score,
            team2_score = excluded.team2_score
    """, [filename, file_path, file_size, file_hash, map_name, 
          total_rounds, total_ticks, team1_score, team2_score])
    
    print(f"Inserted metadata for {filename}")

def insert_ticks_data(db_manager: DatabaseManager, demo_obj, file_path: str):
    """Insert ticks data using CSV export + DuckDB COPY (ultra-fast)"""
    if demo_obj.ticks is None or demo_obj.ticks.is_empty():
        print("No ticks data to insert")
        return
    
    filename = os.path.basename(file_path)
    map_name = get_map_name_from_demo(demo_obj, file_path)
    
    # Convert to pandas
    ticks_df = demo_obj.ticks.to_pandas()
    total_ticks = len(ticks_df)
    
    print(f"🚀 Ultra-fast processing {total_ticks:,} ticks via CSV import...")
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
        csv_path = temp_file.name
        writer = csv.writer(temp_file)
        
        print("📝 Writing CSV file...")
        start_time = time.time()
        
        # Write data directly to CSV (much faster than individual inserts)
        for idx, row in ticks_df.iterrows():
            writer.writerow([
                row.get('tick', idx),
                row.get('roundNum', 0),
                row.get('seconds', 0.0),
                row.get('clockTime', ''),
                row.get('tScore', 0),
                row.get('ctScore', 0),
                row.get('steamID', 0),
                row.get('name', ''),
                row.get('team', ''),
                row.get('side', ''),
                row.get('isAlive', True),
                row.get('hp', 100),
                row.get('armor', 0),
                row.get('x', 0.0),
                row.get('y', 0.0),
                row.get('z', 0.0),
                row.get('viewX', 0.0),
                row.get('viewY', 0.0),
                row.get('activeWeapon', ''),
                filename,
                map_name
            ])
    
    csv_write_time = time.time() - start_time
    print(f"📝 CSV written in {csv_write_time:.2f} seconds")
    
    try:
        print("💾 Importing CSV into DuckDB...")
        import_start = time.time()
        
        # Use DuckDB's ultra-fast CSV import
        db_manager.connection.execute(f"""
            INSERT INTO demo_ticks (
                tick, round_num, seconds, clock_time, t_score, ct_score,
                steam_id, name, team, side, is_alive, hp, armor,
                x, y, z, view_x, view_y, active_weapon, demo_filename, map_name
            )
            SELECT * FROM read_csv(
                '{csv_path.replace(chr(92), '/')}',
                header=false,
                columns={{
                    'tick': 'INTEGER',
                    'round_num': 'INTEGER', 
                    'seconds': 'DOUBLE',
                    'clock_time': 'VARCHAR',
                    't_score': 'INTEGER',
                    'ct_score': 'INTEGER',
                    'steam_id': 'BIGINT',
                    'name': 'VARCHAR',
                    'team': 'VARCHAR',
                    'side': 'VARCHAR',
                    'is_alive': 'BOOLEAN',
                    'hp': 'INTEGER',
                    'armor': 'INTEGER',
                    'x': 'DOUBLE',
                    'y': 'DOUBLE',
                    'z': 'DOUBLE',
                    'view_x': 'DOUBLE',
                    'view_y': 'DOUBLE',
                    'active_weapon': 'VARCHAR',
                    'demo_filename': 'VARCHAR',
                    'map_name': 'VARCHAR'
                }}
            )
        """)
        
        import_time = time.time() - import_start
        total_time = time.time() - start_time
        
        print(f"💾 Database import completed in {import_time:.2f} seconds")
        print(f"🚀 Total processing time: {total_time:.2f} seconds ({total_ticks/total_time:,.0f} ticks/sec)")
        print(f"✅ Successfully inserted {total_ticks:,} ticks")
        
    except Exception as e:
        print(f"❌ Error during CSV import: {e}")
        # Fall back to batch processing
        print("🔄 Falling back to batch processing...")
        return insert_ticks_data_fallback(db_manager, demo_obj, file_path)
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(csv_path)
        except:
            pass

def insert_ticks_data_fallback(db_manager: DatabaseManager, demo_obj, file_path: str):
    """Fallback batch insert method"""
    filename = os.path.basename(file_path)
    map_name = get_map_name_from_demo(demo_obj, file_path)
    
    # Convert to pandas for easier manipulation
    ticks_df = demo_obj.ticks.to_pandas()
    total_ticks = len(ticks_df)
    print(f"Fallback: Processing {total_ticks:,} ticks with batch insert...")
    
    # Use larger batch size for better performance
    batch_size = 5000
    total_inserted = 0
    
    # Prepare the insert statement
    insert_sql = """
        INSERT INTO demo_ticks (
            tick, round_num, seconds, clock_time, t_score, ct_score,
            steam_id, name, team, side, is_alive, hp, armor,
            x, y, z, view_x, view_y, active_weapon, demo_filename, map_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Process in large batches with transaction control
    try:
        db_manager.connection.execute("BEGIN TRANSACTION")
        
        for start_idx in tqdm(range(0, total_ticks, batch_size), desc="Inserting batches"):
            end_idx = min(start_idx + batch_size, total_ticks)
            batch_df = ticks_df.iloc[start_idx:end_idx]
            
            # Prepare batch data efficiently
            batch_data = [
                (
                    row.get('tick', idx + start_idx),
                    row.get('roundNum', 0),
                    row.get('seconds', 0.0),
                    row.get('clockTime', ''),
                    row.get('tScore', 0),
                    row.get('ctScore', 0),
                    row.get('steamID', 0),
                    row.get('name', ''),
                    row.get('team', ''),
                    row.get('side', ''),
                    row.get('isAlive', True),
                    row.get('hp', 100),
                    row.get('armor', 0),
                    row.get('x', 0.0),
                    row.get('y', 0.0),
                    row.get('z', 0.0),
                    row.get('viewX', 0.0),
                    row.get('viewY', 0.0),
                    row.get('activeWeapon', ''),
                    filename,
                    map_name
                )
                for idx, row in batch_df.iterrows()
            ]
            
            # Insert the batch
            db_manager.connection.executemany(insert_sql, batch_data)
            total_inserted += len(batch_data)
        
        # Commit the transaction
        db_manager.connection.execute("COMMIT")
        print(f"Fallback method inserted {total_inserted:,} ticks")
        
    except Exception as e:
        # Rollback on error
        db_manager.connection.execute("ROLLBACK")
        print(f"Error during fallback batch insert: {e}")

def query_demo_data(db_manager: DatabaseManager):
    """Example queries on the structured data"""
    print("\n=== Demo Analysis Queries ===")
    
    # Query metadata
    metadata = db_manager.connection.execute("""
        SELECT filename, map_name, total_rounds, total_ticks, team1_score, team2_score
        FROM demo_metadata
        ORDER BY parsed_at DESC
        LIMIT 5
    """).fetchall()
    
    print("Recent demos:")
    for row in metadata:
        print(f"  {row[0]} - {row[1]} - {row[2]} rounds - Score: {row[4]}-{row[5]}")
    
    # Query player performance
    players = db_manager.connection.execute("""
        SELECT name, COUNT(*) as ticks, 
               AVG(hp) as avg_hp,
               COUNT(CASE WHEN is_alive = true THEN 1 END) as alive_ticks
        FROM demo_ticks 
        WHERE name IS NOT NULL AND name != ''
        GROUP BY name
        ORDER BY ticks DESC
        LIMIT 10
    """).fetchall()
    
    print("\nPlayer statistics:")
    for row in players:
        alive_pct = (row[3] / row[1] * 100) if row[1] > 0 else 0
        print(f"  {row[0]}: {row[1]} ticks, {row[2]:.1f} avg HP, {alive_pct:.1f}% alive")

def process_demo_file(demo_file_path: str, db_manager: DatabaseManager, max_ticks: int = None):
    """Process a single demo file with optional tick limit"""
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(demo_file_path)}")
    print(f"{'='*60}")
    
    try:
        # Parse the demo
        print("Parsing demo...")
        dem = awpy.Demo(demo_file_path)
        dem.parse()
        
        total_ticks = len(dem.ticks) if dem.ticks is not None and not dem.ticks.is_empty() else 0
        total_rounds = len(dem.rounds) if dem.rounds is not None and not dem.rounds.is_empty() else 0
        
        print(f"Demo loaded: {total_ticks} ticks, {total_rounds} rounds")
        
        # Check if we should limit ticks for testing
        if max_ticks and total_ticks > max_ticks:
            print(f"⚠️  Large demo detected ({total_ticks:,} ticks). Limiting to {max_ticks:,} ticks for testing.")
            # Truncate the ticks dataframe
            if dem.ticks is not None:
                dem.ticks = dem.ticks.head(max_ticks)
        
        # Insert metadata
        insert_demo_metadata(db_manager, dem, demo_file_path)
        
        # Insert ticks data
        insert_ticks_data(db_manager, dem, demo_file_path)
        
        print(f"✅ Successfully processed {os.path.basename(demo_file_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(demo_file_path)}: {e}")
        return False

def find_demo_files(demos_dir: str) -> list:
    """Find all .dem files in the demos directory"""
    demo_files = []
    if os.path.exists(demos_dir):
        for filename in os.listdir(demos_dir):
            if filename.endswith('.dem'):
                demo_files.append(os.path.join(demos_dir, filename))
    return sorted(demo_files)

# Initialize database manager and run migrations
print("Initializing database...")
db_manager = DatabaseManager("sf.duckdb")
db_manager.connect()
db_manager.migrate()

# Show schema info
db_manager.get_schema_info()

# Find all demo files
demos_directory = "demos"
demo_files = find_demo_files(demos_directory)

if not demo_files:
    print(f"No .dem files found in {demos_directory} directory")
    exit(1)

print(f"\nFound {len(demo_files)} demo files:")
for demo_file in demo_files:
    print(f"  - {os.path.basename(demo_file)}")

# Process all demo files
print(f"\nProcessing {len(demo_files)} demo files...")
print("🚀 Processing FULL datasets (no tick limit)")
successful = 0
failed = 0

# Remove tick limit for full processing
TICK_LIMIT = None  # Process all ticks

for demo_file in demo_files:
    if process_demo_file(demo_file, db_manager, max_ticks=TICK_LIMIT):
        successful += 1
    else:
        failed += 1

# Summary
print(f"\n{'='*60}")
print(f"PROCESSING SUMMARY")
print(f"{'='*60}")
print(f"✅ Successfully processed: {successful} demos")
print(f"❌ Failed to process: {failed} demos")
print(f"📊 Total demos: {len(demo_files)}")

# Run comprehensive analysis queries
query_demo_data(db_manager)

print(f"\nDatabase operations completed. Database: {db_manager.db_path}")
# Keep connection open or close it
# db_manager.close()
