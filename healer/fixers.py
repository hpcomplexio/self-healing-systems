from __future__ import annotations

from pathlib import Path

from healer.types import FailureInfo, FailureType

ROOT = Path(__file__).resolve().parents[1]
LOGIC_FILE = ROOT / "app" / "logic.py"
TEST_FILE = ROOT / "tests" / "test_compute.py"

ZERO_GUARD = """    # GUARD_ZERO_START\n    if denominator == 0:\n        raise ValueError(\"denominator must be non-zero\")\n    # GUARD_ZERO_END\n"""
NONE_GUARD = """    # GUARD_NONE_START\n    if numerator is None or denominator is None:\n        raise ValueError(\"numerator and denominator must be numbers\")\n    # GUARD_NONE_END\n"""

ZERO_REGRESSION_TEST = """

def test_logic_zero_division_regression():
    from app.logic import compute_ratio

    try:
        compute_ratio(1, 0)
    except ValueError as exc:
        assert "denominator must be non-zero" in str(exc)
    else:
        raise AssertionError("Expected ValueError for zero denominator")
"""

NONE_REGRESSION_TEST = """

def test_logic_none_type_regression():
    from app.logic import compute_ratio

    try:
        compute_ratio(None, 2)
    except ValueError as exc:
        assert "must be numbers" in str(exc)
    else:
        raise AssertionError("Expected ValueError for None input")
"""


def _restore_guard(guard: str, anchor: str) -> bool:
    source = LOGIC_FILE.read_text()
    if guard in source:
        return False

    if anchor not in source:
        raise ValueError(f"anchor not found while restoring guard: {anchor}")

    source = source.replace(anchor, guard + anchor)
    LOGIC_FILE.write_text(source)
    return True


def _ensure_regression_test(snippet: str, test_name: str) -> bool:
    source = TEST_FILE.read_text()
    if test_name in source:
        return False

    TEST_FILE.write_text(source.rstrip() + "\n" + snippet.strip() + "\n")
    return True


def apply_fix(failure: FailureInfo) -> list[Path]:
    changed: list[Path] = []

    if failure.failure_type == FailureType.ZERO_DIVISION:
        if _restore_guard(ZERO_GUARD, "    return numerator / denominator\n"):
            changed.append(LOGIC_FILE)
        if _ensure_regression_test(
            ZERO_REGRESSION_TEST, "test_logic_zero_division_regression"
        ):
            changed.append(TEST_FILE)
        return changed

    if failure.failure_type == FailureType.NONE_TYPE_ERROR:
        if _restore_guard(NONE_GUARD, "    return numerator / denominator\n"):
            changed.append(LOGIC_FILE)
        if _ensure_regression_test(
            NONE_REGRESSION_TEST, "test_logic_none_type_regression"
        ):
            changed.append(TEST_FILE)
        return changed

    return changed
