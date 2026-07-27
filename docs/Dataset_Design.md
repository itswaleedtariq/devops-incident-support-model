# Dataset Design — Milestone 4

The supervised fine-tuning dataset is JSONL: one complete `DatasetRecord` per
line. The source-of-truth Pydantic contract is
`backend/app/dataset/schemas.py`; its exported JSON Schema is stored at
`data/schema/incident_dataset.schema.json`.

## Required record sections

1. `id` — stable unique identifier.
2. `instruction` — constant analysis instruction.
3. `input` — environment, incident description, logs and optional context.
4. `output` — category, causes, evidence, safe steps, risk and verification.
5. `metadata` — source type, source URL/license, review status and tags.

## Supported categories

Docker, GitHub Actions, Linux, NGINX, Gunicorn, Kubernetes and Django.

## Quality constraints

- Unknown fields are rejected.
- High/critical-risk steps require confirmation and a warning.
- Confidence must be between 0 and 1.
- Every record needs at least one cause, evidence item, recommended step and
  verification step.
- Duplicate IDs and duplicate incident content are rejected.
- Cross-split duplicates are rejected to protect evaluation integrity.

## Split purpose

- `train.jsonl`: examples used by QLoRA training.
- `validation.jsonl`: hyperparameter/model-selection feedback.
- `test.jsonl`: final held-out evaluation only.

The committed files are schema examples, not the Milestone 5 production-size
dataset.
