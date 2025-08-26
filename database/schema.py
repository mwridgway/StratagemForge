import duckdb
import os
from datetime import datetime
from typing import Dict, List

class DatabaseManager:
    def __init__(self, db_path: str = "sf.duckdb"):
        """Initialize database manager with schema versioning"""
        self.db_path = db_path
        self.connection = None
        self.current_version = 0
        self._ensure_db_directory()
        
    def _ensure_db_directory(self):
        """Ensure database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    def connect(self):
        """Connect to database and initialize schema versioning"""
        self.connection = duckdb.connect(self.db_path)
        self._init_schema_versioning()
        self.current_version = self._get_current_version()
        return self.connection
    
    def _init_schema_versioning(self):
        """Initialize schema versioning table"""
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        """)
    
    def _get_current_version(self) -> int:
        """Get current schema version"""
        result = self.connection.execute("""
            SELECT COALESCE(MAX(version), 0) 
            FROM schema_migrations
        """).fetchone()
        return result[0] if result else 0
    
    def get_migrations(self) -> List[Dict]:
        """Define all schema migrations"""
        return [
            {
                'version': 1,
                'description': 'Create demo_ticks table',
                'sql': """
                    CREATE SEQUENCE demo_ticks_id_seq;
                    CREATE TABLE demo_ticks (
                        id INTEGER PRIMARY KEY DEFAULT nextval('demo_ticks_id_seq'),
                        tick INTEGER NOT NULL,
                        round_num INTEGER,
                        seconds DOUBLE,
                        clock_time TEXT,
                        t_score INTEGER,
                        ct_score INTEGER,
                        game_phase TEXT,
                        bomb_planted BOOLEAN DEFAULT FALSE,
                        bomb_defused BOOLEAN DEFAULT FALSE,
                        
                        -- Player identification
                        steam_id BIGINT,
                        name TEXT,
                        team TEXT,
                        side TEXT,
                        
                        -- Player status
                        is_alive BOOLEAN DEFAULT TRUE,
                        hp INTEGER DEFAULT 100,
                        armor INTEGER DEFAULT 0,
                        has_helmet BOOLEAN DEFAULT FALSE,
                        has_defuse_kit BOOLEAN DEFAULT FALSE,
                        money INTEGER DEFAULT 0,
                        
                        -- Position and movement
                        x DOUBLE,
                        y DOUBLE,
                        z DOUBLE,
                        view_x DOUBLE,  -- yaw/pitch for view direction
                        view_y DOUBLE,
                        velocity_x DOUBLE DEFAULT 0,
                        velocity_y DOUBLE DEFAULT 0,
                        velocity_z DOUBLE DEFAULT 0,
                        
                        -- Equipment
                        active_weapon TEXT,
                        primary_weapon TEXT,
                        secondary_weapon TEXT,
                        grenades TEXT,  -- JSON array of grenades
                        
                        -- Game state flags
                        is_ducking BOOLEAN DEFAULT FALSE,
                        is_walking BOOLEAN DEFAULT FALSE,
                        is_scoped BOOLEAN DEFAULT FALSE,
                        is_reloading BOOLEAN DEFAULT FALSE,
                        is_defusing BOOLEAN DEFAULT FALSE,
                        is_planting BOOLEAN DEFAULT FALSE,
                        
                        -- Metadata
                        demo_filename TEXT NOT NULL,
                        map_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
            },
            {
                'version': 2,
                'description': 'Create indexes for performance',
                'sql': """
                    CREATE INDEX idx_demo_ticks_tick ON demo_ticks(tick);
                    CREATE INDEX idx_demo_ticks_round_num ON demo_ticks(round_num);
                    CREATE INDEX idx_demo_ticks_steam_id ON demo_ticks(steam_id);
                    CREATE INDEX idx_demo_ticks_name ON demo_ticks(name);
                    CREATE INDEX idx_demo_ticks_demo_filename ON demo_ticks(demo_filename);
                    CREATE INDEX idx_demo_ticks_map_name ON demo_ticks(map_name);
                    CREATE INDEX idx_demo_ticks_position ON demo_ticks(x, y, z);
                """
            },
            {
                'version': 3,
                'description': 'Create demo_metadata table',
                'sql': """
                    CREATE SEQUENCE demo_metadata_id_seq;
                    CREATE TABLE demo_metadata (
                        id INTEGER PRIMARY KEY DEFAULT nextval('demo_metadata_id_seq'),
                        filename TEXT UNIQUE NOT NULL,
                        file_path TEXT NOT NULL,
                        file_size_bytes BIGINT,
                        file_hash TEXT,
                        map_name TEXT,
                        game_mode TEXT,
                        server_name TEXT,
                        date_recorded TIMESTAMP,
                        total_rounds INTEGER,
                        total_ticks BIGINT,
                        team1_name TEXT,
                        team2_name TEXT,
                        team1_score INTEGER,
                        team2_score INTEGER,
                        match_duration_seconds INTEGER,
                        parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """
            },
            {
                'version': 4,
                'description': 'Create players table for normalization',
                'sql': """
                    CREATE SEQUENCE players_id_seq;
                    CREATE TABLE players (
                        id INTEGER PRIMARY KEY DEFAULT nextval('players_id_seq'),
                        steam_id BIGINT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        total_matches INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    
                    CREATE INDEX idx_players_steam_id ON players(steam_id);
                    CREATE INDEX idx_players_name ON players(name);
                """
            }
        ]
    
    def migrate(self):
        """Run all pending migrations"""
        migrations = self.get_migrations()
        pending_migrations = [m for m in migrations if m['version'] > self.current_version]
        
        if not pending_migrations:
            print(f"Database is up to date (version {self.current_version})")
            return
        
        print(f"Running {len(pending_migrations)} migration(s)...")
        
        for migration in pending_migrations:
            print(f"Applying migration {migration['version']}: {migration['description']}")
            
            try:
                # Execute the migration SQL
                self.connection.execute(migration['sql'])
                
                # Record the migration
                self.connection.execute("""
                    INSERT INTO schema_migrations (version, description, applied_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, [migration['version'], migration['description']])
                
                print(f"✓ Migration {migration['version']} applied successfully")
                
            except Exception as e:
                print(f"✗ Error applying migration {migration['version']}: {e}")
                raise
        
        self.current_version = self._get_current_version()
        print(f"Database migrated to version {self.current_version}")
    
    def rollback(self, target_version: int):
        """Rollback to a specific version (basic implementation)"""
        if target_version >= self.current_version:
            print("Cannot rollback to same or higher version")
            return
        
        print(f"WARNING: Rolling back from version {self.current_version} to {target_version}")
        print("This will drop tables and data. Are you sure? (This is a basic implementation)")
        
        # For now, just recreate from scratch
        self.connection.execute("DROP TABLE IF EXISTS demo_ticks")
        self.connection.execute("DROP TABLE IF EXISTS demo_metadata") 
        self.connection.execute("DROP TABLE IF EXISTS players")
        self.connection.execute("DELETE FROM schema_migrations WHERE version > ?", [target_version])
        
        # Re-run migrations up to target version
        self.current_version = target_version
        self.migrate()
    
    def get_schema_info(self):
        """Get information about current schema"""
        tables = self.connection.execute("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            AND table_name != 'schema_migrations'
            ORDER BY table_name
        """).fetchall()
        
        print(f"Current schema version: {self.current_version}")
        print("Tables:")
        for table_name, table_type in tables:
            # Get column info
            columns = self.connection.execute(f"DESCRIBE {table_name}").fetchall()
            print(f"  {table_name} ({len(columns)} columns)")
            for col_name, col_type, _, _, _, _ in columns[:5]:  # Show first 5 columns
                print(f"    - {col_name}: {col_type}")
            if len(columns) > 5:
                print(f"    ... and {len(columns) - 5} more columns")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()