# Development Guide

Step-by-step guide for setting up, running, and extending the DevOps Incident Support Model.

---

## Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.11 |
| pip | 23+ |
| Docker Desktop | 4.x |
| Docker Compose | 2.x |
| Node.js (Milestone 2) | 20 LTS |

---

## Local Setup (Backend)

### 1 — Clone the repository

```bash
git clone https://github.com/your-org/devops-incident-support-model.git
cd devops-incident-support-model
```

### 2 — Create a virtual environment

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

### 5 — Run the development server

```bash
# From the backend/ directory
uvicorn app.main:app --reload
```

The API is now available at:

| URL | Description |
|---|---|
| `http://localhost:8000/` | Root endpoint |
| `http://localhost:8000/api/v1/health` | Health check |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/redoc` | ReDoc UI |
| `http://localhost:8000/openapi.json` | OpenAPI schema |

---

## Running Tests

```bash
# From the backend/ directory (with venv active)
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing
```

---

## Running with Docker

### Build and start all services

```bash
# From the project root
cp .env.example .env
docker-compose up --build
```

### Stop services

```bash
docker-compose down
```

### Rebuild after code changes

```bash
docker-compose up --build backend
```

---

## Environment Modes

The `APP_ENV` variable selects the settings class:

| Value | Class | Debug | Log Level |
|---|---|---|---|
| `development` | `DevelopmentSettings` | ✅ | DEBUG |
| `testing` | `TestingSettings` | ✅ | WARNING |
| `production` | `ProductionSettings` | ❌ | WARNING |

Override in `.env`:

```
APP_ENV=production
```

---

## Adding a New API Endpoint

1. Create a new file: `backend/app/api/v1/endpoints/your_feature.py`
2. Define an `APIRouter` and your route handlers.
3. Register the router in `backend/app/api/v1/router.py`:

```python
from app.api.v1.endpoints.your_feature import router as your_feature_router
api_v1_router.include_router(your_feature_router, prefix="/your-feature")
```

---

## Adding a New Service

1. Create `backend/app/services/your_service.py`
2. Implement a class with injected dependencies.
3. Register a `Depends()` provider in `backend/app/dependencies/__init__.py`.

---

## Logging

Use `get_logger` anywhere in the application:

```python
from app.core.logging import get_logger

logger = get_logger("api.v1.your_feature")
logger.info("Processing request for %s", some_value)
```

Logs appear in:
- **Console** — formatted with timestamp, level, and logger name.
- **`logs/app.log`** — rotating file, max 10 MB, 5 backups.

---

## Code Style

- **PEP 8** compliance enforced.
- **Type hints** on all public functions and methods.
- **Docstrings** on all public modules, classes, and functions.
- **`from __future__ import annotations`** in every module for forward references.

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready code only |
| `develop` | Integration branch |
| `feature/xxx` | Individual feature work |
| `milestone/N` | Milestone-level integration |

---

## Milestone Roadmap

| Milestone | Focus | Status |
|---|---|---|
| 1 | Foundation (this milestone) | ✅ Complete |
| 2 | Frontend + PostgreSQL + Auth | 🔲 Planned |
| 3 | RAG pipeline + ChromaDB | 🔲 Planned |
| 4 | AI model (Qwen2.5-Coder-3B) | 🔲 Planned |
| 5 | Fine-tuning + deployment | 🔲 Planned |
