# ============================================================
# DevOps Incident Support Model — Backend Makefile
# ============================================================
# Run from the backend/ directory.
# Requires the virtual environment to be active.
#
# Usage:
#   make migrate       — Apply all pending migrations
#   make rollback      — Revert the last migration
#   make seed          — Seed default application data
#   make reset         — Full schema reset (destructive!)
#   make current       — Show current migration revision
#   make history       — Show migration history
#   make check         — Verify schema is up to date
#   make test          — Run the test suite
#   make test-int      — Run integration tests (requires live DB)
# ============================================================

PYTHON  := python
SCRIPTS := scripts/db.py
PYTEST  := python -m pytest

.PHONY: migrate rollback reset seed current history check test test-cov test-int validate-data

## Apply all pending Alembic migrations
migrate:
	$(PYTHON) $(SCRIPTS) migrate

## Revert the last Alembic migration
rollback:
	$(PYTHON) $(SCRIPTS) rollback

## Downgrade to base then re-apply all migrations (DESTRUCTIVE)
reset:
	@echo "WARNING: This will drop and recreate all database tables."
	$(PYTHON) $(SCRIPTS) reset

## Seed the database with default roles
seed:
	$(PYTHON) $(SCRIPTS) seed

## Show the current migration revision
current:
	$(PYTHON) $(SCRIPTS) current

## Show the full migration history
history:
	$(PYTHON) $(SCRIPTS) history

## Verify the database schema is up to date
check:
	$(PYTHON) $(SCRIPTS) check

## Run unit tests (no database required)
test:
	$(PYTEST) -v

## Run all tests including integration tests (requires live PostgreSQL)
test-int:
	$(PYTEST) -v --integration

## Create a new migration — usage: make create-migration MSG="add column foo"
create-migration:
	$(PYTHON) $(SCRIPTS) create-migration -m "$(MSG)"

## Run unit tests with branch coverage
test-cov:
	$(PYTEST) -v --cov=app --cov-report=term-missing --cov-report=html

## Validate all committed dataset splits
validate-data:
	$(PYTHON) scripts/validate_dataset.py --all
