# Repository Layer

## Purpose

Repositories translate service intent into SQLAlchemy operations against a
single ORM model.  They **do not** contain business logic — that lives in
the service layer.

## Base

`app/repositories/base.py` defines the generic `BaseRepository[ModelT]`:

| Method | Purpose |
|---|---|
| `create(**fields)` | Insert and return |
| `add(instance)` | Add an already-built instance |
| `bulk_create(items)` | Bulk insert |
| `get(id_)` / `get_or_raise(id_)` | Primary-key lookup |
| `find_one(**filters)` / `find_all(**filters)` | Filtered read |
| `exists(**filters)` / `count(**filters)` | Predicates |
| `paginate(...)` | Pagination + sort + ILIKE search + filters |
| `update(instance, **fields)` | Field-level update |
| `bulk_update(filters, values)` | Multi-row update |
| `delete(instance)` / `delete_by_id(id_)` | Physical delete |
| `soft_delete(instance)` | Sets `is_deleted=True` + `deleted_at=now()` |

## Concrete Repositories

| Class | Table | Extra methods |
|---|---|---|
| `UserRepository` | users | `get_by_email`, `get_by_username`, `get_with_role` |
| `RoleRepository` | roles | `get_by_name` |
| `IncidentRepository` | incidents | — (only base) |
| `FeedbackRepository` | feedbacks | — |
| `DocumentRepository` | documents | — |
| `EmbeddingRepository` | embedding_metadata | — |
| `RefreshTokenRepository` | refresh_tokens | `get_by_hash`, `revoke`, `revoke_all_for_user` |

## Provisioning via Dependency Injection

`app/dependencies/repositories.py` exposes one FastAPI `Depends` provider
per repository, each bound to the current request's `AsyncSession`:

```python
def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)
```

Services accept repositories in their `__init__` — no repository is
instantiated inside a service, keeping the composition root at the API layer.

## Testing Strategy

- **Unit tests**: fake repositories (dict-backed) injected via
  `app.dependency_overrides` — see `tests/test_auth_endpoints.py`.
- **Integration tests**: exercise the real repositories against a live
  PostgreSQL instance — marked `pytest.mark.integration`, run with
  `pytest --integration`.
