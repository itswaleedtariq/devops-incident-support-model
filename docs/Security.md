# Security

## Password Storage

- **Algorithm**: bcrypt via `passlib` (`app/core/security.py`).
- **Work factor**: `BCRYPT_ROUNDS=12` — configurable via env.
- **Salt**: unique per hash, embedded in the bcrypt output.
- **Never** stored: plain-text passwords.
- **Transparent upgrade**: `PasswordService.needs_rehash()` — on login the
  hash is re-computed if the work factor increased.

## Password Policy

Enforced twice — once at the schema layer (`UserCreate.password` validator)
and once at the service layer (`PasswordService.validate_strength`):

- Minimum length (`PASSWORD_MIN_LENGTH`)
- Uppercase / lowercase / digit / special-character requirements

## JWT

- **Library**: `PyJWT` (`app/core/jwt.py`).
- **Algorithm**: `HS256` (configurable).
- **Secret**: `JWT_SECRET_KEY` — MUST be overridden in production.
- **Claims**: `sub`, `iat`, `exp`, `jti`, `type` (`access`/`refresh`), plus
  `role` on access tokens.
- **Access TTL**: 15 min. **Refresh TTL**: 7 days.

## Refresh-Token Store

- Only the SHA-256 hash of the raw token is stored in the `refresh_tokens`
  table — never the raw token.
- Rotation on every `/refresh` (old row's `revoked_at` set, new row inserted).
- Explicit revocation on `/logout`.
- Full revocation on password change.

## Rate Limiting (SlowAPI)

Global limiter keyed by client IP.  Per-endpoint limits:

| Endpoint | Limit |
|---|---|
| `POST /auth/login` | 5/min |
| `POST /auth/register` | 3/min |
| `POST /auth/forgot-password` | 3/min |
| `POST /auth/reset-password` | 5/min |
| `POST /auth/refresh` | 20/min |

Configurable in `.env` (`RATE_LIMIT_*`).  Disabled globally when
`RATE_LIMIT_ENABLED=false`.

## HTTP Security Headers

Added by `SecurityHeadersMiddleware`:

| Header | Value |
|---|---|
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` |
| `Content-Security-Policy` | `default-src 'self'; frame-ancestors 'none';` |
| `Strict-Transport-Security` | *production only* — `max-age=63072000; includeSubDomains; preload` |

## CORS & Trusted Hosts

- **CORS**: `CORS_ALLOWED_ORIGINS` (comma-separated).  Set to real origins
  in production; `"*"` only in dev.
- **Trusted hosts**: `TRUSTED_HOSTS` blocks Host-header forgery attacks.
  Set to the real DNS name(s) in production.

## Input Validation

- Pydantic v2 schemas validate every request body.
- Email → `EmailStr`.
- Username → `^[a-zA-Z0-9_.-]{3,100}$`, forced lowercase.
- UUIDs → path-parameter type coercion (`uuid.UUID`).
- Search / sort parameters have length limits and pattern allow-lists.

## Secret Management

- Never commit `.env`.
- Rotate `JWT_SECRET_KEY` regularly — a rotation event invalidates every
  outstanding access token (they cannot be re-signed).
- Rotate the DB password by updating the container's `POSTGRES_PASSWORD`
  and the app's `DATABASE_PASSWORD` together.
- In production, source secrets from AWS Secrets Manager / Vault / GCP
  Secret Manager rather than env files.
