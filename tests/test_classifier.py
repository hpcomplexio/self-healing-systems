from __future__ import annotations

from healer.classifier import classify_pytest_output
from healer.types import FailureType


def test_classify_zero_division():
    output = "tests/test_compute.py:10: ZeroDivisionError: division by zero"
    failure = classify_pytest_output(output)

    assert failure.failure_type == FailureType.ZERO_DIVISION
    assert failure.file == "tests/test_compute.py"
    assert failure.line == 10


def test_classify_none_type_error():
    output = "app/logic.py:6: TypeError: unsupported operand type(s) for /: 'NoneType' and 'int'"
    failure = classify_pytest_output(output)

    assert failure.failure_type == FailureType.NONE_TYPE_ERROR


def test_classify_unknown():
    failure = classify_pytest_output("something unrelated")
    assert failure.failure_type == FailureType.UNKNOWN
