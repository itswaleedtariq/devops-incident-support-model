"""Command-line validation for Milestone 4 JSONL dataset files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.dataset.validator import validate_jsonl, validate_splits  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate DevOps incident JSONL data.")
    parser.add_argument("files", nargs="*", type=Path, help="One or more JSONL files.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate data/train.jsonl, validation.jsonl and test.jsonl together.",
    )
    parser.add_argument("--json", action="store_true", help="Print the report as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        files = [
            PROJECT_ROOT / "data" / "train.jsonl",
            PROJECT_ROOT / "data" / "validation.jsonl",
            PROJECT_ROOT / "data" / "test.jsonl",
        ]
        report = validate_splits(files)
    elif args.files:
        files = [path if path.is_absolute() else Path.cwd() / path for path in args.files]
        report = validate_splits(files) if len(files) > 1 else validate_jsonl(files[0])
    else:
        print("Provide JSONL files or pass --all.", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print("Dataset validation")
        print(f"  Files:      {len(report.files)}")
        print(f"  Records:    {report.total_records}")
        print(f"  Valid:      {report.valid_records}")
        print(f"  Invalid:    {report.invalid_records}")
        print(f"  Duplicates: {report.duplicate_records}")
        print(f"  Result:     {'PASS' if report.is_valid else 'FAIL'}")
        for issue in report.issues:
            print(f"  - {issue.file}:{issue.line}: {issue.message}")

    return 0 if report.is_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
