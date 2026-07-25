# Database Models

## Overview

All ORM models use SQLAlchemy 2.x declarative mapping with full type annotations.
Tables are registered under a shared `Base` (`app.database.base.Base`) with a consistent
`MetaData` naming convention so every constraint and index gets a deterministic name for
reliable Alembic migrations.

---

## Entity Relationship Diagram

```
┌──────────────┐          ┌──────────────────────────────────────────┐
│    roles     │  1     * │                  users                   │
│──────────────│──────────│──────────────────────────────────────────│
│ id (PK, UUID)│          │ id (PK, UUID)                            │
│ name         │          │ full_name                                │
│ description  │          │ username (UQ)                            │
│ created_at   │          │ email    (UQ)                            │
│ updated_at   │          │ password_hash                            │
└──────────────┘          │ is_active                                │
                          │ is_verified                              │
                          │ role_id (FK → roles.id)                  │
                          │ created_at / updated_at                  │
                          │ is_deleted / deleted_at  [soft delete]   │
                          └─────────────────────┬────────────────────┘
                                                │ 1
                                      ┌─────────┘ *
                          ┌───────────▼──────────────────────────────┐
                          │               incidents                  │
                          │──────────────────────────────────────────│
                          │ id (PK, UUID)                            │
                          │ title                                    │
                          │ description                              │
                          │ environment                              │
                          │ logs                                     │
                          │ status      (ENUM, idx)                  │
                          │ severity    (ENUM, idx)                  │
                          │ created_by  (FK → users.id)              │
                          │ created_at / updated_at                  │
                          │ is_deleted / deleted_at  [soft delete]   │
                          └─────────────┬────────────────────────────┘
                                        │ 1
                                   *    ▼
                          ┌─────────────────────┐
                          │      feedbacks      │
                          │─────────────────────│
                          │ id (PK, UUID)       │
                          │ incident_id (FK)    │──── * ──► incidents
                          │ user_id     (FK)    │──── * ──► users
                          │ rating   (1–5 CHECK)│
                          │ comment             │
                          │ created_at          │
                          └─────────────────────┘

┌──────────────────────────────────┐
│            documents             │
│──────────────────────────────────│
│ id (PK, UUID)                    │
│ title                            │
│ source                           │
│ category  (ENUM, idx)            │
│ path                             │
│ description                      │
│ created_at / updated_at          │
└──────────────────┬───────────────┘
                   │ 1
              *    ▼
┌─────────────────────────────────────┐
│         embedding_metadata          │
│─────────────────────────────────────│
│ id (PK, UUID)                       │
│ document_id  (FK → documents.id)    │
│ chunk_number                        │
│ embedding_model                     │
│ vector_id  (idx, nullable)          │
│ created_at                          │
│ UNIQUE (document_id, chunk_number)  │
└─────────────────────────────────────┘
```

---

## Model Descriptions

### Role (`roles`)

Represents an access-control role (e.g. *admin*, *engineer*, *viewer*).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, default=uuid4 | Python-generated before INSERT |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Short identifier |
| `description` | TEXT | nullable | Human-readable explanation |
| `created_at` | TIMESTAMPTZ | NOT NULL, server_default=now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL, onupdate=now() | |

**Relationships:** `users` ← one-to-many

---

### User (`users`)

Represents an authenticated engineer or administrator.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `full_name` | VARCHAR(200) | NOT NULL | |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Login handle |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | |
| `password_hash` | VARCHAR(255) | NOT NULL | Argon2/bcrypt — never store plaintext |
| `is_active` | BOOLEAN | NOT NULL, default=True | Disables login without deleting |
| `is_verified` | BOOLEAN | NOT NULL, default=False | Email confirmation flag |
| `role_id` | UUID | FK → roles.id (SET NULL), INDEX | Nullable — no role = least privilege |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `is_deleted` | BOOLEAN | NOT NULL, default=False | Soft delete flag |
| `deleted_at` | TIMESTAMPTZ | nullable | |

