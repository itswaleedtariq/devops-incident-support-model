# Backend Testing and Coverage

## Test layers

- Unit tests: schemas, JWT, passwords, permissions, services and dataset rules.
- API contract tests: health, authentication, users and incidents.
- Integration tests: PostgreSQL connectivity and Alembic migrations.
- Dataset tests: JSONL schema validation and split-leakage detection.

## Commands

Run from `backend/` with the virtual environment active:

```powershell
pytest -v
pytest -v --cov=app --cov-report=term-missing --cov-report=html
pytest -v --integration
```

The HTML report is written to `backend/htmlcov/index.html`.

## Coverage policy

The initial target is 80% for backend business logic. Authentication, RBAC,
incident ownership, validation, safety-sensitive branches and error responses
must be tested even when the overall percentage target has already been met.

Integration tests are skipped unless `--integration` is supplied because they
require the PostgreSQL test database configured in the environment.
