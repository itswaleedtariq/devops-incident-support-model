# Service Layer

## Purpose

Services own business logic.  They coordinate one or more repositories,
enforce invariants (uniqueness, password policy, token expiry), and raise
domain exceptions.  The API layer converts those exceptions to HTTP
responses.

## Services

| Service | Responsibility | Depends on |
|---|---|---|
| `PasswordService` | Hash / verify / policy | (stateless) |
| `TokenService` | Issue / verify / rotate / revoke JWTs | `RefreshTokenRepository` |
| `PermissionService` | RBAC lookups | (stateless) |
| `UserService` | Create / update / delete users, enforce uniqueness | `UserRepository` |
| `AuthService` | Register / login / refresh / change-password | `UserService`, `TokenService`, `RoleRepository` |

## Composition (call graph)

```
                       ┌───────────────┐
                       │   Endpoint    │
                       └───────┬───────┘
                               │ Depends()
                       ┌───────▼───────┐
                       │  AuthService  │
                       └───┬──────┬──┬─┘
                           │      │  └───────────────┐
             ┌─────────────┘      │                  │
             ▼                    ▼                  ▼
     ┌──────────────┐     ┌──────────────┐   ┌──────────────┐
     │ UserService  │     │ TokenService │   │ RoleRepo     │
     └──────┬───────┘     └──────┬───────┘   └──────────────┘
            │                    │
            ▼                    ▼
     ┌──────────────┐     ┌──────────────────┐
     │ UserRepo     │     │ RefreshTokenRepo │
     └──────┬───────┘     └────────┬─────────┘
            │                       │
            ▼                       ▼
                    AsyncSession
                          │
                          ▼
                      PostgreSQL
```

## Domain Exceptions

Services raise `AppBaseException` subclasses from
`app/exceptions/__init__.py`:

| Exception | Meaning | Typical HTTP mapping |
|---|---|---|
| `NotFoundError` | Requested resource missing | 404 |
| `DuplicateResourceError` | Unique-constraint conflict | 409 |
| `InvalidCredentialsError` | Bad email / password | 401 |
| `InactiveUserError` | Disabled account | 403 |
| `InvalidTokenError` | Malformed / expired / revoked | 401 |
| `WeakPasswordError` | Password policy violation | 422 |
| `PermissionDeniedError` | RBAC denial | 403 |

## Design Rules

- Services **never** import `Request`, `Response`, `HTTPException` or any
  FastAPI type — they are transport-agnostic.
- Services **never** access `self.session` directly — repositories do.
- Repositories **never** raise HTTP errors — they raise plain
  `LookupError` or return `None`; services convert to domain exceptions.
- Endpoint code translates domain exceptions into `HTTPException` and
  wraps successful returns in `StandardResponse`.
