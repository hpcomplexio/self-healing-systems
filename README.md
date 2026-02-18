# Self-Healing Systems Lab

Deterministic, local-first lab that demonstrates two recovery loops:

- Code healing: inject a known bug, classify failure, apply a targeted fix, add regression coverage.
- Runtime healing: simulate unhealthy service state, restart, then rollback to a known-good image if needed.

## What This Repo Contains

- `app/`: FastAPI service with health endpoints and a small compute function.
- `healer/`: failure classifier, bug injector, and healing runner.
- `watchdog/`: runtime watchdog that performs restart and rollback actions.
- `tests/`: baseline + regression test coverage.
- `artifacts/`: generated reports and diffs from demo runs.

## Prerequisites

- Python 3.11+
- `make`
- Docker + Docker Compose plugin (`docker compose`)
- `curl`

## Quick Start

```bash
make setup
make test
make demo
```

`make demo` runs both demos in sequence:

1. `demo-code` (code self-healing)
2. `demo-runtime` (runtime self-healing)

## Command Reference

- `make setup`
  - Creates `.venv`
  - Upgrades pip
  - Installs package + dev dependencies
- `make test`
  - Runs `pytest`
- `make demo-code`
  - Injects deterministic bug (`BUG_MODE=zero_division` by default)
  - Confirms tests fail
  - Runs healer
  - Verifies tests pass
  - Writes code-healing artifacts
- `make demo-runtime`
  - Promotes a known-good image tag (`:good`)
  - Starts current runtime image (`:current`)
  - Simulates unhealthy service
  - Runs watchdog restart + rollback policy
  - Verifies recovery and writes runtime artifacts
- `make demo`
  - Runs both demos
- `make clean`
  - Removes local virtualenv and Python build/test cache

## Demo Artifacts

After `make demo-code`:

- `artifacts/pre_heal_pytest.txt`: failing test output captured after injection.
- `artifacts/healing_patch.diff`: unified diff of healer edits.
- `artifacts/incident_report.json`: structured code-healing incident report.

After `make demo-runtime`:

- `artifacts/runtime_simulation_response.json`: response from unhealthy simulation endpoint.
- `artifacts/runtime_incident_report.json`: structured runtime incident report.
- `artifacts/runtime_post_heal_healthz.json`: health response after watchdog actions.

## Code Healing Flow

1. `healer.injector` removes a guard from `app/logic.py`.
2. Test suite fails with a deterministic error signature.
3. `healer.classifier` maps output to a known failure type.
4. `healer.fixers` restores logic guard and appends a regression test.
5. `healer.runner` writes patch/report artifacts and re-runs tests.

Supported injected failures:

- `zero_division`
- `none_type`

Use an alternate mode:

```bash
make demo-code BUG_MODE=none_type
```

## Runtime Healing Flow

1. Build and tag known-good image (`<APP_IMAGE>:good`).
2. Start current image (`<APP_IMAGE>:current`) via Docker Compose.
3. Force `/healthz` to return `503` using `/__simulate/unhealthy`.
4. Watchdog waits for threshold failures, then:
   - restarts service
   - if still unhealthy, rolls back to `:good`
5. Watchdog emits runtime incident report.

## API Endpoints (for local inspection)

- `GET /healthz` -> health status (`200` healthy, `503` simulated unhealthy)
- `GET /readyz` -> readiness status
- `POST /compute` -> compute ratio with input validation
- `POST /__simulate/unhealthy` -> enable unhealthy mode
- `POST /__simulate/healthy` -> disable unhealthy mode

## Running the App Manually

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then call:

```bash
curl -fsS http://localhost:8000/healthz
```

## Troubleshooting

- `docker compose` not found:
  - Install/enable Docker Compose v2 plugin.
- `make demo-runtime` fails waiting for health:
  - Check service logs: `docker compose -f docker-compose.yml logs --tail=80 app`
- Healer reports unsupported failure type:
  - This lab only auto-heals predefined deterministic failure classes.

## Notes

- This repo is intentionally deterministic and scoped for demonstration, not autonomous general-purpose repair.
- Runtime simulation uses a marker file at `/tmp/self_healing_force_unhealthy` inside the app environment.
