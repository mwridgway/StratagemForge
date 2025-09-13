#!/usr/bin/env python3
"""
Build DuckDB-native spatial zones and zone-tagged views using the Spatial extension.

Features
- Loads zone polygons from data/zones/<map>.json (game-unit coordinates)
- Creates/updates a DuckDB table zones(map TEXT, zone_name TEXT, priority INT, wkt TEXT, geom GEOMETRY)
- Creates spatial join views to tag player ticks with zone names using ST_Contains
- Optional materialization of the zone-tagged view into a base table for performance

Usage examples
  # Build zones for Inferno and create a sampled zone-tagged view
  .venv/Scripts/python.exe scripts/build_spatial_zones.py --map inferno

  # Also materialize a base table for faster queries
  .venv/Scripts/python.exe scripts/build_spatial_zones.py --map inferno --materialize

Notes
- Requires DuckDB Spatial extension (script will INSTALL/LOAD it)
- Requires the unified views to exist; we initialize via the repo connector
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import List, Tuple

import duckdb  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from duckdb_connector_optimized import CSGODataAnalyzer  # type: ignore
except Exception:
    from duckdb_connector import CSGODataAnalyzer  # type: ignore


def _to_polygon_wkt(points: List[Tuple[float, float]]) -> str:
    """Convert list of (x,y) to a closed POLYGON WKT string."""
    if not points or len(points) < 3:
        raise ValueError("Polygon must have at least 3 points")
    coords = [(float(x), float(y)) for x, y in points]
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    coord_str = ", ".join(f"{x} {y}" for x, y in coords)
    return f"POLYGON(({coord_str}))"


def _load_zones_json(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    zones = []
    for z in data.get("zones", []):
        name = z.get("name")
        poly = z.get("polygon") or []
        prio = int(z.get("priority", 0))
        if name and isinstance(poly, list) and len(poly) >= 3:
            wkt = _to_polygon_wkt([(float(x), float(y)) for x, y in poly])
            zones.append({"zone_name": name, "priority": prio, "wkt": wkt})
    return data.get("map", None), zones


def _extract_map_suffix_expr(col: str = "demo_name") -> str:
    """SQL expression to extract map suffix from demo_name (text after last '-')."""
    # Uses regex to extract last token after '-'
    return "lower(regexp_extract(" + col + ", '-([^\\-]+)$', 1))"


def main():
    ap = argparse.ArgumentParser(description="Build spatial zones in DuckDB and create zone-tagged views")
    ap.add_argument("--map", required=True, help="Map short name (e.g., inferno)")
    ap.add_argument("--zones", default=None, help="Path to zones JSON (defaults to data/zones/<map>.json)")
    ap.add_argument("--full", action="store_true", help="Use full ticks instead of sampled for the view")
    ap.add_argument("--materialize", action="store_true", help="Materialize zone-tagged view into a base table")
    args = ap.parse_args()

    zones_path = Path(args.zones) if args.zones else (ROOT / "data" / "zones" / f"{args.map}.json")
    if not zones_path.exists():
        print(f"Zones file not found: {zones_path}")
        return 1

    # Initialize analyzer to create unified views
    analyzer = CSGODataAnalyzer()
    con = analyzer.conn

    # Enable Spatial extension
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    # Prepare zones table
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS zones (
            map TEXT,
            zone_name TEXT,
            priority INTEGER,
            wkt TEXT
        )
        """
    )

    map_name, zones = _load_zones_json(zones_path)
    if not zones:
        print("No valid zones in JSON; ensure polygons have 3+ points")
        return 1

    json_map = map_name or f"de_{args.map}"  # fallback label
    # Normalize map key to the short form we extract from demo_name
    map_key = args.map.lower()

    # Upsert zones for this map (simple replace strategy)
    con.execute("DELETE FROM zones WHERE lower(map)=?", [map_key])
    con.executemany(
        "INSERT INTO zones(map, zone_name, priority, wkt) VALUES (?, ?, ?, ?)",
        [(map_key, z["zone_name"], z["priority"], z["wkt"]) for z in zones],
    )

    # Create a view with geometry column
    con.execute(
        """
        CREATE OR REPLACE VIEW zones_geom AS
        SELECT map, zone_name, priority,
               wkt,
               ST_GeomFromText(wkt) AS geom
        FROM zones;
        """
    )

    # Build zone-tagged view for ticks
    ticks_view = "all_player_ticks" if args.full else "all_player_ticks_sampled"
    map_expr = _extract_map_suffix_expr("t.demo_name")

    con.execute(
        f"""
        CREATE OR REPLACE VIEW {ticks_view}_with_zone AS
        SELECT t.*, zg.zone_name
        FROM {ticks_view} t
        JOIN zones_geom zg
          ON {map_expr} = zg.map
         AND ST_Contains(zg.geom, ST_Point(t.X, t.Y));
        """
    )

    if args.materialize:
        mat = f"{ticks_view}_with_zone_mat"
        con.execute(f"CREATE OR REPLACE TABLE {mat} AS SELECT * FROM {ticks_view}_with_zone")
        # Simple index on zone_name for faster grouping
        try:
            con.execute(f"CREATE INDEX IF NOT EXISTS idx_{mat}_zone ON {mat}(zone_name)")
        except Exception:
            pass
        print(f"Materialized table created: {mat}")

    print(f"Spatial zones updated for map '{args.map}'. View created: {ticks_view}_with_zone")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

