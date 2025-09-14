"""Command-line interface for CS2 Economy Pipeline.

This module provides CLI commands for recomputing economic data,
exporting results, and verifying data integrity.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import polars as pl
import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .io_parquet import (
    read_events_eager,
    write_balances,
    write_snapshots,
    write_state,
    read_existing_snapshots,
    clear_output_files,
)
from .reducer import reduce_match
from .rules import DEFAULT_RULES

# Set up rich console
console = Console()
app = typer.Typer(name="cs2econ", help="CS2 Economy Analysis Pipeline")


def setup_logging(verbose: bool = False) -> None:
    """Set up logging with rich handler."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )


@app.command()
def recompute(
    events_root: str = typer.Option("data/events", help="Root directory for event parquet files"),
    out_root: str = typer.Option("data", help="Root directory for output files"),
    match_id: Optional[str] = typer.Option(None, help="Process specific match only"),
    clear: bool = typer.Option(False, help="Clear existing output files first"),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
) -> None:
    """Recompute economic data from events."""
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    console.print("🎮 [bold blue]CS2 Economy Pipeline - Recompute[/bold blue]")
    console.print(f"Events root: {events_root}")
    console.print(f"Output root: {out_root}")
    if match_id:
        console.print(f"Match filter: {match_id}")
    
    try:
        if clear:
            clear_output_files(out_root)
        
        events_df = read_events_eager(events_root, match_id)
        
        if events_df.is_empty():
            console.print("❌ [red]No events found to process[/red]")
            raise typer.Exit(1)
        
        console.print(f"📊 Loaded {len(events_df)} events")
        
        balances_df, snapshots_df, state_df = reduce_match(events_df, DEFAULT_RULES)
        
        write_balances(balances_df, out_root)
        write_snapshots(snapshots_df, out_root)
        write_state(state_df, out_root)
        
        console.print("✅ [green]Economic data recomputed successfully![/green]")
        console.print(f"📊 Generated {len(balances_df)} balance records")
        console.print(f"📈 Generated {len(snapshots_df)} team snapshots")
        console.print(f"💾 Generated {len(state_df)} state records")
        
    except Exception as e:
        logger.error(f"Recompute failed: {e}")
        console.print(f"❌ [red]Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    match_id: str = typer.Argument(..., help="Match ID to export"),
    round_num: Optional[int] = typer.Option(None, help="Specific round number"),
    format: str = typer.Option("table", help="Output format: table, csv, json"),
    output_file: Optional[str] = typer.Option(None, help="Output file path"),
    data_root: str = typer.Option("data", help="Root directory for data files"),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
) -> None:
    """Export economic data for analysis."""
    setup_logging(verbose)
    
    console.print(f"📤 [bold blue]Exporting data for match {match_id}[/bold blue]")
    
    try:
        snapshots_df = read_existing_snapshots(data_root, match_id)
        
        if snapshots_df.is_empty():
            console.print("❌ [red]No snapshot data found for match[/red]")
            raise typer.Exit(1)
        
        if round_num is not None:
            snapshots_df = snapshots_df.filter(pl.col("round_number") == round_num)
        
        if format == "table":
            _display_table(snapshots_df)
        elif format == "csv":
            _export_csv(snapshots_df, output_file, match_id, round_num)
        elif format == "json":
            _export_json(snapshots_df, output_file, match_id, round_num)
        
        console.print("✅ [green]Export completed![/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def verify(
    match_id: str = typer.Argument(..., help="Match ID to verify"),
    data_root: str = typer.Option("data", help="Root directory for data files"),
    events_root: str = typer.Option("data/events", help="Root directory for event files"),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
) -> None:
    """Verify data integrity by recomputing and comparing checksums."""
    setup_logging(verbose)
    
    console.print(f"🔍 [bold blue]Verifying data for match {match_id}[/bold blue]")
    
    try:
        existing_snapshots = read_existing_snapshots(data_root, match_id)
        
        if existing_snapshots.is_empty():
            console.print("❌ [red]No existing snapshots found for verification[/red]")
            raise typer.Exit(1)
        
        events_df = read_events_eager(events_root, match_id)
        _, new_snapshots, _ = reduce_match(events_df, DEFAULT_RULES)
        
        # Compare checksums
        mismatches = 0
        for row in existing_snapshots.iter_rows(named=True):
            round_num = row["round_number"]
            team = row["team"]
            existing_checksum = row["checksum"]
            
            new_row = new_snapshots.filter(
                (pl.col("round_number") == round_num) & 
                (pl.col("team") == team)
            )
            
            if new_row.is_empty() or new_row["checksum"][0] != existing_checksum:
                mismatches += 1
        
        if mismatches == 0:
            console.print("✅ [green]All checksums verified successfully![/green]")
        else:
            console.print(f"❌ [red]{mismatches} verification failures found[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"❌ [red]Failed: {e}[/red]")
        raise typer.Exit(1)


def _display_table(df: pl.DataFrame) -> None:
    """Display snapshot data as a rich table."""
    table = Table(title="Economic Snapshots")
    table.add_column("Round", justify="right")
    table.add_column("Team")
    table.add_column("Start Bank", justify="right")
    table.add_column("Spend", justify="right")
    table.add_column("Kill Rewards", justify="right")
    table.add_column("End Bank", justify="right")
    
    for row in df.iter_rows(named=True):
        table.add_row(
            str(row["round_number"]),
            row["team"],
            f"${row['bank_total_start']:,}",
            f"${row['spend_sum']:,}",
            f"${row['kill_reward_sum']:,}",
            f"${row['bank_total_end']:,}",
        )
    
    console.print(table)


def _export_csv(df: pl.DataFrame, output_file: Optional[str], match_id: str, round_num: Optional[int]) -> None:
    """Export data as CSV."""
    if not output_file:
        suffix = f"_round_{round_num}" if round_num else ""
        output_file = f"cs2_economy_{match_id}{suffix}.csv"
    
    df.write_csv(output_file)
    console.print(f"📁 Exported to: {output_file}")


def _export_json(df: pl.DataFrame, output_file: Optional[str], match_id: str, round_num: Optional[int]) -> None:
    """Export data as JSON."""
    if not output_file:
        suffix = f"_round_{round_num}" if round_num else ""
        output_file = f"cs2_economy_{match_id}{suffix}.json"
    
    df.write_json(output_file)
    console.print(f"📁 Exported to: {output_file}")


def main() -> None:
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n❌ [red]Operation cancelled by user[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
