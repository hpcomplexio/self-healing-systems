from __future__ import annotations


def compute_ratio(numerator: float | None, denominator: float | None) -> float:
    # GUARD_NONE_START
    if numerator is None or denominator is None:
        raise ValueError("numerator and denominator must be numbers")
    # GUARD_NONE_END
    # GUARD_ZERO_START
    if denominator == 0:
        raise ValueError("denominator must be non-zero")
    # GUARD_ZERO_END
    return numerator / denominator
