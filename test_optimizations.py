"""
Test script to verify performance optimizations work correctly.
"""

import time
import logging
from duckdb_connector import CSGODataAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_optimizations():
    """Test the optimized components."""
    print("🧪 Testing CS:GO Analysis Optimizations")
    print("=" * 60)
    
    try:
        # Test 1: Initialize analyzer with optimized views
        print("\n📋 Test 1: Database Connection & View Creation")
        start_time = time.time()
        analyzer = CSGODataAnalyzer()
        init_time = time.time() - start_time
        print(f"✅ Analyzer initialized in {init_time:.2f}s")
        
        # Test 2: Test sampled views exist
        print("\n📋 Test 2: Verify Sampled Views")
        schema_info = analyzer.get_schema_info()
        sampled_views = [view for view in schema_info.keys() if 'sampled' in view]
        print(f"✅ Found {len(sampled_views)} sampled views: {sampled_views}")
        
        # Test 3: Performance comparison - full vs sampled
        print("\n📋 Test 3: Performance Comparison")
        
        # Full query
        full_query = """
        SELECT demo_name, COUNT(*) as total_rows
        FROM all_player_ticks
        GROUP BY demo_name
        """
        start_time = time.time()
        full_result = analyzer.query(full_query, use_cache=False)
        full_time = time.time() - start_time
        print(f"📊 Full query: {len(full_result)} demos, {full_result['total_rows'].sum():,} total rows in {full_time:.2f}s")
        
        # Sampled query
        sampled_query = """
        SELECT demo_name, COUNT(*) as sampled_rows
        FROM all_player_ticks_sampled
        GROUP BY demo_name
        """
        start_time = time.time()
        sampled_result = analyzer.query(sampled_query, use_cache=False)
        sampled_time = time.time() - start_time
        print(f"📊 Sampled query: {len(sampled_result)} demos, {sampled_result['sampled_rows'].sum():,} sampled rows in {sampled_time:.2f}s")
        
        if full_time > 0:
            speedup = full_time / sampled_time if sampled_time > 0 else float('inf')
            data_reduction = (1 - sampled_result['sampled_rows'].sum() / full_result['total_rows'].sum()) * 100
            print(f"🚀 Performance improvement: {speedup:.1f}x faster, {data_reduction:.1f}% data reduction")
        
        # Test 4: Cache functionality
        print("\n📋 Test 4: Query Caching")
        test_query = "SELECT COUNT(*) as total FROM all_grenades"
        
        # First execution (uncached)
        start_time = time.time()
        result1 = analyzer.query(test_query, use_cache=True)
        first_time = time.time() - start_time
        
        # Second execution (cached)
        start_time = time.time()
        result2 = analyzer.query(test_query, use_cache=True)
        second_time = time.time() - start_time
        
        print(f"📊 First query: {first_time:.3f}s")
        print(f"📊 Cached query: {second_time:.3f}s")
        
        if first_time > second_time and second_time < 0.1:
            print(f"✅ Cache working: {(first_time/second_time):.1f}x speedup")
        else:
            print("⚠️  Cache may not be working as expected")
        
        # Test 5: Optimized expert validation query
        print("\n📋 Test 5: Optimized Expert Query")
        expert_query = """
        SELECT 
            demo_name,
            COUNT(DISTINCT name) as unique_players,
            ROUND(X/400)*400 as zone_x,
            ROUND(Y/400)*400 as zone_y,
            COUNT(*) as activity
        FROM all_player_ticks_sampled
        WHERE m_iTeamNum IN (2, 3) AND name IS NOT NULL
        GROUP BY demo_name, zone_x, zone_y
        HAVING activity >= 10
        ORDER BY activity DESC
        LIMIT 5
        """
        
        start_time = time.time()
        result = analyzer.query(expert_query, timeout=10)
        expert_time = time.time() - start_time
        print(f"✅ Expert query completed in {expert_time:.2f}s, returned {len(result)} strategic zones")
        
        # Test 6: Data type optimizations
        print("\n📋 Test 6: Data Type Information")
        sample_query = "SELECT * FROM all_player_ticks LIMIT 1"
        sample_df = analyzer.query(sample_query)
        
        if not sample_df.empty:
            memory_usage = sample_df.memory_usage(deep=True).sum()
            print(f"📊 Sample row memory usage: {memory_usage} bytes")
            print(f"📊 Data types: {dict(sample_df.dtypes)}")
        
        analyzer.close()
        print(f"\n🎉 All optimization tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        logger.error(f"Test failed: {str(e)}", exc_info=True)

def test_expert_validation():
    """Quick test of optimized expert validation."""
    print(f"\n🧪 Testing Optimized Expert Validation")
    print("=" * 60)
    
    try:
        from expert_validation import ExpertValidationAnalyzer
        
        validator = ExpertValidationAnalyzer()
        
        # Test just one section with timing
        print("🔧 Testing Map Control Analysis (optimized)...")
        start_time = time.time()
        validator.run_map_control_analysis()
        analysis_time = time.time() - start_time
        
        print(f"✅ Map control analysis completed in {analysis_time:.2f}s")
        
        if analysis_time < 10:  # Should be much faster now
            print(f"🚀 Performance target met: < 10s (achieved {analysis_time:.2f}s)")
        else:
            print(f"⚠️  Still slower than target: {analysis_time:.2f}s")
        
        validator.close()
        
    except Exception as e:
        print(f"❌ Expert validation test failed: {str(e)}")
        logger.error(f"Expert validation test failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_optimizations()
    test_expert_validation()
