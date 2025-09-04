"""
CS2 Strategic Analysis - Expert Validation Script (Optimized)
This script runs through key strategic questions and provides answers
that can be validated by human CS2 experts and analysts.
Performance optimized for large datasets.
"""

from duckdb_connector_optimized import CSGODataAnalyzer
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
        """Analyze map control and territory questions with optimizations."""
        self.print_section_header("Map Control & Territory Analysis")
        
        # Use sampled data for performance
        table_name = 'all_player_ticks_sampled' if self.use_sampling else 'all_player_ticks'
        
        # Question 1: Territory Control (Optimized with sampling)
        self.print_question(1, "Which areas does each team control most effectively on each map?")
        
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
        """Analyze player positioning and role patterns with optimizations."""
        self.print_section_header("Player Role & Positioning Intelligence")
        
        table_name = 'all_player_ticks_sampled' if self.use_sampling else 'all_player_ticks'
        
        # Question 3: Player Mobility Patterns (Optimized with sampling)
        self.print_question(3, "Which players are most/least mobile and what does this tell us about their roles?")
        
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
        
    def run_utility_analysis(self):
        """Analyze utility usage patterns with optimizations."""
        self.print_section_header("Utility Usage Analysis")
        
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
            self.run_utility_analysis()
            
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
