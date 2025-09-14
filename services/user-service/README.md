# User Service

This is the User Service for StratagemForge, built with Go and Gin.

## Features

- Health check endpoint (`/health`)
- Ready check endpoint (`/ready`)
- Configuration endpoint (`/config`) - demonstrates environment variable usage
- Placeholder user management endpoints

## Environment Variables

- `PORT` - Port to listen on (default: 8080)
- `DATABASE_URL` - PostgreSQL connection string

## Development

```bash
# Run locally
go mod tidy
go run main.go

# Build
go build -o user-service main.go

# Docker build
docker build -t user-service .
```

## Endpoints

- `GET /health` - Health check with database connectivity test
- `GET /ready` - Readiness probe
- `GET /config` - Show configuration (for debugging)
- `GET /users` - List users (placeholder)
- `POST /auth/login` - User login (placeholder)