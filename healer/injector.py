from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGIC_FILE = ROOT / "app" / "logic.py"

ZERO_GUARD = """    # GUARD_ZERO_START\n    if denominator == 0:\n        raise ValueError(\"denominator must be non-zero\")\n    # GUARD_ZERO_END\n"""
NONE_GUARD = """    # GUARD_NONE_START\n    if numerator is None or denominator is None:\n        raise ValueError(\"numerator and denominator must be numbers\")\n    # GUARD_NONE_END\n"""


def inject_bug(mode: str) -> Path:
    source = LOGIC_FILE.read_text()

    if mode == "zero_division":
        if ZERO_GUARD not in source:
            raise ValueError("zero_division bug is already injected or marker not found")
        source = source.replace(ZERO_GUARD, "")
    elif mode == "none_type":
        if NONE_GUARD not in source:
            raise ValueError("none_type bug is already injected or marker not found")
        source = source.replace(NONE_GUARD, "")
    else:
        raise ValueError(f"unsupported mode: {mode}")

    LOGIC_FILE.write_text(source)
    return LOGIC_FILE


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject deterministic bug into app logic")
    parser.add_argument("--mode", choices=["zero_division", "none_type"], required=True)
    args = parser.parse_args()

    changed = inject_bug(args.mode)
    print(f"Injected {args.mode} bug into {changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
