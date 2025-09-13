#!/usr/bin/env python3
"""Tag sampled player ticks with named zones and summarize.

Usage:
  python scripts/tag_zones.py --map inferno --out parquet/zones_summary_inferno.parquet

Notes:
- Expects a zones JSON at data/zones/<map>.json (e.g., data/zones/inferno.json)
- Uses sampled ticks by default for performance.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from duckdb_connector_optimized import CSGODataAnalyzer  # type: ignore
except Exception:
    from duckdb_connector import CSGODataAnalyzer  # type: ignore

from scripts.zones import load_zones_json, assign_zones


def main():
    ap = argparse.ArgumentParser(description="Assign zones and summarize activity per zone")
    ap.add_argument("--map", required=True, help="Map short name (e.g., inferno)")
    ap.add_argument("--full", action="store_true", help="Use full ticks instead of sampled")
    ap.add_argument("--limit", type=int, default=None, help="Row limit for tagging (for quick tests)")
    ap.add_argument("--out", default=None, help="Output Parquet path (default: parquet/zones_summary_<map>.parquet)")
    args = ap.parse_args()

    zones_path = ROOT / "data" / "zones" / f"{args.map}.json"
    if not zones_path.exists():
        print(f"Zones file not found: {zones_path}. Please fill polygons in the template.")
        return 1
    zones = load_zones_json(zones_path)
    if not zones:
        print("No valid zones defined in JSON (need at least one polygon with 3+ points)")
        return 1

    analyzer = CSGODataAnalyzer()
    ticks = "all_player_ticks" if args.full else "all_player_ticks_sampled"
    df = analyzer.query(
        f"SELECT demo_name, name, m_iTeamNum, X, Y, tick FROM {ticks} WHERE X IS NOT NULL AND Y IS NOT NULL"
    )

    # Filter rows to the requested map (demo_name endswith -<map>)
    df = df[df["demo_name"].str.endswith(f"-{args.map}")].copy()
    if args.limit:
        df = df.head(args.limit)

    # Assign zone names
    pts = list(zip(df["X"].astype(float), df["Y"].astype(float)))
    df["zone"] = assign_zones(pts, zones)
    df = df[df["zone"].notna()].copy()

    # Summarize per demo/zone/team
    summary = (
        df.groupby(["demo_name", "zone", "m_iTeamNum"], as_index=False)
        .agg(total_ticks=("tick", "count"), unique_players=("name", "nunique"))
        .sort_values(["demo_name", "total_ticks"], ascending=[True, False])
    )

    out_path = Path(args.out) if args.out else ROOT / "parquet" / f"zones_summary_{args.map}.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_parquet(out_path, index=False)

    # Also print a preview
    print("Saved:", out_path)
    print(summary.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

