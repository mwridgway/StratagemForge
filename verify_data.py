import pandas as pd
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_parquet_files():
    """Verify the contents of the generated parquet files"""
    
    parquet_folder = Path("parquet")
    
    if not parquet_folder.exists():
        logger.error("Parquet folder not found!")
        return
    
    # Get all demo folders
    demo_folders = [folder for folder in parquet_folder.iterdir() if folder.is_dir()]
    
    logger.info(f"Found {len(demo_folders)} demo folders")
    
    for demo_folder in demo_folders:
        logger.info(f"\n--- {demo_folder.name} ---")
        
        # Get all parquet files in this demo folder
        parquet_files = list(demo_folder.glob("*.parquet"))
        
        for parquet_file in parquet_files:
            try:
                # Read the parquet file
                df = pd.read_parquet(parquet_file)
                
                logger.info(f"  {parquet_file.name}: {len(df)} rows, {len(df.columns)} columns")
                
                # Show column names
                logger.info(f"    Columns: {list(df.columns)}")
                
                # Show first few rows for small datasets
                if len(df) <= 50:
                    logger.info(f"    Sample data:\n{df.head()}")
                else:
                    logger.info(f"    Sample data (first 3 rows):\n{df.head(3)}")
                
            except Exception as e:
                logger.error(f"  Error reading {parquet_file.name}: {str(e)}")
    
    # Summary statistics
    logger.info("\n--- SUMMARY ---")
    total_files = 0
    total_rows = 0
    
    for demo_folder in demo_folders:
        parquet_files = list(demo_folder.glob("*.parquet"))
        total_files += len(parquet_files)
        
        for parquet_file in parquet_files:
            try:
                df = pd.read_parquet(parquet_file)
                total_rows += len(df)
            except:
                pass
    
    logger.info(f"Total parquet files created: {total_files}")
    logger.info(f"Total rows across all files: {total_rows:,}")

if __name__ == "__main__":
    verify_parquet_files()
