from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _fixture_files(path: Path) -> list[Path]:
    return sorted([p for p in path.iterdir() if p.suffix == ".json"])


def test_event_schema_fixtures() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = Path(
        os.getenv(
            "EVENT_SCHEMA_PATH",
            str(repo_root / "contracts" / "event-schema.json"),
        )
    )

    if not schema_path.exists():
        pytest.skip(f"schema not found at {schema_path}")

    schema = _load_json(schema_path)
    validate = jsonschema.Draft202012Validator(schema)

    fixtures_root = Path(__file__).resolve().parent / "fixtures"

    for fixture_path in _fixture_files(fixtures_root / "valid"):
        errors = sorted(validate.iter_errors(_load_json(fixture_path)), key=str)
        assert not errors, f"expected valid fixture to pass: {fixture_path} :: {errors}"

    for fixture_path in _fixture_files(fixtures_root / "invalid"):
        errors = sorted(validate.iter_errors(_load_json(fixture_path)), key=str)
        assert errors, f"expected invalid fixture to fail: {fixture_path}"
