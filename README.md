# CS2 Demo Data Analysis with DuckDB

This repository contains tools to parse CS2 demo files and analyze them using DuckDB for efficient SQL-based analysis, with a comprehensive economic analysis pipeline for professional CS2 match preparation.

## Development & Agent Guidelines

- `codex.yaml` — Canonical agent and engineering guidelines (Python best practices, performance, error handling, data optimization, tooling).
- `.github/copilot-instructions.md` — Extended context and preferences for AI-assisted coding in this repo.
- `PIPELINE_GUIDE.md` — End-to-end pipeline overview and operational notes.

Note: Prior `CODE_INSTRUCTIONS.md` has been consolidated into `codex.yaml`.

## Files Overview

### Core Pipeline
- `pipeline.py` - Parses demo files using demoparser2 and converts to parquet format
- `duckdb_connector.py` - Provides DuckDB connection and analysis interface
- `example_analysis.py` - Demonstrates various analysis capabilities
- `verify_data.py` - Verifies the generated parquet files

### CS2 Economy Analysis (`cs2econ/`)
- `cli.py` - Command-line interface for economy operations
- `schemas.py` - Data schemas and validation for economic events
- `rules.py` - CS2 economic rules engine (2025 ruleset)
- `reducer.py` - Deterministic economic state computation
- `io_parquet.py` - Parquet I/O operations with caching

### Data Transformation
- `transform_demo_data.py` - Bridges demo parser output to economy pipeline format

## Quick Start

### 1. Parse Demo Files
```bash
python pipeline.py
```

### 2. Transform Data for Economic Analysis
```bash
python transform_demo_data.py --parquet-root parquet --output-root data
```

### 3. Generate Economic Analysis
```bash
# Recompute economic state from events
python -m cs2econ.cli recompute --events-root data/events

# Export economic analysis for a specific match
python -m cs2econ.cli export falcons-vs-vitality-m1-inferno --format json --output-file reports/economic_analysis.json

# Verify data integrity
python -m cs2econ.cli verify falcons-vs-vitality-m1-inferno --data-root data
```

### 4. Analyze Data with DuckDB
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

### CS2 Economy Analysis
- `balances/balances.parquet` - Economic balance records by round and team
- `snapshots/snapshots.parquet` - Round-by-round economic summaries
- `state/state.parquet` - Detailed economic state transitions with audit trails
- `events/match_id=*/events.parquet` - Transformed economic events (Hive partitioned)

### Unified Views (across all demos):
- `all_player_ticks` - Player positions and movement data (11.6M+ rows)
- `all_grenades` - Grenade usage and trajectories (15.8M+ rows)  
- `all_player_info` - Player information and team assignments (50 rows)
- `all_skins` - Weapon skin data (145 rows)

### Individual Demo Views:
- `{demo_name}_{data_type}` - e.g., `falcons_vs_vitality_m1_inferno_player_ticks`

## Sample Analysis Queries

### CS2 Economic Analysis
```sql
-- Team economic performance by round
SELECT match_id, round_number, team,
       bank_total_start, spend_sum, kill_reward_sum,
       plant_bonus_team + planter_bonus as plant_bonus_total,
       bank_total_end
FROM read_parquet('data/balances/balances.parquet')
ORDER BY match_id, round_number, team;

-- Economic efficiency analysis
SELECT match_id, team,
       AVG(bank_total_start) as avg_start_money,
       AVG(spend_sum) as avg_spending,
       AVG(kill_reward_sum) as avg_kill_rewards,
       AVG(bank_total_end) as avg_end_money
FROM read_parquet('data/balances/balances.parquet')
GROUP BY match_id, team
ORDER BY match_id, team;

-- Economic momentum analysis
SELECT s1.match_id, s1.round_number,
       s1.team, s1.bank_total_end as current_bank,
       s2.bank_total_end as next_bank,
       (s2.bank_total_end - s1.bank_total_end) as bank_change
FROM read_parquet('data/snapshots/snapshots.parquet') s1
LEFT JOIN read_parquet('data/snapshots/snapshots.parquet') s2 
  ON s1.match_id = s2.match_id 
  AND s1.team = s2.team 
  AND s1.round_number = s2.round_number - 1
ORDER BY s1.match_id, s1.round_number, s1.team;
```

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

### CS2 Economy Data

#### balances.parquet
Economic balance records tracking money flow by round and team:
- `match_id` - Match identifier
- `round_number` - Round number (1-30)
- `team` - Team identifier ("T" or "CT")
- `bank_total_start` - Team money at round start
- `equip_total_start` - Equipment value at round start
- `spend_sum` - Total spending during round
- `kill_reward_sum` - Money earned from kills
- `win_reward` - Money from round win
- `loss_bonus` - Loss bonus money
- `plant_bonus_team` - Team plant bonus ($800)
- `planter_bonus` - Individual planter bonus ($300)
- `defuse_bonus` - Defuse bonus ($250)
- `bank_total_end` - Team money at round end
- `equip_total_end` - Equipment value at round end
- `checksum` - Data integrity checksum
- `rules_version` - Economic rules version

