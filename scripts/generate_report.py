#!/usr/bin/env python3
"""
Generate a brief CS2 tactical analysis report using a local Ollama model.

This script:
- Loads unified DuckDB views via the optimized connector
- Extracts compact aggregates (sampled where appropriate)
- Builds a concise prompt with data snippets
- Calls a local Ollama model to produce a Markdown report
- Saves to reports/<timestamp>_brief_report.md

Requirements:
- Ollama installed and a model pulled (e.g., `ollama pull llama3.1:8b`)
- Python deps available in your venv (duckdb, pandas)
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

import pandas as pd
import sys

# Ensure repo root is on sys.path so we can import local modules when running from scripts/
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    # Prefer optimized connector (has sampled/unified helpers)
    from duckdb_connector_optimized import CSGODataAnalyzer  # type: ignore
except Exception:
    from duckdb_connector import CSGODataAnalyzer  # type: ignore

# Optional zones support
try:
    from scripts.zones import load_zones_json, assign_zones  # type: ignore
except Exception:
    load_zones_json = assign_zones = None  # type: ignore


def _df_to_csv_snippet(df: pd.DataFrame, max_rows: int, max_cols: int = 8) -> str:
    if df is None or df.empty:
        return ""
    cols = list(df.columns[:max_cols])
    slim = df.loc[:, cols].head(max_rows)
    return slim.to_csv(index=False)


def _infer_map_from_demo(demo_name: str) -> Optional[str]:
    # Expects suffix like ...-inferno
    if not demo_name:
        return None
    parts = demo_name.split('-')
    return parts[-1] if parts else None


def collect_aggregates(use_sampled: bool = True, limits: dict | None = None) -> dict:
    limits = limits or {}
    top_players = int(limits.get("top_players", 15))
    top_utils = int(limits.get("top_utils", 30))
    top_zones = int(limits.get("top_zones", 10))
    top_maps = int(limits.get("top_maps", 10))

    analyzer = CSGODataAnalyzer()

    ticks = "all_player_ticks_sampled" if use_sampled else "all_player_ticks"

    payload = {"tables": {}, "sql": {}}

    # Map summary
    sql_map_summary = f"""
    SELECT demo_name,
           COUNT(DISTINCT name) AS unique_players,
           COUNT(*) AS total_ticks
    FROM {ticks}
    GROUP BY demo_name
    ORDER BY total_ticks DESC
    LIMIT {top_maps}
    """
    df_map = analyzer.query(sql_map_summary)
    payload["tables"]["map_summary"] = _df_to_csv_snippet(df_map, top_maps)
    payload["sql"]["map_summary"] = sql_map_summary.strip()

    # Player mobility/role hint
    sql_mobility = f"""
    SELECT name,
           COUNT(DISTINCT demo_name) AS maps_played,
           COUNT(*) AS total_ticks,
           ROUND(STDDEV(X) + STDDEV(Y), 2) AS mobility_score
    FROM {ticks}
    WHERE name IS NOT NULL
    GROUP BY name
    HAVING total_ticks >= 500
    ORDER BY total_ticks DESC
    LIMIT {top_players}
    """
    df_mob = analyzer.query(sql_mobility)
    payload["tables"]["player_mobility"] = _df_to_csv_snippet(df_mob, top_players)
    payload["sql"]["player_mobility"] = sql_mobility.strip()

    # Utility usage
    sql_utils = f"""
    SELECT name,
           grenade_type,
           COUNT(*) AS total_throws,
           COUNT(DISTINCT demo_name) AS maps_with_usage
    FROM all_grenades
    WHERE name IS NOT NULL
    GROUP BY name, grenade_type
    ORDER BY total_throws DESC
    LIMIT {top_utils}
    """
    df_utils = analyzer.query(sql_utils)
    payload["tables"]["utility_usage"] = _df_to_csv_snippet(df_utils, top_utils)
    payload["sql"]["utility_usage"] = sql_utils.strip()

    # Contested zones (grid aggregation)
    sql_zones = f"""
    SELECT demo_name,
           ROUND(X/400)*400 AS zone_x,
           ROUND(Y/400)*400 AS zone_y,
           COUNT(*) AS total_activity,
           COUNT(DISTINCT m_iTeamNum) AS teams_present
    FROM {ticks}
    WHERE m_iTeamNum IN (2,3) AND name IS NOT NULL
    GROUP BY demo_name, zone_x, zone_y
    HAVING teams_present > 1
    ORDER BY total_activity DESC
    LIMIT {top_zones}
    """
    df_zones = analyzer.query(sql_zones)
    payload["tables"]["contested_zones"] = _df_to_csv_snippet(df_zones, top_zones)
    payload["sql"]["contested_zones"] = sql_zones.strip()

    # Named zones, if zone files exist for the maps in data
    if load_zones_json and assign_zones and not df_zones.empty:
        df_nz = df_zones.copy()
        df_nz["map"] = df_nz["demo_name"].apply(_infer_map_from_demo)
        # Center of the 400x400 bucket
        df_nz["cx"] = df_nz["zone_x"].astype(float) + 200.0
        df_nz["cy"] = df_nz["zone_y"].astype(float) + 200.0
        named_rows = []
        for m in sorted(df_nz["map"].dropna().unique()):
            zones_path = Path("data/zones") / f"{m}.json"
            if not zones_path.exists():
                continue
            zones = load_zones_json(zones_path)
            sub = df_nz[df_nz["map"] == m].copy()
            labels = assign_zones(list(zip(sub["cx"], sub["cy"])), zones)
            sub["zone_name"] = labels
            sub = sub[sub["zone_name"].notna()]
            named_rows.append(sub)
        if named_rows:
            nz = pd.concat(named_rows, ignore_index=True)
            nz_sum = (
                nz.groupby(["map", "zone_name"], as_index=False)["total_activity"].sum()
                .sort_values(["map", "total_activity"], ascending=[True, False])
            )
            payload["tables"]["named_contested_zones"] = _df_to_csv_snippet(nz_sum, top_zones)

    return payload


def build_prompt(payload: dict, brief: bool = True) -> str:
    objective = (
        "Generate a concise tactical report for CS2 coaches. "
        "Use only the provided tables. If data is insufficient, state it."
    )
    constraints = (
        "Output Markdown only. Avoid overclaims. Cite evidence by table name. "
        "Prefer 3-5 bullet insights."
    )

    header = f"Objective: {objective}\nConstraints: {constraints}\n\n"

    tables_section = ["Tables (CSV excerpts):"]
    for name, csv_snip in payload.get("tables", {}).items():
        if not csv_snip:
            continue
        tables_section.append(f"- {name}\n```")
        tables_section.append(csv_snip.strip())
        tables_section.append("```")
    tables_text = "\n".join(tables_section)

    sql_section = ["SQL used (truncated as needed):"]
    for name, sql in payload.get("sql", {}).items():
        sql_section.append(f"- {name}\n```sql")
        sql_section.append(sql)
        sql_section.append("```")
    sql_text = "\n".join(sql_section)

    guidelines = (
        "Produce the following sections in Markdown:\n"
        "1. Executive Summary (3-4 sentences)\n"
        "2. Key Insights (3-5 bullets). Each bullet: finding + evidence table/fields\n"
        "3. Player Spotlights (2-3 players). role hint, mobility, utility profile\n"
        "4. Contested Zones (up to 5). Prefer named_contested_zones if available; otherwise use contested_zones with (map, zone_x, zone_y). Include rationale.\n"
        "5. Caveats (2-3 bullets)\n"
        "6. Next Actions (short checklist)\n"
    )

    prompt = "\n\n".join([header, tables_text, sql_text, guidelines]).strip()
    return prompt


def run_ollama(model: str, prompt: str, timeout: int = 120) -> str:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    # Prefer `ollama run <model>` with prompt piped via stdin
    cmd = ["ollama", "run", model]
    try:
        res = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as e:
        raise RuntimeError("Ollama CLI not found. Install Ollama and ensure it's on PATH.") from e

    if res.returncode != 0:
        raise RuntimeError(f"Ollama returned non-zero exit code: {res.stderr.strip()}")
    return res.stdout


def save_report(md_text: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"brief_report_{ts}.md"
    path.write_text(md_text, encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description="Generate a brief CS2 analysis report with Ollama")
    ap.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "llama3.1:8b"), help="Ollama model (e.g., llama3.1:8b)")
    ap.add_argument("--full", action="store_true", help="Use full ticks instead of sampled")
    ap.add_argument("--out", default="reports", help="Output directory for the report")
    ap.add_argument("--timeout", type=int, default=180, help="Generation timeout (seconds)")
    ap.add_argument("--top-players", type=int, default=15, help="Rows for player table")
    ap.add_argument("--top-utils", type=int, default=30, help="Rows for utility table")
    ap.add_argument("--top-zones", type=int, default=10, help="Rows for contested zones table")
    ap.add_argument("--top-maps", type=int, default=10, help="Rows for map summary table")
    args = ap.parse_args()

    payload = collect_aggregates(
        use_sampled=not args.full,
        limits={
            "top_players": args.top_players,
            "top_utils": args.top_utils,
            "top_zones": args.top_zones,
            "top_maps": args.top_maps,
        },
    )
    prompt = build_prompt(payload, brief=True)
    md = run_ollama(args.model, prompt, timeout=args.timeout)
    report_path = save_report(md, Path(args.out))
    print(f"Saved report: {report_path}")


if __name__ == "__main__":
    main()
