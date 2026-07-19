from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_step(name: str, command: list[str], timeout_seconds: int) -> dict[str, Any]:
    started = utc_now()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env={**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        return {
            "name": name,
            "status": "PASS" if completed.returncode == 0 else "FAILED",
            "return_code": completed.returncode,
            "started_at": started,
            "finished_at": utc_now(),
            "timeout_seconds": timeout_seconds,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "status": "TIMEOUT",
            "return_code": DATA_UNAVAILABLE,
            "started_at": started,
            "finished_at": utc_now(),
            "timeout_seconds": timeout_seconds,
            "stdout": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-12000:] if isinstance(exc.stderr, str) else "",
        }
    except Exception as exc:
        return {
            "name": name,
            "status": "ERROR",
            "return_code": DATA_UNAVAILABLE,
            "started_at": started,
            "finished_at": utc_now(),
            "timeout_seconds": timeout_seconds,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP bounded one-shot final research orchestration")
    parser.add_argument("--collector-timeout", type=int, default=900)
    parser.add_argument("--dashboard-timeout", type=int, default=180)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()

    steps: list[dict[str, Any]] = []
    if not args.skip_tests:
        steps.append(run_step(
            "pack_regression",
            [sys.executable, "-m", "pytest", "tests/test_phase_u_pack_3_4_9.py", "tests/test_phase_u_pack_3_4_10.py", "tests/test_phase_u_final_research.py", "-q"],
            300,
        ))
        if steps[-1]["status"] != "PASS":
            return write_summary(steps)

    steps.append(run_step(
        "one_shot_research",
        [sys.executable, "tools/afip_phase_u_pack_3_4_10_collector.py", "--root", ".", "--once"],
        max(60, args.collector_timeout),
    ))

    # Dashboard generation is useful even when a data provider times out: it must
    # show DATA_UNAVAILABLE/TIMEOUT rather than fake READY values.
    steps.append(run_step(
        "dashboard_generation",
        [sys.executable, "-m", "afip.dashboard_ui"],
        max(60, args.dashboard_timeout),
    ))
    return write_summary(steps)


def write_summary(steps: list[dict[str, Any]]) -> int:
    overall = "PASS" if all(step["status"] == "PASS" for step in steps) else "PARTIAL"
    summary = {
        "schema_version": "phase_u_final_integration_v1",
        "generated_at": utc_now(),
        "status": overall,
        "execution_authority": False,
        "research_mode": "ONE_SHOT_BOUNDED",
        "steps": steps,
    }
    output = ROOT / "runtime" / "research" / "final_research_run.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if overall == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
