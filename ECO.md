You are my senior engineer. Build a deterministic CS2 economy snapshot pipeline that reads demo events already stored in Parquet, reduces them into per round player balances and team snapshots with lineage, and writes Parquet outputs. Keep it simple, testable, and replayable. Use Python 3.12 with Polars for the reducer and DuckDB for SQL rollups; no servers; local only.

## Objectives
1) Read normalized events from Parquet partitions into a stable, sorted stream.
2) Deterministically reduce events into:
   a) per player balances at round start and end
   b) per team round snapshots with accounting fields and lineage
3) Persist outputs to Parquet; keep schemas versioned with a rules_version tag.
4) Provide a tiny CLI for ingest-from-parquet, recompute, and export.
5) Ship unit tests plus a golden fixture to verify checksums and totals.

## Input layout in Parquet
Partitioned by match and optionally round.
- path: events/match_id=*/round_number=*/part-*.parquet

Event schema; evolve if needed for clarity.
- match_id: STRING
- round_number: INT
- tick: INT
- event_id: STRING               # unique and stable
- type: STRING                   # buy, kill, assist, plant, defuse, round_start, round_end, money, death_after_time
- actor_steamid: STRING
- victim_steamid: STRING null
- team: STRING                   # T or CT
- weapon: STRING null
- price: INT null                # for buy events
- amount: INT null               # explicit money deltas when present
- payload: JSON                  # win_type, winner, planted_site, etc.
- ingest_source: STRING
- ts_ingested: TIMESTAMP

Sorting rule for determinism:
- order by match_id, round_number, tick, event_id

## Output schemas in Parquet
balances/part-*.parquet
- match_id, round_number, player_steamid, team, at    # 'start' or 'end'
- bank: INT
- equipment_value: INT
- loss_streak: INT
- cap_hit: INT default 0
- rules_version: STRING

snapshots/part-*.parquet
- match_id, round_number, team
- bank_total_start: INT
- equip_total_start: INT
- spend_sum: INT
- kill_reward_sum: INT
- win_reward: INT
- loss_bonus: INT
- plant_bonus_team: INT
- planter_bonus: INT
- defuse_bonus: INT
- bank_total_end: INT
- equip_total_end: INT
- inputs_event_ids: LIST<STRING>    # sorted
- checksum: STRING                  # sha256 of "sorted input ids" plus rules_version
- rules_version: STRING

state/part-*.parquet
- match_id, round_number, team, loss_streak_after
- match_id, round_number, player_steamid, zero_income_next_round

## Rules module
Create rules.py with a frozen Rules dataclass and helpers.
- money_cap: 16000
- start_money: 800
- kill_reward categories:
  knife 1500; smg_default 600; p90 300; shotgun_default 900; xm1014 600; rifle 300; pistol 300; grenade 300; awp 100; zeus 100
- win_reward:
  elimination 3250; t_bomb_explosion 3500; ct_defuse 3500; ct_time_expired_no_plant 3250
- loss_bonus_ladder = [1400, 1900, 2400, 2900, 3400]
- t_plant_team_bonus_on_loss = 800
- actor_objective_bonus = 300
- zero_income_condition = "t_dies_after_time_no_plant"
- version string like "2025_09"
Expose:
- kill_reward_for(weapon_name: str) -> int
- DEFAULT_RULES constant

## Project layout
.
├─ cs2econ/
│  ├─ rules.py
│  ├─ reducer.py
│  ├─ schemas.py
│  ├─ io_parquet.py
│  ├─ rollups_duckdb.sql
│  ├─ cli.py
│  └─ __init__.py
├─ data/
│  ├─ events/...
│  ├─ balances/
│  ├─ snapshots/
│  └─ state/
├─ tests/
│  ├─ test_rules.py
│  ├─ test_reducer_unit.py
│  ├─ test_reducer_golden.py
│  └─ test_duckdb_rollups.py
├─ pyproject.toml
├─ Makefile
└─ README.md

## Implementation details
Use Polars for the reducer.
- Scan events with pl.scan_parquet("events/match_id=*/round_number=*/*.parquet")
- Sort by match_id, round_number, tick, event_id
- Group by match_id, round_number; collect per round into a DataFrame; run a pure reducer

Reducer contract in reducer.py:
- reduce_round(prev_team_state, prev_player_state, round_df, rules) -> tuple:
  new_team_state, new_player_state, balances_rows, snapshot_row, lineage_event_ids
- prev_team_state holds loss_streak per team and carries across rounds
- prev_player_state holds bank, equipment_value, zero_income flags per player
- Apply buy events; subtract price from bank; add to equipment_value
- Apply kill rewards using rules.kill_reward_for
- On plant; award planter personal 300 at round end; if T loses after plant award 800 per T player
- On defuse; add defuser personal 300 and CT win reward 3500
- On round_end; award win rewards; apply loss bonus ladder using current loss streak; reset or increment streaks
- Handle zero income next round for T who dies after time with no plant
- Clamp to money cap at end of round
- Compute spend_sum, kill_reward_sum, win_reward, loss_bonus, plant_bonus_team, planter_bonus, defuse_bonus
- Produce lineage as a sorted list of event_id; compute checksum as sha256(joined ids plus rules_version)

State machine loop:
- For each match_id order rounds ascending
- Carry forward team and player state
- Write balances rows (start and end) and snapshot row for each round

I/O in io_parquet.py:
- read_events() -> LazyFrame
- write_balances(df) -> Parquet
- write_snapshots(df) -> Parquet
- write_state(df) -> Parquet

DuckDB rollups in rollups_duckdb.sql:
- A view that computes per round aggregates from events for cross-checks
- A weapon classification macro for SQL parity with rules
- Optional: materialize snapshots from events only and compare against reducer outputs

## CLI in cli.py
- python -m cs2econ.cli recompute --events-root data/events --out-root data
  Scans events, runs reducer, writes balances, snapshots, and state
- python -m cs2econ.cli export --match <id> --round <n> --format csv
- python -m cs2econ.cli verify --match <id>
  Rebuild from events and compare checksums against snapshots

## Tests
Golden fixture in data/events for one small match that covers:
- pistol conversion
- T plant but round loss
- CT defuse
- P90 and AWP kills
- death after time with no plant
Tests should assert:
- mapping of weapons to reward categories
- no bank below zero or above cap
- round accounting identity:
  start_bank + win_reward + loss_bonus + kill_reward_sum + planter_bonus + defuse_bonus + plant_bonus_team − spend_sum = end_bank
- checksums are stable across runs
- DuckDB rollups match reducer totals for spend and kill rewards

## Tooling
- pyproject.toml with polars, duckdb, rich, pytest, ruff, black
- Makefile targets:
  make venv; make fmt; make lint; make test; make run
- README with quickstart and sample commands

## Acceptance criteria
- Running the CLI produces balances.parquet, snapshots.parquet, and state.parquet under data
- Recompute is deterministic; checksums are stable
- Golden fixture tests pass
- Code is typed; reducer is pure; no hidden global state
- Works without network access

Start by scaffolding the package, rules, and reducer skeleton with types and docstrings. Then implement the reducer, write the CLI, create the tests, and finalize the DuckDB verification script. Keep functions small; prefer clarity over cleverness.
