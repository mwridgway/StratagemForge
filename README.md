# Strategem Forge: AI-Powered Counter-Strike 2 Analytics Platform

## 1\. Overview

Strategem Forge self-hostable analytics platform designed to give Counter-Strike 2 teams a competitive edge. 

### Core Technologies

**Backend Microservices:**
- **Go**: High-performance services for user management and data ingestion
- **Python**: ML and data analytics service with pandas/numpy
- **Node.js/TypeScript**: BFF (Backend for Frontend) API gateway
- **PostgreSQL**: Primary data storage for structured data
- **Podman**: Container orchestration for development and deployment

**Frontend:**
- **Next.js 14**: Modern React framework with App Router
- **TypeScript**: Type-safe development experience
- **Tailwind CSS**: Utility-first styling framework

**Architecture:**
- **Microservices**: Loosely coupled, independently deployable services
- **API Gateway Pattern**: BFF service handles frontend-specific API aggregation
- **Container-First**: Fully containerized with multi-stage Docker builds
- **Database-Per-Service**: Each service can have isolated data storage


## 2\. Phased Implementation Plan

This project is designed to be built in distinct, sequential phases. Each phase delivers a functional component of the platform, allowing for incremental development and immediate value at every stage.

### Phase 1: The Foundation - Automated Demo Parsing

### Phase 2: The Command Center - Interactive Dashboard

### Phase 3: The AI Analyst - "Query-Your-Demos" with RAG

### Phase 4: Advanced Insight - GNN for Tactic Classification

### Phase 5: Automation & Expansion - Fine-Tuning for Scouting

## 3\. Setup and Installation

### Prerequisites

- **Podman** (or Docker) - Container runtime for running microservices
  - Windows: Install Podman Desktop or use `winget install podman`
  - macOS: `brew install podman`
  - Linux: Install via package manager
- **podman-compose** - Docker Compose compatibility for Podman
  - Install: `pip install podman-compose`
- **Git** - Version control for cloning the repository
- **8GB+ RAM** - Recommended for running all services simultaneously
- **Windows, macOS, or Linux** - Cross-platform compatible

**Note**: On Windows, you'll need to start the Podman machine first:
```bash
podman machine init
podman machine start
```

### Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/mwridgway/StratagemForge.git
   cd StratagemForge
   
   # For the latest containerized version, use the refactor branch:
   git checkout refactor/scorched-earth
   ```

2. **Start All Services**
   ```bash
   # Start the complete platform with one command
   podman-compose up -d
   ```

3. **Access the Platform**
   - **Web Application**: http://localhost:3000
   - **BFF API Gateway**: http://localhost:8080
   - **BFF Endpoints**: http://localhost:8080/ (lists all available endpoints)
   - **System Health**: http://localhost:8080/health

4. **Verify Everything is Running**
   ```bash
   # Check all service status
   podman-compose ps
   
   # Test web application
   curl http://localhost:3000
   
   # Test API gateway and see all available endpoints
   curl http://localhost:8080/
   
   # Test API gateway health
   curl http://localhost:8080/health
   ```

### What Gets Started

The `podman-compose up -d` command starts all 6 microservices:

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **Web App** | Next.js/React | 3000 | User interface |
| **BFF Service** | Node.js/TypeScript | 8080 | API orchestration & Gateway |
| **User Service** | Go/Gin | 8081 | Authentication & User Management |
| **Ingestion Service** | Go/Gin | 8083 | Demo file processing |
| **Analysis Service** | Python/FastAPI | 8082 | Data analytics & ML |
| **PostgreSQL** | Database | 5432 | Data storage |

### Development Mode

For development with hot reloading:

```bash
# Start infrastructure only
podman-compose up postgres -d

# Run services individually in development mode
cd services/user-service && go run main.go
cd services/ingestion-service && go run main.go  
cd services/analysis-service && python main.py
cd services/bff && npm run dev
cd web-app && npm run dev
```

### Stopping Services

```bash
# Stop all services
podman-compose down

# Stop and remove volumes (clean slate)
podman-compose down -v
```

### Troubleshooting

**Services not starting?**
- Check if ports 3000, 5432, 8080-8083 are available
- Ensure Podman machine is running: `podman machine start`
- Check Podman status: `podman version`
- View logs: `podman-compose logs [service-name]`

**Database connection issues?**
- Wait 30-60 seconds for PostgreSQL to fully initialize
- Check health status: `curl http://localhost:8080/health`

**Need to rebuild after changes?**
```bash
# Rebuild all images
podman-compose build

# Rebuild specific service
podman-compose build user-service

# Rebuild and restart
podman-compose up --build -d
```

## 4\. Usage

### Uploading Demo Files

1. Navigate to http://localhost:3000/demos
2. Click "Upload Demo" 
3. Select your Counterstrike 2 `.dem` files
4. Monitor processing status

### Viewing Analysis

1. Go to http://localhost:3000/analysis
2. Select processed demos
3. View statistics, heatmaps, and insights
4. Export reports and data

### API Access

Access the full API through the BFF service:
- **Available endpoints**: `GET http://localhost:8080/` (shows all endpoints)
- **Health checks**: `GET http://localhost:8080/health`
- **Service config**: `GET http://localhost:8080/config`
- **Demo management**: `GET http://localhost:8080/api/demos`
- **User management**: `GET http://localhost:8080/api/users`
- **Run analysis**: `POST http://localhost:8080/api/analysis`

### System Monitoring

Monitor system health and service status:
- **BFF Gateway**: http://localhost:8080/health
- **Individual services**: 
  - User Service: http://localhost:8081/health
  - Analysis Service: http://localhost:8082/health  
  - Ingestion Service: http://localhost:8083/health
- **Container status**: `podman-compose ps`
- **Service configuration**: http://localhost:8080/config

## 5\. Contributing

## 6\. License

This project is licensed under the MIT License. See the `LICENSE` file for details.