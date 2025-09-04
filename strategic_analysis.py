"""
CS2 Strategic Analysis Queries
Comprehensive analysis questions for team preparation and anti-stratting
"""

from duckdb_connector import CSGODataAnalyzer
import pandas as pd

class CS2StrategicAnalyzer:
    """Strategic analysis tools for CS2 demo data."""
    
    def __init__(self):
        self.analyzer = CSGODataAnalyzer()
        
    def map_control_analysis(self):
        """Analyze which areas each team controls most effectively."""
        queries = {
            "Territory Control by Team": """
            SELECT 
                demo_name,
                m_iTeamNum as team,
                COUNT(*) as position_samples,
                ROUND(AVG(X), 1) as avg_x_control,
                ROUND(AVG(Y), 1) as avg_y_control,
                ROUND(STDDEV(X), 1) as x_spread,
                ROUND(STDDEV(Y), 1) as y_spread
            FROM all_player_ticks 
            WHERE m_iTeamNum IN (2, 3)
            GROUP BY demo_name, m_iTeamNum
            ORDER BY demo_name, team
            """,
            
            "Most Contested Areas (High Variance Zones)": """
            SELECT 
                demo_name,
                ROUND(X/200)*200 as x_zone,
                ROUND(Y/200)*200 as y_zone,
                COUNT(DISTINCT m_iTeamNum) as teams_present,
                COUNT(DISTINCT name) as unique_players,
                COUNT(*) as total_presence
            FROM all_player_ticks
            WHERE m_iTeamNum IN (2, 3)
            GROUP BY demo_name, x_zone, y_zone
            HAVING teams_present > 1
            ORDER BY total_presence DESC
            LIMIT 20
            """
        }
        return queries
    
    def player_role_analysis(self):
        """Analyze player roles and positioning patterns."""
        queries = {
            "Player Positioning Preferences": """
            SELECT 
                name,
                demo_name,
                ROUND(AVG(X), 1) as avg_x_position,
                ROUND(AVG(Y), 1) as avg_y_position,
                ROUND(AVG(Z), 1) as avg_height,
                ROUND(STDDEV(X), 1) as x_variance,
                ROUND(STDDEV(Y), 1) as y_variance,
                COUNT(*) as position_samples
            FROM all_player_ticks
            WHERE name IS NOT NULL
            GROUP BY name, demo_name
            ORDER BY x_variance DESC
            """,
            
            "Most Mobile Players (High Movement Variance)": """
            SELECT 
                name,
                ROUND(AVG(STDDEV(X)), 1) as avg_x_mobility,
                ROUND(AVG(STDDEV(Y)), 1) as avg_y_mobility,
                COUNT(DISTINCT demo_name) as maps_played,
                SUM(COUNT(*)) as total_positions
            FROM all_player_ticks
            WHERE name IS NOT NULL
            GROUP BY name, demo_name
            GROUP BY name
            ORDER BY avg_x_mobility + avg_y_mobility DESC
            """
        }
        return queries
    
    def utility_coordination_analysis(self):
        """Analyze grenade usage patterns for tactical insights."""
        queries = {
            "Grenade Usage by Situation": """
            SELECT 
                demo_name,
                name,
                grenade_type,
                COUNT(DISTINCT tick) as unique_throws,
                ROUND(AVG(x), 1) as avg_throw_x,
                ROUND(AVG(y), 1) as avg_throw_y,
                COUNT(*) as total_grenade_ticks
            FROM all_grenades
            WHERE x IS NOT NULL AND y IS NOT NULL
            GROUP BY demo_name, name, grenade_type
            ORDER BY unique_throws DESC
            """,
            
            "Team Utility Coordination": """
            SELECT 
                g1.demo_name,
                g1.tick,
                g1.name as player1,
                g2.name as player2,
                g1.grenade_type as nade1_type,
                g2.grenade_type as nade2_type,
                ABS(g1.tick - g2.tick) as tick_difference
            FROM all_grenades g1
            JOIN all_grenades g2 ON g1.demo_name = g2.demo_name
            WHERE g1.name != g2.name
            AND ABS(g1.tick - g2.tick) <= 32  -- Within ~1 second
            AND g1.tick < g2.tick
            ORDER BY g1.demo_name, g1.tick
            LIMIT 100
            """,
            
            "Most Effective Utility Spots": """
            SELECT 
                demo_name,
                grenade_type,
                ROUND(x/100)*100 as throw_zone_x,
                ROUND(y/100)*100 as throw_zone_y,
                COUNT(DISTINCT name) as different_players,
                COUNT(DISTINCT tick) as unique_throws
            FROM all_grenades
            WHERE x IS NOT NULL AND y IS NOT NULL
            GROUP BY demo_name, grenade_type, throw_zone_x, throw_zone_y
            HAVING unique_throws >= 5
            ORDER BY unique_throws DESC
            LIMIT 30
            """
        }
        return queries
    
    def team_coordination_analysis(self):
        """Analyze team movement and coordination patterns."""
        queries = {
            "Team Grouping Patterns": """
            SELECT 
                demo_name,
                tick,
                m_iTeamNum as team,
                COUNT(*) as players_active,
                ROUND(AVG(X), 1) as team_center_x,
                ROUND(AVG(Y), 1) as team_center_y,
                ROUND(STDDEV(X), 1) as team_spread_x,
                ROUND(STDDEV(Y), 1) as team_spread_y
            FROM all_player_ticks
            WHERE m_iTeamNum IN (2, 3) AND tick % 64 = 0  -- Sample every ~2 seconds
            GROUP BY demo_name, tick, m_iTeamNum
            HAVING players_active >= 3
            ORDER BY demo_name, tick
            """,
            
            "Player Proximity Analysis": """
            WITH player_distances AS (
                SELECT 
                    p1.demo_name,
                    p1.tick,
                    p1.name as player1,
                    p2.name as player2,
                    p1.m_iTeamNum,
                    SQRT(POWER(p1.X - p2.X, 2) + POWER(p1.Y - p2.Y, 2)) as distance
                FROM all_player_ticks p1
                JOIN all_player_ticks p2 ON p1.demo_name = p2.demo_name 
                    AND p1.tick = p2.tick 
                    AND p1.m_iTeamNum = p2.m_iTeamNum
                WHERE p1.name < p2.name  -- Avoid duplicates
                AND p1.tick % 128 = 0  -- Sample every ~4 seconds
            )
            SELECT 
                player1,
                player2,
                COUNT(*) as time_samples,
                ROUND(AVG(distance), 1) as avg_distance,
                ROUND(MIN(distance), 1) as min_distance,
                COUNT(CASE WHEN distance <= 500 THEN 1 END) as close_proximity_count
            FROM player_distances
            GROUP BY player1, player2
            ORDER BY avg_distance ASC
            LIMIT 30
            """
        }
        return queries
    
    def timing_and_flow_analysis(self):
        """Analyze round timing and flow patterns."""
        queries = {
            "Round Duration Analysis": """
            SELECT 
                demo_name,
                MAX(tick) - MIN(tick) as round_duration_ticks,
                ROUND((MAX(tick) - MIN(tick)) / 128.0, 1) as round_duration_seconds,
                COUNT(DISTINCT name) as players_active,
                COUNT(*) as total_actions
            FROM all_player_ticks
            GROUP BY demo_name
            ORDER BY round_duration_seconds DESC
            """,
            
            "Peak Activity Periods": """
            SELECT 
                demo_name,
                FLOOR(tick / 1280) * 10 as time_window_seconds,  -- 10-second windows
                COUNT(*) as player_actions,
                COUNT(DISTINCT name) as active_players,
                ROUND(AVG(X), 1) as avg_action_x,
                ROUND(AVG(Y), 1) as avg_action_y
            FROM all_player_ticks
            GROUP BY demo_name, time_window_seconds
            ORDER BY demo_name, time_window_seconds
            """,
            
            "Grenade Timing Patterns": """
            SELECT 
                demo_name,
                FLOOR(tick / 1280) * 10 as time_window_seconds,
                COUNT(DISTINCT tick) as grenade_throws,
                COUNT(DISTINCT name) as throwers,
                grenade_type
            FROM all_grenades
            GROUP BY demo_name, time_window_seconds, grenade_type
            HAVING grenade_throws >= 2
            ORDER BY demo_name, time_window_seconds, grenade_throws DESC
            """
        }
        return queries
    
    def anti_stratting_analysis(self):
        """Find predictable patterns for counter-strategies."""
        queries = {
            "Predictable Player Positions": """
            SELECT 
                name,
                demo_name,
                ROUND(X/300)*300 as position_zone_x,
                ROUND(Y/300)*300 as position_zone_y,
                COUNT(*) as time_in_zone,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY name, demo_name), 1) as zone_percentage
            FROM all_player_ticks
            WHERE name IS NOT NULL
            GROUP BY name, demo_name, position_zone_x, position_zone_y
            HAVING time_in_zone >= 100
            ORDER BY name, demo_name, zone_percentage DESC
            """,
            
            "Repetitive Utility Usage": """
            SELECT 
                name,
                demo_name,
                grenade_type,
                ROUND(x/200)*200 as throw_zone_x,
                ROUND(y/200)*200 as throw_zone_y,
                COUNT(DISTINCT tick) as repeated_throws
            FROM all_grenades
            WHERE x IS NOT NULL AND y IS NOT NULL
            GROUP BY name, demo_name, grenade_type, throw_zone_x, throw_zone_y
            HAVING repeated_throws >= 3
            ORDER BY repeated_throws DESC
            """,
            
            "Team Formation Patterns": """
            WITH team_formations AS (
                SELECT 
                    demo_name,
                    tick,
                    m_iTeamNum,
                    STRING_AGG(name ORDER BY X) as formation_pattern
                FROM all_player_ticks
                WHERE m_iTeamNum IN (2, 3) AND tick % 256 = 0  -- Sample every ~8 seconds
                GROUP BY demo_name, tick, m_iTeamNum
                HAVING COUNT(*) >= 4
            )
            SELECT 
                demo_name,
                m_iTeamNum as team,
                formation_pattern,
                COUNT(*) as pattern_frequency
            FROM team_formations
            GROUP BY demo_name, m_iTeamNum, formation_pattern
            HAVING pattern_frequency >= 2
            ORDER BY pattern_frequency DESC
            LIMIT 20
            """
        }
        return queries
    
    def run_strategic_analysis(self, analysis_type="all"):
        """Run comprehensive strategic analysis."""
        
        analyses = {
            "map_control": self.map_control_analysis(),
            "player_roles": self.player_role_analysis(),
            "utility": self.utility_coordination_analysis(),
            "coordination": self.team_coordination_analysis(),
            "timing": self.timing_and_flow_analysis(),
            "anti_strat": self.anti_stratting_analysis()
        }
        
        if analysis_type != "all":
            analyses = {analysis_type: analyses.get(analysis_type, {})}
        
        results = {}
        for analysis_name, queries in analyses.items():
            print(f"\n{'='*60}")
            print(f"🎯 {analysis_name.upper().replace('_', ' ')} ANALYSIS")
            print(f"{'='*60}")
            
            analysis_results = {}
            for query_name, query in queries.items():
                try:
                    print(f"\n📊 {query_name}")
                    print("-" * 50)
                    result = self.analyzer.query(query)
                    print(result.head(10).to_string(index=False))
                    analysis_results[query_name] = result
                except Exception as e:
                    print(f"❌ Error in {query_name}: {str(e)}")
            
            results[analysis_name] = analysis_results
        
        return results
    
    def close(self):
        """Close the database connection."""
        self.analyzer.close()

def main():
    """Run strategic analysis demonstration."""
    
    print("🔍 CS2 STRATEGIC ANALYSIS")
    print("=" * 60)
    print("This analysis helps with team preparation and anti-stratting")
    
    analyzer = CS2StrategicAnalyzer()
    
    # Run specific analysis types
    print("\n🎯 Select analysis type:")
    print("1. Map Control & Territory")
    print("2. Player Roles & Positioning") 
    print("3. Utility Coordination")
    print("4. Team Coordination")
    print("5. Timing & Flow")
    print("6. Anti-Stratting Patterns")
    print("7. All Analyses")
    
    try:
        choice = input("\nEnter choice (1-7) or press Enter for all: ").strip()
        
        analysis_map = {
            "1": "map_control",
            "2": "player_roles", 
            "3": "utility",
            "4": "coordination",
            "5": "timing",
            "6": "anti_strat",
            "7": "all",
            "": "all"
        }
        
        analysis_type = analysis_map.get(choice, "all")
        results = analyzer.run_strategic_analysis(analysis_type)
        
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    finally:
        analyzer.close()
        print(f"\n✅ Strategic analysis complete!")

if __name__ == "__main__":
    main()
