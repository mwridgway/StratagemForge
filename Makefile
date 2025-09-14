# CS2 Economy Analysis Pipeline

.PHONY: venv fmt lint test run clean

# Virtual environment setup
venv:
	python -m venv .venv
	.\.venv\Scripts\pip install -e ".[dev]"

# Code formatting
fmt:
	.\.venv\Scripts\black cs2econ tests
	.\.venv\Scripts\ruff check --fix cs2econ tests

# Linting
lint:
	.\.venv\Scripts\ruff check cs2econ tests
	.\.venv\Scripts\mypy cs2econ

# Testing
test:
	.\.venv\Scripts\pytest -v

# Run pipeline
run:
	.\.venv\Scripts\python -m cs2econ.cli recompute --events-root data/events --out-root data

# Clean outputs
clean:
	Remove-Item -Recurse -Force data/balances/* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force data/snapshots/* -ErrorAction SilentlyContinue
	Remove-Item -Recurse -Force data/state/* -ErrorAction SilentlyContinue

# All formatting and checks
all: fmt lint test
