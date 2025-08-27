#!/usr/bin/env python3
"""
Performance comparison between Go (demoinfocs-golang) and Python (awpy) demo parsers
"""

import os
import json
import time
import subprocess
import sys
from pathlib import Path
import tempfile
from database.schema import DatabaseManager

def test_go_parser(demo_file_path: str):
    """Test the Go-based demo parser"""
    print("🚀 Testing Go Parser (demoinfocs-golang)")
    print("=" * 60)
    
    go_dir = Path("go_parser")
    if not go_dir.exists():
        print("❌ Go parser directory not found")
        return None
    
    # Check if Go is installed
    try:
        subprocess.run(["go", "version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Go not installed. Install from https://golang.org/")
        return None
    
    # Initialize Go module if needed
    if not (go_dir / "go.sum").exists():
        print("📦 Initializing Go dependencies...")
        subprocess.run(["go", "mod", "tidy"], cwd=go_dir, check=True)
    
    # Run the Go parser
    print(f"📊 Parsing: {os.path.basename(demo_file_path)}")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["go", "run", "main.go", demo_file_path],
            cwd=go_dir,
            capture_output=True,
            text=True,
            check=True
        )
        
        parse_time = time.time() - start_time
        print("Go Parser Output:")
        print(result.stdout)
        
        return {
            "success": True,
            "parse_time": parse_time,
            "output": result.stdout
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Go parser failed: {e}")
        print(f"stderr: {e.stderr}")
        return {
            "success": False,
            "error": str(e)
        }

def test_python_parser(demo_file_path: str):
    """Test the Python-based demo parser"""
    print("\n🐍 Testing Python Parser (awpy)")
    print("=" * 60)
    
    try:
        import awpy
        from parse_demo import process_demo_file, DatabaseManager
        
        # Use temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.duckdb', delete=False) as temp_db:
            temp_db_path = temp_db.name
        
        try:
            db_manager = DatabaseManager(temp_db_path)
            db_manager.connect()
            db_manager.migrate()
            
            print(f"📊 Parsing: {os.path.basename(demo_file_path)}")
            start_time = time.time()
            
            # Limit to 50k ticks for fair comparison
            success = process_demo_file(demo_file_path, db_manager, max_ticks=50000)
            
            parse_time = time.time() - start_time
            
            if success:
                # Get statistics
                stats = db_manager.connection.execute("""
                    SELECT COUNT(*) as tick_count,
                           COUNT(DISTINCT name) as player_count
                    FROM demo_ticks 
                    WHERE demo_filename = ?
                """, [os.path.basename(demo_file_path)]).fetchone()
                
                return {
                    "success": True,
                    "parse_time": parse_time,
                    "tick_count": stats[0] if stats else 0,
                    "player_count": stats[1] if stats else 0
                }
            else:
                return {"success": False, "error": "Processing failed"}
                
        finally:
            # Cleanup
            try:
                db_manager.close()
                os.unlink(temp_db_path)
            except:
                pass
                
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def load_go_results():
    """Load results from Go parser JSON output"""
    output_dir = Path("go_parser_output")
    if not output_dir.exists():
        return None
    
    # Find metadata file
    metadata_files = list(output_dir.glob("*_metadata.json"))
    if not metadata_files:
        return None
    
    with open(metadata_files[0]) as f:
        metadata = json.load(f)
    
    # Count ticks from all chunk files
    tick_files = list(output_dir.glob("*_ticks_*.json"))
    total_ticks = 0
    
    for tick_file in tick_files:
        with open(tick_file) as f:
            ticks = json.load(f)
            total_ticks += len(ticks)
    
    return {
        "metadata": metadata,
        "total_ticks": total_ticks,
        "total_files": len(tick_files)
    }

def run_comparison(demo_file_path: str):
    """Run a complete comparison between Go and Python parsers"""
    print(f"🏁 Demo Parser Performance Comparison")
    print(f"📁 Demo file: {demo_file_path}")
    print(f"📏 File size: {os.path.getsize(demo_file_path) / 1024 / 1024:.1f} MB")
    print("=" * 80)
    
    # Test Go parser
    go_result = test_go_parser(demo_file_path)
    
    # Test Python parser
    python_result = test_python_parser(demo_file_path)
    
    # Load Go results
    go_data = load_go_results() if go_result and go_result.get("success") else None
    
    # Print comparison results
    print("\n📊 COMPARISON RESULTS")
    print("=" * 80)
    
    if go_result and go_result.get("success"):
        print(f"🚀 Go Parser:")
        print(f"   ✅ Success: {go_result['success']}")
        print(f"   ⏱️  Parse time: {go_result['parse_time']:.2f} seconds")
        if go_data:
            print(f"   📈 Total ticks: {go_data['total_ticks']:,}")
            print(f"   🎯 Performance: {go_data['total_ticks'] / go_result['parse_time']:,.0f} ticks/sec")
    else:
        print(f"🚀 Go Parser: ❌ Failed")
    
    if python_result and python_result.get("success"):
        print(f"\n🐍 Python Parser:")
        print(f"   ✅ Success: {python_result['success']}")
        print(f"   ⏱️  Parse time: {python_result['parse_time']:.2f} seconds")
        print(f"   📈 Total ticks: {python_result['tick_count']:,}")
        print(f"   👥 Players: {python_result['player_count']}")
        if python_result['tick_count'] > 0:
            print(f"   🎯 Performance: {python_result['tick_count'] / python_result['parse_time']:,.0f} ticks/sec")
    else:
        print(f"🐍 Python Parser: ❌ Failed")
    
    # Performance comparison
    if (go_result and go_result.get("success") and 
        python_result and python_result.get("success") and go_data):
        
        go_perf = go_data['total_ticks'] / go_result['parse_time']
        python_perf = python_result['tick_count'] / python_result['parse_time']
        
        if go_perf > python_perf:
            speedup = go_perf / python_perf
            print(f"\n🏆 Winner: Go parser is {speedup:.1f}x faster!")
        else:
            speedup = python_perf / go_perf  
            print(f"\n🏆 Winner: Python parser is {speedup:.1f}x faster!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # Test with a demo file
    demo_files = [
        "demos/vitality-vs-mouz-m1-mirage-p1.dem",
        "demos/falcons-vs-vitality-m1-inferno.dem"
    ]
    
    for demo_file in demo_files:
        if os.path.exists(demo_file):
            run_comparison(demo_file)
            break
    else:
        print("❌ No demo files found for testing")
