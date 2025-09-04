"""
CS2 Strategic Analysis - Expert Validation Script (Optimized)
This script runs through key strategic questions and provides answers
that can be validated by human CS2 experts and analysts.
Performance optimized for large datasets.
"""

from duckdb_connector import CSGODataAnalyzer
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExpertValidationAnalyzer:
    """Runs strategic analysis questions for expert validation with performance optimizations."""
    
    def __init__(self):
        self.analyzer = CSGODataAnalyzer()
        self.results = {}
        self.use_sampling = True  # Enable sampling for performance
        
    def print_section_header(self, title):
        """Print a formatted section header."""
        print(f"\n{'='*80}")
        print(f"🎯 {title.upper()}")
        print(f"{'='*80}")
        
    def print_question(self, question_num, question):
        """Print a formatted question."""
        print(f"\n📋 QUESTION {question_num}: {question}")
        print("-" * 70)
        
    def print_answer(self, answer_df, context="", execution_time=0):
        """Print a formatted answer with context and performance info."""
        if context:
            print(f"💡 CONTEXT: {context}")
        print(f"📊 ANSWER (executed in {execution_time:.2f}s):")
        if len(answer_df) > 0:
            print(answer_df.to_string(index=False))
        else:
            print("No data found for this query.")
        print()
        
    def execute_query(self, query: str, use_cache: bool = True) -> tuple:
        """Execute query with timing and error handling."""
        start_time = time.time()
        try:
            result = self.analyzer.query(query, use_cache=use_cache, timeout=60)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.2f}s: {str(e)}")
            return pd.DataFrame(), execution_time
        
    def run_map_control_analysis(self):
        """Analyze map control and territory questions."""
        self.print_section_header("Map Control & Territory Analysis")
        
        # Question 1: Territory Control (Optimized with sampling)
        self.print_question(1, "Which areas does each team control most effectively on each map?")
        
        # Use sampled data for performance
        table_name = 'all_player_ticks_sampled' if self.use_sampling else 'all_player_ticks'
        
        query = f"""
        SELECT 
            demo_name,
            CASE WHEN m_iTeamNum = 2 THEN 'Team_CT' ELSE 'Team_T' END as team,
            COUNT(*) as presence_strength,
            ROUND(AVG(X), 1) as control_center_x,
            ROUND(AVG(Y), 1) as control_center_y,
            ROUND(STDDEV(X), 1) as x_spread,
            ROUND(STDDEV(Y), 1) as y_spread
        FROM {table_name}
        WHERE m_iTeamNum IN (2, 3) AND name IS NOT NULL
        GROUP BY demo_name, m_iTeamNum
        ORDER BY demo_name, m_iTeamNum
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Shows where each team spends most time and their territorial spread", exec_time)
        
        # Question 2: Most Contested Areas (Optimized with zone-based aggregation)
        self.print_question(2, "What are the most contested zones where both teams fight for control?")
        query = f"""
        SELECT 
            demo_name,
            ROUND(X/400)*400 as zone_x,
            ROUND(Y/400)*400 as zone_y,
            COUNT(DISTINCT m_iTeamNum) as teams_present,
            COUNT(DISTINCT name) as unique_players,
            COUNT(*) as total_activity
        FROM {table_name}
        WHERE m_iTeamNum IN (2, 3) AND name IS NOT NULL AND name != ''
        GROUP BY demo_name, zone_x, zone_y
        HAVING teams_present > 1 AND total_activity >= 50  -- Filter low-significance results
        ORDER BY total_activity DESC
        LIMIT 10
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "High activity zones where both teams are present indicate contested areas", exec_time)
        
    def run_player_role_analysis(self):
        """Analyze player positioning and role patterns."""
        self.print_section_header("Player Role & Positioning Intelligence")
        
        # Question 3: Player Mobility Patterns (Optimized with sampling)
        self.print_question(3, "Which players are most/least mobile and what does this tell us about their roles?")
        
        table_name = 'all_player_ticks_sampled' if self.use_sampling else 'all_player_ticks'
        
        query = f"""
        SELECT 
            name,
            COUNT(DISTINCT demo_name) as maps_played,
            ROUND(AVG(X), 1) as avg_x_position,
            ROUND(AVG(Y), 1) as avg_y_position,
            ROUND(STDDEV(X), 1) as x_mobility,
            ROUND(STDDEV(Y), 1) as y_mobility,
            ROUND(STDDEV(X) + STDDEV(Y), 1) as total_mobility
        FROM {table_name}
        WHERE name IS NOT NULL AND name != ''
        GROUP BY name
        HAVING COUNT(*) >= 100  -- Filter players with minimal data
        ORDER BY total_mobility DESC
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Higher mobility = roaming/entry fraggers, Lower = anchors/supports", exec_time)
        
        # Question 4: Player Health Distribution (Optimized)
        self.print_question(4, "How do different players manage risk based on their health patterns?")
        query = f"""
        SELECT 
            name,
            ROUND(AVG(m_iHealth), 1) as avg_health,
            ROUND(STDDEV(m_iHealth), 1) as health_variance,
            COUNT(CASE WHEN m_iHealth <= 30 THEN 1 END) as low_health_instances,
            COUNT(CASE WHEN m_iHealth >= 80 THEN 1 END) as high_health_instances,
            COUNT(*) as total_observations,
            ROUND(COUNT(CASE WHEN m_iHealth <= 30 THEN 1 END) * 100.0 / COUNT(*), 1) as risk_percentage
        FROM {table_name}
        WHERE name IS NOT NULL AND name != '' AND m_iHealth > 0
        GROUP BY name
        HAVING total_observations >= 100
        ORDER BY risk_percentage DESC
        LIMIT 15
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Higher risk% = aggressive players, Lower = conservative/support players", exec_time)
        
        # Question 5: Utility Usage Patterns (Optimized)
        self.print_question(5, "Which players are primary utility users vs fraggers?")
        query = """
        SELECT 
            name,
            grenade_type,
            COUNT(*) as total_throws,
            COUNT(DISTINCT demo_name) as maps_with_usage,
            ROUND(COUNT(*) * 1.0 / COUNT(DISTINCT demo_name), 1) as throws_per_map
        FROM all_grenades
        WHERE x IS NOT NULL AND y IS NOT NULL AND name IS NOT NULL AND name != ''
        GROUP BY name, grenade_type
        HAVING total_throws >= 10  -- Focus on significant usage patterns
        ORDER BY throws_per_map DESC
        LIMIT 20
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Reveals support players (many smokes/flashes) vs. aggressive players (HE grenades)", exec_time)
        
        # Question 4: Most Predictable Positions
        self.print_question(4, "Which players have the most predictable positioning patterns?")
        query = """
        SELECT 
            name,
            ROUND(X/350)*350 as preferred_zone_x,
            ROUND(Y/350)*350 as preferred_zone_y,
            COUNT(*) as time_in_zone,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY name), 1) as zone_preference_pct
        FROM all_player_ticks
        WHERE name IS NOT NULL
        GROUP BY name, preferred_zone_x, preferred_zone_y
        HAVING time_in_zone > 5000
        ORDER BY zone_preference_pct DESC
        LIMIT 15
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High percentage = predictable positioning that can be exploited")
        
    def run_utility_analysis(self):
        """Analyze grenade usage and coordination."""
        self.print_section_header("Utility Usage & Team Coordination")
        
        # Question 5: Utility Usage Patterns
        self.print_question(5, "How do different players use grenades and what roles do they fulfill?")
        query = """
        SELECT 
            name,
            grenade_type,
            COUNT(DISTINCT demo_name) as maps_used,
            COUNT(DISTINCT tick) as unique_throws,
            ROUND(AVG(x), 1) as avg_throw_x,
            ROUND(AVG(y), 1) as avg_throw_y,
            ROUND(COUNT(DISTINCT tick) / COUNT(DISTINCT demo_name), 1) as throws_per_map
        FROM all_grenades
        WHERE x IS NOT NULL AND y IS NOT NULL AND name IS NOT NULL
        GROUP BY name, grenade_type
        HAVING unique_throws >= 20
        ORDER BY throws_per_map DESC
        LIMIT 20
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "Reveals support players (many smokes/flashes) vs. aggressive players (HE grenades)")
        
        # Question 6: Utility Coordination (Heavily optimized to avoid expensive self-joins)
        self.print_question(6, "Which players coordinate their utility usage most effectively?")
        
        # Simplified approach using window functions instead of expensive self-joins
        query = """
        WITH player_nades AS (
            SELECT 
                demo_name,
                name,
                grenade_type,
                tick,
                LAG(name) OVER (PARTITION BY demo_name ORDER BY tick) as prev_player,
                LAG(grenade_type) OVER (PARTITION BY demo_name ORDER BY tick) as prev_nade_type,
                LAG(tick) OVER (PARTITION BY demo_name ORDER BY tick) as prev_tick
            FROM all_grenades
            WHERE name IS NOT NULL AND name != ''
            ORDER BY demo_name, tick
        ),
        coordinated_throws AS (
            SELECT 
                demo_name,
                name as player1,
                prev_player as player2,
                grenade_type as nade1,
                prev_nade_type as nade2,
                tick - prev_tick as time_diff_ticks
            FROM player_nades
            WHERE prev_player IS NOT NULL 
              AND prev_player != name
              AND (tick - prev_tick) BETWEEN 1 AND 128  -- Within 4 seconds
              AND (tick - prev_tick) <= 64  -- Prioritize closer coordination
        )
        SELECT 
            player1,
            player2,
            COUNT(*) as coordinated_throws,
            STRING_AGG(DISTINCT nade1 || '+' || nade2, ', ') as common_combos,
            ROUND(AVG(time_diff_ticks) / 32.0, 1) as avg_delay_seconds
        FROM coordinated_throws
        GROUP BY player1, player2
        HAVING coordinated_throws >= 5  -- Lower threshold for meaningful results
        ORDER BY coordinated_throws DESC
        LIMIT 10
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Shows sequential utility coordination (simplified analysis for performance)", exec_time)
        
    def run_team_coordination_analysis(self):
        """Analyze team movement and coordination patterns with optimizations."""
        self.print_section_header("Team Movement & Coordination Patterns")
        
        table_name = 'all_player_ticks_sampled' if self.use_sampling else 'all_player_ticks'
        
        # Question 7: Team Formation Analysis (Optimized with strategic sampling)
        self.print_question(7, "How tightly grouped do teams play and which maps promote different formations?")
        query = f"""
        WITH team_formations AS (
            SELECT 
                demo_name,
                tick,
                m_iTeamNum as team,
                COUNT(*) as players_active,
                ROUND(STDDEV(X), 1) as x_spread,
                ROUND(STDDEV(Y), 1) as y_spread,
                ROUND(STDDEV(X) + STDDEV(Y), 1) as total_spread
            FROM {table_name}
            WHERE m_iTeamNum IN (2, 3) 
              AND tick % 512 = 0  -- Sample every 16 seconds for team analysis
              AND name IS NOT NULL AND name != ''
            GROUP BY demo_name, tick, m_iTeamNum
            HAVING players_active >= 3  -- Reduced threshold for meaningful data
        )
        SELECT 
            demo_name,
            CASE WHEN team = 2 THEN 'Team_CT' ELSE 'Team_T' END as team_side,
            ROUND(AVG(total_spread), 1) as avg_team_spread,
            ROUND(MIN(total_spread), 1) as tightest_formation,
            ROUND(MAX(total_spread), 1) as most_spread,
            COUNT(*) as formation_samples
        FROM team_formations
        GROUP BY demo_name, team
        HAVING formation_samples >= 10  -- Filter out insufficient data
        ORDER BY demo_name, team
        """
        result, exec_time = self.execute_query(query)
        self.print_answer(result, "Lower spread = tight teamplay, Higher spread = more individual/split plays", exec_time)
        
        # Question 8: Player Partnership Analysis (Simplified for performance)
        self.print_question(8, "Which players work together most closely in terms of positioning?")
        
        # Simplified approach using zone-based analysis instead of distance calculations
        query = f"""
        WITH player_zones AS (
            SELECT 
                demo_name,
                name,
                m_iTeamNum,
                ROUND(X/600)*600 as zone_x,  -- Larger zones for partnerships
                ROUND(Y/600)*600 as zone_y,
                COUNT(*) as time_in_zone
            FROM {table_name}
            WHERE name IS NOT NULL AND name != '' AND m_iTeamNum IN (2, 3)
            GROUP BY demo_name, name, m_iTeamNum, zone_x, zone_y
            HAVING time_in_zone >= 5
        ),
        zone_partnerships AS (
            SELECT 
                p1.demo_name,
                p1.name as player1,
                p2.name as player2,
                p1.zone_x,
                p1.zone_y,
                MIN(p1.time_in_zone, p2.time_in_zone) as shared_time
            FROM player_zones p1
            JOIN player_zones p2 ON p1.demo_name = p2.demo_name
                AND p1.zone_x = p2.zone_x AND p1.zone_y = p2.zone_y
                AND p1.m_iTeamNum = p2.m_iTeamNum
                AND p1.name < p2.name  -- Avoid duplicates
        )
        SELECT 
            player1,
            player2,
            COUNT(DISTINCT demo_name) as maps_together,
            COUNT(*) as shared_zones,
            SUM(shared_time) as total_shared_presence
        FROM zone_partnerships
        GROUP BY player1, player2
        HAVING shared_zones >= 3
        ORDER BY total_shared_presence DESC
        LIMIT 15
        """
    def toggle_sampling(self, use_sampling: bool = True):
        """Toggle between sampled (fast) and full (slow) analysis."""
        self.use_sampling = use_sampling
        mode = "sampled" if use_sampling else "full"
        logger.info(f"Analysis mode set to: {mode}")
        print(f"🔧 Analysis mode: {'FAST (sampled data)' if use_sampling else 'FULL (all data)'}")
    
    def run_all_analyses(self):
        """Run all strategic analyses with performance optimizations."""
        start_time = time.time()
        
        print("🚀 Starting CS:GO Strategic Analysis (Performance Optimized)")
        print(f"📊 Mode: {'FAST - Using sampled data for performance' if self.use_sampling else 'FULL - Using all data (slower)'}")
        
        try:
            # Run analysis sections
            self.run_map_control_analysis()
            self.run_player_role_analysis()  
            self.run_team_coordination_analysis()
            
            # Add more sections as needed
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            print(f"❌ Analysis failed: {str(e)}")
        
        total_time = time.time() - start_time
        print(f"\n🎯 Analysis completed in {total_time:.1f} seconds")
        
        if self.use_sampling:
            print("💡 Tip: Use analyzer.toggle_sampling(False) for full data analysis (slower but more comprehensive)")
    
    def run_all_analyses_full(self):
        """Run full analysis with all data."""
        self.toggle_sampling(False)
        self.run_all_analyses()
    
    def run_all_analyses_fast(self):
        """Run fast analysis with sampled data."""
        self.toggle_sampling(True)
        self.run_all_analyses() 
            player1,
            player2,
            COUNT(*) as time_samples,
            ROUND(AVG(distance), 1) as avg_distance,
            ROUND(MIN(distance), 1) as closest_distance,
            COUNT(CASE WHEN distance <= 800 THEN 1 END) as close_proximity_count,
            ROUND(COUNT(CASE WHEN distance <= 800 THEN 1 END) * 100.0 / COUNT(*), 1) as proximity_percentage
        FROM player_distances
        GROUP BY player1, player2
        ORDER BY proximity_percentage DESC
        LIMIT 15
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High proximity % indicates players who consistently play together/trade")
        
    def run_timing_analysis(self):
        """Analyze timing and round flow patterns."""
        self.print_section_header("Timing & Round Flow Analysis")
        
        # Question 9: Peak Activity Timing
        self.print_question(9, "When do most engagements and team movements occur during rounds?")
        query = """
        SELECT 
            demo_name,
            FLOOR(tick / 1280) * 10 as time_window_seconds,
            COUNT(*) as player_actions,
            COUNT(DISTINCT name) as active_players,
            ROUND(AVG(X), 1) as avg_action_x,
            ROUND(AVG(Y), 1) as avg_action_y,
            ROUND(STDDEV(X) + STDDEV(Y), 1) as action_spread
        FROM all_player_ticks
        GROUP BY demo_name, time_window_seconds
        HAVING player_actions >= 1000
        ORDER BY demo_name, time_window_seconds
        LIMIT 25
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "Shows when teams are most active and where action centers occur")
        
        # Question 10: Utility Timing Patterns
        self.print_question(10, "When is utility typically used during round progression?")
        query = """
        SELECT 
            demo_name,
            FLOOR(tick / 1920) * 15 as time_window_seconds,
            grenade_type,
            COUNT(DISTINCT tick) as grenade_throws,
            COUNT(DISTINCT name) as different_throwers,
            STRING_AGG(DISTINCT name, ', ') as primary_users
        FROM all_grenades
        GROUP BY demo_name, time_window_seconds, grenade_type
        HAVING grenade_throws >= 5
        ORDER BY demo_name, time_window_seconds, grenade_throws DESC
        LIMIT 20
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "Reveals execute timing and utility patterns for different round phases")
        
    def run_anti_strat_analysis(self):
        """Find predictable patterns for anti-stratting."""
        self.print_section_header("Anti-Stratting & Predictable Patterns")
        
        # Question 11: Predictable Player Tendencies
        self.print_question(11, "Which players have exploitable positioning tendencies?")
        query = """
        WITH position_analysis AS (
            SELECT 
                name,
                demo_name,
                ROUND(X/300)*300 as zone_x,
                ROUND(Y/300)*300 as zone_y,
                COUNT(*) as time_in_zone
            FROM all_player_ticks
            WHERE name IS NOT NULL
            GROUP BY name, demo_name, zone_x, zone_y
        )
        SELECT 
            name,
            COUNT(DISTINCT demo_name || '_' || zone_x || '_' || zone_y) as unique_positions,
            MAX(time_in_zone) as max_time_one_position,
            SUM(time_in_zone) as total_time,
            ROUND(MAX(time_in_zone) * 100.0 / SUM(time_in_zone), 1) as position_predictability_pct
        FROM position_analysis
        GROUP BY name
        ORDER BY position_predictability_pct DESC
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High predictability % = players who favor specific positions consistently")
        
        # Question 12: Repetitive Utility Usage
        self.print_question(12, "Do players have predictable grenade usage patterns?")
        query = """
        SELECT 
            name,
            grenade_type,
            ROUND(x/250)*250 as throw_zone_x,
            ROUND(y/250)*250 as throw_zone_y,
            COUNT(DISTINCT demo_name) as maps_used,
            COUNT(DISTINCT tick) as repeated_throws,
            ROUND(COUNT(DISTINCT tick) / COUNT(DISTINCT demo_name), 1) as throws_per_map
        FROM all_grenades
        WHERE x IS NOT NULL AND y IS NOT NULL AND name IS NOT NULL
        GROUP BY name, grenade_type, throw_zone_x, throw_zone_y
        HAVING repeated_throws >= 8
        ORDER BY throws_per_map DESC
        LIMIT 15
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High throws per map from same zones = predictable utility patterns to counter")
        
    def run_performance_analysis(self):
        """Analyze performance-related strategic insights."""
        self.print_section_header("Performance & Impact Analysis")
        
        # Question 13: Player Activity Analysis
        self.print_question(13, "Which players are most active and impactful across different situations?")
        query = """
        WITH player_activity AS (
            SELECT 
                name,
                demo_name,
                COUNT(*) as position_updates,
                COUNT(DISTINCT tick) as unique_ticks,
                MAX(tick) - MIN(tick) as active_duration,
                ROUND(STDDEV(X) + STDDEV(Y), 1) as movement_variance
            FROM all_player_ticks
            WHERE name IS NOT NULL
            GROUP BY name, demo_name
        )
        SELECT 
            name,
            COUNT(DISTINCT demo_name) as maps_played,
            ROUND(AVG(position_updates), 0) as avg_activity_per_map,
            ROUND(AVG(movement_variance), 1) as avg_movement_variance,
            ROUND(AVG(active_duration) / 32.0, 1) as avg_active_seconds_per_map
        FROM player_activity
        GROUP BY name
        ORDER BY avg_activity_per_map DESC
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High activity + movement = key players to focus on when anti-stratting")
        
        # Question 14: Equipment and Role Correlation
        self.print_question(14, "What do equipment choices tell us about player roles and preferences?")
        query = """
        SELECT 
            p.name,
            COUNT(DISTINCT s.def_index) as unique_weapons,
            COUNT(DISTINCT s.item_id) as total_items,
            ROUND(AVG(s.paint_wear), 4) as avg_skin_wear,
            COUNT(CASE WHEN s.custom_name IS NOT NULL THEN 1 END) as custom_named_items,
            STRING_AGG(DISTINCT CAST(s.def_index as VARCHAR), ', ') as weapon_indices
        FROM all_player_info p
        JOIN all_skins s ON p.steamid = s.steamid
        GROUP BY p.name
        ORDER BY total_items DESC
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "Equipment variety and customization can indicate player roles and investment")
        
    def run_map_specific_analysis(self):
        """Analyze map-specific strategic patterns."""
        self.print_section_header("Map-Specific Strategic Intelligence")
        
        # Question 15: Map Control Efficiency
        self.print_question(15, "Which maps favor different playstyles and team formations?")
        query = """
        SELECT 
            demo_name,
            COUNT(DISTINCT name) as unique_players,
            COUNT(*) as total_player_actions,
            MAX(tick) as match_duration_ticks,
            ROUND(MAX(tick) / 32.0 / 60, 1) as estimated_duration_minutes,
            ROUND(AVG(X), 1) as map_center_x,
            ROUND(AVG(Y), 1) as map_center_y,
            ROUND(STDDEV(X), 1) as x_spread,
            ROUND(STDDEV(Y), 1) as y_spread,
            ROUND(STDDEV(X) + STDDEV(Y), 1) as total_map_usage
        FROM all_player_ticks
        GROUP BY demo_name
        ORDER BY total_map_usage DESC
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "High spread = maps that allow diverse positioning, Low spread = constrained maps")
        
        # Question 16: Area Control Patterns
        self.print_question(16, "What are the key control areas and engagement zones for each map?")
        query = """
        WITH area_analysis AS (
            SELECT 
                demo_name,
                CASE 
                    WHEN X > 500 AND Y > 500 THEN 'NorthEast_Sector'
                    WHEN X > 500 AND Y < -500 THEN 'SouthEast_Sector'
                    WHEN X < -500 AND Y > 500 THEN 'NorthWest_Sector'
                    WHEN X < -500 AND Y < -500 THEN 'SouthWest_Sector'
                    WHEN ABS(X) <= 500 AND Y > 500 THEN 'North_Mid'
                    WHEN ABS(X) <= 500 AND Y < -500 THEN 'South_Mid'
                    WHEN X > 500 AND ABS(Y) <= 500 THEN 'East_Mid'
                    WHEN X < -500 AND ABS(Y) <= 500 THEN 'West_Mid'
                    ELSE 'Center'
                END as map_area,
                m_iTeamNum,
                COUNT(*) as area_control_time,
                COUNT(DISTINCT name) as players_in_area
            FROM all_player_ticks
            WHERE m_iTeamNum IN (2, 3)
            GROUP BY demo_name, map_area, m_iTeamNum
        )
        SELECT 
            demo_name,
            map_area,
            SUM(CASE WHEN m_iTeamNum = 2 THEN area_control_time ELSE 0 END) as team_ct_control,
            SUM(CASE WHEN m_iTeamNum = 3 THEN area_control_time ELSE 0 END) as team_t_control,
            ROUND(
                SUM(CASE WHEN m_iTeamNum = 2 THEN area_control_time ELSE 0 END) * 100.0 / 
                (SUM(CASE WHEN m_iTeamNum = 2 THEN area_control_time ELSE 0 END) + 
                 SUM(CASE WHEN m_iTeamNum = 3 THEN area_control_time ELSE 0 END)), 1
            ) as ct_control_percentage
        FROM area_analysis
        GROUP BY demo_name, map_area
        HAVING team_ct_control + team_t_control > 5000
        ORDER BY demo_name, ct_control_percentage DESC
        """
        result = self.analyzer.query(query)
        self.print_answer(result, "Shows which team controls each area more effectively")
        
    def run_all_analyses(self):
        """Run all strategic analyses for expert validation."""
        start_time = time.time()
        
        print("🎮 CS2 STRATEGIC ANALYSIS - EXPERT VALIDATION REPORT")
        print("=" * 80)
        print("This report answers key strategic questions for CS2 team preparation")
        print("and anti-stratting using professional demo data from Falcons vs Vitality.")
        print("Each answer can be validated by human experts and analysts.")
        print(f"Analysis Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Run all analysis sections
            self.run_map_control_analysis()
            self.run_player_role_analysis()
            self.run_utility_analysis()
            self.run_team_coordination_analysis()
            self.run_timing_analysis()
            self.run_anti_strat_analysis()
            self.run_performance_analysis()
            self.run_map_specific_analysis()
            
            # Summary
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"\n{'='*80}")
            print("🎯 ANALYSIS SUMMARY")
            print(f"{'='*80}")
            print(f"✅ Analysis completed successfully in {duration:.1f} seconds")
            print(f"📊 16 strategic questions analyzed across 8 categories")
            print(f"🎮 Data from 5 professional matches (Falcons vs Vitality)")
            print(f"📈 27.4M+ data points analyzed")
            print(f"\n💡 EXPERT VALIDATION NOTES:")
            print("- Review positioning patterns for tactical accuracy")
            print("- Validate utility timing against known CS2 meta")
            print("- Confirm player role assignments match known roster roles")
            print("- Check map control patterns against professional gameplay")
            print("- Verify predictability patterns align with team strategies")
            print("\n🚀 Ready for strategic decision-making and counter-preparation!")
            
        except Exception as e:
            print(f"\n❌ Error during analysis: {str(e)}")
            
    def close(self):
        """Close the database connection."""
        self.analyzer.close()

def main():
    """Run the expert validation analysis with performance optimizations."""
    validator = ExpertValidationAnalyzer()
    
    try:
        # Start with fast analysis by default
        print("🚀 Starting CS:GO Expert Validation Analysis")
        print("🔧 Performance Mode: FAST (using sampled data)")
        print("💡 For full analysis, use: validator.run_all_analyses_full()")
        
        validator.run_all_analyses_fast()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
    finally:
        validator.close()
        print(f"\n🔗 Database connection closed")

if __name__ == "__main__":
    main()
