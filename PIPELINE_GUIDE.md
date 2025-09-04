# 🎮 Complete Pipeline Execution Guide

## Quick Start - Run Everything

### Option 1: Full Clean Pipeline (Recommended)
```powershell
# Complete clean run (removes all previous data)
python run_complete_pipeline.py --clean
```

### Option 2: Fast Re-analysis (Keep Parsed Data)
```powershell
# Skip parsing if parquet files exist, just run analysis
python run_complete_pipeline.py --skip-parsing
```

### Option 3: Full Data Analysis (Slower, More Comprehensive)
```powershell
# Use full dataset instead of sampled (takes longer)
python run_complete_pipeline.py --full-analysis
```

---

## Manual Step-by-Step Execution

### Step 1: Parse Demo Files
```powershell
# Parse all .dem files in demos/ folder to parquet format
python pipeline.py
```
**Expected Output**: Creates `parquet/` directory with optimized data files  
**Time**: ~30-60 seconds for 5 demo files  
**Data**: 27M+ rows processed with optimizations

### Step 2: Run Strategic Analysis
```powershell
# Run all 16 strategic analysis questions
python expert_validation_optimized.py
```
**Expected Output**: Comprehensive tactical intelligence  
**Time**: ~4-8 seconds (optimized performance)  
**Analysis**: Territory control, player roles, utility usage, etc.

### Step 3: Interactive Analysis (Optional)
```powershell
# Open interactive analysis session
python interactive_analysis.py
```
**Usage**: Custom SQL queries and exploration

---

## Performance Benchmarking

### Check Current Performance
```powershell
# Run performance tests and view optimizations
python optimization_summary.py
```

### Test Different Modes
```powershell
# Fast mode (sampled data)
python expert_validation_optimized.py

# Full mode (complete dataset) 
python expert_validation_optimized.py --full
```

---

## File Structure After Pipeline Run

```
StratagemForge/
├── demos/                          # Original .dem files
│   ├── falcons-vs-vitality-m1-inferno.dem
│   ├── falcons-vs-vitality-m2-dust2.dem
│   ├── falcons-vs-vitality-m3-train.dem
│   ├── falcons-vs-vitality-m4-mirage.dem
│   └── falcons-vs-vitality-m5-nuke.dem
├── parquet/                        # Processed data (optimized)
│   ├── falcons-vs-vitality-m1-inferno/
│   │   ├── grenades.parquet        # Utility usage data
│   │   ├── player_info.parquet     # Player metadata
│   │   ├── player_ticks.parquet    # Movement/positioning
│   │   └── skins.parquet           # Equipment data
│   ├── ... (4 more demo datasets)
├── *.csv                           # Analysis output files
└── *.py                            # Analysis scripts
```

---

## Command Examples

### Clean Everything and Start Fresh
```powershell
# Remove all data and reprocess everything
Remove-Item -Recurse -Force parquet -ErrorAction SilentlyContinue
Remove-Item -Force *.db -ErrorAction SilentlyContinue  
Remove-Item -Force *.csv -ErrorAction SilentlyContinue
python run_complete_pipeline.py
```

### Quick Performance Check
```powershell
# See current performance metrics
python optimization_summary.py
```

### Custom Analysis Session  
```powershell
# Interactive SQL analysis
python -c "
from duckdb_connector_optimized import CSGODataAnalyzer
analyzer = CSGODataAnalyzer()
result = analyzer.query('SELECT name, COUNT(*) FROM all_player_info GROUP BY name')
print(result)
analyzer.close()
"
```

---

## Performance Expectations

| Operation | Time (Optimized) | Data Processed |
|-----------|------------------|----------------|
| Demo Parsing | ~30s | 5 demos → 27M rows |
| Strategic Analysis | ~4s | 16 questions |
| Database Setup | ~1s | Views + indexes |
| Query Execution | <0.1s | Most queries |

**Performance Improvements**: >15x faster than original implementation  
**Data Reduction**: 98.4% through strategic sampling  
**Memory Usage**: Optimized data types (int32, int8, category)

---

## Troubleshooting

### If Pipeline Fails
1. **Check Python environment**: Ensure all dependencies installed
2. **Check demo files**: Verify `.dem` files exist in `demos/` folder  
3. **Check disk space**: Parquet files need ~500MB storage
4. **Check logs**: All operations include timing and error information

### Common Issues
- **"No demo files found"**: Add `.dem` files to `demos/` directory
- **Timeout errors**: Use `--skip-parsing` to avoid re-parsing large files
- **Memory issues**: The optimized version uses <2GB RAM typically

### Performance Tuning
- **Faster analysis**: Use default sampled mode
- **More detailed**: Use `--full-analysis` flag  
- **Development**: Use `--skip-parsing` to iterate quickly on analysis code

---

*This pipeline is optimized for professional esports team analysis with >15x performance improvement over the original implementation.*
