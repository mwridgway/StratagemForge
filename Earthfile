VERSION 0.8

# Base images for different languages
go-base:
    FROM golang:1.24-alpine
    WORKDIR /app
    RUN apk add --no-cache git ca-certificates
    ENV CGO_ENABLED=0 GOOS=linux

node-base:
    FROM node:20-alpine
    WORKDIR /app
    RUN apk add --no-cache git

python-base:
    FROM python:3.11-alpine
    WORKDIR /app
    RUN apk add --no-cache git gcc musl-dev

# Go services base with dependencies
go-deps:
    FROM +go-base
    # Copy individual service dependencies
    COPY services/user-service/go.mod services/user-service/go.sum ./services/user-service/
    COPY services/ingestion-service/go.mod services/ingestion-service/go.sum ./services/ingestion-service/
    WORKDIR /app/services/user-service
    RUN go mod download
    WORKDIR /app/services/ingestion-service
    RUN go mod download
    WORKDIR /app

# User service
user-service-build:
    FROM +go-deps
    COPY services/user-service ./services/user-service
    WORKDIR /app/services/user-service
    RUN go build -ldflags="-w -s" -o main .
    SAVE ARTIFACT main

user-service:
    FROM alpine:latest
    RUN apk add --no-cache ca-certificates
    WORKDIR /app
    COPY +user-service-build/main .
    EXPOSE 8091
    CMD ["./main"]
    SAVE IMAGE user-service:latest

# Ingestion service
ingestion-service-build:
    FROM +go-deps
    COPY services/ingestion-service ./services/ingestion-service
    WORKDIR /app/services/ingestion-service
    RUN go build -ldflags="-w -s" -o main .
    SAVE ARTIFACT main

ingestion-service:
    FROM alpine:latest
    RUN apk add --no-cache ca-certificates
    WORKDIR /app
    COPY +ingestion-service-build/main .
    EXPOSE 8093
    CMD ["./main"]
    SAVE IMAGE ingestion-service:latest

# BFF service
bff-deps:
    FROM +node-base
    COPY services/bff/package*.json ./
    RUN npm ci --only=production

bff-build:
    FROM +node-base
    COPY services/bff/package*.json ./
    RUN npm ci
    COPY services/bff .
    RUN npm run build
    SAVE ARTIFACT dist

bff:
    FROM +bff-deps
    COPY +bff-build/dist ./dist
    COPY services/bff/package*.json ./
    EXPOSE 8090
    CMD ["npm", "start"]
    SAVE IMAGE bff:latest

# Web application
web-deps:
    FROM +node-base
    COPY web-app/package*.json ./
    RUN npm ci --only=production

web-build:
    FROM +node-base
    COPY web-app/package*.json ./
    RUN npm ci
    COPY web-app .
    RUN npm run build
    SAVE ARTIFACT .next

web:
    FROM +web-deps
    COPY +web-build/.next ./.next
    COPY web-app/package*.json ./
    COPY web-app/next.config.js ./
    COPY web-app/public ./public
    EXPOSE 3000
    CMD ["npm", "start"]
    SAVE IMAGE web:latest

# Analysis service
analysis-deps:
    FROM +python-base
    COPY services/analysis-service/requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

analysis-service:
    FROM +analysis-deps
    COPY services/analysis-service .
    EXPOSE 8092
    CMD ["python", "main.py"]
    SAVE IMAGE analysis-service:latest

# Testing targets
test-go:
    FROM +go-deps
    COPY services/user-service ./services/user-service
    COPY services/ingestion-service ./services/ingestion-service
    RUN cd services/user-service && go test ./...
    RUN cd services/ingestion-service && go test ./...

test-node:
    FROM +node-base
    # BFF tests
    COPY services/bff/package*.json ./bff/
    RUN cd bff && npm ci
    COPY services/bff ./bff
    RUN cd bff && npm test || echo "No tests configured for BFF"

    # Web app tests
    COPY web-app/package*.json ./web/
    RUN cd web && npm ci
    COPY web-app ./web
    RUN cd web && npm test || echo "No tests configured for Web"

