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

> **Note**: This microservices architecture is adopted from the start based on prior experience with modular monoliths. The team has already validated the domain boundaries and service decomposition patterns in previous projects.


## 2\. Phased Implementation Plan

This project is designed to be built in distinct, sequential phases. Each phase delivers a functional component of the platform, allowing for incremental development and immediate value at every stage.

### Phase 1: The Foundation - Automated Demo Parsing

### Phase 2: The Command Center - Interactive Dashboard

### Phase 3: The AI Analyst - "Query-Your-Demos" with RAG

### Phase 4: Advanced Insight - GNN for Tactic Classification

### Phase 5: Automation & Expansion - Fine-Tuning for Scouting

## 3\. Setup and Installation

### Setup Workflow

StratagemForge offers three approaches to get started:

1. **🚀 Quick Start** - Get running immediately with containers (5 minutes)
2. **🛠️ Development Setup** - Full development environment with build tools (15 minutes)  
3. **🏗️ Advanced Setup** - Container-native builds with Earthly (30 minutes)

Choose the approach that best fits your needs:
- **Just want to try it?** → Quick Start
- **Planning to develop?** → Development Setup  
- **Need production builds?** → Advanced Setup

### Prerequisites

**Core Requirements:**
- **Node.js 20+** - Required for BFF service and web application
  - Windows: Download from [nodejs.org](https://nodejs.org/) or `winget install nodejs`
  - macOS: `brew install node`
  - Linux: Install via package manager or NodeSource
- **Go 1.24+** - Required for user and ingestion services
  - Download from [golang.org](https://golang.org/dl/)
  - Verify: `go version` should show 1.24 or higher
- **Python 3.11+** - Required for analysis service
  - Windows: Download from [python.org](https://python.org/) or `winget install python`
  - macOS: `brew install python@3.11`
  - Linux: Install via package manager
- **Podman** (or Docker) - Container runtime for microservices
  - Windows: Install Podman Desktop or `winget install RedHat.Podman-Desktop`
  - macOS: `brew install podman`
  - Linux: Install via package manager
- **podman-compose** - Docker Compose compatibility
  - Install: `pip install podman-compose`
- **Git** - Version control
- **8GB+ RAM** - Recommended for running all services

**Build Tool Options (Optional):**
- **Task Runner** - Modern task automation (recommended for development)
  - Install: `go install github.com/go-task/task/v3/cmd/task@latest`
  - Add to PATH: `$(go env GOPATH)/bin` or `%GOPATH%\bin`
- **Earthly** - Container-native build system (for advanced workflows)
  - Windows: Download from [earthly.dev](https://earthly.dev/get-earthly)
  - macOS/Linux: `curl -sSL https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -o /usr/local/bin/earthly && chmod +x /usr/local/bin/earthly`

**Platform Setup:**

*Windows users:*
```powershell
# Start Podman machine
podman machine init
podman machine start

# Verify installation
podman version
go version
node --version
python --version
```

*macOS/Linux users:*
```bash
# Verify installation
podman version
go version  
node --version
python3 --version

# Start Podman service (Linux)
sudo systemctl enable --now podman.socket
```

### 🚀 Quick Start (5 minutes)

*Get StratagemForge running immediately with containers - no build tools required.*

**Step 1: Install Prerequisites**
```bash
# Install only the essentials
# - Podman (container runtime)
# - podman-compose (orchestration)
# - Git (to clone repository)
```

**Step 2: Clone and Start**
```bash
git clone https://github.com/mwridgway/StratagemForge.git
cd StratagemForge

# Start all services with one command
podman-compose up -d
```

**Step 3: Access the Platform**
- **Web Application**: http://localhost:3000
- **API Gateway**: http://localhost:8090 (lists all endpoints)
- **Health Check**: http://localhost:8090/health

**Step 4: Verify**
```bash
# Check all services are running
podman-compose ps

# Test the web app
curl http://localhost:3000
```

**That's it!** 🎉 StratagemForge is now running.

### 🛠️ Development Setup (15 minutes)

*Set up a full development environment with build tools and hot reloading.*

**Step 1: Install All Prerequisites**
- Complete the full prerequisites list above (Node.js, Go, Python, etc.)

**Step 2: Install Development Dependencies**
```bash
git clone https://github.com/mwridgway/StratagemForge.git
cd StratagemForge

# Install dependencies for all services
npm install                    # Root orchestration
cd services/bff && npm install # BFF service
cd ../.. && cd web-app && npm install  # Web application
cd ..

# Install Python dependencies
cd services/analysis-service
pip install -r requirements.txt
cd ../..
```

**Step 3: Install Build Tools (Recommended)**
```bash
# Install Task runner for enhanced development workflow
go install github.com/go-task/task/v3/cmd/task@latest

# Add to PATH (Windows)
$env:Path = $env:Path + ";" + (go env GOPATH) + "\bin"

# Add to PATH (macOS/Linux)
export PATH=$PATH:$(go env GOPATH)/bin
```

**Step 4: Verify Development Environment**
```bash
# Test builds
npm run build    # Test npm build system
task build       # Test Task runner (if installed)

# Start development with hot reloading
task dev         # Recommended
# OR manually start services for development
podman-compose up postgres -d  # Start database only
# Then run services individually in separate terminals
```

### 🏗️ Advanced Setup (30 minutes)

*Set up container-native builds with Earthly for production-grade workflows.*

**Step 1: Complete Development Setup**
- Follow the Development Setup steps above first

**Step 2: Install Earthly**
```bash
# Windows
iwr https://github.com/earthly/earthly/releases/latest/download/earthly-windows-amd64.exe -OutFile earthly.exe
.\earthly.exe bootstrap

# macOS/Linux  
curl -sSL https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -o /usr/local/bin/earthly
chmod +x /usr/local/bin/earthly
earthly bootstrap
```

**Step 3: Test Earthly Builds**
```bash
# List available targets
earthly ls

# Build individual service
earthly +user-service-build

# Build all services as containers
earthly +ci-build

# Run complete CI pipeline
earthly +ci-full
```

**Step 4: Production Deployment**
```bash
# Build multi-architecture images
earthly +all-services-multiarch

# Security scanning
earthly +security-scan

# Deploy to registry
earthly +deploy-images
```
```
   ```bash
   # Check all service status
   podman-compose ps
   
   # Test web application
   curl http://localhost:3000
   
   # Test API gateway and see all available endpoints
   curl http://localhost:8090/
   
   # Test API gateway health
   curl http://localhost:8090/health
   ```

### What Gets Started

The `podman-compose up -d` command starts all 6 microservices:

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **Web App** | Next.js/React | 3000 | User interface |
| **BFF Service** | Node.js/TypeScript | 8090 | API orchestration & Gateway |
| **User Service** | Go/Gin | 8091 | Authentication & User Management |
| **Ingestion Service** | Go/Gin | 8093 | Demo file processing |
| **Analysis Service** | Python/FastAPI | 8092 | Data analytics & ML |
| **PostgreSQL** | Database | 5432 | Data storage |

## Build Options

StratagemForge provides multiple build orchestration options to suit different workflows:

### Option 1: NPM Scripts (Default)
Best for: Simple builds and CI/CD integration

```bash
# Build all services
npm run build

# Build individual services
npm run build:bff
npm run build:web

# Development
npm run dev:bff
npm run dev:web
```

### Option 2: Task Runner (Recommended)
Best for: Local development and complex workflows

**Installation:**
```bash
# Install Task runner
go install github.com/go-task/task/v3/cmd/task@latest
# Or via package manager: brew install go-task/tap/go-task
```

**Usage:**
```bash
# List all available tasks
task

# Build everything
task build

# Run CI pipeline (lint, build, test)
task ci

# Development with hot reloading
task dev:bff
task dev:web

# Run all tests
task test

# Format all code
task format

# Clean build artifacts
task clean

# Start/stop services
task services:start
task services:stop
task services:logs
```

### Option 3: Earthly (Advanced)
Best for: Container-based builds, CI/CD, and multi-platform deployments

**Installation:**
```bash
# Install Earthly
curl -sSL https://github.com/earthly/earthly/releases/latest/download/earthly-windows-amd64.exe -o earthly.exe
```

**Usage:**
```bash
# Build all services as Docker images
earthly +all

# Run complete CI pipeline
earthly +ci-full

# Build for multiple architectures
earthly +all-services-multiarch

# Run tests in isolated containers
earthly +test-go
earthly +test-node

# Security scanning
earthly +security-scan

# Build and push for deployment
earthly +deploy-images
```

### Development Mode

For development with hot reloading:

```bash
# Option 1: Using Task (Recommended)
task dev

# Option 2: Using npm scripts
# Start infrastructure only
podman-compose up postgres -d

# Run services individually in development mode
cd services/user-service && go run main.go
cd services/ingestion-service && go run main.go  
cd services/analysis-service && python main.py
cd services/bff && npm run dev
cd web-app && npm run dev

# Option 3: Using Earthly
earthly +dev
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
- Check if ports 3000, 5432, 8090-8093 are available
- Ensure Podman machine is running: `podman machine start`
- Check Podman status: `podman version`
- View logs: `podman-compose logs [service-name]`

**Database connection issues?**
- Wait 30-60 seconds for PostgreSQL to fully initialize
- Check health status: `curl http://localhost:8090/health`

**Build tool issues?**
- **Task not found**: Ensure `$(go env GOPATH)/bin` is in your PATH
- **Earthly daemon**: Run `earthly bootstrap` to initialize
- **Go version**: Services require Go 1.24+, check with `go version`

**Need to rebuild after changes?**
```bash
# Rebuild all images
podman-compose build

# Rebuild specific service
podman-compose build user-service

# Rebuild and restart
podman-compose up --build -d
```

### Setup Verification

**1. Verify Prerequisites**
```bash
# Check versions
node --version     # Should be 20+
go version        # Should be 1.24+
python --version  # Should be 3.11+
podman version    # Should show client and server

# Check build tools (optional)
task --version    # If installed
earthly --version # If installed
```

**2. Test Build Systems**
```bash
# Test npm build
npm run build

# Test Task runner (if installed)
task build

# Test Earthly (if installed)
earthly +user-service-build
```

**3. Verify Running Services**
```bash
# Check all containers
podman-compose ps

# Test endpoints
curl http://localhost:3000                    # Web app
curl http://localhost:8090                    # BFF API (lists endpoints)
curl http://localhost:8090/health            # Health check
curl http://localhost:8090/api/system-status # System status
```

**4. Common Port Conflicts**
If you encounter port conflicts, these are the default ports used:
- **3000**: Next.js web application
- **5432**: PostgreSQL database  
- **8090**: BFF service (API Gateway)
- **8091**: User service
- **8092**: Analysis service
- **8093**: Ingestion service

To use different ports, modify the `compose.yml` file.

### Quick Setup for Build Tools

**Install Task Runner (Recommended for Development)**
```powershell
# Windows (PowerShell)
go install github.com/go-task/task/v3/cmd/task@latest
$env:Path = $env:Path + ";" + (go env GOPATH) + "\bin"

# Verify installation
task --version
```

```bash
# macOS/Linux
go install github.com/go-task/task/v3/cmd/task@latest
export PATH=$PATH:$(go env GOPATH)/bin

# Or via Homebrew (macOS)
brew install go-task/tap/go-task

# Verify installation
task --version
```

**Install Earthly (Advanced Container Builds)**
```powershell
# Windows (PowerShell)
iwr https://github.com/earthly/earthly/releases/latest/download/earthly-windows-amd64.exe -OutFile earthly.exe
.\earthly.exe bootstrap

# Verify installation  
.\earthly.exe --version
```

```bash
# macOS/Linux
curl -sSL https://github.com/earthly/earthly/releases/latest/download/earthly-linux-amd64 -o /usr/local/bin/earthly
chmod +x /usr/local/bin/earthly
earthly bootstrap

# Verify installation
earthly --version
```
- **8092**: Analysis service
- **8093**: Ingestion service

To use different ports, modify the `compose.yml` file.

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
- **Available endpoints**: `GET http://localhost:8090/` (shows all endpoints)
- **Health checks**: `GET http://localhost:8090/health`
- **Service config**: `GET http://localhost:8090/config`
- **Demo management**: `GET http://localhost:8090/api/demos`
- **User management**: `GET http://localhost:8090/api/users`
- **Run analysis**: `POST http://localhost:8090/api/analysis`

### System Monitoring

Monitor system health and service status:
- **BFF Gateway**: http://localhost:8090/health
- **Individual services**: 
  - User Service: http://localhost:8091/health
  - Analysis Service: http://localhost:8092/health  
  - Ingestion Service: http://localhost:8093/health
- **Container status**: `podman-compose ps`
- **Service configuration**: http://localhost:8090/config

## 5\. Contributing

## 6\. Assistant Guidelines
- **Important**: This project is for **Counter-Strike 2** (CS2), NOT CS:GO (Counter-Strike: Global Offensive)
- Architecture requirements are detailed in `Requirements/TEST_AUTOMATION.md`
- Features are in `Requirements/HIGH_LEVEL_FEATURES.md`
- Tech stack and design patterns are in `Requirements/TECH_STACK.md`
- Automation and testing guidelines are in `Requirements/TEST_AUTOMATION.md`

## 7\. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
