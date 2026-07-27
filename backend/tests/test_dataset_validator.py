"""Tests for the Milestone 4 dataset contract and validator."""

from __future__ import annotations

import json
from pathlib import Path

from app.dataset.validator import validate_jsonl, validate_splits


def valid_record(record_id: str, description: str = "A container fails during startup.") -> dict:
    return {
        "id": record_id,
        "instruction": "Analyze this incident and return a safe structured troubleshooting response.",
        "input": {
            "environment": "Docker on Ubuntu",
            "incident_description": description,
            "logs": f"error for {record_id}",
            "recent_changes": None,
            "expected_behavior": None,
            "commands_already_tried": [],
        },
        "output": {
            "problem_category": "docker",
            "probable_causes": ["The startup configuration is invalid."],
            "evidence": [f"error for {record_id}"],
            "recommended_steps": [{
                "command": "docker logs container",
                "purpose": "Inspect the complete container logs.",
                "action_type": "diagnostic",
                "risk": "low",
                "requires_confirmation": False,
                "warning": None,
            }],
            "risk_level": "medium",
            "verification_steps": ["Restart the corrected container and inspect its health."],
            "confidence": 0.8,
            "missing_information": [],
        },
        "metadata": {
            "source_type": "synthetic",
            "source_url": None,
            "license": "Project-authored",
            "reviewed": True,
            "tags": [],
        },
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def test_valid_jsonl_passes(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    write_jsonl(path, [valid_record("docker_case_001")])
    report = validate_jsonl(path)
    assert report.is_valid
    assert report.valid_records == 1


def test_invalid_category_fails(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    record = valid_record("docker_case_002")
    record["output"]["problem_category"] = "database"
    write_jsonl(path, [record])
    report = validate_jsonl(path)
    assert not report.is_valid
    assert report.invalid_records == 1


def test_high_risk_step_requires_warning_and_confirmation(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    record = valid_record("docker_case_003")
    record["output"]["recommended_steps"][0]["risk"] = "high"
    write_jsonl(path, [record])
    report = validate_jsonl(path)
    assert not report.is_valid
    assert "must require confirmation" in report.issues[0].message


def test_cross_split_duplicate_is_detected(tmp_path: Path) -> None:
    train = tmp_path / "train.jsonl"
    test = tmp_path / "test.jsonl"
    record = valid_record("docker_case_004")
    write_jsonl(train, [record])
    duplicated = {**record, "id": "docker_case_005"}
    write_jsonl(test, [duplicated])
    report = validate_splits([train, test])
    assert not report.is_valid
    assert report.duplicate_records == 1
