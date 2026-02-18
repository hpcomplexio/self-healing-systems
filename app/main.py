from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.logic import compute_ratio

UNHEALTHY_MARKER = Path("/tmp/self_healing_force_unhealthy")


class ComputeRequest(BaseModel):
    numerator: float
    denominator: float


app = FastAPI(title="Self-Healing Systems Lab")


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
