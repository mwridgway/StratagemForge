"""
Example script showing how to use the DuckDB connector for CS:GO data analysis.
This script demonstrates various analytical queries that can be used with LLMs.
"""

from duckdb_connector import CSGODataAnalyzer
import pandas as pd

def demonstrate_analysis():
    """Demonstrate various analysis capabilities."""
    
    # Initialize the analyzer
    print("🔗 Connecting to CS:GO data...")
    analyzer = CSGODataAnalyzer()
    
    print("\n📊 Running analytical queries...\n")
    
    # 1. Player performance across maps
    print("1️⃣ Player Activity Across Maps")
    print("=" * 50)
    query = """
    SELECT 
        name,
        COUNT(DISTINCT demo_name) as maps_played,
        COUNT(*) as total_ticks,
        AVG(X) as avg_x_position,
        AVG(Y) as avg_y_position,
        AVG(Z) as avg_z_position
    FROM all_player_ticks 
    WHERE name IS NOT NULL
    GROUP BY name 
    ORDER BY total_ticks DESC
    """
    result = analyzer.query(query)
    print(result)
    
    # 2. Team comparison
    print("\n\n2️⃣ Team Performance Comparison")
    print("=" * 50)
    query = """
    SELECT 
        demo_name,
        m_iTeamNum as team,
        COUNT(DISTINCT name) as players,
        COUNT(*) as total_ticks,
        AVG(X) as avg_x,
        AVG(Y) as avg_y,
        ROUND(AVG(Z), 2) as avg_height
    FROM all_player_ticks 
    WHERE m_iTeamNum IN (2, 3)
    GROUP BY demo_name, m_iTeamNum
    ORDER BY demo_name, team
    """
    result = analyzer.query(query)
    print(result)
    
    # 3. Grenade usage patterns
    print("\n\n3️⃣ Grenade Usage by Type and Map")
    print("=" * 50)
    query = """
    SELECT 
        demo_name,
        grenade_type,
        COUNT(DISTINCT name) as unique_users,
        COUNT(DISTINCT tick) as unique_throws,
        COUNT(*) as total_grenade_ticks
    FROM all_grenades 
    WHERE name IS NOT NULL
    GROUP BY demo_name, grenade_type
    ORDER BY demo_name, total_grenade_ticks DESC
    """
    result = analyzer.query(query)
    print(result)
    
    # 4. Player equipment analysis
    print("\n\n4️⃣ Player Skin Collections")
    print("=" * 50)
    query = """
    SELECT 
        pi.name,
        COUNT(s.item_id) as total_skins,
        ROUND(AVG(s.paint_wear), 6) as avg_wear,
        COUNT(CASE WHEN s.custom_name IS NOT NULL THEN 1 END) as custom_named_items
    FROM all_player_info pi
    JOIN all_skins s ON pi.steamid = s.steamid
    GROUP BY pi.name
    ORDER BY total_skins DESC
    """
    result = analyzer.query(query)
    print(result)
    
    # 5. Map-specific positioning analysis
    print("\n\n5️⃣ Average Player Positions by Map")
    print("=" * 50)
    query = """
    SELECT 
        demo_name,
        name,
        ROUND(AVG(X), 1) as avg_x,
        ROUND(AVG(Y), 1) as avg_y,
        ROUND(AVG(Z), 1) as avg_z,
        COUNT(*) as position_samples
    FROM all_player_ticks 
    WHERE name IS NOT NULL
    GROUP BY demo_name, name
    ORDER BY demo_name, position_samples DESC
    """
    result = analyzer.query(query)
    print(result.head(15))  # Show top 15 for brevity
    
    return analyzer