#### snapshots.parquet
Round-by-round economic summaries:
- Similar to balances but aggregated per round
- Includes event IDs for audit trail
- Deterministic checksums for verification

#### state.parquet  
Detailed economic state transitions:
- Granular state changes during rounds
- Event-by-event economic impacts
- Full audit trail with timestamps

#### events.parquet (Hive partitioned by match_id)
Transformed economic events:
- `match_id` - Match identifier
- `round_number` - Estimated round number
- `tick` - Game tick timestamp
- `event_id` - Unique event identifier
- `type` - Event type (kill, death_after_time, plant, defuse, round_start, round_end)
- `actor_steamid` - Player performing action
- `victim_steamid` - Target player (for kills/deaths)
- `team` - Team of the actor
- `weapon` - Weapon used
- `price` - Economic value (if applicable)
- `amount` - Monetary amount
- `payload` - Additional event data (JSON)
- `ingest_source` - Data source ("demo_parser")
- `ts_ingested` - Processing timestamp

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

## CS2 Economy Analysis Features

### Professional Team Preparation
- **Deterministic economic calculations** following official CS2 rules (2025 ruleset)
- **Round-by-round financial tracking** with complete audit trails
- **Anti-stratting insights** - identify predictable economic patterns
- **Force-buy detection** and economic pressure analysis
- **Plant/defuse bonus tracking** for tactical planning

### Economic Analysis Types
1. **Balance Analysis** - Track team money flow round by round
2. **Spending Patterns** - Analyze purchasing decisions and timing
3. **Economic Efficiency** - Measure return on investment for equipment
4. **Momentum Analysis** - Identify economic advantages and vulnerabilities
5. **Force-Buy Situations** - Detect when teams are economically pressured

### Data Integrity & Reliability
- **Checksums** for all economic calculations
- **Deterministic processing** ensures consistent results
- **Event audit trails** for complete transparency
- **Rules engine** based on official CS2 economic mechanics
- **Validation commands** to verify data accuracy

### CLI Commands
```bash
# Recompute all economic data
python -m cs2econ.cli recompute --events-root data/events --output-root data

# Export analysis for specific match (all rounds)
python -m cs2econ.cli export <match_id> --format [table|json] --data-root data

# Export analysis for specific round
python -m cs2econ.cli export <match_id> --round-num <round_number> --format table --data-root data

# Verify data integrity
python -m cs2econ.cli verify <match_id> --data-root data

# Example: Export round 1 analysis for inferno match
python -m cs2econ.cli export falcons-vs-vitality-m1-inferno --round-num 1 --format table
```

**Note**: The demo data contains only partial rounds (typically rounds 1-2 per match) due to truncated demo files. The CLI will show available rounds if you request a non-existent round number.

## LLM Analysis Tips

This data is perfect for LLM analysis! You can:

1. **Ask questions in natural language** about player performance, positioning, team coordination, and economic strategies
2. **Request specific SQL queries** for tactical analysis and economic insights
3. **Generate visualizations** using the coordinate data and economic trends
4. **Compare players/teams** across different maps and economic situations
5. **Analyze temporal patterns** using tick data and round progression
6. **Economic strategy analysis** - force buys, eco rounds, investment patterns
7. **Anti-stratting preparation** - identify predictable economic behaviors

### Example LLM Prompts:
#### Tactical Analysis
- "Which player moved the most across all maps?"
- "Show me the grenade usage patterns for each team"
- "Compare the average positions of players on different maps"
- "Find the most active areas on each map based on player movement"
- "Analyze team coordination patterns over time"

#### Economic Analysis
- "Show me the economic performance of each team by round"
- "Which team had better economic efficiency in this match?"
- "Identify rounds where teams were forced to eco or force-buy"
- "Analyze the impact of plant bonuses on team economics"
- "Compare spending patterns between T and CT sides"
- "Find economic momentum shifts during the match"
- "Show me round 1 vs round 2 economic differences for falcons-vs-vitality-m1-inferno"

## Data Statistics
- **Total parquet files**: 20+ (including economic analysis data)
- **Total data rows**: 27,464,627+ (demo data) + 396 (economic records)
- **Demos analyzed**: 5 (Falcons vs Vitality match series)
- **Maps**: Inferno, Dust2, Train, Mirage, Nuke
- **Players tracked**: 10 professional players
- **Time range**: Full match data with tick-level precision
- **Economic records**: 240 balance records, 12 snapshots, 144 state records
- **Economic events**: 1,905 transformed events (kills, deaths, plants, defuses)

## Requirements
- pandas
- duckdb  
- demoparser2
- pyarrow
- pathlib
- logging
- polars (for economic analysis)
- typer (for CLI interface)
- rich (for formatted output)
