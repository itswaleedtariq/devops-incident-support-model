# Milestone 4 — Dataset Design

This directory contains the versioned contract for training and evaluating the
DevOps Incident Support Model. It intentionally contains only a small set of
reviewed examples; collecting 1,000+ incidents belongs to Milestone 5.

## Files

- `schema/incident_dataset.schema.json` — machine-readable JSON Schema.
- `categories.json` — supported incident categories.
- `risk_levels.json` — output and command risk definitions.
- `output_schema.json` — concise model-output contract.
- `train.jsonl`, `validation.jsonl`, `test.jsonl` — non-overlapping examples.

Each line is one complete JSON object. Never place the same incident, a lightly
rewritten duplicate, or the same log block in more than one split.

## Validate

From the project root:

```powershell
python backend/scripts/validate_dataset.py --all
```

A valid result exits with code `0`. Invalid JSON, schema errors, duplicate IDs,
duplicate incident content, and cross-split leakage exit with code `1`.

## Collection rules for Milestone 5

- Store source type, URL and license where applicable.
- Remove credentials, personal data, internal hostnames and private addresses.
- Keep confirmed log evidence separate from hypotheses.
- Explain every command and classify its risk.
- High/critical-risk actions require confirmation and a warning.
- Manually review every example before training.
