from __future__ import annotations

from pathlib import Path

import healer.injector as injector


def test_inject_zero_division_removes_zero_guard(monkeypatch, tmp_path: Path):
    logic = tmp_path / "logic.py"
    logic.write_text(
        "from __future__ import annotations\n\n\ndef compute_ratio(numerator: float | None, denominator: float | None) -> float:\n"
        "    # GUARD_ZERO_START\n"
        "    if denominator == 0:\n"
        "        raise ValueError(\"denominator must be non-zero\")\n"
        "    # GUARD_ZERO_END\n"
        "    return numerator / denominator\n"
    )

    monkeypatch.setattr(injector, "LOGIC_FILE", logic)

    injector.inject_bug("zero_division")

    assert "GUARD_ZERO_START" not in logic.read_text()


def test_inject_none_type_removes_none_guard(monkeypatch, tmp_path: Path):
    logic = tmp_path / "logic.py"
    logic.write_text(
        "from __future__ import annotations\n\n\ndef compute_ratio(numerator: float | None, denominator: float | None) -> float:\n"
        "    # GUARD_NONE_START\n"
        "    if numerator is None or denominator is None:\n"
        "        raise ValueError(\"numerator and denominator must be numbers\")\n"
        "    # GUARD_NONE_END\n"
        "    return numerator / denominator\n"
    )

    monkeypatch.setattr(injector, "LOGIC_FILE", logic)

    injector.inject_bug("none_type")

    assert "GUARD_NONE_START" not in logic.read_text()
