# Ingestion Service

This is the Ingestion Service for StratagemForge, built with Go and Gin. It handles CS:GO demo file uploads and processing.

## Features

- Health check endpoint (`/health`)
- Ready check endpoint (`/ready`) 
- Configuration endpoint (`/config`) - demonstrates environment variable usage
- Demo file upload endpoint (`/upload`)
- Processing status tracking (`/status/:id`)
- List uploaded demos (`/demos`)

## Environment Variables

- `PORT` - Port to listen on (default: 8080)
- `DATABASE_URL` - PostgreSQL connection string
- `DATA_PATH` - Directory for storing demo files and parquet data (default: /app/data)

## Development

```bash
# Run locally
go mod tidy
go run main.go

# Build
go build -o ingestion-service main.go

# Docker build
docker build -t ingestion-service .
```

## Endpoints

- `GET /health` - Health check with database and filesystem connectivity tests
- `GET /ready` - Readiness probe
- `GET /config` - Show configuration (for debugging)
- `POST /upload` - Upload demo file for processing
- `GET /status/:id` - Get processing status for uploaded demo
- `GET /demos` - List all uploaded demo files

## Demo Processing Workflow

1. Demo file uploaded via `/upload` endpoint
2. File saved to `DATA_PATH` directory
3. Background processing begins (placeholder implementation)
4. Parsed data written to parquet files in `DATA_PATH`
5. Metadata stored in PostgreSQL database
6. Status can be tracked via `/status/:id` endpoint