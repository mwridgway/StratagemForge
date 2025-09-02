#!/usr/bin/env python3
"""Simple database schema inspector for DuckDB"""

import duckdb

def inspect_database():
    # Connect to the database
    conn = duckdb.connect('sf.duckdb')
    
    print("=== DATABASE SCHEMA INFORMATION ===\n")
    
    # Get all tables
    print("1. Available tables:")
    tables_result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
    tables = [row[0] for row in tables_result]
    for table in tables:
        print(f"  - {table}")
    print()
    
    # Get detailed schema for each table
    print("2. Table schemas:")
    for table in tables:
        print(f"\n--- {table.upper()} ---")
        schema_result = conn.execute(f"DESCRIBE {table}").fetchall()
        for row in schema_result:
            print(f"  {row[0]:<20} {row[1]:<15} {row[2]:<10}")
        
        # Get row count
        count_result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        print(f"  Records: {count_result[0]:,}")
    
    # Sample data from key tables
    print("\n3. Sample data:")
    
    if 'demo_metadata' in tables:
        print("\n--- DEMO_METADATA (first 3 rows) ---")
        sample = conn.execute("SELECT * FROM demo_metadata LIMIT 3").fetchall()
        columns = [desc[0] for desc in conn.description]
        print(f"Columns: {columns}")
        for row in sample:
            print(f"  {dict(zip(columns, row))}")
    
    if 'players' in tables:
        print("\n--- PLAYERS (first 5 rows) ---")
        sample = conn.execute("SELECT * FROM players LIMIT 5").fetchall()
        columns = [desc[0] for desc in conn.description]
        print(f"Columns: {columns}")
        for row in sample:
            print(f"  {dict(zip(columns, row))}")
    
    if 'demo_ticks' in tables:
        print("\n--- DEMO_TICKS (first 2 rows) ---")
        sample = conn.execute("SELECT * FROM demo_ticks LIMIT 2").fetchall()
        columns = [desc[0] for desc in conn.description]
        print(f"Columns: {columns}")
        for row in sample:
            print(f"  {dict(zip(columns, row))}")
    
    # Some useful aggregations
    print("\n4. Quick stats:")
    if 'demo_ticks' in tables and 'players' in tables:
        # Unique players
        unique_players = conn.execute("SELECT COUNT(DISTINCT steam_id) FROM players").fetchone()
        print(f"  Unique players: {unique_players[0]}")
        
        # Date range
        date_range = conn.execute("SELECT MIN(created_at), MAX(created_at) FROM demo_ticks").fetchone()
        if date_range[0]:
            print(f"  Data range: {date_range[0]} to {date_range[1]}")
        
        # Top weapons by usage
        print("\n--- TOP 5 WEAPONS BY USAGE ---")
        weapons = conn.execute("""
            SELECT active_weapon, COUNT(*) as usage_count 
            FROM demo_ticks 
            WHERE active_weapon IS NOT NULL AND active_weapon != ''
            GROUP BY active_weapon 
            ORDER BY usage_count DESC 
            LIMIT 5
        """).fetchall()
        for weapon, count in weapons:
            print(f"  {weapon}: {count:,} times")
    
    conn.close()

if __name__ == "__main__":
    inspect_database()
