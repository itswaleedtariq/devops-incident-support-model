# DevOps Incident Support Model

A safety-focused AI-assisted platform for recording DevOps incidents and later
producing evidence-grounded troubleshooting guidance with Qwen2.5-Coder-3B,
QLoRA and RAG.

## Current implementation status

- ✅ Milestone 1 — Project foundation and architecture
- ✅ Milestone 2 — PostgreSQL, SQLAlchemy, Alembic, JWT authentication and RBAC
- ✅ Milestone 2.9 — Comprehensive backend tests and coverage configuration
- ✅ Milestone 2.10 — Final backend/API/testing documentation
- ✅ Milestone 3 — Incident management API
- ✅ Milestone 4 — Dataset design, JSONL splits and validator
- ⏳ Milestone 5 — Collection of 1,000+ reviewed incidents

The model is not connected yet. Milestones 1–4 establish the application,
incident history and strict training-data contract required before collection
and fine-tuning.

## Implemented backend features

- Async PostgreSQL with SQLAlchemy 2 and Alembic
- Registration, login, refresh-token rotation, logout and password changes
- Role-based authorization for Admin, DevOps Engineer, AI Engineer and Viewer
- User-management APIs
- Incident create/read/update/status/history/search/filter/pagination/soft-delete
- Ownership isolation: non-admin users see only their own incidents
- Standard API envelope and global error handling
- Security headers, trusted hosts, CORS, rate limiting and request logging
- Dataset JSON Schema, Pydantic validation and cross-split duplicate detection
- Unit, API and optional PostgreSQL integration tests

## Incident API

| Method | Endpoint |
|---|---|
| POST | `/api/v1/incidents` |
| GET | `/api/v1/incidents` |
| GET | `/api/v1/incidents/history` |
| GET | `/api/v1/incidents/{incident_id}` |
| PATCH | `/api/v1/incidents/{incident_id}` |
| PATCH | `/api/v1/incidents/{incident_id}/status` |
| DELETE | `/api/v1/incidents/{incident_id}` |

Interactive API documentation is available at `/docs` when the backend runs.

## Local setup

Use Python 3.11.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Start PostgreSQL through Docker from the project root:

```powershell
docker compose up -d postgres
```

Apply migrations and seed roles from `backend/`:

```powershell
python scripts/db.py migrate
python scripts/db.py seed
uvicorn app.main:app --reload
```

## Tests and coverage

```powershell
cd backend
pytest -v
pytest -v --cov=app --cov-report=term-missing --cov-report=html
```

PostgreSQL integration tests:

```powershell
pytest -v --integration
```

## Validate Milestone 4 data

From the repository root:

```powershell
python backend/scripts/validate_dataset.py --all
```

## Main project structure

```text
backend/app/
├── api/v1/endpoints/       # Auth, users, health and incidents
├── dataset/                # Fine-tuning record schema and validator
├── models/                 # SQLAlchemy models
├── repositories/           # Data-access layer
├── schemas/                # API request/response schemas
├── services/               # Business logic
└── core/                   # Security, JWT, logging, permissions

data/
├── schema/
├── train.jsonl
├── validation.jsonl
├── test.jsonl
├── categories.json
└── risk_levels.json
```

## Documentation

- [Architecture](docs/Architecture.md)
- [Development Guide](docs/Development_Guide.md)
- [Authentication](docs/Authentication.md)
- [Authorization](docs/Authorization.md)
- [Incident API](docs/Incident_API.md)
- [Dataset Design](docs/Dataset_Design.md)
- [Testing and Coverage](docs/Testing.md)
- [Database Models](docs/Database_Models.md)

## Next milestone

Milestone 5 should collect 1,000+ licensed or project-authored incidents, redact
secrets, preserve source metadata and send every example through manual review
before it enters the training split.
