# Authorization (RBAC)

## Model

```
┌──────────────┐              ┌────────────────────────────┐
│    User      │ role_id ──▶  │           Role             │
│              │              │  Admin / DevOps Eng /      │
│              │              │  AI Eng / Viewer           │
└──────────────┘              └─────────────┬──────────────┘
                                            │
                                            ▼
                              ROLE_PERMISSIONS: dict
                              ────────────────────
                              Admin           → { all }
                              DevOps Engineer → { create/update/view incident,
                                                  view document, submit feedback }
                              AI Engineer     → { view incident, upload/delete/view
                                                  document, manage feedback }
                              Viewer          → { view incident, view document,
                                                  submit feedback }
```

## Enforcement

Three FastAPI dependencies do all the work:

| Dependency | Behaviour |
|---|---|
| `get_current_user` | Decode Bearer JWT → load `User`; raises 401 if any step fails |
| `get_current_active_user` | Above **plus** `is_active=True AND is_deleted=False`; raises 403 |
| `get_current_admin` | Above **plus** `role.name == "Admin"`; raises 403 |
| `require_permission("permission:name")` | Factory — raises 403 unless user's role holds the specified permission |

## Usage in endpoints

```python
from app.core.permissions import Permission
from app.dependencies.current_user import require_permission

@router.delete("/documents/{doc_id}")
async def delete_doc(
    doc_id: uuid.UUID,
    _: User = Depends(require_permission(Permission.DELETE_DOCUMENT)),
): ...
```

Admin-only routes prefer the shorter `get_current_admin`:

```python
@router.get("/users", dependencies=[Depends(get_current_admin)])
async def list_users(...): ...
```

## Permissions Reference

| Constant | Value | Admin | DevOps | AI | Viewer |
|---|---|:-:|:-:|:-:|:-:|
| `CREATE_INCIDENT` | `incident:create` | ✅ | ✅ | ❌ | ❌ |
| `UPDATE_INCIDENT` | `incident:update` | ✅ | ✅ | ❌ | ❌ |
| `DELETE_INCIDENT` | `incident:delete` | ✅ | ❌ | ❌ | ❌ |
| `VIEW_INCIDENT` | `incident:view` | ✅ | ✅ | ✅ | ✅ |
| `MANAGE_USERS` | `users:manage` | ✅ | ❌ | ❌ | ❌ |
| `VIEW_USERS` | `users:view` | ✅ | ❌ | ❌ | ❌ |
| `MANAGE_ROLES` | `roles:manage` | ✅ | ❌ | ❌ | ❌ |
| `UPLOAD_DOCUMENT` | `document:upload` | ✅ | ❌ | ✅ | ❌ |
| `DELETE_DOCUMENT` | `document:delete` | ✅ | ❌ | ✅ | ❌ |
| `VIEW_DOCUMENT` | `document:view` | ✅ | ✅ | ✅ | ✅ |
| `MANAGE_FEEDBACK` | `feedback:manage` | ✅ | ❌ | ✅ | ❌ |
| `SUBMIT_FEEDBACK` | `feedback:submit` | ✅ | ✅ | ❌ | ✅ |
| `MANAGE_SYSTEM` | `system:manage` | ✅ | ❌ | ❌ | ❌ |

Extending: add a new constant to `Permission` and update `ROLE_PERMISSIONS` in `app/core/permissions.py`.
