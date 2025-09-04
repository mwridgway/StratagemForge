"""
Interactive CS:GO Data Analysis Script
Perfect for use with LLMs for data exploration and analysis.
"""

from duckdb_connector import CSGODataAnalyzer
import pandas as pd
import sys

def interactive_query_session():
    """Start an interactive query session."""
    
    print("🎮 CS:GO Demo Data Analysis - Interactive Mode")
    print("=" * 55)
    print("Loading data...")
    
    try:
        analyzer = CSGODataAnalyzer()
        print("✅ Connected to CS:GO demo data successfully!")
        
        # Show available data summary
        print(f"\n📊 Available Data:")
        summary = analyzer.get_demo_summary()
        print(summary)
        
        print(f"\n🔍 Available Views:")
        print("• all_player_ticks - Player movement and positioning")
        print("• all_grenades - Grenade usage and trajectories") 
        print("• all_player_info - Player and team information")
        print("• all_skins - Weapon skin collections")
        
        print(f"\n💡 Sample Queries:")
        sample_queries = analyzer.get_sample_queries()
        for i, query in enumerate(sample_queries[:3], 1):
            print(f"{i}. {query.split('--')[1].split('SELECT')[0].strip()}")
        
        print(f"\n" + "="*55)
        print("🤖 Ready for LLM Analysis!")
        print("You can now ask questions about the CS:GO data.")
        print("Example: 'Show me player performance across all maps'")
        print("="*55)
        
        return analyzer
        
    except Exception as e:
        print(f"❌ Error connecting to data: {str(e)}")
        return None

def run_quick_analysis(analyzer):
    """Run some quick analysis examples."""
    
    print("\n🔬 Quick Analysis Examples:")
    print("-" * 30)
    
    # 1. Player summary
    print("\n1. Top Players by Activity:")
    result = analyzer.query("""
    SELECT name, 
           COUNT(DISTINCT demo_name) as maps_played,
           COUNT(*) as total_ticks,
           ROUND(AVG(X), 1) as avg_x,
           ROUND(AVG(Y), 1) as avg_y
    FROM all_player_ticks 
    WHERE name IS NOT NULL
    GROUP BY name 
    ORDER BY total_ticks DESC
    LIMIT 10
    """)
    print(result.to_string(index=False))
    
    # 2. Map activity
    print("\n\n2. Map Activity Summary:")
    result = analyzer.query("""
    SELECT demo_name,
           COUNT(DISTINCT name) as players,
           COUNT(*) as total_ticks,
           MAX(tick) as max_tick
    FROM all_player_ticks
    GROUP BY demo_name
    ORDER BY total_ticks DESC
    """)
    print(result.to_string(index=False))
    
    # 3. Grenade usage
    print("\n\n3. Top Grenade Users:")
    result = analyzer.query("""
    SELECT name, 
           COUNT(DISTINCT demo_name) as maps,
           COUNT(DISTINCT tick) as unique_throws,
           COUNT(*) as total_grenade_ticks
    FROM all_grenades 
    WHERE name IS NOT NULL
    GROUP BY name
    ORDER BY unique_throws DESC
    LIMIT 10
    """)
    print(result.to_string(index=False))

def get_custom_query():
    """Get and execute a custom query from user."""
    
    print("\n📝 Enter your SQL query (or 'help' for examples, 'quit' to exit):")
    
    while True:
        query = input("\nSQL> ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        elif query.lower() == 'help':
            show_help()
            continue
        elif not query:
            continue
            
        try:
            analyzer = CSGODataAnalyzer()
            result = analyzer.query(query)
            print(f"\n📊 Results ({len(result)} rows):")
            print(result.to_string(index=False))
            analyzer.close()
        except Exception as e:
            print(f"❌ Query error: {str(e)}")

def show_help():
    """Show help examples."""
    
    examples = [
        "SELECT name, COUNT(*) FROM all_player_info GROUP BY name",
        "SELECT demo_name, COUNT(DISTINCT name) FROM all_player_ticks GROUP BY demo_name",
        "SELECT grenade_type, COUNT(*) FROM all_grenades GROUP BY grenade_type",
        "SELECT name, AVG(X), AVG(Y) FROM all_player_ticks GROUP BY name"
    ]
    
    print("\n💡 Example queries:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")

def main():
    """Main function."""
    
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        # Interactive mode for custom queries
        get_custom_query()
    else:
        # Standard analysis mode
        analyzer = interactive_query_session()
        if analyzer:
            run_quick_analysis(analyzer)
            analyzer.close()
            
            print(f"\n\n🎯 Analysis Complete!")
            print(f"For interactive queries, run: python interactive_analysis.py --interactive")

if __name__ == "__main__":
    main()
