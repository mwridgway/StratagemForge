"""Transform demo parser data into CS2 economy pipeline format.

This script converts raw demo parser parquet files into the structured
format expected by the CS2 economy analysis pipeline.
"""

import logging
import pandas as pd
import polars as pl
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def estimate_round_from_tick(tick: int, ticks_per_round: int = 120000) -> int:
    """Estimate round number from tick (rough approximation)."""
    # CS2 rounds are roughly 2 minutes (120 seconds) at 128 ticks/second
    # This is a rough estimate - real round detection would need game state events
    return max(1, (tick // ticks_per_round) + 1)


def transform_player_death_events(df: pd.DataFrame, match_id: str) -> pd.DataFrame:
    """Transform player_death events to economy pipeline format."""
    if df.empty:
        return pd.DataFrame()
    
    events = []
    for _, row in df.iterrows():
        # Create kill event
        kill_event = {
            "match_id": match_id,
            "round_number": estimate_round_from_tick(row["tick"]),
            "tick": row["tick"],
            "event_id": f"{match_id}_kill_{row['tick']}_{row.get('attacker_steamid', 'unknown')}",
            "type": "kill",
            "actor_steamid": row.get("attacker_steamid", ""),
            "victim_steamid": row.get("user_steamid", ""),
            "team": "T" if "terrorist" in str(row.get("attacker_name", "")).lower() else "CT",  # Rough team detection
            "weapon": row.get("weapon", ""),
            "price": None,
            "amount": None,
            "payload": json.dumps({
                "headshot": row.get("headshot", False),
                "damage": row.get("dmg_health", 0),
                "distance": row.get("distance", 0)
            }),
            "ingest_source": "demo_parser",
            "ts_ingested": datetime.now().isoformat()
        }
        events.append(kill_event)
        
        # Create death event for victim
        death_event = {
            "match_id": match_id,
            "round_number": estimate_round_from_tick(row["tick"]),
            "tick": row["tick"],
            "event_id": f"{match_id}_death_{row['tick']}_{row.get('user_steamid', 'unknown')}",
            "type": "death_after_time",
            "actor_steamid": row.get("user_steamid", ""),
            "victim_steamid": None,
            "team": "CT" if "terrorist" in str(row.get("attacker_name", "")).lower() else "T",  # Opposite team
            "weapon": row.get("weapon", ""),
            "price": None,
            "amount": None,
            "payload": json.dumps({
                "killer": row.get("attacker_steamid", ""),
                "weapon": row.get("weapon", "")
            }),
            "ingest_source": "demo_parser",
            "ts_ingested": datetime.now().isoformat()
        }
        events.append(death_event)
    
    return pd.DataFrame(events)


def transform_bomb_events(df: pd.DataFrame, match_id: str, event_type: str) -> pd.DataFrame:
    """Transform bomb plant/defuse events to economy pipeline format."""
    if df.empty:
        return pd.DataFrame()
    
    events = []
    for _, row in df.iterrows():
        event = {
            "match_id": match_id,
            "round_number": estimate_round_from_tick(row["tick"]),
            "tick": row["tick"],
            "event_id": f"{match_id}_{event_type}_{row['tick']}_{row.get('user_steamid', 'unknown')}",
            "type": event_type,
            "actor_steamid": row.get("user_steamid", ""),
            "victim_steamid": None,
            "team": "T" if event_type == "plant" else "CT",
            "weapon": None,
            "price": None,
            "amount": None,
            "payload": json.dumps({
                "site": row.get("site", ""),
                "tick": row["tick"]
            }),
            "ingest_source": "demo_parser",
            "ts_ingested": datetime.now().isoformat()
        }
        events.append(event)
    
    return pd.DataFrame(events)


def create_round_start_end_events(match_id: str, max_tick: int) -> pd.DataFrame:
    """Create synthetic round start/end events based on tick estimation."""
    events = []
    ticks_per_round = 120000  # Rough estimate
    
    # Estimate number of rounds
    max_round = estimate_round_from_tick(max_tick)
    
    for round_num in range(1, max_round + 1):
        start_tick = (round_num - 1) * ticks_per_round
        end_tick = round_num * ticks_per_round
        
        # Round start event
        start_event = {
            "match_id": match_id,
            "round_number": round_num,
            "tick": start_tick,
            "event_id": f"{match_id}_round_start_{round_num}",
            "type": "round_start",
            "actor_steamid": "",
            "victim_steamid": None,
            "team": "",
            "weapon": None,
            "price": None,
            "amount": None,
            "payload": json.dumps({"round": round_num}),
            "ingest_source": "demo_parser",
            "ts_ingested": datetime.now().isoformat()
        }
        events.append(start_event)
        
        # Round end event (assume T wins for now - would need actual game state)
        end_event = {
            "match_id": match_id,
            "round_number": round_num,
            "tick": end_tick,
            "event_id": f"{match_id}_round_end_{round_num}",
            "type": "round_end",
            "actor_steamid": "",
            "victim_steamid": None,
            "team": "T",  # Simplified - would need actual win detection
            "weapon": None,
            "price": None,
            "amount": None,
            "payload": json.dumps({
                "winner": "T",
                "win_type": "elimination",
                "round": round_num
            }),
            "ingest_source": "demo_parser",
            "ts_ingested": datetime.now().isoformat()
        }
        events.append(end_event)
    
    return pd.DataFrame(events)


def transform_match_to_economy_events(match_folder: Path) -> pd.DataFrame:
    """Transform all events from a single match into economy pipeline format."""
    match_id = match_folder.name.replace("match_id=", "")
    logger.info(f"Transforming {match_id}...")
    
    all_events = []
    max_tick = 0
    
    # Process player death events
    death_file = match_folder / "event_player_death" / "event_player_death.parquet"
    if death_file.exists():
        death_df = pd.read_parquet(death_file)
        if not death_df.empty:
            max_tick = max(max_tick, death_df["tick"].max())
            death_events = transform_player_death_events(death_df, match_id)
            all_events.append(death_events)
    
    # Process bomb plant events
    plant_file = match_folder / "event_bomb_planted" / "event_bomb_planted.parquet"
    if plant_file.exists():
        plant_df = pd.read_parquet(plant_file)
        if not plant_df.empty:
            max_tick = max(max_tick, plant_df["tick"].max())
            plant_events = transform_bomb_events(plant_df, match_id, "plant")
            all_events.append(plant_events)
    
    # Process bomb defuse events
    defuse_file = match_folder / "event_bomb_defused" / "event_bomb_defused.parquet"
    if defuse_file.exists():
        defuse_df = pd.read_parquet(defuse_file)
        if not defuse_df.empty:
            max_tick = max(max_tick, defuse_df["tick"].max())
            defuse_events = transform_bomb_events(defuse_df, match_id, "defuse")
            all_events.append(defuse_events)
    
    # Create round start/end events
    if max_tick > 0:
        round_events = create_round_start_end_events(match_id, max_tick)
        all_events.append(round_events)
    
    # Combine all events
    if all_events:
        combined_df = pd.concat(all_events, ignore_index=True)
        # Sort by tick for deterministic ordering
        combined_df = combined_df.sort_values(["round_number", "tick", "event_id"])
        return combined_df
    else:
        return pd.DataFrame()


def transform_all_matches(parquet_root: str, output_root: str) -> None:
    """Transform all matches from demo format to economy pipeline format."""
    parquet_path = Path(parquet_root)
    output_path = Path(output_root)
    output_path.mkdir(exist_ok=True)
    
    # Find all match folders
    match_folders = [f for f in parquet_path.iterdir() if f.is_dir() and f.name.startswith("match_id=")]
    
    logger.info(f"Found {len(match_folders)} matches to transform")
    
    all_events = []
    
    for match_folder in match_folders:
        try:
            match_events = transform_match_to_economy_events(match_folder)
            if not match_events.empty:
                all_events.append(match_events)
                logger.info(f"  Transformed {len(match_events)} events from {match_folder.name}")
        except Exception as e:
            logger.error(f"  Failed to transform {match_folder.name}: {e}")
    
    if all_events:
        # Combine all events
        final_df = pd.concat(all_events, ignore_index=True)
        
        # Save as parquet with match_id partitioning for economy pipeline
        output_events_path = output_path / "events"
        output_events_path.mkdir(exist_ok=True)
        
        # Write each match to its own partition folder in Hive format
        for match_id, group_df in final_df.groupby("match_id"):
            match_partition_path = output_events_path / f"match_id={match_id}"
            match_partition_path.mkdir(exist_ok=True)
            
            # Write to parquet file within the partition
            group_df.to_parquet(
                match_partition_path / "events.parquet",
                engine="pyarrow",
                compression="snappy"
            )
        
        logger.info(f"✅ Transformed {len(final_df)} total events and saved to {output_events_path}")
        logger.info(f"📊 Events breakdown:")
        event_counts = final_df.groupby("type").size().sort_values(ascending=False)
        for event_type, count in event_counts.items():
            logger.info(f"  {event_type}: {count:,} events")
    else:
        logger.warning("No events found to transform")


if __name__ == "__main__":
    import typer
    
    def main(
        parquet_root: str = typer.Option("parquet", help="Root directory with demo parser parquet files"),
        output_root: str = typer.Option("data", help="Output directory for economy pipeline events"),
    ):
        """Transform demo parser data into CS2 economy pipeline format."""
        transform_all_matches(parquet_root, output_root)
    
    typer.run(main)
