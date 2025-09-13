#!/usr/bin/env python3
"""
Complete CS:GO Demo Analysis Pipeline Runner
=============================================

This script runs the entire optimized analysis pipeline from demo parsing to strategic analysis.

Usage:
    python run_complete_pipeline_new.py [--mode fast|full] [--force-reparse] [--clean]

Options:
    --mode fast      : Use sampled data for fast analysis (default)
    --mode full      : Use complete dataset for comprehensive analysis  
    --force-reparse  : Re-parse demo files even if parquet files exist
    --clean          : Remove all existing data before starting (clean run)
    --help           : Show this help message

Performance Notes:
    - Fast mode: Uses 98.4% sampled data, completes in ~4 seconds
    - Full mode: Uses complete dataset, takes longer but comprehensive
    - Optimized pipeline provides >15x performance improvement
"""

import argparse
import sys
import time
from pathlib import Path
import logging
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_prerequisites():
    """Check if all required files and dependencies are available."""
    print("🔍 Checking prerequisites...")
    
    # Check demo files
    demos_folder = Path("demos")
    if not demos_folder.exists():
        print("❌ Error: 'demos' folder not found!")
        return False
    
    demo_files = list(demos_folder.glob("*.dem"))
    if not demo_files:
        print("❌ Error: No .dem files found in demos folder!")
        return False
    
    print(f"✅ Found {len(demo_files)} demo files")
    
    # Check if parquet data exists
    parquet_folder = Path("parquet")
    has_parquet = parquet_folder.exists() and any(parquet_folder.iterdir())
    
    if has_parquet:
        print("✅ Existing parquet data found")
    else:
        print("ℹ️  No parquet data found - will parse demos")
    
    return True

def clean_previous_data():
    """Remove all existing data for a clean run."""
    print("🧹 Cleaning previous data...")
    
    # Remove parquet directory
    parquet_dir = Path("parquet")
    if parquet_dir.exists():
        shutil.rmtree(parquet_dir)
        print("   ✓ Removed parquet directory")
    
    # Remove database files
    for db_file in Path(".").glob("*.db"):
        db_file.unlink()
        print(f"   ✓ Removed {db_file}")
    
    # Remove any cache files
    cache_dir = Path("__pycache__")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
        print("   ✓ Removed cache directory")

def run_demo_parsing(force_reparse=False):
    """Parse demo files into optimized parquet format."""
    parquet_folder = Path("parquet")
    
    # Check if we need to parse
    if not force_reparse and parquet_folder.exists() and any(parquet_folder.iterdir()):
        print("⚡ Skipping demo parsing - parquet data already exists")
        print("   Use --force-reparse to reparse demos")
        return True
    
    print("🎮 Starting optimized demo parsing...")
    start_time = time.time()
    
    try:
        # Import and run the optimized pipeline
        from pipeline import parse_demo_files
        
        # Parse all demos with optimizations
        results = parse_demo_files()
        
        parse_time = time.time() - start_time
        print(f"✅ Demo parsing completed in {parse_time:.1f} seconds")
        
        # Show parsing results
        if results:
            total_rows = sum(sum(demo_data.values()) for demo_data in results.values())
            print(f"   📊 Processed {len(results)} demos with {total_rows:,} total rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo parsing failed: {str(e)}")
        logger.error(f"Demo parsing error: {str(e)}", exc_info=True)
        return False

def run_strategic_analysis(mode="fast"):
    """Run the strategic analysis with the specified mode."""
    print(f"🧠 Starting strategic analysis (mode: {mode})...")
    start_time = time.time()
    
    try:
        # Import the optimized expert validation
        from expert_validation_optimized import ExpertValidationAnalyzer
        
        # Create analyzer and run analysis
        validator = ExpertValidationAnalyzer()
        
        if mode == "fast":
            print("   🚀 Using fast mode with sampled data (98.4% reduction)")
            validator.run_all_analyses_fast()
        else:
            print("   📊 Using full mode with complete dataset")
            validator.run_all_analyses_full()
        
        validator.close()
        
        analysis_time = time.time() - start_time
        print(f"✅ Strategic analysis completed in {analysis_time:.1f} seconds")
        return True
        
    except Exception as e:
        print(f"❌ Strategic analysis failed: {str(e)}")
        logger.error(f"Strategic analysis error: {str(e)}", exc_info=True)
        return False

def show_results_summary():
    """Show a summary of available results and next steps."""
    print("\n" + "🎯 ANALYSIS RESULTS SUMMARY")
    print("=" * 50)
    
    # Check for parquet files
    parquet_dir = Path("parquet")
    if parquet_dir.exists():
        subfolders = [d for d in parquet_dir.iterdir() if d.is_dir()]
        print(f"📁 Parsed data: {len(subfolders)} demo files processed")
        
        # Count total files
        total_files = sum(len(list(folder.glob("*.parquet"))) for folder in subfolders)
        print(f"📄 Generated files: {total_files} parquet files")
    
    print("\n💡 Next Steps:")
    print("   • Review strategic analysis results in the console output")
    print("   • Use interactive_analysis.py for custom queries")
    print("   • Check expert_validation_optimized.py for detailed insights")
    print("   • Consider running --mode full for comprehensive analysis")

def main():
    """Main pipeline execution function."""
    parser = argparse.ArgumentParser(
        description="Complete CS:GO Demo Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--mode", 
        choices=["fast", "full"], 
        default="fast",
        help="Analysis mode: fast (sampled data) or full (complete dataset)"
    )
    
    parser.add_argument(
        "--force-reparse", 
        action="store_true",
        help="Force re-parsing of demo files even if parquet data exists"
    )
    
    parser.add_argument(
        "--clean", 
        action="store_true",
        help="Remove all existing data before starting (clean run)"
    )
    
    args = parser.parse_args()
    
    print("🚀 CS:GO Demo Analysis Pipeline")
    print("=" * 50)
    print(f"📊 Analysis mode: {args.mode.upper()}")
    print(f"🔄 Force reparse: {'Yes' if args.force_reparse else 'No'}")
    print(f"🧹 Clean run: {'Yes' if args.clean else 'No'}")
    print()
    
    # Start pipeline
    pipeline_start = time.time()
    
    # Step 0: Clean data if requested
    if args.clean:
        clean_previous_data()
        print()
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites check failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Step 2: Parse demos (if needed)
    if not run_demo_parsing(force_reparse=args.force_reparse or args.clean):
        print("❌ Demo parsing failed. Exiting.")
        sys.exit(1)
    
    print()
    
    # Step 3: Run strategic analysis
    if not run_strategic_analysis(mode=args.mode):
        print("❌ Strategic analysis failed. Exiting.")
        sys.exit(1)
    
    # Pipeline complete
    total_time = time.time() - pipeline_start
    print("\n" + "=" * 50)
    print("🎯 PIPELINE COMPLETE!")
    print(f"⏱️  Total execution time: {total_time:.1f} seconds")
    print(f"📊 Analysis mode used: {args.mode.upper()}")
    
    if args.mode == "fast":
        print("💡 Tip: Use --mode full for comprehensive analysis with complete dataset")
    
    # Show results summary
    show_results_summary()
    
    print("\n🎮 Your CS:GO strategic analysis is ready!")
    print("📈 Use the results for team preparation and tactical planning")

if __name__ == "__main__":
    main()
