"""
Quick diagnostic script to check what views are being created.
"""

from duckdb_connector import CSGODataAnalyzer

def diagnose_views():
    print("🔍 Diagnosing View Creation")
    print("=" * 50)
    
    analyzer = CSGODataAnalyzer()
    
    # Check what views exist
    views_query = """
    SELECT table_name, table_type 
    FROM information_schema.tables 
    WHERE table_type = 'VIEW'
    ORDER BY table_name
    """
    
    views = analyzer.query(views_query)
    print(f"📊 Found {len(views)} views:")
    for view in views['table_name']:
        print(f"  - {view}")
    
    # Check specifically for unified views
    unified_views = [v for v in views['table_name'] if v.startswith('all_')]
    print(f"\n🔗 Unified views ({len(unified_views)}):")
    for view in unified_views:
        print(f"  - {view}")
    
    # Check sampled views
    sampled_views = [v for v in views['table_name'] if 'sampled' in v]
    print(f"\n⚡ Sampled views ({len(sampled_views)}):")
    for view in sampled_views:
        print(f"  - {view}")
    
    analyzer.close()

if __name__ == "__main__":
    diagnose_views()
