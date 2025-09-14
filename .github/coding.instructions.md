# AI Coding Guidelines for StratagemForge

## 1. Core Principles & Directives

Welcome, AI assistant. Your purpose is to help build the **StratagemForge** analytics platform. Before generating any code, you must understand and adhere to the following core principles. These are non-negotiable.

* **Architecture is Truth:** The `ARCHITECTURE.md` document is the single source of truth for the system's structure. All code must respect the defined container boundaries, responsibilities, and communication patterns. **Do not** create code that allows the Web App to talk directly to a database, for example.
* **Tech Stack is Law:** The technologies listed in `TECH_STACK.md` have been chosen for specific reasons. You must use the prescribed stack for each service. Do not introduce new frameworks, languages, or databases without explicit instruction.
* **Follow the Phased Plan:** Development must follow the implementation plan in the `README.md`. Our current focus is **Phase 1: The Foundation**, so your tasks should primarily relate to demo parsing and management.
* **Security is Paramount:** Follow the security principles in `ARCHITECTURE.md`. The BFF is the gatekeeper. Internal services should not be directly exposed.
* **BFF is an Orchestrator, Not a Doer:** The BFF's primary role is to aggregate data and orchestrate calls to downstream services. It should contain minimal business logic itself. The heavy lifting is done by the User, Ingestion, and Analysis services.

## 2. Prompting Template & Workflow

To ensure you have the correct context, I (the user) will try to follow this template. Your role is to plan, then execute.

### My Prompt Structure:

```
## Goal
A clear, concise description of the task.

## Current Phase
The current project phase from `README.md`.

## Relevant Service(s)
The container(s) from `ARCHITECTURE.md` this task applies to.

## Key Constraints & Requirements
Specific instructions, e.g., "Create a FastAPI endpoint that accepts X and returns Y," or "The function must be idempotent."

## Attached Files for Context
A list of files you must read before starting, typically including this one, `ARCHITECTURE.md`, and `TECH_STACK.md`.
```

### Your Expected Workflow:

1.  **Acknowledge & Plan:** Before writing code, briefly state your plan. For example: "Understood. I will create three new files in the `user-service/handlers` directory. The main function will handle request validation, call the database model, and then return a JWT." This gives me a chance to correct your course.
2.  **Generate Code:** Write clean, well-commented, and modular code that adheres to all principles.
3.  **Explain:** Provide a brief summary of the generated code and any important decisions you made.

## 3. Service-Specific Instructions

Adhere to these rules for each specific container:

* **Web Application (SPA):**
    * Framework: **React with Next.js**
    * UI: Use **shadcn/ui** and **Tailwind CSS** components.
    * State: Use **Zustand** or **Jotai** for state management.
    * Data: All data fetching must go through the **BFF**. No direct calls to other services.

* **BFF (Backend for Frontend):**
    * Technology: **Node.js with Fastify** and **TypeScript**.
    * Responsibility: Act as the sole entry point for the Web App. Aggregate data from other services for frontend-optimized responses. Handle user session validation.

* **User Service:**
    * Technology: **Go** with the **Gin** framework.
    * Responsibility: Manage user CRUD, authentication (username/password), and JWT token generation/validation.

* **Ingestion Service:**
    * Technology: **Go**.
    * Responsibility: Process `.dem` files. This should be an internal service, likely triggered by a call from the BFF. It should not expose a public HTTP API. Its main function will receive a file to process.

* **Demo Analysis Service:**
    * Technology: **Python** with **FastAPI** and **Polars**.
    * Responsibility: Expose specific, high-level analytical endpoints (e.g., `/api/v1/demos/{demo_id}/player-stats`). It queries the analytical database.

* **Databases:**
    * **Relational (PostgreSQL):** For user data, demo metadata, tags, and notes.
    * **Analytical (DuckDB/Parquet):** For raw, high-volume game tick and event data parsed from demos.

By adhering to these guidelines, you will function as a highly effective and context-aware coding assistant for this project.