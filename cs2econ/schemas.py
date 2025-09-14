"""Schema definitions for CS2 Economy Pipeline.

This module defines the data schemas for input events and output tables
used in the economy analysis pipeline.
"""

from typing import Any, Dict, List, Optional
import polars as pl
from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    """Schema for input event data."""
    
    match_id: str
    round_number: int
    tick: int
    event_id: str = Field(description="Unique and stable event identifier")
    type: str = Field(description="Event type: buy, kill, assist, plant, defuse, round_start, round_end, money, death_after_time")
    actor_steamid: str
    victim_steamid: Optional[str] = None
    team: str = Field(description="T or CT")
    weapon: Optional[str] = None
    price: Optional[int] = Field(default=None, description="For buy events")
    amount: Optional[int] = Field(default=None, description="Explicit money deltas when present")
    payload: Optional[Dict[str, Any]] = Field(default=None, description="win_type, winner, planted_site, etc.")
    ingest_source: str
    ts_ingested: str  # timestamp as string for Polars compatibility


class BalanceSchema(BaseModel):
    """Schema for player balance snapshots."""
    
    match_id: str
    round_number: int
    player_steamid: str
    team: str
    at: str = Field(description="'start' or 'end'")
    bank: int
    equipment_value: int
    loss_streak: int
    cap_hit: int = Field(default=0, description="Amount capped due to money limit")
    rules_version: str


class SnapshotSchema(BaseModel):
    """Schema for team round economic snapshots."""
    
    match_id: str
    round_number: int
    team: str
    bank_total_start: int
    equip_total_start: int
    spend_sum: int
    kill_reward_sum: int
    win_reward: int
    loss_bonus: int
    plant_bonus_team: int
    planter_bonus: int
    defuse_bonus: int
    bank_total_end: int
    equip_total_end: int
    inputs_event_ids: List[str] = Field(description="Sorted list of input event IDs")
    checksum: str = Field(description="SHA256 of sorted input IDs plus rules_version")
    rules_version: str


class StateSchema(BaseModel):
    """Schema for persistent state between rounds."""
    
    match_id: str
    round_number: int
    team: Optional[str] = None
    player_steamid: Optional[str] = None
    loss_streak_after: Optional[int] = None
    zero_income_next_round: Optional[bool] = None


# Polars schema definitions for efficient I/O
EVENTS_POLARS_SCHEMA = {
    "match_id": pl.Utf8,
    "round_number": pl.Int32,
    "tick": pl.Int32,
    "event_id": pl.Utf8,
    "type": pl.Utf8,
    "actor_steamid": pl.Utf8,
    "victim_steamid": pl.Utf8,
    "team": pl.Utf8,
    "weapon": pl.Utf8,
    "price": pl.Int32,
    "amount": pl.Int32,
    "payload": pl.Utf8,  # JSON string
    "ingest_source": pl.Utf8,
    "ts_ingested": pl.Utf8,
}

BALANCES_POLARS_SCHEMA = {
    "match_id": pl.Utf8,
    "round_number": pl.Int32,
    "player_steamid": pl.Utf8,
    "team": pl.Utf8,
    "at": pl.Utf8,
    "bank": pl.Int32,
    "equipment_value": pl.Int32,
    "loss_streak": pl.Int32,
    "cap_hit": pl.Int32,
    "rules_version": pl.Utf8,
}

SNAPSHOTS_POLARS_SCHEMA = {
    "match_id": pl.Utf8,
    "round_number": pl.Int32,
    "team": pl.Utf8,
    "bank_total_start": pl.Int32,
    "equip_total_start": pl.Int32,
    "spend_sum": pl.Int32,
    "kill_reward_sum": pl.Int32,
    "win_reward": pl.Int32,
    "loss_bonus": pl.Int32,
    "plant_bonus_team": pl.Int32,
    "planter_bonus": pl.Int32,
    "defuse_bonus": pl.Int32,
    "bank_total_end": pl.Int32,
    "equip_total_end": pl.Int32,
    "inputs_event_ids": pl.List(pl.Utf8),
    "checksum": pl.Utf8,
    "rules_version": pl.Utf8,
}

STATE_POLARS_SCHEMA = {
    "match_id": pl.Utf8,
    "round_number": pl.Int32,
    "team": pl.Utf8,
    "player_steamid": pl.Utf8,
    "loss_streak_after": pl.Int32,
    "zero_income_next_round": pl.Boolean,
}


def create_empty_balance_df() -> pl.DataFrame:
    """Create empty balance DataFrame with correct schema."""
    return pl.DataFrame(schema=BALANCES_POLARS_SCHEMA)


def create_empty_snapshot_df() -> pl.DataFrame:
    """Create empty snapshot DataFrame with correct schema."""
    return pl.DataFrame(schema=SNAPSHOTS_POLARS_SCHEMA)


def create_empty_state_df() -> pl.DataFrame:
    """Create empty state DataFrame with correct schema."""
    return pl.DataFrame(schema=STATE_POLARS_SCHEMA)


def validate_events_df(df: pl.DataFrame) -> None:
    """Validate that events DataFrame has required columns and types.
    
    Args:
        df: Events DataFrame to validate
        
    Raises:
        ValueError: If schema validation fails
    """
    required_cols = {"match_id", "round_number", "tick", "event_id", "type", "actor_steamid", "team"}
    missing_cols = required_cols - set(df.columns)
    
    if missing_cols:
        raise ValueError(f"Events DataFrame missing required columns: {missing_cols}")
    
    # Check that we can sort by the required columns
    try:
        df.select(["match_id", "round_number", "tick", "event_id"]).head(1)
    except Exception as e:
        raise ValueError(f"Events DataFrame cannot be sorted by required columns: {e}")


def ensure_events_sorted(df: pl.DataFrame) -> pl.DataFrame:
    """Ensure events DataFrame is sorted deterministically.
    
    Args:
        df: Events DataFrame
        
    Returns:
        Sorted DataFrame
    """
    return df.sort(["match_id", "round_number", "tick", "event_id"])
