# Code Generation Instructions

## 📝 Instructions for AI Code Generation

This file contains CS:GO-specific instructions for the StratagemForge project.

> **Note**: General Python development standards and Copilot instructions are in `.github/copilot-instructions.md`

---

## 🎯 Current Project Context
- **Project**: CS:GO/CS2 Demo Analysis Tool
- **Tech Stack**: Python, DuckDB, demoparser2, pandas, pyarrow
- **Purpose**: Strategic analysis of professional CS matches for team preparation

---

## 🔧 Code Style & Standards

### **Performance Requirements**
- [ ] Always optimize for query performance (use sampling, indexing)
- [ ] Prefer columnar operations over row-by-row processing
- [ ] Use strategic data sampling (every 32-64 ticks) for large datasets
- [ ] Include timing/performance logging for operations > 1 second
- [ ] Cache frequently accessed data and query results

### **Error Handling**
- [ ] Always include try-catch blocks for database operations
- [ ] Log errors with context (query, data size, timing)
- [ ] Provide graceful degradation when optional features fail
- [ ] Include user-friendly error messages

### **Code Organization**
- [ ] Use descriptive function/variable names
- [ ] Include docstrings for all functions
- [ ] Separate concerns (parsing, analysis, visualization)
- [ ] Use type hints where appropriate
- [ ] Keep functions focused and under 50 lines when possible

---

## 📊 Data Optimization Guidelines

### **SQL Query Optimization**
```sql
-- Always sample large datasets
WHERE tick % 64 = 0  -- Every 2 seconds

-- Use zone-based aggregation for positioning
ROUND(X/400)*400, ROUND(Y/400)*400

-- Filter early and use HAVING for post-aggregation filtering
WHERE name IS NOT NULL AND name != ''
HAVING COUNT(*) >= 100
```

### **Data Types**
- Use `int32` for coordinates (strategic analysis doesn't need float64 precision)
- Use `int8` for categorical data (team numbers, health 0-100)
- Use `category` dtype for repeated strings (player names, map names)
- Compress parquet files with 'snappy' compression

### **Memory Management**
- Process data in chunks when possible
- Use generators for large datasets
- Clear intermediate DataFrames when done
- Monitor memory usage for operations on >1M rows

---

## 🎮 CS:GO/CS2 Domain Knowledge

### **Strategic Analysis Priorities**
1. **Player positioning and movement patterns**
2. **Team coordination and formations**
3. **Utility usage and timing**
4. **Map control and territory analysis**
5. **Anti-stratting and predictable patterns**

### **Data Sampling Strategy**
- **High frequency** (tick % 32 = 0): Player movement, health changes
- **Medium frequency** (tick % 128 = 0): Team formations, utility usage
- **Low frequency** (tick % 512 = 0): Strategic positioning analysis

### **Zone Sizes for Analysis**
- **Fine analysis**: 200x200 units (detailed positioning)
- **Strategic analysis**: 400x400 units (tactical zones)
- **Map overview**: 600x600 units (major areas)

---

## 🚀 Current Optimization Needs

### **Immediate Priorities**
- [ ] Apply optimizations to existing `pipeline.py`
- [ ] Update `duckdb_connector.py` with indexing and caching
- [ ] Optimize `expert_validation.py` queries
- [ ] Create optimized views in database setup

### **Performance Targets**
- **Pipeline processing**: < 5 minutes for all 5 demos
- **Query execution**: < 2 seconds for strategic analyses
- **Memory usage**: < 2GB for full dataset analysis
- **Storage**: < 500MB for all parquet files

---

## 📋 Specific Instructions

### **When Modifying Existing Files**
1. **Always backup approach**: Create new optimized versions first
2. **Incremental updates**: Apply optimizations section by section
3. **Backward compatibility**: Keep existing function signatures
4. **Testing**: Include simple tests to verify optimizations work

### **When Creating New Analysis Queries**
1. **Start with sampling**: Use tick % N = 0 for performance
2. **Zone-based grouping**: Use ROUND(X/size)*size for spatial analysis
3. **Early filtering**: Apply WHERE clauses before GROUP BY
4. **Result limiting**: Use HAVING to filter low-significance results

### **When Adding New Features**
1. **Performance first**: Consider optimization from the start
2. **Logging**: Add INFO logs for major operations
3. **Error handling**: Graceful failure with meaningful messages
4. **Documentation**: Update README and add examples

---

## 🔍 Code Review Checklist

Before submitting code, ensure:
- [ ] Performance optimizations applied (sampling, indexing, caching)
- [ ] Error handling for all database operations
- [ ] Logging for operations > 1 second
- [ ] Memory-efficient data processing
- [ ] Clear function names and docstrings
- [ ] Type hints where appropriate
- [ ] Examples or tests included

---

## 💡 Special Considerations

### **For LLM Integration**
- Include context in query results
- Provide interpretation hints for strategic insights
- Use descriptive column names
- Include sample queries and expected results

### **For Professional Use**
- Results must be accurate for competitive analysis
- Performance must support interactive exploration
- Insights should be actionable for team preparation
- Data security and integrity are critical

---

## 🎯 Current Task Context

**Active Goal**: Apply performance optimizations to existing pipeline and analysis scripts

**Key Areas**:
1. `pipeline.py` - Optimize demo parsing and data storage
2. `duckdb_connector.py` - Add indexing and caching
3. `expert_validation.py` - Optimize strategic analysis queries
4. `interactive_analysis.py` - Improve query performance

**Success Criteria**:
- 10x faster query execution
- Maintain analytical accuracy
- Professional-grade results
- Ready for expert validation

---

## 📝 Additional Instructions

### **Project-Specific Notes**

*Add CS:GO analysis specific instructions below:*

<!-- 
Example CS:GO specific instructions:
- Always validate demo file integrity before parsing
- Use specific map coordinate systems for each map
- Include round-by-round analysis capabilities
- Follow specific esports terminology and conventions
- Include specific performance benchmarks for demo parsing
- Use domain-specific error handling for demo parsing failures
-->

---

*Last updated: 2025-09-04*  
*For general Python development standards, see `.github/copilot-instructions.md`*
