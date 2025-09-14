"""Parquet I/O operations for CS2 Economy Pipeline.

This module handles reading events from partitioned Parquet files and
writing output data to Parquet format.
"""

import logging
from pathlib import Path
from typing import Optional

import polars as pl

from .schemas import (
    BALANCES_POLARS_SCHEMA,
    SNAPSHOTS_POLARS_SCHEMA,
    STATE_POLARS_SCHEMA,
    ensure_events_sorted,
    validate_events_df,
)

logger = logging.getLogger(__name__)


def read_events(events_root: str | Path, match_id: Optional[str] = None) -> pl.LazyFrame:
    """Read events from partitioned Parquet files.
    
    Args:
        events_root: Root directory containing partitioned event data
        match_id: Optional match ID filter for single match processing
        
    Returns:
        LazyFrame with events sorted deterministically
        
    Raises:
        FileNotFoundError: If events directory doesn't exist
        ValueError: If no event files found
    """
    events_path = Path(events_root)
    
    if not events_path.exists():
        raise FileNotFoundError(f"Events directory not found: {events_path}")
    
    # Build glob pattern based on whether we're filtering by match
    if match_id:
        pattern = f"match_id={match_id}/**/*.parquet"
    else:
        pattern = "match_id=*/**/*.parquet"
    
    # Find all matching parquet files
    parquet_files = list(events_path.glob(pattern))
    
    if not parquet_files:
        raise ValueError(f"No parquet files found in {events_path} with pattern {pattern}")
    
    logger.info(f"Found {len(parquet_files)} event files to process")
    
    # Read all files as a lazy frame
    lf = pl.scan_parquet(events_path / pattern)
    
    # Sort deterministically for consistent processing
    lf = lf.sort(["match_id", "round_number", "tick", "event_id"])
    
    return lf


def read_events_eager(events_root: str | Path, match_id: Optional[str] = None) -> pl.DataFrame:
    """Read events into memory as DataFrame.
    
    Args:
        events_root: Root directory containing partitioned event data
        match_id: Optional match ID filter for single match processing
        
    Returns:
        DataFrame with events sorted deterministically
    """
    lf = read_events(events_root, match_id)
    df = lf.collect()
    
    # Validate the schema
    validate_events_df(df)
    
    # Ensure proper sorting
    df = ensure_events_sorted(df)
    
    logger.info(f"Loaded {len(df)} events from {events_root}")
    
    return df


def write_balances(df: pl.DataFrame, output_root: str | Path) -> None:
    """Write player balance data to Parquet.
    
    Args:
        df: Balance DataFrame to write
        output_root: Root directory for output files
    """
    output_path = Path(output_root) / "balances"
    output_path.mkdir(parents=True, exist_ok=True)
    
    if df.is_empty():
        logger.warning("No balance data to write")
        return
    
    # Validate schema
    expected_cols = set(BALANCES_POLARS_SCHEMA.keys())
    actual_cols = set(df.columns)
    
    if not expected_cols.issubset(actual_cols):
        missing = expected_cols - actual_cols
        raise ValueError(f"Balance DataFrame missing columns: {missing}")
    
    # Write partitioned by match_id for efficient querying
    output_file = output_path / "balances.parquet"
    
    df.write_parquet(
        output_file,
        compression="snappy",
        use_pyarrow=True,
        pyarrow_options={"write_statistics": True}
    )
    
    logger.info(f"Wrote {len(df)} balance records to {output_file}")


