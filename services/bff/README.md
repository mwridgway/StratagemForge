# BFF Service

Backend for Frontend service for StratagemForge, built with Node.js, TypeScript, and Fastify.

## Features

- **Service Orchestration**: Coordinates calls between frontend and backend microservices
- **Health Monitoring**: Comprehensive health checks for all service dependencies
- **API Gateway**: Single entry point for frontend applications
- **Rate Limiting**: Built-in request rate limiting and security
- **Auto Documentation**: Swagger/OpenAPI documentation with interactive UI
- **Service Discovery**: Configurable service URLs via environment variables

## Technology Stack

- **Framework**: Fastify (Node.js/TypeScript)
- **Security**: Helmet, CORS, Rate Limiting
- **Documentation**: Swagger/OpenAPI with SwaggerUI
- **HTTP Client**: Axios for service communication
- **Logging**: Pino with pretty printing for development

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `3000` | Service port |
| `NODE_ENV` | `development` | Environment (development/production) |
| `LOG_LEVEL` | `info` | Logging level |
| `USER_SERVICE_URL` | `http://user-service:8080` | User service endpoint |
| `INGESTION_SERVICE_URL` | `http://ingestion-service:8080` | Ingestion service endpoint |
| `ANALYSIS_SERVICE_URL` | `http://analysis-service:8080` | Analysis service endpoint |
| `CORS_ORIGIN` | `*` | CORS allowed origins |
| `REQUEST_TIMEOUT` | `30000` | HTTP request timeout (ms) |

## API Endpoints

### Core Endpoints
- `GET /` - Service information and available endpoints
- `GET /health` - Detailed health check with all service dependencies
- `GET /ready` - Simple readiness probe for container orchestration
- `GET /config` - Current service configuration and service URLs

### API Orchestration
- `GET /api/users` - User management (proxies to user-service)
- `GET /api/demos` - Demo file operations (proxies to ingestion-service)
- `POST /api/analysis` - Analysis operations (proxies to analysis-service)

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /swagger.json` - OpenAPI specification

## Development

### Local Development

```bash
# Install dependencies
npm install

# Start in development mode (with hot reload)
npm run dev

# Build for production
npm run build

# Start production build
npm start
```

### Testing

```bash
# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Linting

```bash
# Check code style
npm run lint

# Fix code style issues
npm run lint:fix

# Type checking only
npm run type-check
```

## Container Usage

### Building the Image

```bash
# Build the Docker image
podman build -t bff-service .
```

### Running with Podman

```bash
# Run the container
podman run -p 3000:3000 \
  -e USER_SERVICE_URL="http://user-service:8080" \
  -e INGESTION_SERVICE_URL="http://ingestion-service:8080" \
  -e ANALYSIS_SERVICE_URL="http://analysis-service:8080" \
  bff-service
```

### Using podman-compose

```bash
# Start all services
podman-compose up

# Check BFF service health
curl http://localhost:3000/health
```

## Service Architecture

### Request Flow
1. **Frontend** → **BFF Service** (single entry point)
2. **BFF Service** → **Backend Services** (orchestrated calls)
3. **Backend Services** → **BFF Service** (aggregated responses)
4. **BFF Service** → **Frontend** (unified API response)

### Health Monitoring
- **Service Health**: Individual health checks for each backend service
- **Dependency Health**: Aggregated health status from all dependencies
- **Circuit Breaker**: Graceful degradation when services are unavailable
- **Logging**: Comprehensive request/response logging with service identification

### Security Features
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Per-IP request limiting to prevent abuse
- **Security Headers**: Helmet.js for security best practices
- **Request Timeout**: Configurable timeouts to prevent hanging requests

## Integration with StratagemForge

This BFF service acts as the central API gateway for the StratagemForge platform:

- **Web Application**: Next.js frontend communicates only with BFF
- **User Service**: Authentication, user management
- **Ingestion Service**: Counterstrike 2 demo file uploads and processing
- **Analysis Service**: Demo analysis and statistics generation
- **Service Discovery**: All backend services accessed via environment variables

### Development Notes

**Current Implementation**:
- Basic service structure with health checks
- Placeholder API endpoints for development
- Swagger documentation setup
- Environment-based configuration

**Production Roadmap**:
- Implement actual service proxying with axios clients
- Add authentication/authorization middleware
- Implement request caching and response aggregation
- Add comprehensive error handling and retry logic
- Implement circuit breaker pattern for service resilience

For complete system architecture, see the main project ARCHITECTURE.md.