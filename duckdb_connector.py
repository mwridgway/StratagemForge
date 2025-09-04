import duckdb
import pandas as pd
from pathlib import Path
import logging
import time
from typing import Optional, Dict, List
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CSGODataAnalyzer:
    """
    A class to provide DuckDB connection and analysis capabilities for CS:GO demo data.
    Optimized for performance with caching and indexing.
    """
    
    def __init__(self, parquet_folder: str = "parquet", db_path: Optional[str] = None):
        """
        Initialize the analyzer with parquet data.
        
        Args:
            parquet_folder: Path to the folder containing parquet files
            db_path: Optional path to persistent DuckDB database file
        """
        self.parquet_folder = Path(parquet_folder)
        self.db_path = db_path
        self.conn = None
        self.demos = []
        self.query_cache = {}
        
        if not self.parquet_folder.exists():
            raise FileNotFoundError(f"Parquet folder {parquet_folder} not found!")
        
        self._discover_demos()
        self._initialize_connection()
        self._create_optimized_views()
    
    def _discover_demos(self):
        """Discover all demo folders and their data files."""
        self.demos = []
        demo_folders = [folder for folder in self.parquet_folder.iterdir() if folder.is_dir()]
        
        for demo_folder in demo_folders:
            demo_info = {
                'name': demo_folder.name,
                'path': demo_folder,
                'files': {}
            }
            
            # Find all parquet files
            for parquet_file in demo_folder.glob("*.parquet"):
                data_type = parquet_file.stem
                demo_info['files'][data_type] = str(parquet_file)
            
            self.demos.append(demo_info)
        
        logger.info(f"Discovered {len(self.demos)} demos with parquet data")
    
    def _initialize_connection(self):
        """Initialize DuckDB connection."""
        if self.db_path:
            self.conn = duckdb.connect(self.db_path)
            logger.info(f"Connected to persistent DuckDB database: {self.db_path}")
        else:
            self.conn = duckdb.connect()
            logger.info("Connected to in-memory DuckDB database")
    
    def _create_views(self):
        """Create SQL views for all parquet data."""
        logger.info("Creating DuckDB views for parquet data...")
        
        # Create individual demo views
        for demo in self.demos:
            demo_name = demo['name'].replace('-', '_')
            
            for data_type, file_path in demo['files'].items():
                view_name = f"{demo_name}_{data_type}"
                
                # Create view for this specific demo and data type
                sql = f"""
                CREATE OR REPLACE VIEW {view_name} AS 
                SELECT *, '{demo['name']}' as demo_name, '{data_type}' as data_type
                FROM read_parquet('{file_path}')
                """
                    self.conn.execute(sql)
                    logger.info(f"Created view: {view_name}")
        
        logger.info("Individual views created, now creating unified views...")
        # Create unified views across all demos
        self._create_unified_views()
        
        logger.info("Unified views created, now creating indexes...")
        # Create indexes after all views are created
        self._create_indexes()    def _create_indexes(self):
        """Create indexes on commonly queried columns for better performance."""
        try:
            logger.info("Creating performance indexes...")
            
            # Common indexes for player_ticks (most queried table)
            index_queries = [
                # Indexes for player ticks - most common queries
                "CREATE INDEX IF NOT EXISTS idx_player_ticks_name ON all_player_ticks(name)",
                "CREATE INDEX IF NOT EXISTS idx_player_ticks_team ON all_player_ticks(m_iTeamNum)", 
                "CREATE INDEX IF NOT EXISTS idx_player_ticks_tick ON all_player_ticks(tick)",
                "CREATE INDEX IF NOT EXISTS idx_player_ticks_demo ON all_player_ticks(demo_name)",
                "CREATE INDEX IF NOT EXISTS idx_player_ticks_position ON all_player_ticks(X, Y)",
                
                # Indexes for grenades
                "CREATE INDEX IF NOT EXISTS idx_grenades_name ON all_grenades(name)",
                "CREATE INDEX IF NOT EXISTS idx_grenades_type ON all_grenades(grenade_type)",
                "CREATE INDEX IF NOT EXISTS idx_grenades_tick ON all_grenades(tick)",
                "CREATE INDEX IF NOT EXISTS idx_grenades_position ON all_grenades(x, y)",
            ]
            
            for query in index_queries:
                try:
                    self.conn.execute(query)
                    logger.debug(f"Created index: {query.split('ON')[1] if 'ON' in query else query}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {str(e)}")
                    
            logger.info("Performance indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {str(e)}")
    
    def _create_optimized_views(self):
        """Create views with performance optimizations."""
        logger.info("Creating optimized views...")
        
        # Create views for each demo and data type with optimizations
        for demo in self.demos:
            demo_name = demo['name'].replace('-', '_')
            
            for data_type, file_path in demo['files'].items():
                view_name = f"{demo_name}_{data_type}"
                
                # Create view with strategic sampling for large datasets
                if data_type == 'player_ticks':
                    # Create both full and sampled views for player ticks
                    sql_full = f"""
                    CREATE OR REPLACE VIEW {view_name} AS 
                    SELECT *, '{demo['name']}' as demo_name, '{data_type}' as data_type
                    FROM read_parquet('{file_path}')
                    """
                    
                    sql_sampled = f"""
                    CREATE OR REPLACE VIEW {view_name}_sampled AS 
                    SELECT *, '{demo['name']}' as demo_name, '{data_type}' as data_type
                    FROM read_parquet('{file_path}')
                    WHERE tick % 64 = 0  -- Every 2 seconds for performance
                    """
                    
                    self.conn.execute(sql_full)
                    self.conn.execute(sql_sampled)
                    logger.info(f"Created views: {view_name} (full + sampled)")
                else:
                    # Standard view for other data types
                    sql = f"""
                    CREATE OR REPLACE VIEW {view_name} AS 
                    SELECT *, '{demo['name']}' as demo_name, '{data_type}' as data_type
                    FROM read_parquet('{file_path}')
                    """
                    self.conn.execute(sql)
                    logger.info(f"Created view: {view_name}")
    
    def _create_unified_views(self):
        """Create unified views that combine data across all demos with optimizations."""
        data_types = set()
        for demo in self.demos:
            data_types.update(demo['files'].keys())
        
        for data_type in data_types:
            # Find all demos that have this data type
            demo_views = []
            sampled_views = []
            
            for demo in self.demos:
                if data_type in demo['files']:
                    demo_name = demo['name'].replace('-', '_')
                    demo_views.append(f"{demo_name}_{data_type}")
                    if data_type == 'player_ticks':
                        sampled_views.append(f"{demo_name}_{data_type}_sampled")
            
            if demo_views:
                # Create unified view
                unified_view_name = f"all_{data_type}"
                union_query = " UNION ALL ".join([f"SELECT * FROM {view}" for view in demo_views])
                
                sql = f"""
                CREATE OR REPLACE VIEW {unified_view_name} AS 
                {union_query}
                """
                self.conn.execute(sql)
                logger.info(f"Created unified view: {unified_view_name}")
                
                # Create sampled unified view for player_ticks
                if data_type == 'player_ticks' and sampled_views:
                    sampled_unified_name = f"all_{data_type}_sampled"
                    sampled_union_query = " UNION ALL ".join([f"SELECT * FROM {view}" for view in sampled_views])
                    
                    sql_sampled = f"""
                    CREATE OR REPLACE VIEW {sampled_unified_name} AS 
                    {sampled_union_query}
                    """
                    self.conn.execute(sql_sampled)
                    logger.info(f"Created sampled unified view: {sampled_unified_name}")
    
    def query(self, sql: str, use_cache: bool = True, timeout: int = 30) -> pd.DataFrame:
        """
        Execute a SQL query and return results as a pandas DataFrame.
        
        Args:
            sql: SQL query string
            use_cache: Whether to use query result caching
            timeout: Query timeout in seconds (not implemented in current DuckDB version)
            
        Returns:
            pandas DataFrame with query results
        """
        # Simple cache key based on SQL
        cache_key = hash(sql.strip().lower())
        
        # Check cache first
        if use_cache and cache_key in self.query_cache:
            logger.debug("Returning cached query result")
            return self.query_cache[cache_key].copy()
        
        try:
            start_time = time.time()
            
            # Note: DuckDB timeout setting not available in current version
            # self.conn.execute(f"SET query_timeout = '{timeout}s'")
            
            result = self.conn.execute(sql).df()
            execution_time = time.time() - start_time
            
            logger.info(f"Query executed in {execution_time:.2f}s, returned {len(result):,} rows")
            
            # Cache result if it's reasonable size (< 10MB) and took time to compute
            if use_cache and execution_time > 0.5 and result.memory_usage(deep=True).sum() < 10 * 1024 * 1024:
                self.query_cache[cache_key] = result.copy()
                logger.debug(f"Cached query result ({len(result):,} rows)")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.2f}s: {str(e)}")
            logger.error(f"Query: {sql[:200]}...")
            raise
    
    def get_sampled_query_suggestion(self, original_query: str) -> str:
        """
        Suggest a sampled version of a query for better performance.
        
        Args:
            original_query: Original SQL query
            
        Returns:
            Optimized query suggestion
        """
        # Replace all_player_ticks with sampled version for performance
        if 'all_player_ticks' in original_query.lower():
            suggested = original_query.replace('all_player_ticks', 'all_player_ticks_sampled')
            logger.info("Performance tip: Consider using 'all_player_ticks_sampled' for faster queries")
            return suggested
        
        return original_query
    
    def get_schema_info(self) -> Dict:
        """Get information about all available views and their schemas."""
        views_info = {}
        
        # Get all views
        views_query = "SELECT table_name FROM information_schema.tables WHERE table_type = 'VIEW'"
        views = self.conn.execute(views_query).fetchall()
        
        for view_tuple in views:
            view_name = view_tuple[0]
            
            # Get schema for this view
            schema_query = f"DESCRIBE {view_name}"
            schema = self.conn.execute(schema_query).df()
            
            views_info[view_name] = {
                'columns': schema['column_name'].tolist(),
                'types': schema['column_type'].tolist(),
                'schema': schema
            }
        
        return views_info
    
    def get_demo_summary(self) -> pd.DataFrame:
        """Get a summary of all demos and their data."""
        summary_data = []
        
        for demo in self.demos:
            demo_summary = {'demo_name': demo['name']}
            
            for data_type, file_path in demo['files'].items():
                # Get row count for each data type
                df = pd.read_parquet(file_path)
                demo_summary[f"{data_type}_rows"] = len(df)
            
            summary_data.append(demo_summary)
        
        return pd.DataFrame(summary_data)
    
    def get_sample_queries(self) -> List[str]:
        """Get a list of sample SQL queries for analysis."""
        return [
            # Player movement analysis
            """
            -- Get average player positions by map
            SELECT demo_name, name, 
                   AVG(X) as avg_x, AVG(Y) as avg_y, AVG(Z) as avg_z,
                   COUNT(*) as tick_count
            FROM all_player_ticks 
            GROUP BY demo_name, name
            ORDER BY demo_name, name;
            """,
            
            # Team performance
            """
            -- Compare team positioning
            SELECT demo_name, m_iTeamNum as team,
                   AVG(X) as avg_x, AVG(Y) as avg_y,
                   COUNT(DISTINCT name) as player_count,
                   COUNT(*) as total_ticks
            FROM all_player_ticks 
            WHERE m_iTeamNum IS NOT NULL
            GROUP BY demo_name, m_iTeamNum
            ORDER BY demo_name, team;
            """,
            
            # Grenade usage
            """
            -- Grenade usage by player and type
            SELECT demo_name, name, grenade_type,
                   COUNT(*) as grenade_count,
                   COUNT(DISTINCT tick) as unique_throws
            FROM all_grenades 
            WHERE name IS NOT NULL
            GROUP BY demo_name, name, grenade_type
            ORDER BY demo_name, grenade_count DESC;
            """,
            
            # Map-specific analysis
            """
            -- Player activity by map (demo)
            SELECT demo_name,
                   COUNT(DISTINCT name) as unique_players,
                   COUNT(*) as total_ticks,
                   MAX(tick) as max_tick,
                   AVG(CASE WHEN m_iTeamNum = 2 THEN 1 ELSE 0 END) * 100 as team2_percentage
            FROM all_player_ticks
            GROUP BY demo_name
            ORDER BY total_ticks DESC;
            """,
            
            # Player equipment
            """
            -- Most expensive skins by player
            SELECT p.name, p.demo_name,
                   COUNT(s.item_id) as skin_count,
                   AVG(s.paint_wear) as avg_wear
            FROM all_player_info p
            JOIN all_skins s ON p.steamid = s.steamid
            GROUP BY p.name, p.demo_name
            ORDER BY skin_count DESC;
            """
        ]
    
    def print_available_data(self):
        """Print information about available data and views."""
        print("=== CS:GO Demo Data Analysis ===\n")
        
        print("Available Demos:")
        for demo in self.demos:
            print(f"  📁 {demo['name']}")
            for data_type in demo['files'].keys():
                print(f"    - {data_type}")
        
        print(f"\nAvailable Views:")
        schema_info = self.get_schema_info()
        for view_name, info in schema_info.items():
            print(f"  📊 {view_name} ({len(info['columns'])} columns)")
        
        print(f"\nUnified Views (across all demos):")
        unified_views = [view for view in schema_info.keys() if view.startswith('all_')]
        for view in unified_views:
            print(f"  🔗 {view}")
        
        print(f"\nSample usage:")
        print(f"  analyzer = CSGODataAnalyzer()")
        print(f"  df = analyzer.query('SELECT * FROM all_player_info LIMIT 10')")
        print(f"  print(df)")
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Demonstrate the analyzer usage."""
    try:
        # Initialize analyzer
        analyzer = CSGODataAnalyzer()
        
        # Print available data
        analyzer.print_available_data()
        
        # Show demo summary
        print("\n=== Demo Summary ===")
        summary = analyzer.get_demo_summary()
        print(summary)
        
        # Run a sample query
        print("\n=== Sample Query: Player Information ===")
        player_info = analyzer.query("SELECT * FROM all_player_info LIMIT 10")
        print(player_info)
        
        print("\n=== Sample Queries for LLM Analysis ===")
        sample_queries = analyzer.get_sample_queries()
        for i, query in enumerate(sample_queries, 1):
            print(f"\n{i}. {query.strip()}")
        
        return analyzer
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        return None


if __name__ == "__main__":
    analyzer = main()
