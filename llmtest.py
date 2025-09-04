# Working LangChain SQL Agent with DuckDB
from langchain_community.agent_toolkits.sql.base import create_sql_agent  # Updated import
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from sqlalchemy import create_engine

# Connect to your DuckDB file
engine = create_engine("duckdb:///sf.duckdb")
db = SQLDatabase(engine)

print("=== LangChain SQL Agent Test ===\n")

print("Database connected successfully!")
print(f"Available tables: {db.get_usable_table_names()}")
print()

# Set up LLM (make sure Ollama is running with llama3:8b model)
try:
    llm = ChatOllama(model="llama3:8b", temperature=0.1)
    print("LLM connected successfully!")
except Exception as e:
    print(f"Error connecting to LLM: {e}")
    print("Make sure Ollama is running and llama3:8b model is available")
    exit(1)

# Provide detailed schema context to the LLM
schema_context = """
You are working with a Counter-Strike 2 (CS2) demo analysis database with the following structure:

## Tables Overview:
- **demo_metadata**: Information about each demo file (8 records)
- **demo_ticks**: Main data table with tick-by-tick player information (26+ million records)  
- **players**: Player lookup table (currently empty)
- **schema_migrations**: Database version tracking

## Key Table: demo_ticks (Primary analysis table)
This table contains detailed tick-by-tick game state information:

### Player Information:
- steam_id (BIGINT): Player's Steam ID
- name (VARCHAR): Player name (e.g., 'TeSeS', 'mezii', 'apEX')
- team (VARCHAR): Team affiliation
- side (VARCHAR): 'ct' (Counter-Terrorist) or 't' (Terrorist)

### Player Status:
- is_alive (BOOLEAN): Whether player is alive
- hp (INTEGER): Health points (0-100)
- armor (INTEGER): Armor value
- has_helmet (BOOLEAN): Has head armor
- has_defuse_kit (BOOLEAN): Has defuse kit (CT only)
- money (INTEGER): Player's money

### Position & Movement:
- x, y, z (DOUBLE): Player position coordinates
- view_x, view_y (DOUBLE): View direction
- velocity_x, velocity_y, velocity_z (DOUBLE): Movement velocity

### Weapons & Equipment:
- active_weapon (VARCHAR): Currently held weapon
- primary_weapon (VARCHAR): Primary weapon in inventory
- secondary_weapon (VARCHAR): Secondary weapon in inventory
- grenades (VARCHAR): Grenades in inventory

### Actions:
- is_ducking, is_walking, is_scoped, is_reloading (BOOLEAN)
- is_defusing, is_planting (BOOLEAN): Bomb-related actions

### Game Context:
- tick (INTEGER): Game tick number
- round_num (INTEGER): Round number
- seconds (DOUBLE): Time in seconds
- t_score, ct_score (INTEGER): Team scores
- bomb_planted, bomb_defused (BOOLEAN): Bomb status
- demo_filename (VARCHAR): Source demo file
- map_name (VARCHAR): Map name (e.g., 'de_inferno', 'de_dust2')

## demo_metadata Table:
- filename, file_path: Demo file information
- map_name: Map played
- total_rounds, total_ticks: Match statistics
- parsed_at, created_at: Processing timestamps

## Common Query Patterns:
- Player performance: GROUP BY name, steam_id
- Map analysis: GROUP BY map_name
- Round analysis: GROUP BY round_num, demo_filename
- Weapon usage: GROUP BY active_weapon, primary_weapon
- Team performance: GROUP BY side, team
- Time-based analysis: Use seconds, tick for temporal queries

## Data Notes:
- Data spans from August 26-27, 2025
- Professional CS2 matches (Vitality vs other teams)
- High-frequency data (multiple ticks per second)
- Some fields may be NULL in early ticks or specific game states

Always use LIMIT clauses for large result sets and handle NULL values appropriately.
"""

# Create SQL agent with optimized configuration
agent = create_sql_agent(
    llm=llm,
    db=db,
    verbose=False,                    # show reasoning and SQL
    top_k=15,                       # show more schema examples 
    prefix=schema_context,          # provide schema context upfront
    max_iterations=10,              # significantly increase iteration limit
    max_execution_time=120,         # increase timeout to 2 minutes
    handle_parsing_errors=True,     # graceful error handling
    early_stopping_method="generate" # stop when answer is generated
)

print("\n=== Testing SQL Agent ===\n")

# Simpler, more focused test queries to avoid timeouts
test_queries = [
    "How many demo files are in the database?",
    "List all the unique map names",
    "What are the player names in the data?",
    "Show total ticks per map",
    "What's the average HP of alive players?"
]

for i, question in enumerate(test_queries, 1):
    print(f"\n--- Query {i}: {question} ---")
    try:
        # Add timeout wrapper for individual queries
        result = agent.invoke({
            "input": question
        })
        if 'output' in result:
            print(f"Answer: {result['output']}")
        else:
            print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        # Try a simpler direct SQL approach if agent fails
        print("Attempting direct SQL query...")
        try:
            if "demo files" in question.lower():
                with engine.connect() as conn:
                    count = conn.execute("SELECT COUNT(*) FROM demo_metadata").scalar()
                    print(f"Direct answer: {count} demo files")
            elif "map names" in question.lower():
                with engine.connect() as conn:
                    maps = conn.execute("SELECT DISTINCT map_name FROM demo_metadata WHERE map_name IS NOT NULL").fetchall()
                    print(f"Direct answer: Maps are {[m[0] for m in maps]}")
        except Exception as e2:
            print(f"Direct SQL also failed: {e2}")
    print("-" * 60)