**Relationships:** `role` → many-to-one; `incidents` ← one-to-many; `feedbacks` ← one-to-many

---

### Incident (`incidents`)

A DevOps failure event submitted for AI analysis.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `title` | VARCHAR(500) | NOT NULL | Short description |
| `description` | TEXT | NOT NULL | Full symptom description |
| `environment` | VARCHAR(100) | nullable | production, staging, dev, … |
| `logs` | TEXT | nullable | Raw log output for AI analysis |
| `status` | ENUM(IncidentStatus) | NOT NULL, INDEX | open → in_progress → resolved → closed |
| `severity` | ENUM(IncidentSeverity) | NOT NULL, INDEX | critical / high / medium / low / info |
| `created_by` | UUID | FK → users.id (SET NULL), INDEX | Soft FK — survives user deletion |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `is_deleted` | BOOLEAN | NOT NULL | Soft delete |
| `deleted_at` | TIMESTAMPTZ | nullable | |

**Composite index:** `(status, severity)` — common "open + critical" filter query.

**Relationships:** `created_by_user` → many-to-one; `feedbacks` ← one-to-many (cascade delete)

---

### Feedback (`feedbacks`)

User rating and comment on an incident's AI response.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `incident_id` | UUID | FK → incidents.id (CASCADE), INDEX | Physical FK cascade |
| `user_id` | UUID | FK → users.id (SET NULL), INDEX | Nullable — survives user deletion |
| `rating` | INTEGER | NOT NULL, CHECK (1–5) | RLHF signal |
| `comment` | TEXT | nullable | Optional written feedback |
| `created_at` | TIMESTAMPTZ | NOT NULL | No updated_at — feedback is immutable |

**Relationships:** `incident` → many-to-one; `user` → many-to-one

---

### Document (`documents`)

Metadata for a RAG knowledge-base source document.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `title` | VARCHAR(500) | NOT NULL | |
| `source` | VARCHAR(1000) | nullable | Origin URL |
| `category` | ENUM(DocumentCategory) | NOT NULL, INDEX | Filters retrieval scope |
| `path` | VARCHAR(1000) | nullable | Local filesystem path |
| `description` | TEXT | nullable | Summary |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**Relationships:** `embedding_metadata` ← one-to-many (cascade delete)

---

### EmbeddingMetadata (`embedding_metadata`)

One text chunk of a source document, indexed in ChromaDB.

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK | |
| `document_id` | UUID | FK → documents.id (CASCADE), INDEX | |
| `chunk_number` | INTEGER | NOT NULL | Zero-based chunk position |
| `embedding_model` | VARCHAR(200) | NOT NULL | e.g. Qwen2.5-Coder-3B-Instruct |
| `vector_id` | VARCHAR(500) | nullable, INDEX | ChromaDB vector reference |
| `created_at` | TIMESTAMPTZ | NOT NULL | No updated_at — immutable once embedded |
| UNIQUE | — | `(document_id, chunk_number)` | One chunk per position |

**Relationships:** `document` → many-to-one

---

## Mixins

### `UUIDMixin`

Provides a `uuid.UUID` primary key named `id` generated client-side with `uuid.uuid4()`.
UUID generation at the Python level (not server-side) means the ID is available on the object
immediately after construction — before the INSERT round-trip — enabling it to be passed to
message queues and caches without an extra query.

### `TimestampMixin`

Provides `created_at` and `updated_at` columns (both `TIMESTAMP WITH TIME ZONE`).
`created_at` is set by the PostgreSQL server on INSERT (`server_default=now()`).
`updated_at` is refreshed by SQLAlchemy on every ORM-level UPDATE (`onupdate=now()`).

### `SoftDeleteMixin`

Provides `is_deleted: bool` and `deleted_at: datetime | None`. Records are never physically
deleted; the service layer must filter `WHERE is_deleted = false` in all standard queries.
Physical DELETE is reserved for GDPR erasure requests or administrative cleanup.

