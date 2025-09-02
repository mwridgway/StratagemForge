#!/usr/bin/env python3
"""Enhanced LangChain SQL Agent with comprehensive schema information"""

from langchain_ollama import ChatOllama
from langchain.agents import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_types import AgentType
from sqlalchemy import create_engine

def create_enhanced_sql_agent():
    """Create SQL agent with comprehensive schema information"""
    
    # Connect to database
    engine = create_engine("duckdb:///sf.duckdb")
    db = SQLDatabase(engine)
    
    # Get actual schema information
    table_info = db.get_table_info()
    
    # Enhanced system prompt with schema context
    system_prompt = f"""You are a SQL expert working with Counter-Strike 2 demo analysis data.

DATABASE SCHEMA:
{table_info}

IMPORTANT CONTEXT:
- This is CS2 professional match data with tick-by-tick player information
- demo_ticks is the main analysis table with 26+ million records
- Each tick represents a moment in time during gameplay
- Players can be on 'ct' (Counter-Terrorist) or 't' (Terrorist) sides
- Common weapons: AK-47, M4A4, AWP, Glock-18, USP-S, etc.
- Maps use standard CS2 naming: de_inferno, de_dust2, de_train, etc.

QUERY GUIDELINES:
- Use LIMIT for large result sets to avoid timeouts
- Aggregate data when possible (COUNT, AVG, SUM, GROUP BY)
- Filter NULL values when analyzing specific attributes
- Use meaningful aliases for calculated columns
- Consider performance with the large demo_ticks table

COMMON PATTERNS:
- Player analysis: GROUP BY name, steam_id
- Map comparison: GROUP BY map_name  
- Weapon usage: GROUP BY active_weapon WHERE active_weapon IS NOT NULL
- Team performance: GROUP BY side, team
- Round analysis: GROUP BY round_num, demo_filename
- Time-based: Use seconds, tick for temporal analysis

When writing SQL:
1. Always use appropriate WHERE clauses to filter meaningful data
2. Use LIMIT to control result size
3. Add helpful column aliases
4. Consider NULL values in your conditions
"""

    # Create LLM with system context
    llm = ChatOllama(
        model="llama3:8b", 
        temperature=0.1,
        system=system_prompt
    )
    
    # Create agent with specific table inclusion
    agent = create_sql_agent(
        llm=llm,
        db=db,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        top_k=15,  # Show more examples in schema
        include_tables=['demo_metadata', 'demo_ticks'],  # Focus on main tables
        max_iterations=5,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )
    
    return agent, db

def run_intelligent_queries():
    """Run queries that demonstrate schema understanding"""
    
    agent, db = create_enhanced_sql_agent()
    
    print("=== Enhanced SQL Agent with Schema Knowledge ===\n")
    print(f"Connected to database with tables: {db.get_usable_table_names()}\n")
    
    # Strategic queries that test different aspects
    strategic_queries = [
        {
            "query": "What professional teams and players are represented in this data?",
            "focus": "Player identification and team structure"
        },
        {
            "query": "Compare weapon preferences between Counter-Terrorist and Terrorist sides",
            "focus": "Weapon usage analysis by team side"
        },
        {
            "query": "Show me the most intense rounds by finding rounds with the most player deaths (HP dropping to 0)",
            "focus": "Complex aggregation with health analysis"
        },
        {
            "query": "What's the economic state analysis - show average money by team side and round number",
            "focus": "Economic analysis with grouping"
        },
        {
            "query": "Find the most active areas of each map by analyzing player position density",
            "focus": "Spatial analysis using coordinates"
        }
    ]
    
    for i, query_info in enumerate(strategic_queries, 1):
        print(f"\n{'='*80}")
        print(f"STRATEGIC QUERY {i}: {query_info['focus']}")
        print(f"Question: {query_info['query']}")
        print('='*80)
        
        try:
            result = agent.invoke({"input": query_info['query']})
            print(f"\nFinal Answer: {result['output']}")
            
            # Show intermediate steps if available
            if 'intermediate_steps' in result:
                print(f"\nReasoning Steps: {len(result['intermediate_steps'])} steps")
                
        except Exception as e:
            print(f"Error: {e}")
            print("This might be due to query complexity or data structure")
        
        print(f"\n{'='*80}\n")

if __name__ == "__main__":
    run_intelligent_queries()
