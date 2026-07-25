# Project Structure

Complete annotated directory tree for the DevOps Incident Support Model.

```
devops-incident-support-model/
│
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # App factory + Uvicorn entry point
│   │   │
│   │   ├── api/                    # HTTP transport layer
│   │   │   ├── __init__.py
│   │   │   └── v1/                 # API version 1
│   │   │       ├── __init__.py
│   │   │       ├── router.py       # Aggregates all v1 routers
│   │   │       └── endpoints/
│   │   │           ├── __init__.py
│   │   │           └── health.py   # GET /api/v1/health
│   │   │
│   │   ├── config/                 # Settings management
│   │   │   ├── __init__.py
│   │   │   └── settings.py         # Pydantic-Settings per environment
│   │   │
│   │   ├── core/                   # Shared infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── logging.py          # Logging setup + get_logger()
│   │   │   └── exceptions.py       # Global exception handlers
│   │   │
│   │   ├── middleware/             # ASGI middleware
│   │   │   ├── __init__.py
│   │   │   └── logging_middleware.py  # Request/response logger
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models (Milestone 2)
│   │   │   └── __init__.py
│   │   │
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   └── response.py         # StandardResponse[T] envelope
│   │   │
│   │   ├── services/               # Business logic (Milestone 2)
│   │   │   └── __init__.py
│   │   │
│   │   ├── repositories/           # Data access layer (Milestone 2)
│   │   │   └── __init__.py
│   │   │
│   │   ├── utils/                  # Shared helper functions
│   │   │   └── __init__.py
│   │   │
│   │   ├── dependencies/           # FastAPI Depends() callables
│   │   │   └── __init__.py
│   │   │
│   │   └── exceptions/             # Custom domain exceptions
│   │       └── __init__.py
│   │
│   ├── tests/                      # Pytest test suite
│   │   ├── __init__.py
│   │   ├── conftest.py             # Shared fixtures (TestClient)
│   │   ├── test_root.py            # Tests for GET /
│   │   └── test_health.py          # Tests for GET /api/v1/health
│   │
│   ├── requirements.txt            # Python dependencies
│   ├── pytest.ini                  # Pytest configuration
│   └── .env.example                # Backend env variable template
│
├── frontend/                       # React + Vite + TypeScript (Milestone 2)
│   └── README.md
│
├── docker/                         # Dockerfiles
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
│
├── docs/                           # Project documentation
│   ├── Architecture.md
│   ├── Project_Structure.md        # This file
│   └── Development_Guide.md
│
├── deployment/                     # Kubernetes / Helm / CI/CD (Milestone 5)
│   └── README.md
│
├── scripts/                        # Utility scripts
│   └── README.md
│
├── data/                           # ML / RAG data
│   ├── raw/                        # Unprocessed incident logs
│   ├── cleaned/                    # Cleaned and normalised data
│   ├── training/                   # Fine-tuning dataset
│   ├── validation/                 # Held-out validation set
│   └── testing/                    # Evaluation set
│
├── rag/                            # RAG pipeline
│   └── documents/                  # Source documents for vector ingestion
│
├── training/                       # Model training scripts (Milestone 4)
├── models/                         # Saved / downloaded model weights
│
├── docker-compose.yml              # Multi-service orchestration
├── .env.example                    # Root env variable template
├── .gitignore
├── LICENSE
└── README.md
```

---

## Key File Descriptions

| File | Role |
|---|---|
| `backend/app/main.py` | Creates the FastAPI app via `create_app()`. Registers middleware, exception handlers, and routers. |
| `backend/app/config/settings.py` | `pydantic-settings` hierarchy: Base → Development / Testing / Production. |
| `backend/app/core/logging.py` | Configures console + rotating-file handlers; `get_logger()` for child loggers. |
| `backend/app/core/exceptions.py` | HTTP, validation, and catch-all exception handlers returning `StandardResponse`. |
| `backend/app/schemas/response.py` | `StandardResponse[T]` generic Pydantic model used by every endpoint. |
| `backend/app/middleware/logging_middleware.py` | Starlette middleware that logs every request with timing and injects `X-Request-ID`. |
| `backend/app/api/v1/endpoints/health.py` | `GET /api/v1/health` — liveness probe. |
| `backend/tests/conftest.py` | Pytest fixtures; provides session-scoped `TestClient`. |
