import os
import pandas as pd
from demoparser2 import DemoParser
from pathlib import Path
import logging
import time
from typing import Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_datatypes(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Optimize DataFrame data types for better storage and performance."""
    if df.empty:
        return df
    
    try:
        # Optimize based on data type
        if data_type == 'player_ticks':
            # Optimize coordinates to int32 (strategic analysis doesn't need float64 precision)
            for col in ['X', 'Y', 'Z']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int32')
            
            # Optimize health and armor to int8 (0-100 range)
            for col in ['m_iHealth', 'm_ArmorValue']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int8')
            
            # Optimize team numbers to int8
            if 'm_iTeamNum' in df.columns:
                df['m_iTeamNum'] = pd.to_numeric(df['m_iTeamNum'], errors='coerce').fillna(0).astype('int8')
            
            # Optimize angles to float32
            for col in ['m_angEyeAngles[0]', 'm_angEyeAngles[1]']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('float32')
                    
            # Convert player names to category for repeated strings
            if 'name' in df.columns:
                df['name'] = df['name'].astype('category')
                
        elif data_type == 'grenades':
            # Optimize grenade coordinates
            for col in ['x', 'y', 'z']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype('int32')
            
            # Convert categorical columns
            for col in ['name', 'grenade_type']:
                if col in df.columns:
                    df[col] = df[col].astype('category')
                    
        elif data_type == 'player_info':
            # Convert categorical columns
            for col in ['name', 'steam_id']:
                if col in df.columns:
                    df[col] = df[col].astype('category')
                    
        # Convert tick to int32 for all data types
        if 'tick' in df.columns:
            df['tick'] = pd.to_numeric(df['tick'], errors='coerce').fillna(0).astype('int32')
            
        logger.debug(f"Optimized {data_type} datatypes: {df.memory_usage(deep=True).sum() / 1024**2:.2f}MB")
        
    except Exception as e:
        logger.warning(f"Failed to optimize datatypes for {data_type}: {str(e)}")
        
    return df

def parse_demo_files():
    """Parse all demo files in the demos folder and save as optimized parquet files"""
    start_time = time.time()
    
    # Define paths
    demos_folder = Path("demos")
    parquet_folder = Path("parquet")
    
    # Create parquet folder if it doesn't exist
    parquet_folder.mkdir(exist_ok=True)
    
    # Get all .dem files
    demo_files = list(demos_folder.glob("*.dem"))
    
    if not demo_files:
        logger.warning("No demo files found in the demos folder")
        return
    
    logger.info(f"Found {len(demo_files)} demo files to process")
    total_rows = 0
    
    for demo_file in demo_files:
        try:
            demo_start_time = time.time()
            logger.info(f"Processing {demo_file.name}...")
            
            # Parse the demo file
            parser = DemoParser(str(demo_file))
            
            # Get available events for this demo
            available_events = parser.list_game_events()
            
            # Define common events to extract
            common_events = ['player_death', 'round_start', 'round_end', 'bomb_planted', 'bomb_defused', 'bomb_exploded', 'weapon_fire', 'player_hurt']
            events_to_parse = [event for event in common_events if event in available_events]
            
            # Define optimized player properties for strategic analysis
            player_props = [
                'X', 'Y', 'Z',  # Position (will be converted to int32)
                'm_iHealth', 'm_ArmorValue',  # Health and armor (will be converted to int8)
                'm_iTeamNum',  # Team (will be converted to int8)
                'm_bIsAlive',  # Alive status
                'm_angEyeAngles[0]', 'm_angEyeAngles[1]',  # View angles (will be converted to float32)
                'm_hActiveWeapon'  # Active weapon
            ]
            
            # Parse different types of data
            data_to_parse = {
                'grenades': lambda: parser.parse_grenades(),
                'player_info': lambda: parser.parse_player_info(),
                'item_drops': lambda: parser.parse_item_drops(),
                'skins': lambda: parser.parse_skins(),
            }
            
            # Add player ticks if we have properties
            if player_props:
                data_to_parse['player_ticks'] = lambda: parser.parse_ticks(player_props)
            
            # Add events - parse_events expects a list of event names
            for event in events_to_parse:
                data_to_parse[f'event_{event}'] = lambda e=event: parser.parse_events([e])
            
            # Create output folder for this demo
            demo_name = demo_file.stem  # filename without extension
            demo_output_folder = parquet_folder / demo_name
            demo_output_folder.mkdir(exist_ok=True)
            
            # Parse and save each data type with optimizations
            demo_rows = 0
            for data_type, parse_method in data_to_parse.items():
                try:
                    parse_start_time = time.time()
                    logger.info(f"  Parsing {data_type}...")
                    data = parse_method()
                    
                    # Handle case where parse_events returns a list of DataFrames
                    if isinstance(data, list) and len(data) > 0:
                        # Concatenate all DataFrames in the list
                        data = pd.concat(data, ignore_index=True)
                    elif isinstance(data, list) and len(data) == 0:
                        data = pd.DataFrame()  # Empty DataFrame
                    
                    if data is not None and not data.empty:
                        # Apply data type optimizations
                        data = optimize_datatypes(data, data_type)
                        
                        # Save as parquet with compression
                        output_file = demo_output_folder / f"{data_type}.parquet"
                        data.to_parquet(
                            output_file, 
                            index=False,
                            compression='snappy',  # Better compression for repeated strings
                            engine='pyarrow'
                        )
                        
                        rows_count = len(data)
                        demo_rows += rows_count
                        total_rows += rows_count
                        parse_time = time.time() - parse_start_time
                        
                        logger.info(f"  Saved {data_type} to {output_file} ({rows_count:,} rows, {parse_time:.1f}s)")
                    else:
                        logger.warning(f"  No data found for {data_type}")
                        
                except Exception as e:
                    logger.error(f"  Error parsing {data_type}: {str(e)}")
                    continue
            
            demo_time = time.time() - demo_start_time
            logger.info(f"Successfully processed {demo_file.name} ({demo_rows:,} total rows, {demo_time:.1f}s)")
            
        except Exception as e:
            logger.error(f"Error processing {demo_file.name}: {str(e)}")
            continue
    
    total_time = time.time() - start_time
    logger.info(f"Demo parsing completed! ({total_rows:,} total rows processed in {total_time:.1f}s)")

def main():
    """Main function to run the demo parsing pipeline"""
    logger.info("Starting demo parsing pipeline...")
    parse_demo_files()

if __name__ == "__main__":
    main()