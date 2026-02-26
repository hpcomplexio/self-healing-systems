from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from healer.classifier import classify_pytest_output
from healer.fixers import apply_fix
from healer.types import FailureType

KNOWN_FAILURE_TYPES = {FailureType.ZERO_DIVISION, FailureType.NONE_TYPE_ERROR}


@dataclass(frozen=True)
class HealOutcome:
    status: str
    reason_code: str | None
    human_context: dict[str, Any] | None
    patch_summary: str | None
    changed_files: list[str]


def _extract_failure_output(payload: dict[str, Any]) -> str:
    candidates = (
        payload.get("output"),
        payload.get("failingOutput"),
        payload.get("pytestOutput"),
        payload.get("logs"),
        payload.get("build", {}).get("output") if isinstance(payload.get("build"), dict) else None,
    )
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return ""


def heal_from_payload(payload: dict[str, Any]) -> HealOutcome:
    output = _extract_failure_output(payload)
    failure = classify_pytest_output(output)

    if failure.failure_type not in KNOWN_FAILURE_TYPES:
        lines = output.splitlines()
        return HealOutcome(
            status="escalated",
            reason_code="unknown_failure_signature",
            human_context={
                "summary": failure.message,
                "failingOutputPreview": lines[:100],
                "candidateFiles": ["app/logic.py", "tests/test_compute.py"],
            },
            patch_summary=None,
            changed_files=[],
        )

    changed_paths = apply_fix(failure)
    changed_files: list[str] = []
    for path in changed_paths:
        try:
            changed_files.append(str(path.relative_to(Path.cwd())))
        except ValueError:
            changed_files.append(str(path))

    return HealOutcome(
        status="completed",
        reason_code=None,
        human_context=None,
        patch_summary=f"Applied {failure.failure_type.value} remediation.",
        changed_files=changed_files,
    )
