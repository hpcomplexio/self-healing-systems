from __future__ import annotations

import re

from healer.types import FailureInfo, FailureType

_FILE_LINE_RE = re.compile(r"(?P<file>[\w./-]+\.py):(?P<line>\d+)")


def _extract_file_line(output: str) -> tuple[str | None, int | None]:
    match = _FILE_LINE_RE.search(output)
    if not match:
        return None, None
    return match.group("file"), int(match.group("line"))


def classify_pytest_output(output: str) -> FailureInfo:
    file, line = _extract_file_line(output)

    if "ZeroDivisionError" in output:
        return FailureInfo(
            failure_type=FailureType.ZERO_DIVISION,
            file=file,
            line=line,
            message="Detected division by zero from pytest output.",
        )

    if "TypeError" in output and "NoneType" in output:
        return FailureInfo(
            failure_type=FailureType.NONE_TYPE_ERROR,
            file=file,
            line=line,
            message="Detected NoneType arithmetic TypeError from pytest output.",
        )

    if "AssertionError" in output:
        return FailureInfo(
            failure_type=FailureType.ASSERTION_FAILURE,
            file=file,
            line=line,
            message="Detected assertion failure from pytest output.",
        )

    return FailureInfo(
        failure_type=FailureType.UNKNOWN,
        file=file,
        line=line,
        message="Could not classify pytest failure output.",
    )