def show_llm_friendly_queries():
    """Show example queries that are perfect for LLM analysis."""
    
    print("\n\n🤖 LLM-Friendly Analysis Queries")
    print("=" * 60)
    
    queries = {
        "Player Movement Heatmap Data": """
        SELECT demo_name, name, X, Y, Z, tick
        FROM all_player_ticks 
        WHERE name = 'ZywOo' 
        AND demo_name = 'falcons-vs-vitality-m1-inferno'
        ORDER BY tick
        """,
        
        "Grenade Timing Analysis": """
        SELECT demo_name, name, grenade_type, tick, x, y, z
        FROM all_grenades 
        WHERE x IS NOT NULL AND y IS NOT NULL AND z IS NOT NULL
        ORDER BY demo_name, tick
        """,
        
        "Team Coordination Patterns": """
        SELECT 
            demo_name, 
            tick,
            COUNT(CASE WHEN m_iTeamNum = 2 THEN 1 END) as team2_players,
            COUNT(CASE WHEN m_iTeamNum = 3 THEN 1 END) as team3_players,
            AVG(CASE WHEN m_iTeamNum = 2 THEN X END) as team2_avg_x,
            AVG(CASE WHEN m_iTeamNum = 3 THEN X END) as team3_avg_x
        FROM all_player_ticks
        WHERE m_iTeamNum IN (2, 3) AND tick % 100 = 0
        GROUP BY demo_name, tick
        ORDER BY demo_name, tick
        """,
        
        "Player Performance Metrics": """
        SELECT 
            name,
            demo_name,
            COUNT(*) as total_ticks,
            MAX(tick) - MIN(tick) as match_duration_ticks,
            COUNT(DISTINCT CASE WHEN X IS NOT NULL THEN CONCAT(ROUND(X/100), ',', ROUND(Y/100)) END) as unique_positions
        FROM all_player_ticks
        GROUP BY name, demo_name
        ORDER BY total_ticks DESC
        """
    }
    
    for title, query in queries.items():
        print(f"\n📈 {title}")
        print("-" * 40)
        print(query.strip())

def save_sample_data_for_llm():
    """Save sample datasets that an LLM can analyze."""
    print("\n\n💾 Saving sample datasets for LLM analysis...")
    
    analyzer = CSGODataAnalyzer()
    
    # Save player summary
    player_summary = analyzer.query("""
    SELECT 
        name,
        COUNT(DISTINCT demo_name) as maps_played,
        COUNT(*) as total_ticks,
        ROUND(AVG(X), 2) as avg_x,
        ROUND(AVG(Y), 2) as avg_y,
        ROUND(AVG(Z), 2) as avg_z
    FROM all_player_ticks 
    WHERE name IS NOT NULL
    GROUP BY name 
    ORDER BY total_ticks DESC
    """)
    player_summary.to_csv("player_summary.csv", index=False)
    print("✅ Saved player_summary.csv")
    
    # Save grenade summary
    grenade_summary = analyzer.query("""
    SELECT 
        demo_name,
        name,
        grenade_type,
        COUNT(*) as usage_count,
        COUNT(DISTINCT tick) as unique_uses
    FROM all_grenades 
    WHERE name IS NOT NULL
    GROUP BY demo_name, name, grenade_type
    ORDER BY usage_count DESC
    """)
    grenade_summary.to_csv("grenade_summary.csv", index=False)
    print("✅ Saved grenade_summary.csv")
    
    # Save map performance
    map_performance = analyzer.query("""
    SELECT 
        demo_name,
        COUNT(DISTINCT name) as unique_players,
        COUNT(*) as total_player_ticks,
        MAX(tick) as max_tick,
        ROUND(AVG(X), 2) as avg_x,
        ROUND(AVG(Y), 2) as avg_y
    FROM all_player_ticks
    GROUP BY demo_name
    ORDER BY total_player_ticks DESC
    """)
    map_performance.to_csv("map_performance.csv", index=False)
    print("✅ Saved map_performance.csv")
    
    print("\n📋 Files ready for LLM analysis:")
    print("   • player_summary.csv - Player performance across all maps")
    print("   • grenade_summary.csv - Grenade usage patterns")
    print("   • map_performance.csv - Map-level statistics")

if __name__ == "__main__":
    # Run the demonstration
    analyzer = demonstrate_analysis()
    
    # Show LLM-friendly queries
    show_llm_friendly_queries()
    
    # Save sample data
    save_sample_data_for_llm()
    
    print(f"\n\n🎯 Ready for LLM Analysis!")
    print("You can now use the DuckDB connection to query the CS:GO data:")
    print("```python")
    print("from duckdb_connector import CSGODataAnalyzer")
    print("analyzer = CSGODataAnalyzer()")
    print("result = analyzer.query('YOUR_SQL_HERE')")
    print("print(result)")
    print("```")
    
    # Keep connection open for interactive use
    print("\n📡 Database connection is ready for interactive queries!")
    
    # Close the connection when done
    analyzer.close()
