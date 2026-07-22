"""Run exactly one AFIP demo execution cycle for one profile.

This worker is intentionally short-lived. A fresh Python process owns exactly
one MetaTrader5 terminal binding, then exits. This prevents the process-global
MetaTrader5 module from retaining the previous profile's terminal session.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from afip.demo_execution_gateway import DemoExecutionGateway, DemoProfilePolicy
from afip.four_profile_operations.runtime import FourProfileOperationalRuntime

CONFIG = Path("config/four_profile_demo.json")


def run_once(profile_id: str, config_path: Path = CONFIG) -> dict:
    wanted = profile_id.strip().upper()
    raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
    raw_profile = next(
        (item for item in raw.get("profiles", []) if str(item.get("profile_id", "")).upper() == wanted),
        None,
    )
    profile = next(
        (item for item in FourProfileOperationalRuntime(config_path).load() if item.profile_id == wanted),
        None,
    )
    if raw_profile is None or profile is None:
        raise ValueError(f"profile_not_found:{wanted}")
    if not profile.enabled:
        return {"profile_id": wanted, "status": "SKIPPED", "reason": "profile_disabled"}
    if not profile.execution_enabled:
        return {
            "profile_id": wanted,
            "status": "RESEARCH_ONLY",
            "reason": "profile_execution_disabled_research_preserved",
        }

    policy = DemoProfilePolicy.from_mapping(raw_profile)
    return DemoExecutionGateway(profile, policy).run_cycle().as_dict()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True)
    parser.add_argument("--config", default=str(CONFIG))
    args = parser.parse_args()
    try:
        report = run_once(args.profile, Path(args.config))
        print(json.dumps(report, sort_keys=True, default=str), flush=True)
        return 0
    except Exception as exc:
        print(json.dumps({
            "profile_id": args.profile.upper(),
            "status": "ERROR",
            "reason": f"single_profile_worker_error:{type(exc).__name__}:{exc}",
        }, sort_keys=True), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
