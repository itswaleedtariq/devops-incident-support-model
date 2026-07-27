# Incident Management API — Milestone 3

Base path: `/api/v1/incidents`

All routes require a valid Bearer access token and the corresponding RBAC
permission. Admins can see every incident; non-admin users can only see their
own records. Delete is currently restricted to Admin because only Admin holds
`incident:delete`.

| Method | Path | Purpose | Permission |
|---|---|---|---|
| POST | `/incidents` | Create an open incident | `incident:create` |
| GET | `/incidents` | Search/filter/paginate incident history | `incident:view` |
| GET | `/incidents/history` | History alias for dashboard clients | `incident:view` |
| GET | `/incidents/{id}` | Read one visible incident | `incident:view` |
| PATCH | `/incidents/{id}` | Update details/severity | `incident:update` |
| PATCH | `/incidents/{id}/status` | Change workflow status | `incident:update` |
| DELETE | `/incidents/{id}` | Soft-delete while preserving audit data | `incident:delete` |

## Create example

```json
{
  "title": "NGINX returns 502",
  "description": "The public endpoint cannot connect to the application service.",
  "environment": "production",
  "logs": "connect() failed (111: Connection refused) while connecting to upstream",
  "severity": "high"
}
```

New incidents always start with status `open`; clients cannot set the initial
status directly.

## Listing, search and filtering

Example:

```text
GET /api/v1/incidents?page=1&page_size=20&search=nginx&status=open&severity=high&environment=production&sort_by=created_at&sort_order=desc
```

Allowed sort fields: `created_at`, `updated_at`, `title`, `status`, `severity`,
`environment`.

## Security behavior

A request for an incident owned by another non-admin user returns `404`, not
`403`. This prevents resource-ID enumeration. Deletion is soft deletion: the
row remains available for audit and future reviewed dataset preparation, but
normal API queries hide it.