def write_snapshots(df: pl.DataFrame, output_root: str | Path) -> None:
    """Write team round snapshots to Parquet.
    
    Args:
        df: Snapshot DataFrame to write
        output_root: Root directory for output files
    """
    output_path = Path(output_root) / "snapshots"
    output_path.mkdir(parents=True, exist_ok=True)
    
    if df.is_empty():
        logger.warning("No snapshot data to write")
        return
    
    # Validate schema
    expected_cols = set(SNAPSHOTS_POLARS_SCHEMA.keys())
    actual_cols = set(df.columns)
    
    if not expected_cols.issubset(actual_cols):
        missing = expected_cols - actual_cols
        raise ValueError(f"Snapshot DataFrame missing columns: {missing}")
    
    # Write partitioned by match_id for efficient querying
    output_file = output_path / "snapshots.parquet"
    
    df.write_parquet(
        output_file,
        compression="snappy", 
        use_pyarrow=True,
        pyarrow_options={"write_statistics": True}
    )
    
    logger.info(f"Wrote {len(df)} snapshot records to {output_file}")


def write_state(df: pl.DataFrame, output_root: str | Path) -> None:
    """Write persistent state data to Parquet.
    
    Args:
        df: State DataFrame to write
        output_root: Root directory for output files
    """
    output_path = Path(output_root) / "state"
    output_path.mkdir(parents=True, exist_ok=True)
    
    if df.is_empty():
        logger.warning("No state data to write")
        return
    
    # Validate schema
    expected_cols = set(STATE_POLARS_SCHEMA.keys())
    actual_cols = set(df.columns)
    
    if not expected_cols.issubset(actual_cols):
        missing = expected_cols - actual_cols
        raise ValueError(f"State DataFrame missing columns: {missing}")
    
    # Write partitioned by match_id for efficient querying
    output_file = output_path / "state.parquet"
    
    df.write_parquet(
        output_file,
        compression="snappy",
        use_pyarrow=True,
        pyarrow_options={"write_statistics": True}
    )
    
    logger.info(f"Wrote {len(df)} state records to {output_file}")


def read_existing_snapshots(output_root: str | Path, match_id: Optional[str] = None) -> pl.DataFrame:
    """Read existing snapshot data for verification.
    
    Args:
        output_root: Root directory containing output files
        match_id: Optional match ID filter
        
    Returns:
        DataFrame with existing snapshots, empty if none found
    """
    snapshots_path = Path(output_root) / "snapshots" / "snapshots.parquet"
    
    if not snapshots_path.exists():
        logger.info("No existing snapshots found")
        return pl.DataFrame(schema=SNAPSHOTS_POLARS_SCHEMA)
    
    try:
        df = pl.read_parquet(snapshots_path)
        
        if match_id:
            df = df.filter(pl.col("match_id") == match_id)
        
        logger.info(f"Read {len(df)} existing snapshot records")
        return df
        
    except Exception as e:
        logger.warning(f"Failed to read existing snapshots: {e}")
        return pl.DataFrame(schema=SNAPSHOTS_POLARS_SCHEMA)


def read_existing_balances(output_root: str | Path, match_id: Optional[str] = None) -> pl.DataFrame:
    """Read existing balance data for verification.
    
    Args:
        output_root: Root directory containing output files  
        match_id: Optional match ID filter
        
    Returns:
        DataFrame with existing balances, empty if none found
    """
    balances_path = Path(output_root) / "balances" / "balances.parquet"
    
    if not balances_path.exists():
        logger.info("No existing balances found")
        return pl.DataFrame(schema=BALANCES_POLARS_SCHEMA)
    
    try:
        df = pl.read_parquet(balances_path)
        
        if match_id:
            df = df.filter(pl.col("match_id") == match_id)
        
        logger.info(f"Read {len(df)} existing balance records")
        return df
        
    except Exception as e:
        logger.warning(f"Failed to read existing balances: {e}")
        return pl.DataFrame(schema=BALANCES_POLARS_SCHEMA)


def clear_output_files(output_root: str | Path) -> None:
    """Clear all output files for a fresh run.
    
    Args:
        output_root: Root directory containing output files
    """
    output_path = Path(output_root)
    
    for subdir in ["balances", "snapshots", "state"]:
        dir_path = output_path / subdir
        if dir_path.exists():
            for file in dir_path.glob("*.parquet"):
                file.unlink()
                logger.info(f"Removed {file}")
    
    logger.info("Cleared all output files")
