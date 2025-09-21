# StratagemForge Modular Monolith

A streamlined Python backend for exploring Counter-Strike 2 demo analytics without the operational overhead of a multi-service stack. The new architecture focuses on developer productivity: run one FastAPI application locally, upload demo files, generate parquet artefacts, and experiment with lightweight insights in a few commands.

## Key Features

- **Unified FastAPI application** – ingestion, analysis, and user features live in a single process.
- **Local-first workflow** – no containers or external services required; SQLite powers persistence by default.
- **Demo ingestion pipeline** – upload `.dem` files, compute checksums, and persist parquet summaries for later analysis.
- **Exploratory analytics** – read processed parquet files and return quick metadata statistics through the API.
- **Seeded demo users** – a default "Demo Analyst" account is created automatically to unblock UI experimentation.
- **Extensible modular design** – domain-specific packages (`demos`, `analysis`, `users`) are ready for deeper implementations.

## Project Layout

```
├── pyproject.toml                 # Project and dependency metadata
├── src/
│   └── stratagemforge/
│       ├── core/                  # Configuration, database helpers, FastAPI factory
│       ├── api/                   # Route definitions and dependency wiring
│       └── domain/                # Feature modules (demos, analysis, users)
├── data/                          # Default data directory (raw uploads & processed parquet)
└── tests/                         # Unit and integration tests
```

## Getting Started

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -e .[dev]
```

### 3. Run the API locally

```bash
uvicorn stratagemforge.main:app --reload
```

The API is now available at <http://localhost:8000>. Useful endpoints:

- `GET /` – service overview
- `POST /api/demos/upload` – upload `.dem` files
- `GET /api/demos` – list uploaded demos
- `POST /api/analysis` – run lightweight analysis over processed parquet data
- `GET /docs` – interactive OpenAPI documentation

All data is stored beneath `./data` by default. The application will create subdirectories for raw uploads (`data/uploads`) and processed parquet output (`data/processed`).

## Development Tips

- Settings are powered by `pydantic-settings`. Override defaults by creating a `.env` file (e.g. `DATABASE_URL`, `DATA_DIR`, `MAX_UPLOAD_SIZE`).
- The SQLite database lives at `data/stratagemforge.db`. Remove the file to reset the environment.
- Demo ingestion streams uploads to disk in 4MB chunks to avoid excessive memory usage.
- Processed parquet files contain metadata for each demo. Extend `DemoProcessor` to add richer parsing in future iterations.
- The seeded demo user (`analyst@example.com`) enables quick UI authentication flows. Adjust or extend the seeding logic in `UserService.ensure_seed`.

## Running Tests

```bash
pytest
```

Unit tests cover the ingestion processor and service, while integration tests exercise the FastAPI endpoints end-to-end using temporary data directories.

## Roadmap Ideas

- Replace the placeholder parquet generator with a real demo parser when ready.
- Expand the analysis module with tactical insights, visualisations, or embeddings.
- Introduce authentication and role management once UI requirements solidify.
- Add background processing for long-running demo parsing jobs.

Enjoy building without the microservice overhead!
