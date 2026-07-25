# Architecture

## Overview

DevOps Incident Support Model is an AI-powered assistant that helps on-call engineers diagnose and resolve DevOps incidents faster. The system accepts natural-language incident descriptions and returns step-by-step troubleshooting guidance powered by a fine-tuned Qwen2.5-Coder-3B-Instruct model augmented with Retrieval Augmented Generation (RAG).

---

## Architectural Layers

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)               │
│           Incident Form │ Chat Interface │ Dashboard         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────┐
│                     FastAPI Backend                          │
│  API Layer → Service Layer → Repository Layer → Domain       │
└──────┬───────────────────────────────────────────┬──────────┘
       │                                           │
┌──────▼──────┐                         ┌──────────▼──────────┐
│  PostgreSQL │                         │     ChromaDB         │
│  (Incidents │                         │  (Vector Store /     │
│   History)  │                         │   RAG Documents)     │
└─────────────┘                         └──────────────────────┘
                                                   │
                                        ┌──────────▼──────────┐
                                        │  Qwen2.5-Coder-3B   │
                                        │   (Inference Engine) │
                                        └─────────────────────┘
```

---

## Design Principles

| Principle | Implementation |
|---|---|
| **Clean Architecture** | Strict layer separation: API → Service → Repository → Domain |
| **Dependency Injection** | FastAPI `Depends()` for all cross-cutting concerns |
| **Single Responsibility** | Each module / class has one clear purpose |
| **Open/Closed** | Extend by adding new routers / services, not modifying core |
| **Interface Segregation** | Thin, focused schemas per endpoint |
| **DRY** | Shared response envelope, centralised logging, unified exception handling |

---

## Backend Layer Responsibilities

### API Layer (`app/api/`)
- Route definitions only.
- Calls service layer; never accesses DB directly.
- Input/output validation via Pydantic schemas.
- API versioning via URL prefix (`/api/v1`).

### Service Layer (`app/services/`)
- Business logic and orchestration.
- Coordinates repositories, AI inference, and external calls.
- Returns domain objects or raises domain exceptions.

### Repository Layer (`app/repositories/`)
- All database I/O encapsulated here.
- Returns domain models; no raw SQL leaks into services.
- Swappable storage back-ends (PostgreSQL → SQLite for tests).

### Domain / Models (`app/models/`)
- Pure Python / SQLAlchemy ORM model definitions.
- No business logic; data structure only.

### Schemas (`app/schemas/`)
- Pydantic models for request validation and response serialisation.
- Decoupled from ORM models.

### Configuration (`app/config/`)
- `pydantic-settings` `BaseSettings` subclass per environment.
- Single source of truth for all configuration values.
- Never hard-code values in application code.

### Core (`app/core/`)
- Cross-cutting infrastructure: logging setup, exception handlers.
- No business logic.

### Middleware (`app/middleware/`)
- Starlette ASGI middleware for request-level concerns (logging, tracing, rate limiting).

---

## Request / Response Flow

```
Client Request
    │
    ▼
CORS Middleware
    │
    ▼
RequestLoggingMiddleware  ← logs method, path, status, latency
    │
    ▼
FastAPI Router            ← validates path / query parameters
    │
    ▼
Pydantic Schema           ← validates request body
    │
    ▼
Endpoint Handler
    │
    ▼
Service Layer             ← business logic
    │
    ▼
Repository Layer          ← DB / vector store access
    │
    ▼
Response Schema           ← StandardResponse[T] envelope
    │
    ▼
Client Response
```

---

## Standard Response Envelope

Every endpoint returns:

```json
{
  "success": true,
  "message": "Human-readable description",
  "data": { }
}
```

Errors follow the same shape with `success: false` and `data: null` (or a `{"errors": [...]}` detail object for validation failures).

---

## Technology Decisions

| Technology | Rationale |
|---|---|
| **FastAPI** | Async-native, auto-generates OpenAPI docs, Pydantic integration |
| **Pydantic v2** | Fast Rust-backed validation, `pydantic-settings` for env config |
| **Uvicorn** | Production-grade ASGI server |
| **PostgreSQL** | ACID-compliant, proven at scale (Milestone 2) |
| **ChromaDB** | Lightweight vector store, easy local dev (Milestone 3) |
| **Qwen2.5-Coder-3B** | Code-domain LLM, fits consumer GPU (Milestone 4) |
| **React + Vite** | Fast HMR, TypeScript-first (Milestone 2) |
| **Docker** | Reproducible environments, single `docker-compose up` |

---

## Security Considerations

- Non-root Docker user for all containers.
- Environment variables for all secrets (never hard-coded).
- CORS restricted to known origins in production.
- Centralised input validation at the API boundary.
- Standardised error responses never leak stack traces.
- OWASP Top 10 mitigations applied throughout.
