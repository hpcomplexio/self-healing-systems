from __future__ import annotations

from pathlib import Path

from webhook.service import heal_from_payload


def test_service_known_signature_uses_fixer(monkeypatch):
    changed = [Path("/repo/app/logic.py"), Path("/repo/tests/test_compute.py")]
    monkeypatch.setattr("webhook.service.apply_fix", lambda failure: changed)

    outcome = heal_from_payload({"output": "ZeroDivisionError: division by zero"})

    assert outcome.status == "completed"
    assert outcome.patch_summary is not None
    assert len(outcome.changed_files) == 2


def test_service_unknown_signature_escalates_with_context():
    noisy = "\n".join(f"line {i}" for i in range(150))

    outcome = heal_from_payload({"output": noisy})

    assert outcome.status == "escalated"
    assert outcome.reason_code == "unknown_failure_signature"
    assert outcome.human_context is not None
    assert len(outcome.human_context["failingOutputPreview"]) == 100
