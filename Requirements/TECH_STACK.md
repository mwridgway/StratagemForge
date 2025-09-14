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

* **Authentication Provider: External Service (e.g., Auth0, Clerk)**
    * **Why?** Building authentication is complex and fraught with security risks. Offloading this to a specialized service aligns with the "OAuth-Ready Design," simplifies development, and ensures robust security (MFA, social logins, etc.) is handled by experts.

## 4. Ingestion Service

This service is performance-critical, responsible for parsing potentially large binary demo files.

* **Technology: Go**
    * **Why?** Go is purpose-built for this kind of task. Its excellent performance, first-class concurrency model (goroutines), and strong standard library for handling binary data make it the perfect tool for creating a high-throughput ingestion pipeline.

## 5. Demo Analysis Service

This is the data science core of the application, requiring powerful data manipulation tools.

* **Technology: Python with FastAPI + Polars**
    * **Why?** Python is the industry standard for data analysis. FastAPI provides a high-performance framework to serve analysis results. **Polars** is a modern, lightning-fast replacement for the traditional `pandas` library, offering superior performance on large datasets.

## 6. Databases

The architecture correctly separates transactional and analytical data workloads.

* **Relational DB: PostgreSQL**
    * **Why?** PostgreSQL is the premier open-source relational database. It is powerful, reliable, and highly extensible, making it a safe and scalable choice for storing user data, demo metadata, and other relational information.

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