from __future__ import annotations

import argparse
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from watchdog.runtime_report import write_runtime_incident

ROOT = Path(__file__).resolve().parents[1]


def is_healthy(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:  # nosec B310
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def run_compose(compose_file: Path, args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command = ["docker", "compose", "-f", str(compose_file), *args]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(command, capture_output=True, text=True, check=False, env=merged_env)


def image_exists(tag: str) -> bool:
    result = subprocess.run(
        ["docker", "image", "inspect", tag],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Runtime watchdog with restart and rollback")
    parser.add_argument("--health-url", default="http://localhost:8000/healthz")
    parser.add_argument("--compose-file", default=str(ROOT / "docker-compose.yml"))
    parser.add_argument("--service", default="app")
    parser.add_argument("--interval", type=int, default=5)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--cooldown", type=int, default=20)
    parser.add_argument("--image-base", default="self-healing-lab/app")
    parser.add_argument("--max-cycles", type=int, default=20)
    args = parser.parse_args()

    compose_file = Path(args.compose_file)
    consecutive_failures = 0
    actions: list[str] = []
    status = "no_action"
    recovered = False

    for _ in range(args.max_cycles):
        healthy = is_healthy(args.health_url)
        if healthy:
            if actions:
                recovered = True
                status = "healed"
                break
            time.sleep(args.interval)
            continue

        consecutive_failures += 1
        if consecutive_failures < args.threshold:
            time.sleep(args.interval)
            continue

        restart = run_compose(compose_file, ["restart", args.service])
        actions.append("restart")
        time.sleep(args.cooldown)

        if is_healthy(args.health_url):
            recovered = True
            status = "healed_after_restart"
            break

        good_tag = f"{args.image_base}:good"
        if not image_exists(good_tag):
            status = "rollback_unavailable"
            break

        rollback = run_compose(
            compose_file,
            ["up", "-d", "--force-recreate", args.service],
            env={"APP_IMAGE": args.image_base, "IMAGE_TAG": "good"},
        )
        actions.append("rollback")
        time.sleep(args.cooldown)

        if is_healthy(args.health_url):
            recovered = True
            status = "healed_after_rollback"
        else:
            status = "failed_after_rollback"
        _ = restart, rollback
        break

    report_path = write_runtime_incident(
        {
            "status": status,
            "health_url": args.health_url,
            "actions": actions,
            "recovered": recovered,
            "rollback_available": image_exists(f"{args.image_base}:good"),
            "consecutive_failure_threshold": args.threshold,
            "interval_seconds": args.interval,
            "cooldown_seconds": args.cooldown,
        }
    )

    print(f"Runtime incident report written to {report_path}")
    return 0 if recovered else 1


if __name__ == "__main__":
    raise SystemExit(main())
