# API Authentication — Curl Examples

Every response follows the standard envelope:

```json
{ "success": true, "message": "...", "data": { ... } }
```

## 1. Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Jane Engineer",
    "username": "jane",
    "email": "jane@example.com",
    "password": "StrongPass1!"
  }'
```

Response `201`:

```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "id": "...",
    "username": "jane",
    "email": "jane@example.com",
    "role_name": "Viewer",
    ...
  }
}
```

## 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{ "email": "jane@example.com", "password": "StrongPass1!" }'
```

Response `200`:

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "access_token":  "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type":    "bearer",
    "expires_in":    900
  }
}
```

## 3. Call a protected endpoint

```bash
ACCESS_TOKEN="eyJhbGci..."

curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## 4. Refresh tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "eyJhbGci..." }'
```

## 5. Change password

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "StrongPass1!",
    "new_password":     "EvenStronger2@"
  }'
```

All active refresh tokens are revoked — the caller must log in again.

## 6. Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -d '{ "refresh_token": "eyJhbGci..." }'
```

## 7. Admin — list users

```bash
curl "http://localhost:8000/api/v1/users?page=1&page_size=20&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer $ADMIN_ACCESS_TOKEN"
```

## Swagger UI

Interactive docs with a lock icon for JWT authorization:

```
http://localhost:8000/docs
```

Click **Authorize**, paste `Bearer <access_token>`, then execute any
protected endpoint.
