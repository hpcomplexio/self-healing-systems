PYTHON ?= python3
VENV ?= .venv
BIN := $(VENV)/bin
BUG_MODE ?= zero_division
APP_IMAGE ?= self-healing-lab/app

.PHONY: setup test demo-code demo-runtime demo clean

setup:
	@echo "[1/3] Creating virtual environment"
	$(PYTHON) -m venv $(VENV)
	@echo "[2/3] Upgrading pip"
	$(BIN)/python -m pip install --upgrade pip
	@echo "[3/3] Installing project + dev dependencies"
	$(BIN)/python -m pip install -e ".[dev]"

test:
	@echo "[1/1] Running test suite"
	$(BIN)/python -m pytest

demo-code:
	@echo "[1/5] Injecting deterministic bug ($(BUG_MODE))"
	$(BIN)/python -m healer.injector --mode $(BUG_MODE)
	@echo "[2/5] Running tests to confirm failure"
	@set +e; \
	$(BIN)/python -m pytest > artifacts/pre_heal_pytest.txt 2>&1; \
	code=$$?; \
	set -e; \
	cat artifacts/pre_heal_pytest.txt; \
	if [ $$code -eq 0 ]; then \
		echo "Expected tests to fail after injection, but they passed."; \
		exit 1; \
	fi
	@echo "[3/5] Running healer"
	$(BIN)/python -m healer.runner
	@echo "[4/5] Running full tests after healing"
	$(BIN)/python -m pytest
	@echo "[5/5] Artifact summary"
	@ls -l artifacts/healing_patch.diff artifacts/incident_report.json

demo-runtime:
	@echo "[1/6] Promoting known-good image"
	APP_IMAGE=$(APP_IMAGE) ./scripts/promote_good_image.sh
	@echo "[2/6] Building and starting current runtime"
	APP_IMAGE=$(APP_IMAGE) IMAGE_TAG=current docker compose -f docker-compose.yml up -d --build app
	@echo "[3/7] Waiting for app to become healthy"
	@set +e; \
	ready=0; \
	for i in $$(seq 1 30); do \
		if curl -fsS http://localhost:8000/healthz >/dev/null; then \
			ready=1; \
			break; \
		fi; \
		sleep 1; \
	done; \
	set -e; \
	if [ $$ready -ne 1 ]; then \
		echo "App did not become healthy in time. Recent app logs:"; \
		APP_IMAGE=$(APP_IMAGE) IMAGE_TAG=current docker compose -f docker-compose.yml logs --tail=80 app || true; \
		exit 1; \
	fi
	@echo "[4/7] Simulating unhealthy runtime"
	curl -fsS -X POST http://localhost:8000/__simulate/unhealthy > artifacts/runtime_simulation_response.json
	@echo "[5/7] Running watchdog (restart then rollback if needed)"
	$(BIN)/python -m watchdog.watchdog --compose-file docker-compose.yml --service app --image-base $(APP_IMAGE)
	@echo "[6/7] Verifying post-heal health"
	curl -fsS http://localhost:8000/healthz > artifacts/runtime_post_heal_healthz.json
	@echo "[7/7] Artifact summary"
	@ls -l artifacts/runtime_incident_report.json artifacts/runtime_post_heal_healthz.json

demo: demo-code demo-runtime

clean:
	rm -rf $(VENV) .pytest_cache self_healing_systems.egg-info