---

## Enums

| Enum | Values |
|---|---|
| `IncidentStatus` | `open`, `in_progress`, `resolved`, `closed` |
| `IncidentSeverity` | `critical`, `high`, `medium`, `low`, `info` |
| `DocumentCategory` | `runbook`, `incident_history`, `knowledge_base`, `architecture`, `api_docs`, `other` |
| `UserStatus` | `active`, `inactive`, `suspended`, `pending_verification` |

All enums are backed by native PostgreSQL `ENUM` types.

---

## Indexes

| Index | Table | Columns | Reason |
|---|---|---|---|
| `ix_roles_name` | roles | name | Role lookup by name |
| `ix_users_email` | users | email | Login / uniqueness check |
| `ix_users_username` | users | username | Login / uniqueness check |
| `ix_users_role_id` | users | role_id | FK join optimisation |
| `ix_incidents_status` | incidents | status | Filter open/resolved incidents |
| `ix_incidents_severity` | incidents | severity | Sort by priority |
| `ix_incidents_created_by` | incidents | created_by | User's incident history |
| `ix_incidents_status_severity` | incidents | (status, severity) | Composite: "open + critical" |
| `ix_feedbacks_incident_id` | feedbacks | incident_id | Feedback per incident |
| `ix_feedbacks_user_id` | feedbacks | user_id | Feedback by user |
| `ix_documents_category` | documents | category | RAG category filtering |
| `ix_embedding_metadata_document_id` | embedding_metadata | document_id | Chunk lookup |
| `ix_embedding_metadata_vector_id` | embedding_metadata | vector_id | ChromaDB cross-reference |

---

## Cascade Rules

| Parent → Child | Rule | Reasoning |
|---|---|---|
| `Role → User.role_id` | `SET NULL` | Deleting a role must not delete all its users |
| `User → Incident.created_by` | `SET NULL` | Historical incidents must survive user deletion |
| `Incident → Feedback` | `CASCADE DELETE` | Feedback has no value without its parent incident |
| `User → Feedback.user_id` | `SET NULL` | Feedback signal preserved even after user deletion |
| `Document → EmbeddingMetadata` | `CASCADE DELETE` | Chunk records are meaningless without the document |

---

## Relationship Loading Strategy

| Relationship | Strategy | Reason |
|---|---|---|
| `User.role` | `selectin` | Role is almost always displayed with user info |
| `User.incidents` | `select` (raise in async) | Can be thousands — load explicitly |
| `User.feedbacks` | `select` | Can be thousands — load explicitly |
| `Incident.created_by_user` | `selectin` | Author is always shown with the incident |
| `Incident.feedbacks` | `select` | Load explicitly in feedback listing APIs |
| `Feedback.incident` | `selectin` | Always displayed alongside feedback |
| `Feedback.user` | `selectin` | Author always shown with feedback |
| `Document.embedding_metadata` | `select` | Can be hundreds of chunks |
| `EmbeddingMetadata.document` | `selectin` | Document context always needed |

Use `selectinload()` / `joinedload()` in repository queries for `lazy="select"` relationships.

---

## Why UUIDs?

| Benefit | Explanation |
|---|---|
| **No sequential guessing** | Sequential integer IDs leak record count and enable enumeration attacks |
| **Distributed generation** | Multiple services can generate IDs without coordination |
| **Pre-flush availability** | ID is set at Python level — no DB round-trip needed to pass it downstream |
| **Merge-safe** | Database sharding and replication never produces collisions |

---

## Future Usage

| Milestone | Model(s) | What is added |
|---|---|---|
| 2.3 | All | Alembic migrations generated from `Base.metadata` |
| 2.4 | User | JWT authentication wired to `User.password_hash` |
| 3 | Document, EmbeddingMetadata | RAG ingestion: chunks stored in ChromaDB, `vector_id` populated |
| 4 | Incident | AI response stored on the incident; feedback drives RLHF |
| 5 | All | Production deployment with full migration history |
