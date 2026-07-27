# Project Structure

```text
devops-incident-support-model/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py
│   │   │   ├── health.py
│   │   │   ├── incidents.py
│   │   │   └── users.py
│   │   ├── config/                 # Environment settings
│   │   ├── core/                   # JWT, RBAC, logging, exceptions
│   │   ├── database/               # Engine, sessions and seed data
│   │   ├── dataset/                # Dataset schemas and validation
│   │   ├── dependencies/           # FastAPI providers
│   │   ├── middleware/             # Logging and security headers
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── repositories/           # Async persistence layer
│   │   ├── schemas/                # Pydantic API contracts
│   │   └── services/               # Business rules
│   ├── alembic/                    # Database migrations
│   ├── scripts/
│   │   ├── db.py
│   │   └── validate_dataset.py
│   ├── tests/
│   ├── .coveragerc
│   ├── pytest.ini
│   └── requirements.txt
├── data/
│   ├── schema/incident_dataset.schema.json
│   ├── train.jsonl
│   ├── validation.jsonl
│   ├── test.jsonl
│   ├── categories.json
│   ├── risk_levels.json
│   └── output_schema.json
├── docs/
├── frontend/
├── docker/
├── deployment/
├── models/
├── rag/
├── training/
├── docker-compose.yml
└── README.md
```

The backend follows API → service → repository → database layering. Dataset
validation is deliberately separate from the runtime incident API so future
collection and fine-tuning tools can reuse the same contract.
