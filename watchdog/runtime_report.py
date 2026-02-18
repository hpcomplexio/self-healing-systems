from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = ROOT / "artifacts"
RUNTIME_INCIDENT_FILE = ARTIFACTS_DIR / "runtime_incident_report.json"


def write_runtime_incident(payload: dict[str, Any]) -> Path:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    content = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **payload,
    }
    RUNTIME_INCIDENT_FILE.write_text(json.dumps(content, indent=2) + "\n")
    return RUNTIME_INCIDENT_FILE
