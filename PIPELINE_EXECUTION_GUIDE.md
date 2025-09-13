# 🚀 Complete Pipeline Execution Guide

## Quick Start Commands

### **Option 1: Fast Analysis (Recommended for most use cases)**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the complete optimized pipeline
python run_complete_pipeline_new.py --mode fast
```

### **Option 2: Clean Run (Start fresh)**
```powershell
# Clean all data and rerun everything
python run_complete_pipeline_new.py --mode fast --clean
```

### **Option 3: Full Comprehensive Analysis**
```powershell
# Use complete dataset (slower but comprehensive)
python run_complete_pipeline_new.py --mode full
```

### **Option 4: Force Reparse Demos**
```powershell
# Reparse demo files even if parquet data exists
python run_complete_pipeline_new.py --mode fast --force-reparse
```

---

## 📊 Performance Comparison

| Mode | Data Used | Speed | Use Case |
|------|-----------|--------|----------|
| **Fast** | 98.4% sampled | ~4 seconds | Interactive analysis, team prep |
| **Full** | Complete dataset | ~60 seconds | Deep analysis, research |

---

## 🔧 Step-by-Step Manual Execution

If you prefer to run each step manually:

### **Step 1: Parse Demo Files**
```powershell
# Parse all demo files into optimized parquet format
python -c "from pipeline import parse_demo_files; parse_demo_files()"
```

### **Step 2: Run Strategic Analysis (Fast)**
```powershell
# Run fast strategic analysis with sampled data
python expert_validation_optimized.py
```

### **Step 3: Run Strategic Analysis (Full)**
```powershell
# Run comprehensive analysis with complete dataset
python -c "from expert_validation_optimized import ExpertValidationAnalyzer; analyzer = ExpertValidationAnalyzer(); analyzer.run_all_analyses_full()"
```

### **Step 4: Interactive Analysis**
```powershell
# Open interactive analysis for custom queries
python interactive_analysis.py
```

---

## 📁 Expected Output Structure

After running the pipeline, you'll have:

```
parquet/
├── falcons-vs-vitality-m1-inferno/
│   ├── player_ticks.parquet          # Player movement/status data
│   ├── event_player_death.parquet    # Kill events
│   ├── event_weapon_fire.parquet     # Shooting events
│   ├── grenades.parquet              # Utility usage
│   └── ...
├── falcons-vs-vitality-m2-dust2/
└── ... (other maps)
```

---

## 🎯 Analysis Results

The strategic analysis provides:

1. **Player Movement Patterns** - Heat maps and positioning analysis
2. **Team Coordination** - Formation analysis and tactical insights
3. **Utility Usage** - Grenade timing and effectiveness
4. **Map Control** - Territory control patterns
5. **Anti-Stratting Insights** - Predictable behavior detection
6. **Performance Metrics** - KDA, ADR, and tactical contributions

---

## 🚨 Troubleshooting

### **Common Issues:**

**1. Virtual Environment Not Activated**
```powershell
# Solution: Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```

**2. Missing Demo Files**
```
Error: No .dem files found in demos folder!
```
```powershell
# Solution: Check demos folder
ls demos/
# Should show .dem files
```

**3. Memory Issues with Full Mode**
```powershell
# Solution: Use fast mode instead
python run_complete_pipeline_new.py --mode fast
```

**4. Import Errors**
```powershell
# Solution: Install missing dependencies
pip install -r requirements.txt
```

### **Performance Issues:**

**Slow Parsing:**
- Use default settings (already optimized)
- Check available RAM (needs ~2GB)
- Consider using SSD storage

**Slow Analysis:**
- Use fast mode for interactive work
- Reserve full mode for final analysis
- Check disk space for parquet files

---

## 🔧 Advanced Usage

### **Custom Analysis**
```python
# Custom strategic analysis
from expert_validation_optimized import ExpertValidationAnalyzer

analyzer = ExpertValidationAnalyzer()

# Run specific analysis
results = analyzer.analyze_player_positioning(use_full_data=False)
print(results)

# Custom query
custom_results = analyzer.execute_query("""
    SELECT player_name, AVG(health) as avg_health 
    FROM player_ticks_sampled 
    WHERE map_name = 'de_inferno'
    GROUP BY player_name
""")
```

### **Interactive Exploration**
```powershell
# Start interactive analysis session
python interactive_analysis.py
```

---

## 📈 Expected Performance

With the optimized pipeline:

- **Demo Parsing**: ~30-60 seconds for 5 demos
- **Fast Analysis**: ~4 seconds for all strategic queries
- **Full Analysis**: ~60 seconds for comprehensive insights
- **Memory Usage**: <2GB peak usage
- **Storage**: ~200MB parquet files (compressed)

---

## 💡 Best Practices

1. **Start with Fast Mode** - Use for interactive exploration
2. **Clean Runs** - Use `--clean` when changing analysis parameters
3. **Backup Important Results** - Strategic insights are valuable
4. **Monitor Performance** - Check timing logs for bottlenecks
5. **Use Full Mode Sparingly** - Reserve for final comprehensive analysis

---

## 🎮 Next Steps

After running the pipeline:

1. **Review Console Output** - Strategic insights are printed
2. **Check Parquet Files** - Verify data was processed correctly
3. **Run Interactive Analysis** - Explore custom queries
4. **Use Results for Team Prep** - Apply insights to tactical planning
5. **Share with Team** - Strategic analysis ready for coaching staff

---

*Pipeline optimized for professional CS:GO team analysis*  
*Performance improvements: >15x faster execution*  
*Data reduction: 98.4% sampling for interactive use*
