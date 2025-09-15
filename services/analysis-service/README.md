# Analysis Service

Counterstrike 2 demo analysis service built with FastAPI, Polars, and DuckDB.

## Features

- **Health Checks**: Comprehensive health monitoring with database and filesystem validation
- **Demo Analysis**: Placeholder analysis engine for Counterstrike 2 demo data
- **Data Management**: Lists and processes parquet files from shared data volume
- **Service Discovery**: Configurable via environment variables for container orchestration

## Technology Stack

- **Framework**: FastAPI (Python)
- **Data Processing**: Polars for data manipulation
- **Analytics**: DuckDB for analytical queries
- **Database**: PostgreSQL (optional, for metadata)
- **Containerization**: Docker with multi-stage builds

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Service port |
| `DATABASE_URL` | none | PostgreSQL connection string (optional) |
| `DATA_PATH` | `/app/data` | Path to parquet data files |

## API Endpoints

### Core Endpoints
- `GET /` - Service information and available endpoints
- `GET /health` - Detailed health check with dependencies
- `GET /ready` - Simple readiness probe
- `GET /config` - Current service configuration

### Analysis Endpoints
- `POST /analyze` - Run analysis on a demo file
- `GET /demos` - List available demo files

### API Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /redoc` - ReDoc documentation

## Usage

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/stratagemforge"
export DATA_PATH="/path/to/demo/data"

# Run the service
python main.py
```

### Running with Podman

```bash
# Build the image
podman build -t analysis-service .

# Run the container
podman run -p 8080:8080 \
  -e DATABASE_URL="postgresql://user:pass@localhost:5432/stratagemforge" \
  -v /path/to/data:/app/data \
  analysis-service
```

### Running Analysis

```bash
# Check service health
curl http://localhost:8080/health

# List available demos
curl http://localhost:8080/demos

# Run analysis on a demo
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"demo_id": "demo_001", "analysis_type": "basic"}'
```

## Development Notes

### Current Implementation
- **Placeholder Analysis**: Returns mock data for development
- **File Discovery**: Scans data directory for parquet files
- **Health Monitoring**: Validates PostgreSQL and filesystem access
- **Error Handling**: Comprehensive error responses with logging

### Production Considerations
- Implement actual demo parsing logic
- Add authentication/authorization
- Configure proper logging and monitoring
- Add input validation and rate limiting
- Implement caching for analysis results

### Data Processing Pipeline
1. **Demo Ingestion**: Parquet files written by ingestion-service
2. **Analysis Execution**: DuckDB queries on parquet data
3. **Result Processing**: Polars for data transformation
4. **Response Generation**: Structured JSON responses

## Service Integration

This service integrates with the StratagemForge platform:

- **Ingestion Service**: Consumes parquet files from shared volume
- **BFF Service**: Provides analysis data to frontend applications
- **User Service**: May use user context for personalized analytics
- **Database**: Stores analysis metadata and results cache

For complete system architecture, see the main project README and ARCHITECTURE.md.