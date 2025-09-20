# Technology Stack: StratagemForge

This document outlines the recommended technology choices for the StratagemForge system architecture, based on the high-level design in `ARCHITECTURE.md`. The selections prioritize performance, developer experience, scalability, and modern best practices.

## 1. Web Application (SPA)

The frontend is designed to be technology-agnostic, but this stack provides a powerful and modern starting point.

* **Framework: React with Next.js**
    * **Why?** React offers a vast ecosystem and talent pool. Next.js provides a production-ready framework with a best-in-class developer experience, optimizing for both performance and scalability.

* **UI Components: shadcn/ui + Tailwind CSS**
    * **Why?** This combination provides unstyled, accessible components that can be copied directly into the project. This allows for full customization without fighting library opinions, keeping the application lean and looking unique.

* **State Management: Zustand or Jotai**
    * **Why?** These are lightweight, modern alternatives to Redux. They offer a simpler API for managing state, providing a great balance of power and ease of use for most application needs.

## 2. BFF (Backend for Frontend)

As the central orchestration layer, the BFF must be fast and efficient at handling I/O operations.

* **Technology: TypeScript with Node.js + Fastify**
    * **Why?** Fastify is a high-performance web framework that is significantly faster than Express.js. Its asynchronous nature is perfect for orchestrating calls to internal services. TypeScript adds static typing, which is crucial for API reliability and long-term maintainability.

## 3. User Service

This core service must be secure, fast, and reliable.

* **Technology: Go with the Gin Framework**
    * **Why?** Go is compiled, statically typed, incredibly fast, and has a very low memory footprint. This makes it ideal for a critical, well-defined service like user and identity management.

* **Error Handling Standards:**
    * **Custom Error Types**: Define domain-specific error types that implement the `error` interface
    * **Error Wrapping**: Use `fmt.Errorf("context: %w", err)` to add context while preserving the original error
    * **Structured Error Responses**: Return consistent JSON error responses with error codes, messages, and request IDs
    * **Error Logging**: Log errors with structured fields (request ID, user ID, operation) for traceability
    * **Validation Errors**: Use validation libraries like `go-playground/validator` with custom error messages

* **Authentication Provider: External Service (e.g., Auth0, Clerk)**
    * **Why?** Building authentication is complex and fraught with security risks. Offloading this to a specialized service aligns with the "OAuth-Ready Design," simplifies development, and ensures robust security (MFA, social logins, etc.) is handled by experts.

## 4. Ingestion Service

This service is performance-critical, responsible for parsing potentially large binary demo files.

* **Technology: Go**
    * **Why?** Go is purpose-built for this kind of task. Its excellent performance, first-class concurrency model (goroutines), and strong standard library for handling binary data make it the perfect tool for creating a high-throughput ingestion pipeline.

* **Error Handling Standards:**
    * **Pipeline Error Handling**: Use channels to propagate errors in concurrent processing pipelines
    * **File Processing Errors**: Distinguish between recoverable (retry) and non-recoverable (skip) file processing errors
    * **Context Cancellation**: Use `context.Context` for graceful shutdown and timeout handling
    * **Resource Cleanup**: Always use `defer` statements for closing files, connections, and other resources

## 5. Demo Analysis Service

This is the data science core of the application, requiring powerful data manipulation tools.

* **Technology: Python with FastAPI + Polars**
    * **Why?** Python is the industry standard for data analysis. FastAPI provides a high-performance framework to serve analysis results. **Polars** is a modern, lightning-fast replacement for the traditional `pandas` library, offering superior performance on large datasets.

## 6. Databases

The architecture correctly separates transactional and analytical data workloads.

* **Relational DB: PostgreSQL**
    * **Why?** PostgreSQL is the premier open-source relational database. It is powerful, reliable, and highly extensible, making it a safe and scalable choice for storing user data, demo metadata, and other relational information.

* **Database Migration Strategy:**
    * **Tool**: Use `golang-migrate/migrate` for schema versioning and migrations
    * **Migration Files**: Store migrations in `migrations/` directory with sequential numbering (001_initial_schema.up.sql, 001_initial_schema.down.sql)
    * **CI/CD Integration**: Run migrations automatically in deployment pipeline before service startup
    * **Rollback Strategy**: Always write down migrations for safe rollbacks
    * **Data Migrations**: Separate data migrations from schema migrations when dealing with large datasets
    * **Testing**: Test migrations against production-like data volumes in staging environment

* **Analytical Stack: DuckDB + Parquet Files**
    * **Why?** This is a modern, efficient, and serverless approach to analytics. The Ingestion Service writes parsed game data into highly compressed, columnar **Parquet** files. The Analysis Service can then use **DuckDB**, an embedded analytical database, to run incredibly fast SQL queries directly on those files without needing a separate database server.

## Summary

| Container               | Recommended Technology                                       |
| ----------------------- | ------------------------------------------------------------ |
| **Web Application** | React (Next.js), Tailwind CSS, shadcn/ui                     |
| **BFF** | Node.js (Fastify), TypeScript, Socket.IO                     |
| **User Service** | Go (Gin) + an external provider like Auth0/Clerk             |
| **Ingestion Service** | Go                                                           |
| **Demo Analysis Service** | Python (FastAPI), Polars, DuckDB                             |
| **Relational DB** | PostgreSQL                                                   |
| **Analytical DB** | Parquet Files on Disk/S3                                     |

## Development Standards

### Unit Testing Guidelines (Go Services)

* **Testing Framework**: Use Go's built-in `testing` package with `testify/assert` for assertions
* **Test Structure**: Follow table-driven tests pattern for multiple test cases
* **Mocking**: Use `testify/mock` or `gomock` for dependency mocking
* **Coverage**: Aim for 80%+ test coverage on business logic, 100% on critical paths
* **Test Organization**: Mirror source code structure in `*_test.go` files
* **Integration Tests**: Use `testcontainers` for database integration tests
* **Test Data**: Use test fixtures and builders for consistent test data creation

### SOLID Principles in Go

* **Single Responsibility**: Each package/struct should have one reason to change
* **Open/Closed**: Use interfaces for extensibility without modification
* **Liskov Substitution**: Interfaces should be substitutable by their implementations
* **Interface Segregation**: Keep interfaces small and focused (prefer many small interfaces)
* **Dependency Inversion**: Depend on abstractions (interfaces) not concretions (structs)
* **Go-Specific**: Favor composition over inheritance, use embedding for behavior reuse

### Future Standards (TODO)

* **Logging Standards**: TODO - Structured logging with levels, fields, and correlation IDs
* **Monitoring & Observability**: TODO - Metrics, tracing, and health checks
* **Security Patterns**: TODO - Input validation, rate limiting, and audit logging  
* **Backup & Recovery**: TODO - Database backup strategies and disaster recovery plans
* **Performance Guidelines**: TODO - Profiling, optimization, and performance budgets