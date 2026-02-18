from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureType(str, Enum):
    ZERO_DIVISION = "ZERO_DIVISION"
    NONE_TYPE_ERROR = "NONE_TYPE_ERROR"
    ASSERTION_FAILURE = "ASSERTION_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FailureInfo:
    failure_type: FailureType
    file: str | None = None
    line: int | None = None
    message: str | None = None
