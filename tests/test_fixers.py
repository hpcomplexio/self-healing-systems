from __future__ import annotations

from pathlib import Path

import healer.fixers as fixers
from healer.types import FailureInfo, FailureType


def test_apply_fix_restores_zero_guard_and_adds_regression(monkeypatch, tmp_path: Path):
    logic = tmp_path / "logic.py"
    logic.write_text(
        "from __future__ import annotations\n\n\ndef compute_ratio(numerator: float | None, denominator: float | None) -> float:\n"
        "    # GUARD_NONE_START\n"
        "    if numerator is None or denominator is None:\n"
        "        raise ValueError(\"numerator and denominator must be numbers\")\n"
        "    # GUARD_NONE_END\n"
        "    return numerator / denominator\n"
    )

    tests = tmp_path / "test_compute.py"
    tests.write_text("def test_placeholder():\n    assert True\n")

    monkeypatch.setattr(fixers, "LOGIC_FILE", logic)
    monkeypatch.setattr(fixers, "TEST_FILE", tests)

    changed = fixers.apply_fix(FailureInfo(failure_type=FailureType.ZERO_DIVISION))

    assert logic in changed
    assert tests in changed
    assert "denominator must be non-zero" in logic.read_text()
    assert "test_logic_zero_division_regression" in tests.read_text()


def test_apply_fix_restores_none_guard_and_adds_regression(monkeypatch, tmp_path: Path):
    logic = tmp_path / "logic.py"
    logic.write_text(
        "from __future__ import annotations\n\n\ndef compute_ratio(numerator: float | None, denominator: float | None) -> float:\n"
        "    # GUARD_ZERO_START\n"
        "    if denominator == 0:\n"
        "        raise ValueError(\"denominator must be non-zero\")\n"
        "    # GUARD_ZERO_END\n"
        "    return numerator / denominator\n"
    )

    tests = tmp_path / "test_compute.py"
    tests.write_text("def test_placeholder():\n    assert True\n")

    monkeypatch.setattr(fixers, "LOGIC_FILE", logic)
    monkeypatch.setattr(fixers, "TEST_FILE", tests)

    changed = fixers.apply_fix(FailureInfo(failure_type=FailureType.NONE_TYPE_ERROR))

    assert logic in changed
    assert tests in changed
    assert "must be numbers" in logic.read_text()
    assert "test_logic_none_type_regression" in tests.read_text()
