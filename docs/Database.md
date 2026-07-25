# Database Architecture

## Overview

The database layer provides an async PostgreSQL connection powered by **SQLAlchemy 2.x** with the **asyncpg** driver. Migrations are managed by **Alembic** using the async migration pattern.

---

## Technology Choices

| Component | Technology | Rationale |
|---|---|---|
| RDBMS | PostgreSQL 16 | ACID, JSONB, proven at scale |
| ORM | SQLAlchemy 2.x (`[asyncio]`) | Async-native, type-safe, Alembic integration |
| Driver | asyncpg | Fastest pure-Python PostgreSQL async driver |
| Migrations | Alembic | Industry standard, autogenerate support |
| Schema | Pydantic-Settings | Type-safe, per-environment config |

---

## Architecture

```
FastAPI Application
        │
        ▼
  DatabaseManager               ← Owns the AsyncEngine lifecycle
  (app/database/database.py)
        │
        ├── connect()           ← Called on app startup (lifespan)
        ├── disconnect()        ← Called on app shutdown (lifespan)
        └── ping()              ← Called by health endpoint
                │
                ▼
          AsyncEngine           ← SQLAlchemy 2.x async engine
          (asyncpg driver)
                │
                ▼
  async_sessionmaker            ← Session factory
  (app/database/session.py)
                │
                ▼
          AsyncSession          ← Yielded to endpoint handlers
          (via get_db Depends)
                │
                ▼
         PostgreSQL 16
```

---

## Connection Flow

```
1. FastAPI lifespan starts
        │
        ▼
2. db_manager.connect()
   └── create_async_engine(settings.async_database_url, pool_kwargs)
   └── Engine is LAZY — no socket opened yet
        │
        ▼
3. Request arrives at GET /api/v1/health
        │
        ▼
4. health_check() calls db_manager.ping()
   └── Opens a connection from the pool
   └── Executes: SELECT 1
   └── Returns True / False
        │
        ▼
5. Response returned to client
        │
        ▼
6. FastAPI lifespan ends
        │
        ▼
7. db_manager.disconnect()
   └── engine.dispose() — closes all pool connections
```

---

## Folder Structure

```
backend/
├── app/
│   └── database/
│       ├── __init__.py       Re-exports: db_manager, Base, get_db
│       ├── base.py           DeclarativeBase — parent of all ORM models
│       ├── database.py       DatabaseManager class + db_manager singleton
│       └── session.py        get_session_factory() + get_db() dependency
│
├── alembic/
│   ├── env.py                Migration environment (loads settings, Base.metadata)
│   ├── script.py.mako        Template for generated migration files
│   └── versions/             Generated migration files (empty until Milestone 2.2)
│
└── alembic.ini               Alembic CLI configuration
```

---

## Configuration

### Environment Variables

All database configuration is driven by environment variables, validated by `pydantic-settings`.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_HOST` | `localhost` | PostgreSQL hostname |
| `DATABASE_PORT` | `5432` | PostgreSQL port |
| `DATABASE_NAME` | `devops_incident_db` | Database name |
| `DATABASE_USER` | `devops_user` | PostgreSQL user |
| `DATABASE_PASSWORD` | `devops_password` | PostgreSQL password |
| `DATABASE_URL` | _(empty)_ | Full URL override (takes precedence) |
| `DB_POOL_SIZE` | `5` | Connection pool size |
| `DB_MAX_OVERFLOW` | `10` | Extra connections above pool size |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait for a pool slot |
| `DB_POOL_RECYCLE` | `1800` | Recycle connections older than N seconds |
| `DB_ECHO` | `false` | Log all SQL statements |
| `DB_USE_NULL_POOL` | `false` | Use NullPool (set `true` in tests) |

### Per-Environment Pool Settings

| Setting | Development | Testing | Production |
|---|---|---|---|
| `DB_POOL_SIZE` | 5 | 2 | 20 |
| `DB_MAX_OVERFLOW` | 10 | 0 | 30 |
| `DB_ECHO` | true | false | false |
| `DB_USE_NULL_POOL` | false | **true** | false |

### Computed URLs

Two URLs are derived from the individual fields:

| Property | Scheme | Used by |
|---|---|---|
| `settings.async_database_url` | `postgresql+asyncpg://` | Application runtime |
| `settings.sync_database_url` | `postgresql://` | Alembic migrations |

---

## Running PostgreSQL Locally

### Option A — Docker (recommended)

```bash
# From the project root
cp .env.example .env
docker compose up postgres -d

# Verify it's running
docker compose ps postgres
docker compose exec postgres pg_isready -U devops_user -d devops_incident_db
```

### Option B — Local PostgreSQL install

```sql
-- Connect as postgres superuser
CREATE USER devops_user WITH PASSWORD 'devops_password';
CREATE DATABASE devops_incident_db OWNER devops_user;
GRANT ALL PRIVILEGES ON DATABASE devops_incident_db TO devops_user;
```

---

## Running the Full Stack with Docker

```bash
# From the project root
cp .env.example .env

# Build and start all services (postgres + backend + frontend)
docker compose up --build

# Or start in detached mode
docker compose up --build -d

# View backend logs
docker compose logs -f backend

# Stop all services
docker compose down

# Stop and remove volumes (wipes database)
docker compose down -v
```

---

## Alembic Commands

All Alembic commands are run from the `backend/` directory with the virtual environment active.

```bash
cd backend
source .venv/bin/activate      # macOS / Linux
.venv\Scripts\activate         # Windows

# Show the current revision in the database
alembic current

# Show the full migration history
alembic history

# Apply all pending migrations
alembic upgrade head

# Revert the last applied migration
alembic downgrade -1

# Generate a new migration (after adding models in Milestone 2.2)
alembic revision --autogenerate -m "add incidents table"

# Generate SQL-only migration script (no live DB needed)
alembic upgrade head --sql
```

---

## Health Endpoint

`GET /api/v1/health` now reports database status:

**Database connected:**
```json
{
  "success": true,
  "message": "Service is healthy.",
  "data": {
    "status": "healthy",
    "database": "connected",
    "version": "1.0.0"
  }
}
```

**Database unreachable:**
```json
{
  "success": true,
  "message": "Service is degraded: database unreachable.",
  "data": {
    "status": "degraded",
    "database": "disconnected",
    "version": "1.0.0"
  }
}
```

HTTP status is always `200`.  Upstream load balancers should inspect
`data.status` to determine service health.

---

## Testing

### Unit tests (no database required)

```bash
cd backend
pytest
```

### Integration tests (require live PostgreSQL)

```bash
cd backend

# Start PostgreSQL first
docker compose up postgres -d

# Run all tests including integration
pytest --integration
```

### Test isolation strategy

- `DB_USE_NULL_POOL=true` in `TestingSettings` prevents idle connections.
- `db_manager.ping` is mocked in `conftest.py` for the session-scoped `client` fixture.
- Integration tests are collected but **skipped** by default; pass `--integration` to run them.

---

## Security Notes

- Never commit `.env` to version control.
- In production, set `DATABASE_PASSWORD` via a secrets manager (AWS Secrets Manager, Vault, etc.).
- `DB_ECHO=false` in production (prevents SQL statement leakage in logs).
- PostgreSQL container uses `PGDATA` in a named volume (data persists across restarts).
- Backend container connects to PostgreSQL via the internal Docker network (port 5432 not exposed externally in production).
