from __future__ import annotations

import pytest

from app.logic import compute_ratio


def test_compute_success(client):
    response = client.post("/compute", json={"numerator": 8, "denominator": 2})

    assert response.status_code == 200
    assert response.json() == {"result": 4.0}


def test_compute_bad_input_explicit_error_payload(client):
    response = client.post("/compute", json={"numerator": 8, "denominator": 0})

    assert response.status_code == 400
    assert response.json() == {
        "detail": {
            "error": "invalid_input",
            "message": "denominator must be non-zero",
        }
    }


def test_logic_zero_denominator_raises_value_error():
    with pytest.raises(ValueError, match="non-zero"):
        compute_ratio(8, 0)


def test_logic_none_input_raises_value_error():
    with pytest.raises(ValueError, match="must be numbers"):
        compute_ratio(None, 2)
def test_logic_zero_division_regression():
    from app.logic import compute_ratio

    try:
        compute_ratio(1, 0)
    except ValueError as exc:
        assert "denominator must be non-zero" in str(exc)
    else:
        raise AssertionError("Expected ValueError for zero denominator")
def test_logic_none_type_regression():
    from app.logic import compute_ratio

    try:
        compute_ratio(None, 2)
    except ValueError as exc:
        assert "must be numbers" in str(exc)
    else:
        raise AssertionError("Expected ValueError for None input")
