# Completion Report — Milestones 2.9 to 4

## Milestone 2.9 — Comprehensive Testing and Coverage

Completed:

- Added `pytest-cov` and `backend/.coveragerc` with branch coverage.
- Added `make test-cov` and `make validate-data` commands.
- Added incident service, schema and HTTP contract tests.
- Added dataset schema, risk-rule and cross-split leakage tests.
- Preserved optional PostgreSQL integration tests behind `--integration`.

Validation performed for the newly added components:

- 17 tests passed.
- 87.8% combined coverage for the new incident service/schema and dataset modules.
- Python compile check passed.

## Milestone 2.10 — Final Backend Documentation

Completed:

- Updated the root README to the 15-milestone roadmap and current status.
- Updated the project directory documentation.
- Added incident API, dataset design, and testing/coverage guides.
- Documented ownership isolation, RBAC, soft deletion, filtering and validation.

## Milestone 3 — Incident Management APIs

Completed endpoints:

- Create incident
- List/history
- Search
- Pagination
- Status, severity and environment filters
- Get one incident
- Update incident
- Update status
- Soft-delete incident

Security rules:

- DevOps Engineers can create, update and view incidents.
- Viewers can view but cannot create or update.
- Only Admin can delete incidents under the current RBAC map.
- Non-admin users can access only incidents they own.
- Unauthorized resource lookup returns 404 to prevent ID enumeration.

No database migration was required because the existing `incidents` table
already contains every field used by this milestone.

## Milestone 4 — Dataset Design

Completed:

- Strong Pydantic dataset models.
- Generated JSON Schema.
- Seven supported categories and four risk levels.
- Structured output contract including causes, evidence, commands, risk,
  confirmation, warnings, verification, confidence and missing information.
- Versioned `train.jsonl`, `validation.jsonl` and `test.jsonl` samples.
- Validator for invalid JSON, schema errors, duplicate IDs/content and
  cross-split leakage.
- CLI validation command and documentation.

Milestone 5 should now expand these small reviewed samples to 1,000+ incidents
without changing the contract unless a deliberate schema version is released.
