# Authentication

## Flow Overview

```
┌────────┐         POST /register        ┌────────┐  UserService.create   ┌──────┐
│ Client │ ────────────────────────────▶ │  API   │ ───────────────────▶  │  DB  │
│        │                                │        │                       │      │
│        │◀──── 201 { data: user } ─────  │        │                       │      │
└────────┘                                └────────┘                       └──────┘

┌────────┐          POST /login          ┌────────┐  verify + hash upgrade
│ Client │ ────────────────────────────▶ │  API   │ ──────────────────────┐
│        │                                │        │                       │
│        │◀── { access_token, refresh }── │        │◀── PasswordService ───┘
└────┬───┘                                └────────┘
     │
     │  GET /protected  Authorization: Bearer <access_token>
     ▼
┌────────┐                                ┌────────┐  decode → load user   ┌──────┐
│  API   │ ─────────────────────────────▶ │ Depends│ ───────────────────▶  │  DB  │
│        │                                │        │                       │      │
│        │◀────── endpoint response ────  │  auth  │                       │      │
└────────┘                                └────────┘                       └──────┘

When access token expires (~15 min):

┌────────┐          POST /refresh          ┌────────┐  TokenService.rotate
│ Client │ ─── { refresh_token } ───────▶ │  API   │ ──────────────────────┐
│        │                                 │        │  revoke old + issue   │
│        │◀── { new access + refresh } ──  │        │  fresh pair           │
└────────┘                                 └────────┘                       │
                                                │                           │
                                                ▼                           ▼
                                          RefreshTokenRepo         PostgreSQL
                                          (SHA-256 hashes)
```

## Endpoints

| Method | Route | Public? | Rate Limit | Purpose |
|---|---|---|---|---|
| POST | `/api/v1/auth/register` | Yes | 3/min | Create a new user (auto-assigns Viewer role) |
| POST | `/api/v1/auth/login` | Yes | 5/min | Exchange credentials for token pair |
| POST | `/api/v1/auth/logout` | Yes | — | Revoke a refresh token |
| POST | `/api/v1/auth/refresh` | Yes | 20/min | Rotate refresh token → fresh pair |
| POST | `/api/v1/auth/change-password` | Auth | — | Update own password + revoke all sessions |
| POST | `/api/v1/auth/forgot-password` | Yes | 3/min | (Stub) request reset email |
| POST | `/api/v1/auth/reset-password` | Yes | 5/min | (Stub) complete reset |
| GET  | `/api/v1/auth/me` | Auth | — | Return the authenticated user |

## JWT Payload

```json
{
  "sub": "<user-uuid>",
  "iat": 1743206400,
  "exp": 1743207300,
  "jti": "<hex-random>",
  "type": "access",
  "role": "Admin"        // access tokens only; extracted from user.role.name
}
```

- Signed with HS256 by default (`JWT_ALGORITHM`).
- Access token TTL: `ACCESS_TOKEN_EXPIRE_MINUTES=15`.
- Refresh token TTL: `REFRESH_TOKEN_EXPIRE_DAYS=7`.

## Refresh-Token Storage

- Raw refresh token: returned to the client, **never persisted**.
- SHA-256 hash of the token: stored in the `refresh_tokens` table.
- Columns: `user_id`, `token_hash`, `expires_at`, `revoked_at`.
- Rotation: every `/refresh` revokes the old row and issues a new one.
- Logout: sets `revoked_at = now()` for the presented token.
- Password change: revokes **every** active refresh token for the user.

## Password Policy

Configured via env vars in [backend/.env.example](backend/.env.example):

- `PASSWORD_MIN_LENGTH` (default 8)
- `PASSWORD_REQUIRE_UPPERCASE`
- `PASSWORD_REQUIRE_LOWERCASE`
- `PASSWORD_REQUIRE_DIGIT`
- `PASSWORD_REQUIRE_SPECIAL`

Passwords are hashed with **bcrypt** (`BCRYPT_ROUNDS=12`) via `passlib`. On successful login, the hash is transparently upgraded if the work factor changes.
