from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.logic import compute_ratio
from webhook import EventReporter, ReporterError, heal_from_payload

UNHEALTHY_MARKER = Path("/tmp/self_healing_force_unhealthy")


class ComputeRequest(BaseModel):
    numerator: float
    denominator: float


class HealRequest(BaseModel):
    correlationId: str
    payload: dict[str, Any]


app = FastAPI(title="Self-Healing Systems Lab")


def _require_bearer_token(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("SELF_HEALER_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})

    token = authorization.split(" ", 1)[1]
    if token != expected:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})


def _reporter() -> EventReporter:
    hub_url = os.getenv("MISSION_CONTROL_URL", "http://localhost:3000")
    token = os.getenv("MISSION_CONTROL_TOKEN", "")
    return EventReporter(base_url=hub_url, token=token)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    if UNHEALTHY_MARKER.exists():
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "reason": "simulated"},
        )
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/__simulate/unhealthy")
def simulate_unhealthy() -> dict[str, str]:
    UNHEALTHY_MARKER.write_text("1")
    return {"status": "ok", "simulation": "unhealthy_enabled"}


@app.post("/__simulate/healthy")
def simulate_healthy() -> dict[str, str]:
    if UNHEALTHY_MARKER.exists():
        UNHEALTHY_MARKER.unlink()
    return {"status": "ok", "simulation": "unhealthy_disabled"}


@app.post("/compute")
def compute(payload: ComputeRequest) -> dict[str, float]:
    try:
        result = compute_ratio(payload.numerator, payload.denominator)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_input", "message": str(exc)},
        ) from exc

    return {"result": result}


@app.post("/heal", dependencies=[Depends(_require_bearer_token)])
async def heal(payload: HealRequest) -> dict[str, Any]:
    reporter = _reporter()

    try:
        reporter.emit(
            correlation_id=payload.correlationId,
            event_type="heal.attempted",
            severity="info",
            payload={"status": "started"},
        )
    except ReporterError as exc:
        raise HTTPException(
            status_code=502,
            detail={"error": "reporting_failed", "message": str(exc)},
        ) from exc

    timeout_seconds = float(os.getenv("HEALER_EXECUTION_TIMEOUT_SECONDS", "300"))

    try:
        outcome = await asyncio.wait_for(
            asyncio.to_thread(heal_from_payload, payload.payload), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        escalation_payload = {
            "reasonCode": "healer_timeout",
            "humanContext": {
                "summary": "Healer execution exceeded timeout.",
            },
        }
        reporter.emit(
            correlation_id=payload.correlationId,
            event_type="heal.escalated",
            severity="critical",
            payload=escalation_payload,
        )
        return {"status": "escalated", **escalation_payload}

    if outcome.status == "completed":
        completion_payload = {
            "patchSummary": outcome.patch_summary,
            "changedFiles": outcome.changed_files,
        }
        reporter.emit(
            correlation_id=payload.correlationId,
            event_type="heal.completed",
            severity="info",
            payload=completion_payload,
        )
        return {"status": "completed", **completion_payload}

    escalation_payload = {
        "reasonCode": outcome.reason_code,
        "humanContext": outcome.human_context,
    }
    reporter.emit(
        correlation_id=payload.correlationId,
        event_type="heal.escalated",
        severity="warn",
        payload=escalation_payload,
    )
    return {"status": "escalated", **escalation_payload}
