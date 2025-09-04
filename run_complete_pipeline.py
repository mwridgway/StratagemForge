#!/usr/bin/env python3
"""
Complete CS2 Demo Analysis Pipeline Runner

This script provides a simple way to run the entire CS2 demo analysis pipeline
from start to finish. It handles data parsing, optimization, and strategic analysis.

Usage:
    python run_complete_pipeline.py [--clean] [--full-analysis] [--skip-parsing]
                                    [--workers N] [--tick-sample M]
                                    [--events CSV] [--log-level LEVEL]

Options:
    --clean          : Remove all existing data before starting (clean run)
    --full-analysis  : Use full data for analysis instead of sampled (slower)
    --skip-parsing   : Skip demo parsing if parquet files already exist
    --workers N      : Number of parallel workers for parsing (default: CPU-1)
    --tick-sample M  : Modulo for tick sampling (e.g., 64)
    --events CSV     : Comma-separated list of events to parse
    --log-level      : Logging level for parsing (DEBUG/INFO/WARNING/ERROR)
"""

import argparse
import logging
import time
import os
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_previous_data():
    """Remove all previous analysis data for a clean run"""
    logger.info("🧹 Cleaning previous data...")
    
    # Remove parquet directory
    parquet_dir = Path("parquet")
    if parquet_dir.exists():
        shutil.rmtree(parquet_dir)
        logger.info("   ✓ Removed parquet directory")
    
    # Remove database files
    for db_file in Path(".").glob("*.db"):
        db_file.unlink()
        logger.info(f"   ✓ Removed {db_file}")
    
    # Remove CSV output files
    csv_files = ["grenade_summary.csv", "map_performance.csv", "player_summary.csv"]
    for csv_file in csv_files:
        csv_path = Path(csv_file)
        if csv_path.exists():
            csv_path.unlink()
            logger.info(f"   ✓ Removed {csv_file}")
    
    logger.info("🧹 Cleanup complete")

def run_demo_parsing(workers: int = None, tick_sample: int = None, events: str = None, log_level: str = "INFO"):
    """Parse demo files and create parquet data"""
    logger.info("🎮 Starting demo parsing...")
    start_time = time.time()
    
    import subprocess
    import sys
    
    cmd = [
        sys.executable, "pipeline.py", "run",
        "--log-level", str(log_level),
    ]
    if workers is not None:
        cmd += ["--workers", str(workers)]
    if tick_sample is not None:
        cmd += ["--tick-sample", str(tick_sample)]
    if events:
        cmd += ["--events", str(events)]

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        logger.info(f"🎮 Demo parsing completed successfully ({elapsed:.1f}s)")
        return True
    else:
        logger.error(f"🎮 Demo parsing failed:")
        logger.error(result.stderr)
        return False

def run_strategic_analysis(use_full_data=False, materialize=False):
    """Run strategic analysis in a subprocess to avoid console encoding issues."""
    mode = "full" if use_full_data else "sampled"
    logger.info(f"📊 Starting strategic analysis (mode: {mode})...")
    start_time = time.time()

    import subprocess, sys

    # Build a small driver that toggles sampling if requested
    pycode = (
        "from expert_validation_optimized import ExpertValidationAnalyzer; "
        "v=ExpertValidationAnalyzer(); "
        + ("v.toggle_sampling(False); " if use_full_data else "")
        + "v.run_all_analyses(); v.close()"
    )

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if materialize:
        env["SF_MATERIALIZE"] = "1"

    try:
        result = subprocess.run(
            [sys.executable, "-c", pycode],
            capture_output=True,
            text=True,
            env=env,
            encoding="utf-8",
            errors="replace",
        )

        elapsed = time.time() - start_time
        if result.returncode == 0:
            logger.info(f"📊 Strategic analysis completed successfully ({elapsed:.1f}s)")
            return True
        else:
            logger.error(f"📊 Strategic analysis failed after {elapsed:.1f}s: {result.stderr.strip()}")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"📊 Strategic analysis failed after {elapsed:.1f}s: {e}")
        return False

def check_data_availability():
    """Check if demo files and parquet data exist"""
    demos_dir = Path("demos")
    parquet_dir = Path("parquet")
    
    # Check demo files
    demo_files = list(demos_dir.glob("*.dem")) if demos_dir.exists() else []
    if not demo_files:
        logger.error("❌ No demo files found in demos/ directory")
        return False
    
    logger.info(f"✓ Found {len(demo_files)} demo files")
    
    # Check parquet data
    if parquet_dir.exists():
        parquet_subdirs = [d for d in parquet_dir.iterdir() if d.is_dir()]
        logger.info(f"✓ Found {len(parquet_subdirs)} parquet datasets")
        return True, len(parquet_subdirs) == len(demo_files)
    else:
        logger.info("⚠️ No parquet data found")
        return True, False

def main():
    parser = argparse.ArgumentParser(
        description="Run complete CS2 demo analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove all existing data before starting (clean run)"
    )
    
    parser.add_argument(
        "--full-analysis",
        action="store_true",
        help="Use full data for analysis instead of sampled (slower)"
    )
    
    parser.add_argument(
        "--skip-parsing",
        action="store_true",
        help="Skip demo parsing if parquet files already exist"
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for parsing (default: CPU-1)"
    )
    parser.add_argument(
        "--tick-sample",
        type=int,
        dest="tick_sample",
        default=None,
        help="Modulo for tick sampling (e.g., 64)"
    )
    parser.add_argument(
        "--events",
        type=str,
        default=None,
        help="Comma-separated list of events to parse"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level passed to parsing step (DEBUG/INFO/WARNING/ERROR)"
    )
    parser.add_argument(
        "--materialize-analysis",
        action="store_true",
        help="Materialize unified views into indexed base tables for analysis"
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 CS2 Demo Analysis Pipeline")
    logger.info("=" * 50)
    
    pipeline_start = time.time()
    
    # Step 1: Clean previous data if requested
    if args.clean:
        clean_previous_data()
    
    # Step 2: Check data availability
    data_available, parquet_complete = check_data_availability()
    if not data_available:
        return 1
    
    # Step 3: Parse demo files (if needed)
    if args.skip_parsing and parquet_complete:
        logger.info("⏭️ Skipping demo parsing (--skip-parsing enabled)")
    else:
        if not run_demo_parsing(workers=args.workers, tick_sample=args.tick_sample, events=args.events, log_level=args.log_level):
            logger.error("❌ Pipeline failed at demo parsing stage")
            return 1
    
    # Step 4: Run strategic analysis
    if not run_strategic_analysis(use_full_data=args.full_analysis, materialize=args.materialize_analysis):
        logger.error("❌ Pipeline failed at strategic analysis stage")
        return 1
    
    # Summary
    total_elapsed = time.time() - pipeline_start
    logger.info("=" * 50)
    logger.info(f"✅ Pipeline completed successfully in {total_elapsed:.1f}s")
    logger.info("🎯 Ready for tactical analysis and team preparation!")
    
    return 0

if __name__ == "__main__":
    exit(main())
