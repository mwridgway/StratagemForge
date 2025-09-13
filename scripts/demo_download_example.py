#!/usr/bin/env python3
"""
Demo Download and Analysis Example
==================================

Example workflow showing how to download demos from HLTV and run analysis.
"""

import subprocess
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_and_analyze_example():
    """Example workflow: Download demos and run analysis."""
    
    logger.info("🎮 Demo Download and Analysis Example")
    logger.info("=" * 50)
    
    # Example match IDs from recent tournaments
    # Note: These are example IDs - replace with actual HLTV match IDs
    example_matches = [
        "2378945",  # Example: Recent Blast tournament
        "2378946",  # Example: ESL Pro League
        "2378947",  # Example: Major qualifier
    ]
    
    logger.info("Step 1: Installing requirements if needed...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                      check=True, capture_output=True)
        logger.info("✅ Requirements installed")
    except subprocess.CalledProcessError:
        logger.warning("⚠️  Could not install requirements automatically")
        logger.info("Please run: pip install requests")
        return
    
    logger.info("\nStep 2: Downloading example demos...")
    
    demos_downloaded = 0
    
    for i, match_id in enumerate(example_matches[:1]):  # Just download first one for example
        logger.info(f"Downloading demos for match {match_id}...")
        
        try:
            # Run the demo downloader
            result = subprocess.run([
                sys.executable, 
                "scripts/simple_hltv_downloader.py",
                "--match-id", match_id
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully downloaded demos for match {match_id}")
                demos_downloaded += 1
            else:
                logger.warning(f"⚠️  Failed to download match {match_id}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            logger.warning(f"⚠️  Download timeout for match {match_id}")
        except Exception as e:
            logger.warning(f"⚠️  Error downloading match {match_id}: {e}")
    
    if demos_downloaded == 0:
        logger.info("ℹ️  No demos downloaded. You can manually download demos using:")
        logger.info("   python scripts/simple_hltv_downloader.py --match-id <MATCH_ID>")
        logger.info("\nTo find match IDs:")
        logger.info("1. Go to https://www.hltv.org/matches")
        logger.info("2. Click on a match")
        logger.info("3. Copy the number from the URL (e.g., /matches/2367890/...)")
        return
    
    logger.info(f"\nStep 3: Running analysis pipeline on {demos_downloaded} demo sets...")
    
    try:
        # Check if we have any demo files
        demos_folder = Path("demos")
        demo_files = list(demos_folder.glob("*.dem")) if demos_folder.exists() else []
        
        if demo_files:
            logger.info(f"Found {len(demo_files)} demo files in demos folder")
            
            # Run the optimized pipeline
            result = subprocess.run([
                sys.executable,
                "run_complete_pipeline_new.py",
                "--mode", "fast"
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            if result.returncode == 0:
                logger.info("✅ Analysis pipeline completed successfully!")
                logger.info("\n📊 Pipeline Output:")
                logger.info(result.stdout)
            else:
                logger.warning(f"⚠️  Pipeline failed: {result.stderr}")
        else:
            logger.info("ℹ️  No demo files found to analyze")
            
    except subprocess.TimeoutExpired:
        logger.warning("⚠️  Analysis pipeline timeout")
    except Exception as e:
        logger.warning(f"⚠️  Error running pipeline: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info("🎯 Example Complete!")
    logger.info("\n💡 Next Steps:")
    logger.info("1. Find match IDs from https://www.hltv.org/matches")
    logger.info("2. Download specific demos:")
    logger.info("   python scripts/simple_hltv_downloader.py --match-id <ID>")
    logger.info("3. Run analysis:")
    logger.info("   python run_complete_pipeline_new.py --mode fast")
    logger.info("4. Review strategic insights in console output")

if __name__ == "__main__":
    download_and_analyze_example()
