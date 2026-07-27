"""JSONL validation and cross-split leakage detection."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from pydantic import ValidationError

from app.dataset.schemas import DatasetRecord


@dataclass(slots=True)
class ValidationIssue:
    file: str
    line: int
    message: str


@dataclass(slots=True)
class DatasetValidationReport:
    files: list[str] = field(default_factory=list)
    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    duplicate_records: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.invalid_records == 0 and self.duplicate_records == 0

    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "duplicate_records": self.duplicate_records,
            "is_valid": self.is_valid,
            "issues": [
                {"file": issue.file, "line": issue.line, "message": issue.message}
                for issue in self.issues
            ],
        }


def _fingerprint(record: DatasetRecord) -> str:
    canonical = "\n".join(
        [
            record.input.environment.lower().strip(),
            record.input.incident_description.lower().strip(),
            record.input.logs.lower().strip(),
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_valid_records(path: Path, report: DatasetValidationReport) -> list[tuple[int, DatasetRecord]]:
    records: list[tuple[int, DatasetRecord]] = []
    seen_ids: set[str] = set()
    seen_fingerprints: set[str] = set()

    if not path.exists():
        report.invalid_records += 1
        report.issues.append(ValidationIssue(str(path), 0, "File does not exist."))
        return records

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            if not raw_line.strip():
                continue
            report.total_records += 1
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                report.invalid_records += 1
                report.issues.append(
                    ValidationIssue(str(path), line_number, f"Invalid JSON: {exc.msg}.")
                )
                continue

            try:
                record = DatasetRecord.model_validate(payload)
            except ValidationError as exc:
                report.invalid_records += 1
                compact = "; ".join(
                    f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                    for error in exc.errors()
                )
                report.issues.append(ValidationIssue(str(path), line_number, compact))
                continue

            fingerprint = _fingerprint(record)
            if record.id in seen_ids or fingerprint in seen_fingerprints:
                report.duplicate_records += 1
                report.issues.append(
                    ValidationIssue(str(path), line_number, "Duplicate record ID or incident content.")
                )
                continue

            seen_ids.add(record.id)
            seen_fingerprints.add(fingerprint)
            report.valid_records += 1
            records.append((line_number, record))

    return records


def validate_jsonl(path: str | Path) -> DatasetValidationReport:
    """Validate one dataset JSONL file."""
    resolved = Path(path)
    report = DatasetValidationReport(files=[str(resolved)])
    _load_valid_records(resolved, report)
    return report


def validate_splits(paths: Iterable[str | Path]) -> DatasetValidationReport:
    """Validate multiple splits and detect records repeated across split files."""
    resolved_paths = [Path(path) for path in paths]
    report = DatasetValidationReport(files=[str(path) for path in resolved_paths])
    global_ids: dict[str, tuple[str, int]] = {}
    global_fingerprints: dict[str, tuple[str, int]] = {}

    for path in resolved_paths:
        records = _load_valid_records(path, report)
        for line_number, record in records:
            fingerprint = _fingerprint(record)
            previous_id = global_ids.get(record.id)
            previous_content = global_fingerprints.get(fingerprint)
            if previous_id or previous_content:
                report.duplicate_records += 1
                previous = previous_id or previous_content
                report.issues.append(
                    ValidationIssue(
                        str(path),
                        line_number,
                        f"Cross-split duplicate; first seen in {previous[0]} line {previous[1]}.",
                    )
                )
            else:
                global_ids[record.id] = (str(path), line_number)
                global_fingerprints[fingerprint] = (str(path), line_number)

    return report
