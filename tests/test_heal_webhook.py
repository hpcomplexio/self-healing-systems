from __future__ import annotations

import time

from webhook.service import HealOutcome


class _ReporterSpy:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def emit(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        return {}


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer healer-secret"}


def test_heal_known_failure_emits_attempted_then_completed(client, monkeypatch):
    monkeypatch.setenv("SELF_HEALER_TOKEN", "healer-secret")

    spy = _ReporterSpy()
    monkeypatch.setattr("app.main._reporter", lambda: spy)
    monkeypatch.setattr(
        "app.main.heal_from_payload",
        lambda payload: HealOutcome(
            status="completed",
            reason_code=None,
            human_context=None,
            patch_summary="Applied ZERO_DIVISION remediation.",
            changed_files=["app/logic.py", "tests/test_compute.py"],
        ),
    )

    response = client.post(
        "/heal",
        json={
            "correlationId": "corr-123",
            "payload": {"output": "ZeroDivisionError"},
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    assert [call["event_type"] for call in spy.calls] == [
        "heal.attempted",
        "heal.completed",
    ]


def test_heal_unknown_failure_emits_attempted_then_escalated(client, monkeypatch):
    monkeypatch.setenv("SELF_HEALER_TOKEN", "healer-secret")

    spy = _ReporterSpy()
    monkeypatch.setattr("app.main._reporter", lambda: spy)
    monkeypatch.setattr(
        "app.main.heal_from_payload",
        lambda payload: HealOutcome(
            status="escalated",
            reason_code="unknown_failure_signature",
            human_context={"summary": "Could not classify"},
            patch_summary=None,
            changed_files=[],
        ),
    )

    response = client.post(
        "/heal",
        json={
            "correlationId": "corr-456",
            "payload": {"output": "some random failure"},
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "escalated"
    assert body["reasonCode"] == "unknown_failure_signature"

    assert [call["event_type"] for call in spy.calls] == [
        "heal.attempted",
        "heal.escalated",
    ]


def test_heal_timeout_emits_timeout_escalation(client, monkeypatch):
    monkeypatch.setenv("SELF_HEALER_TOKEN", "healer-secret")
    monkeypatch.setenv("HEALER_EXECUTION_TIMEOUT_SECONDS", "0.01")

    spy = _ReporterSpy()
    monkeypatch.setattr("app.main._reporter", lambda: spy)

    def _slow_heal(payload):  # type: ignore[no-untyped-def]
        time.sleep(0.1)
        return HealOutcome(
            status="completed",
            reason_code=None,
            human_context=None,
            patch_summary="x",
            changed_files=[],
        )

    monkeypatch.setattr("app.main.heal_from_payload", _slow_heal)

    response = client.post(
        "/heal",
        json={"correlationId": "corr-timeout", "payload": {"output": "TypeError"}},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "escalated"
    assert body["reasonCode"] == "healer_timeout"
    assert [call["event_type"] for call in spy.calls] == [
        "heal.attempted",
        "heal.escalated",
    ]


def test_heal_requires_bearer_auth(client, monkeypatch):
    monkeypatch.setenv("SELF_HEALER_TOKEN", "healer-secret")

    response = client.post(
        "/heal",
        json={"correlationId": "corr-unauth", "payload": {"output": "x"}},
    )

    assert response.status_code == 401
