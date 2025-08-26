import os
import csv
import tempfile
import time
from pathlib import Path

def insert_ticks_data_csv(db_manager, demo_obj, file_path: str):
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
                '{csv_path}',
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

# Add this to the imports section in parse_demo.py
from csv_processor import insert_ticks_data_csv
