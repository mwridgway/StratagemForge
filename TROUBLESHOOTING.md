# Build Troubleshooting Guide

This guide helps resolve common build issues when starting StratagemForge services.

## Quick Fixes

### 1. Clean Build (Most Common Solution)
```bash
# Stop all services
podman compose down

# Remove all images and rebuild from scratch
podman compose build --no-cache

# Start services
podman compose up
```

### 2. Check Podman Status
```bash
# Verify Podman is running
podman version

# Check Podman machine status (Windows/macOS)
podman machine list
podman machine start
```

### 3. Free Up Resources
```bash
# Clean up unused containers and images
podman system prune -a

# Remove volumes (warning: deletes data)
podman volume prune
```

## Common Build Errors

### Error: "Cannot connect to Podman"
**Solution:**
```bash
podman machine start
```

### Error: "CMake not installed" (Python services)
This is fixed in the updated Dockerfile by adding CMake to the build dependencies.

### Error: "go.sum missing" (Go services)
**Solution:**
```bash
cd services/user-service && go mod tidy
cd ../ingestion-service && go mod tidy
```

### Error: "Port already in use"
**Solution:**
```bash
# Find processes using the ports
netstat -tulpn | grep :3000
netstat -tulpn | grep :5432

# Kill processes or change ports in compose.yml
```

### Error: "Docker registry authentication"
**Solution:**
```bash
# Pull base images manually
podman pull python:3.11-alpine
podman pull golang:1.21-alpine
podman pull node:18-alpine
podman pull postgres:15-alpine
```

## Service-Specific Issues

### Analysis Service (Python)
- **Issue**: Polars/DuckDB compilation failures
- **Solution**: Use simplified pandas-based version (already implemented)

### BFF Service (Node.js)
- **Issue**: npm install failures
- **Solution**: Clear npm cache and rebuild
```bash
cd services/bff
npm cache clean --force
npm install
```

### Go Services (User/Ingestion)
- **Issue**: Missing dependencies
- **Solution**: Update Go modules
```bash
go mod download
go mod tidy
```

## Development Mode

For faster development, run services individually:

```bash
# Start only database
podman compose up postgres

# Run services in development mode
cd services/user-service
go run main.go

# In another terminal
cd services/bff
npm run dev

# In another terminal  
cd web-app
npm run dev
```

## Build Order Issues

If builds fail due to dependencies, build in order:

```bash
# Build infrastructure first
podman compose build postgres

# Build backend services
podman compose build user-service
podman compose build ingestion-service  
podman compose build analysis-service

# Build frontend services
podman compose build bff
podman compose build web-app
```

## Environment Issues

### Check Environment Variables
```bash
# Verify .env file exists
cat .env

# Check required variables are set
echo $USER_SERVICE_URL
echo $DATABASE_URL
```

### Reset Environment
```bash
# Copy example environment
cp .env.example .env

# Edit with your settings
notepad .env  # Windows
nano .env     # Linux/macOS
```

## Memory Issues

### Increase Docker/Podman Memory
- **Windows**: Docker Desktop → Settings → Resources → Advanced
- **macOS**: Docker Desktop → Preferences → Resources → Advanced  
- **Linux**: Configure cgroup limits

### Reduce Concurrent Builds
```bash
# Build one service at a time
podman compose build user-service
podman compose build ingestion-service
# etc...
```

## Network Issues

### Reset Network
```bash
podman network prune
podman compose down
podman compose up
```

### Check Service Communication
```bash
# Test service endpoints
curl http://localhost:3000/health
curl http://localhost:8080/health
```

## Last Resort Solutions

### Complete Reset
```bash
# WARNING: This removes everything
podman system reset

# Restart Podman
podman machine stop
podman machine start

# Rebuild everything
podman compose build --no-cache
podman compose up
```

### Individual Service Testing
```bash
# Build and test one service
cd services/user-service
podman build -t test-user-service .
podman run -p 8080:8080 test-user-service
```

## Getting Help

1. **Check logs**: `podman compose logs [service-name]`
2. **Verbose output**: `podman compose up --verbose`
3. **Service status**: `podman compose ps`
4. **Resource usage**: `podman stats`

## Success Indicators

When everything works correctly, you should see:
- ✅ All services show "Built" status
- ✅ Web app accessible at http://localhost:3000
- ✅ All health checks pass
- ✅ No error messages in logs