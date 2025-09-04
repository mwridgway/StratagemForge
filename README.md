# CS:GO Demo Data Analysis with DuckDB

This repository contains tools to parse CS:GO demo files and analyze them using DuckDB for efficient SQL-based analysis.

## Files Overview

- `pipeline.py` - Parses demo files using demoparser2 and converts to parquet format
- `duckdb_connector.py` - Provides DuckDB connection and analysis interface
- `example_analysis.py` - Demonstrates various analysis capabilities
- `verify_data.py` - Verifies the generated parquet files

## Quick Start

### 1. Parse Demo Files
```bash
python pipeline.py
```

### 2. Analyze Data with DuckDB
```python
from duckdb_connector import CSGODataAnalyzer

# Initialize connection
analyzer = CSGODataAnalyzer()

# Run SQL queries
result = analyzer.query("SELECT name, COUNT(*) FROM all_player_info GROUP BY name")
print(result)

# Close connection when done
analyzer.close()
```

## Available Data Views

### Unified Views (across all demos):
- `all_player_ticks` - Player positions and movement data (11.6M+ rows)
- `all_grenades` - Grenade usage and trajectories (15.8M+ rows)  
- `all_player_info` - Player information and team assignments (50 rows)
- `all_skins` - Weapon skin data (145 rows)

### Individual Demo Views:
- `{demo_name}_{data_type}` - e.g., `falcons_vs_vitality_m1_inferno_player_ticks`

## Sample Analysis Queries

### Player Performance
```sql
-- Average player positions across all maps
SELECT name, 
       COUNT(DISTINCT demo_name) as maps_played,
       AVG(X) as avg_x, AVG(Y) as avg_y, AVG(Z) as avg_z,
       COUNT(*) as total_ticks
FROM all_player_ticks 
WHERE name IS NOT NULL
GROUP BY name 
ORDER BY total_ticks DESC;
```

### Team Analysis
```sql
-- Team positioning comparison
SELECT demo_name, m_iTeamNum as team,
       COUNT(DISTINCT name) as players,
       AVG(X) as avg_x, AVG(Y) as avg_y,
       COUNT(*) as total_ticks
FROM all_player_ticks 
WHERE m_iTeamNum IN (2, 3)
GROUP BY demo_name, m_iTeamNum
ORDER BY demo_name, team;
```

### Grenade Usage
```sql
-- Grenade usage patterns by player
SELECT name, grenade_type,
       COUNT(DISTINCT demo_name) as maps_used,
       COUNT(DISTINCT tick) as unique_throws,
       COUNT(*) as total_grenade_ticks
FROM all_grenades 
WHERE name IS NOT NULL
GROUP BY name, grenade_type
ORDER BY total_grenade_ticks DESC;
```

### Map-Specific Analysis
```sql
-- Player activity by map
SELECT demo_name,
       COUNT(DISTINCT name) as unique_players,
       COUNT(*) as total_ticks,
       MAX(tick) as match_duration_ticks,
       AVG(X) as avg_x_position,
       AVG(Y) as avg_y_position
FROM all_player_ticks
GROUP BY demo_name
ORDER BY total_ticks DESC;
```

## Data Schema

### player_ticks
- `m_iTeamNum` - Team number (2 or 3)
- `X`, `Y`, `Z` - Player coordinates
- `tick` - Game tick timestamp
- `steamid` - Player Steam ID
- `name` - Player name
- `demo_name` - Source demo file
- `data_type` - Always 'player_ticks'

### grenades  
- `grenade_type` - Type of grenade (CSmokeGrenade, etc.)
- `grenade_entity_id` - Entity ID
- `x`, `y`, `z` - Grenade coordinates (when thrown)
- `tick` - Game tick
- `steamid` - Player who threw grenade
- `name` - Player name
- `demo_name` - Source demo file
- `data_type` - Always 'grenades'

### player_info
- `steamid` - Player Steam ID
- `name` - Player name  
- `team_number` - Team assignment
- `demo_name` - Source demo file
- `data_type` - Always 'player_info'

### skins
- `def_index` - Weapon definition index
- `item_id` - Unique item ID
- `paint_index` - Skin paint pattern index
- `paint_seed` - Paint randomization seed
- `paint_wear` - Wear value (condition)
- `custom_name` - Custom name tag (if any)
- `steamid` - Owner Steam ID
- `demo_name` - Source demo file
- `data_type` - Always 'skins'

## LLM Analysis Tips

This data is perfect for LLM analysis! You can:

1. **Ask questions in natural language** about player performance, positioning, team coordination
2. **Request specific SQL queries** for tactical analysis
3. **Generate visualizations** using the coordinate data
4. **Compare players/teams** across different maps
5. **Analyze temporal patterns** using tick data

### Example LLM Prompts:
- "Which player moved the most across all maps?"
- "Show me the grenade usage patterns for each team"
- "Compare the average positions of players on different maps"
- "Find the most active areas on each map based on player movement"
- "Analyze team coordination patterns over time"

## Data Statistics
- **Total parquet files**: 20
- **Total data rows**: 27,464,627
- **Demos analyzed**: 5 (Falcons vs Vitality match series)
- **Maps**: Inferno, Dust2, Train, Mirage, Nuke
- **Players tracked**: 10 professional players
- **Time range**: Full match data with tick-level precision

## Requirements
- pandas
- duckdb  
- demoparser2
- pyarrow
- pathlib
- logging
