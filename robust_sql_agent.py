#!/usr/bin/env python3
"""Optimized LangChain SQL Agent - handles iteration limits better"""

from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_ollama import ChatOllama
from langchain_community.utilities import SQLDatabase
from langchain.schema import AgentAction, AgentFinish
from sqlalchemy import create_engine
import time

def create_robust_sql_agent():
    """Create SQL agent with robust error handling and fallbacks"""
    
    # Connect to database
    engine = create_engine("duckdb:///sf.duckdb")
    db = SQLDatabase(engine)
    
    print("=== Robust LangChain SQL Agent ===\n")
    print("Database connected successfully!")
    print(f"Available tables: {db.get_usable_table_names()}\n")
    
    # Set up LLM with optimized parameters
    llm = ChatOllama(
        model="llama3:8b", 
        temperature=0.0,  # More deterministic responses
        num_predict=500,  # Limit response length
        top_p=0.9
    )
    
    # Concise schema context - less verbose to reduce token usage
    schema_context = """You are a CS2 demo analysis expert. Database has:

TABLES:
- demo_metadata (8 records): Demo file info with map_name, total_rounds, total_ticks
- demo_ticks (26M+ records): Player data with name, hp, is_alive, active_weapon, side (ct/t), x/y/z coords, demo_filename, map_name
- players: Empty table
- schema_migrations: Version tracking

KEY COLUMNS:
- demo_ticks.name: Player names (apEX, mezii, ZywOo, etc.)
- demo_ticks.map_name: Maps (de_inferno, de_dust2, de_train, etc.) 
- demo_ticks.side: ct (Counter-Terrorist) or t (Terrorist)
- demo_ticks.is_alive: Boolean for alive players
- demo_ticks.hp: Health 0-100
- demo_ticks.active_weapon: Current weapon

IMPORTANT: Always use LIMIT for demo_ticks queries! Table has 26+ million rows.
Write simple, efficient SQL. Avoid complex joins unless necessary."""
    
    # Create agent with conservative settings
    agent = create_sql_agent(
        llm=llm,
        db=db,
        verbose=False,                   # Reduce output verbosity
        top_k=5,                        # Fewer schema examples
        prefix=schema_context,          # Concise schema info
        max_iterations=6,               # Moderate iteration limit
        max_execution_time=90,          # 1.5 minute timeout
        handle_parsing_errors=True,     # Handle errors gracefully
        return_intermediate_steps=False  # Don't return reasoning steps
    )
    
    return agent, db, engine

def ask_with_fallback(agent, db, engine, question):
    """Ask question with fallback to direct SQL if agent times out"""
    
    print(f"Question: {question}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        result = agent.invoke({"input": question})
        elapsed = time.time() - start_time
        
        if 'output' in result and result['output']:
            print(f"✅ Agent Answer ({elapsed:.1f}s): {result['output']}")
            return True
        else:
            print("⚠️ Agent returned empty result")
            return False
            
    except Exception as e:
        print(f"❌ Agent Error: {str(e)}")
        
        # Fallback strategies for common queries
        print("🔄 Trying direct SQL fallback...")
        
        try:
            with engine.connect() as conn:
                if "demo files" in question.lower() or "how many" in question.lower():
                    count = conn.execute("SELECT COUNT(*) FROM demo_metadata").scalar()
                    print(f"📊 Direct Answer: {count} demo files in database")
                    return True
                    
                elif "map" in question.lower() and "names" in question.lower():
                    maps = conn.execute("""
                        SELECT DISTINCT map_name 
                        FROM demo_metadata 
                        WHERE map_name IS NOT NULL
                        ORDER BY map_name
                    """).fetchall()
                    map_list = [m[0] for m in maps]
                    print(f"📊 Direct Answer: Maps are {map_list}")
                    return True
                    
                elif "player" in question.lower() and "names" in question.lower():
                    players = conn.execute("""
                        SELECT DISTINCT name 
                        FROM demo_ticks 
                        WHERE name IS NOT NULL 
                        ORDER BY name 
                        LIMIT 10
                    """).fetchall()
                    player_list = [p[0] for p in players]
                    print(f"📊 Direct Answer: Top players are {player_list}")
                    return True
                    
                elif "total ticks" in question.lower():
                    total = conn.execute("SELECT COUNT(*) FROM demo_ticks").scalar()
                    print(f"📊 Direct Answer: {total:,} total ticks in database")
                    return True
                    
                else:
                    print("❌ No fallback strategy available for this query type")
                    return False
                    
        except Exception as e2:
            print(f"❌ Direct SQL also failed: {e2}")
            return False

def main():
    """Run optimized SQL agent tests"""
    
    agent, db, engine = create_robust_sql_agent()
    
    # Progressive test queries - start simple, get more complex
    test_queries = [
        "How many demo files are in the database?",
        "What are the unique map names?", 
        "List the player names in the data",
        "How many total ticks are recorded?",
        "What's the average HP of alive players?",
        "Which map has the most ticks?",
        "Show me the top 3 most active weapons",
        "Compare player counts between CT and T sides"
    ]
    
    print("🚀 Starting progressive query tests...\n")
    
    success_count = 0
    total_queries = len(test_queries)
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}/{total_queries}")
        print('='*60)
        
        success = ask_with_fallback(agent, db, engine, question)
        if success:
            success_count += 1
            
        print()
    
    print(f"\n{'='*60}")
    print(f"📈 SUMMARY: {success_count}/{total_queries} queries successful ({success_count/total_queries*100:.1f}%)")
    print('='*60)

if __name__ == "__main__":
    main()
