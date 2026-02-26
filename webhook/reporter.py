from __future__ import annotations

import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx


class ReporterError(RuntimeError):
    pass


@dataclass
class EventReporter:
    base_url: str
    token: str
    timeout_seconds: float = 5.0
    max_attempts: int = 3

    def emit(
        self,
        *,
        correlation_id: str,
        event_type: str,
        severity: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        event_id = _new_event_id()
        envelope = {
            "id": event_id,
            "schemaVersion": "1.0.0",
            "eventVersion": 1,
            "source": "self-healing-systems",
            "type": event_type,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "correlationId": correlation_id,
            "payload": payload,
        }

        url = self.base_url.rstrip("/") + "/events"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Idempotency-Key": event_id,
        }

        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            try:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.post(url, json=envelope, headers=headers)

                if response.status_code >= 500:
                    raise ReporterError(f"Server error from mission-control: {response.status_code}")
                response.raise_for_status()
                return envelope
            except (httpx.HTTPError, ReporterError) as exc:
                last_error = exc
                if attempt == self.max_attempts - 1:
                    break

                base_delay = _base_delay_seconds(attempt)
                jitter = random.uniform(0.8, 1.2)
                time.sleep(base_delay * jitter)

        raise ReporterError(f"Failed to report event after retries: {last_error}")


def _base_delay_seconds(attempt: int) -> float:
    schedule = [0.5, 1.0, 2.0]
    return schedule[min(attempt, len(schedule) - 1)]


def _new_event_id() -> str:
    uuid7 = getattr(uuid, "uuid7", None)
    if callable(uuid7):
        return str(uuid7())
    return str(uuid.uuid4())
