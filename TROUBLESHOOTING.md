# Troubleshooting the Modular Monolith

This guide focuses on common issues when running the single FastAPI application locally.

## 1. Environment Setup

### Virtual environment not activating
- Ensure you are using `python -m venv .venv` to create the environment.
- Activate with `source .venv/bin/activate` (macOS/Linux) or `.venv\Scripts\activate` (Windows PowerShell).

### Dependency installation failures
- Upgrade pip: `python -m pip install --upgrade pip`.
- If `pyarrow` wheels fail to install, ensure you are on Python 3.11+ and have recent pip versions.

## 2. Database Problems

### SQLite lock errors
- Close any running FastAPI instance before launching tests or another server.
- Delete `data/stratagemforge.db` to reset the state if corruption occurs (data will be lost).

### Using a custom database location
- Create a `.env` file with `DATABASE_URL=sqlite:///absolute/path/to/stratagemforge.db`.
- Restart the application so the new settings are picked up.

## 3. File Upload Issues

### "Only .dem files are supported"
- The ingestion service restricts uploads to files ending in `.dem`.
- Rename the file if necessary or extend validation logic in `DemoService._stream_to_disk`.

### Uploads exceed size limit
- Default limit is 1 GB. Adjust via `.env`: `MAX_UPLOAD_SIZE=2147483648` for 2 GB.

### Parquet output missing
- Confirm the application has write access to `data/processed`.
- Run `pytest` to ensure the ingestion processor is functioning.

## 4. API Troubleshooting

### FastAPI server does not start
- Verify dependencies: `pip show fastapi uvicorn`.
- Check the console for stack traces – missing directories will be created automatically, so file permission errors are most likely.

### 404 on `/api/demos/upload`
- Ensure you are sending the file with the form field name `demo`.
- Example using curl:
  ```bash
  curl -F "demo=@path/to/file.dem" http://localhost:8000/api/demos/upload
  ```

### 500 on `/api/analysis`
- The request references a demo that has no processed parquet file. Re-upload the demo or inspect the logs for file permission errors.

## 5. Testing Tips

- `pytest` uses temporary directories for isolation; if tests fail with permission errors, ensure your shell user can create folders in the project directory.
- Clean the test cache with `pytest --cache-clear` when debugging flaky tests.

## 6. Resetting the Environment

If things get messy:

```bash
rm -rf data/stratagemforge.db data/uploads data/processed
mkdir -p data/uploads data/processed
```

Then restart the server:

```bash
uvicorn stratagemforge.main:app --reload
```

You're back to a clean slate.
