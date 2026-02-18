#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_IMAGE="${APP_IMAGE:-self-healing-lab/app}"
CHECK_CONTAINER="self-healing-promote-check"
CHECK_URL="http://localhost:18080/healthz"

cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is required but not installed."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

echo "[promote 1/4] Running full local tests"
make test

echo "[promote 2/4] Building current image: ${APP_IMAGE}:current"
docker build -t "${APP_IMAGE}:current" .

echo "[promote 3/4] Verifying health on ephemeral container"
if docker ps -a --format '{{.Names}}' | grep -q "^${CHECK_CONTAINER}$"; then
  docker rm -f "$CHECK_CONTAINER" >/dev/null
fi

docker run -d --name "$CHECK_CONTAINER" -p 18080:8000 "${APP_IMAGE}:current" >/dev/null
trap 'docker rm -f "$CHECK_CONTAINER" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 20); do
  if curl -fsS "$CHECK_URL" >/dev/null; then
    break
  fi
  sleep 1
done

curl -fsS "$CHECK_URL" >/dev/null

echo "[promote 4/4] Tagging known-good image: ${APP_IMAGE}:good"
docker tag "${APP_IMAGE}:current" "${APP_IMAGE}:good"

echo "Promoted ${APP_IMAGE}:good"