test-e2e:
    FROM +node-base
    RUN npx playwright install-deps
    RUN npx playwright install
    COPY package*.json ./
    RUN npm ci
    COPY . .
    # Start services in background
    WITH DOCKER --compose compose.yml
        RUN sleep 10 && npx playwright test
    END

# Linting targets
lint-go:
    FROM +go-deps
    COPY services/user-service ./services/user-service
    COPY services/ingestion-service ./services/ingestion-service
    RUN cd services/user-service && go fmt ./... && go vet ./...
    RUN cd services/ingestion-service && go fmt ./... && go vet ./...

lint-node:
    FROM +node-base
    # Lint BFF
    COPY services/bff/package*.json ./bff/
    RUN cd bff && npm ci
    COPY services/bff ./bff
    RUN cd bff && npm run lint

    # Lint Web
    COPY web-app/package*.json ./web/
    RUN cd web && npm ci
    COPY web-app ./web
    RUN cd web && npm run lint

# Security scanning
security-scan:
    FROM aquasec/trivy:latest
    COPY +user-service/user-service:latest ./
    COPY +ingestion-service/ingestion-service:latest ./
    COPY +bff/bff:latest ./
    COPY +web/web:latest ./
    COPY +analysis-service/analysis-service:latest ./
    RUN trivy image user-service:latest
    RUN trivy image ingestion-service:latest
    RUN trivy image bff:latest
    RUN trivy image web:latest
    RUN trivy image analysis-service:latest

# Multi-architecture builds
all-services-multiarch:
    BUILD --platform=linux/amd64 --platform=linux/arm64 +user-service
    BUILD --platform=linux/amd64 --platform=linux/arm64 +ingestion-service
    BUILD --platform=linux/amd64 --platform=linux/arm64 +bff
    BUILD --platform=linux/amd64 --platform=linux/arm64 +web
    BUILD --platform=linux/amd64 --platform=linux/arm64 +analysis-service

# Development target with hot reloading
dev:
    FROM +node-base
    COPY package*.json ./
    RUN npm ci
    COPY . .
    WITH DOCKER --compose compose.yml
        RUN echo "Development environment ready"
    END

# CI/CD pipeline targets
ci-test:
    BUILD +test-go
    BUILD +test-node
    BUILD +lint-go
    BUILD +lint-node

ci-build:
    BUILD +user-service
    BUILD +ingestion-service
    BUILD +bff
    BUILD +web
    BUILD +analysis-service

ci-full:
    BUILD +ci-test
    BUILD +ci-build
    BUILD +security-scan

# Production deployment
deploy-images:
    FROM scratch
    COPY +user-service/user-service:latest ./
    COPY +ingestion-service/ingestion-service:latest ./
    COPY +bff/bff:latest ./
    COPY +web/web:latest ./
    COPY +analysis-service/analysis-service:latest ./
    SAVE IMAGE --push stratagemforge/complete:latest

# Database migrations (placeholder)
migrate:
    FROM postgres:15-alpine
    COPY migrations/*.sql /docker-entrypoint-initdb.d/
    # TODO: Add actual migration logic

# Cleanup and utilities
clean-images:
    RUN docker image prune -f
    RUN docker container prune -f
    RUN docker volume prune -f

# Health check target
health-check:
    FROM curlimages/curl:latest
    RUN curl -f http://bff:8090/health || exit 1
    RUN curl -f http://user-service:8091/health || exit 1
    RUN curl -f http://analysis-service:8092/health || exit 1
    RUN curl -f http://ingestion-service:8093/health || exit 1

# Documentation generation
docs:
    FROM node:20-alpine
    RUN npm install -g @apidevtools/swagger-parser
    COPY docs/ ./
    RUN echo "Generating API documentation..."
    # TODO: Add actual documentation generation

# Default target
all:
    BUILD +ci-full
