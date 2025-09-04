# Copilot Instructions for StratagemForge

## 📝 Instructions for AI Code Generation

This file contains specific instructions and preferences for generating and modifying code in the StratagemForge project.

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

## 📝 Python Development Standards

You are assisting inside a Python repository. Follow these rules and defaults.

### **Goal**
- Produce production-grade Python with fast installs, strict hygiene, and easy CI.

### **Runtime and packaging**
- Use Python 3.12 by default. If unavailable, 3.11.
- Use uv for dependency management and lockfiles.
- Generate a pyproject.toml with:
  - build-system = "hatchling"
  - tool.uv with exact versions and groups: default, dev
  - tool.ruff for lint + format
  - tool.pytest.ini_options
  - tool.mypy config
- Prefer src/ layout:
  - src/<package_name>/...
  - tests/ with pytest
  - examples/
  - scripts/

### **CLI and configuration**
- Use Typer for CLIs.
- Use pydantic v2 and pydantic-settings for config, loaded from env and .env.
- Log with structlog. Provide JSON logs for production and pretty logs for local.

### **Formatting, linting, types**
- Formatter: ruff format
- Linter: ruff with common rules enabled. Fix what you can.
- Imports: isort via ruff rules
- Static types: mypy in strict mode for src. Allow tests to be less strict.
- Add .editorconfig for 120 char line length and UTF-8.

### **Testing**
- Use pytest with:
  - pytest-cov
  - Hypothesis for property tests when useful
- Create a factory for test data. Prefer fixtures and parametrize.
- Provide a minimal CI workflow that runs pytest and ruff and mypy.

### **Pre-commit**
- Add .pre-commit-config.yaml with hooks:
  - ruff
  - ruff-format
  - mypy
  - detect-private-key
  - end-of-file-fixer
  - trailing-whitespace

### **Makefile or justfile**
- Provide a Makefile with these phony targets:
  - setup: uv venv && uv sync
  - lint: ruff check .
  - fmt: ruff format .
  - type: mypy
  - test: pytest -q
  - cov: pytest --cov=src --cov-report=term-missing
  - all: fmt lint type test
- On Windows, also add equivalent PowerShell scripts under scripts/.

### **Docker and Dev Container**
- Provide a slim Dockerfile that uses python:3.12-slim, uv for install, nonroot user, and multi-stage build:
  - stage 1: builder with uv sync --frozen
  - stage 2: runtime copying .venv or site-packages
- Provide .devcontainer/devcontainer.json that installs uv and enables Python, Ruff, and Copilot extensions.

### **VS Code settings**
- .vscode/settings.json:
  - python.analysis.typeCheckingMode = "strict"
  - ruff.lint.args = []
  - ruff.organizeImports = true
  - editor.formatOnSave = true
  - files.eol = "\n"
  - python.testing.pytestEnabled = true
- .vscode/extensions.json:
  - ms-python.python
  - ms-python.vscode-pylance
  - charliermarsh.ruff
  - ms-toolsai.jupyter

### **Security and reliability**
- Add bandit in dev dependencies and a Makefile target bandit.
- Use httpx with timeouts and retries for HTTP.
- Validate all external inputs with pydantic models.
- Add basic SAST via CodeQL workflow.

### **Performance tips**
- Prefer asyncio when IO bound. Use trio only if asked.
- For CPU hot paths, suggest numpy or numba. Measure with py-spy or scalene. Never guess.

### **Docs**
- Include README with quickstart commands using uv.
- Add mkdocs-material config if docs are requested. Otherwise keep README concise.
- Docstrings in Google style.

### **Repository bootstrap**
- Create these files when asked to scaffold:
  - pyproject.toml
  - README.md
  - src/<package_name>/__init__.py
  - src/<package_name>/cli.py using Typer
  - src/<package_name>/config.py using pydantic-settings
  - tests/test_cli.py and tests/test_config.py
  - .editorconfig
  - .gitignore for Python, uv, VS Code
  - .pre-commit-config.yaml
  - Makefile
  - .vscode/{settings.json,extensions.json}
  - .devcontainer/devcontainer.json
  - Dockerfile
  - .github/workflows/ci.yml running ruff, mypy, pytest, coverage upload

### **Dependency hints**
- Default dependencies:
  - runtime: typer[all], pydantic>=2, pydantic-settings, httpx, structlog
  - dev: ruff, mypy, pytest, pytest-cov, hypothesis, pre-commit, bandit, py-spy, scalene, coverage
- Use uv add and uv lock conventions in README examples.

### **Coding style**
- Pure functions where practical. Small modules. Clear boundaries.
- Raise custom exceptions in a dedicated errors.py. Map exceptions to exit codes in CLI.
- Always set timeouts on IO. Avoid global state. Use dependency injection for testability.
- Include minimal example usage in docstrings.

### **Project types**
- If the user mentions data work:
  - Add duckdb, polars, pyarrow. Prefer Parquet for storage. Provide an ingestion pipeline example that writes to Parquet and queries with DuckDB.
- If the user mentions LLMs:
  - Add litellm or openai, use pydantic models for tool I/O, and create a simple chat module with streaming and retries.

### **Deliverables**
- When asked to scaffold, produce all files with complete content, not placeholders.
- When editing, preserve existing tools and conventions unless explicitly told to change them.

---

*Last updated: 2025-09-04*  
*Update this file with your specific requirements and preferences!*
