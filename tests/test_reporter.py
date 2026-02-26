from __future__ import annotations

import pytest

from webhook.reporter import EventReporter, ReporterError


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("http error")


class _FakeClient:
    attempts = 0
    seen_headers: list[dict[str, str]] = []
    seen_timeout = None

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        _FakeClient.seen_timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, json, headers):  # type: ignore[no-untyped-def]
        _FakeClient.attempts += 1
        _FakeClient.seen_headers.append(headers)
        if _FakeClient.attempts < 3:
            return _FakeResponse(500)
        return _FakeResponse(200)


def test_reporter_retries_with_auth_and_timeout(monkeypatch):
    monkeypatch.setattr("webhook.reporter.httpx.Client", _FakeClient)
    monkeypatch.setattr("webhook.reporter.time.sleep", lambda _: None)

    reporter = EventReporter(
        base_url="http://mission-control:3000",
        token="mission-token",
        timeout_seconds=5.0,
        max_attempts=3,
    )

    envelope = reporter.emit(
        correlation_id="corr-1",
        event_type="heal.attempted",
        severity="info",
        payload={"status": "started"},
    )

    assert envelope["type"] == "heal.attempted"
    assert _FakeClient.attempts == 3
    assert _FakeClient.seen_timeout == 5.0
    assert _FakeClient.seen_headers[0]["Authorization"] == "Bearer mission-token"
    assert "Idempotency-Key" in _FakeClient.seen_headers[0]


def test_reporter_raises_after_retry_budget(monkeypatch):
    class _Always500Client(_FakeClient):
        attempts = 0

        def post(self, url, json, headers):  # type: ignore[no-untyped-def]
            _Always500Client.attempts += 1
            return _FakeResponse(500)

    monkeypatch.setattr("webhook.reporter.httpx.Client", _Always500Client)
    monkeypatch.setattr("webhook.reporter.time.sleep", lambda _: None)

    reporter = EventReporter(
        base_url="http://mission-control:3000",
        token="mission-token",
        timeout_seconds=5.0,
        max_attempts=3,
    )

    with pytest.raises(ReporterError):
        reporter.emit(
            correlation_id="corr-2",
            event_type="heal.completed",
            severity="info",
            payload={"patchSummary": "x", "changedFiles": []},
        )

    assert _Always500Client.attempts == 3
