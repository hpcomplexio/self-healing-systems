from __future__ import annotations

import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path

from healer.classifier import classify_pytest_output
from healer.fixers import apply_fix
from healer.types import FailureType

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
PATCH_FILE = ARTIFACTS_DIR / "healing_patch.diff"
INCIDENT_FILE = ARTIFACTS_DIR / "incident_report.json"


def _run_tests() -> dict[str, object]:
    process = subprocess.run(
        [str(ROOT / ".venv" / "bin" / "python"), "-m", "pytest"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    combined = process.stdout + "\n" + process.stderr
    return {
        "returncode": process.returncode,
        "passed": process.returncode == 0,
        "output": combined,
    }


def _snapshot(paths: list[Path]) -> dict[Path, str]:
    snapshot: dict[Path, str] = {}
    for path in paths:
        if path.exists():
            snapshot[path] = path.read_text()
    return snapshot


def _write_patch(before: dict[Path, str], changed: list[Path]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    diffs: list[str] = []

    for path in changed:
        if path not in before:
            continue
        after_text = path.read_text()
        before_lines = before[path].splitlines(keepends=True)
        after_lines = after_text.splitlines(keepends=True)
        if before_lines == after_lines:
            continue

        rel = path.relative_to(ROOT)
        diff_lines = unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
        diffs.extend(diff_lines)

    PATCH_FILE.write_text("".join(diffs))


def _write_incident(
    status: str,
    failure_type: FailureType,
    files_modified: list[Path],
    tests_before: dict[str, object],
    tests_after: dict[str, object] | None,
    classifier_payload: dict[str, object],
) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    incident = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "failure_type": failure_type.value,
        "files_modified": [str(path.relative_to(ROOT)) for path in files_modified],
        "tests_before": {
            "passed": tests_before["passed"],
            "returncode": tests_before["returncode"],
        },
        "tests_after": None
        if tests_after is None
        else {
            "passed": tests_after["passed"],
            "returncode": tests_after["returncode"],
        },
        "classifier": classifier_payload,
    }
    INCIDENT_FILE.write_text(json.dumps(incident, indent=2) + "\n")


def main() -> int:
    tests_before = _run_tests()

    if tests_before["passed"]:
        _write_incident(
            status="noop",
            failure_type=FailureType.UNKNOWN,
            files_modified=[],
            tests_before=tests_before,
            tests_after=tests_before,
            classifier_payload={"message": "No failing tests to heal."},
        )
        PATCH_FILE.write_text("")
        print("No failing tests detected. Nothing to heal.")
        return 1

    failure = classify_pytest_output(str(tests_before["output"]))

    if failure.failure_type not in {FailureType.ZERO_DIVISION, FailureType.NONE_TYPE_ERROR}:
        _write_incident(
            status="failed",
            failure_type=failure.failure_type,
            files_modified=[],
            tests_before=tests_before,
            tests_after=None,
            classifier_payload=asdict(failure),
        )
        PATCH_FILE.write_text("")
        print(f"Unsupported failure type: {failure.failure_type.value}")
        return 1

    candidate_files = [ROOT / "app" / "logic.py", ROOT / "tests" / "test_compute.py"]
    before = _snapshot(candidate_files)
    changed = apply_fix(failure)
    tests_after = _run_tests()
    _write_patch(before, changed)

    status = "healed" if tests_after["passed"] else "failed"
    _write_incident(
        status=status,
        failure_type=failure.failure_type,
        files_modified=changed,
        tests_before=tests_before,
        tests_after=tests_after,
        classifier_payload=asdict(failure),
    )

    if tests_after["passed"]:
        print("Healing succeeded. Tests are passing.")
        return 0

    print("Healing attempted but tests are still failing.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
