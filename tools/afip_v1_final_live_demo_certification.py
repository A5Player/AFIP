"""AFIP V1 final read-only live demo certification.

Initializes each configured MT5 terminal sequentially through the existing
account-isolation authority. Never calls order_check or order_send.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.afip_verify_account_isolation import verify

PROFILES = ("P1", "P2", "P3", "P4")
CONFIG = Path("config/four_profile_demo.json")
ISOLATION_OUTPUT = Path("runtime/account_isolation_status.json")
OUTPUT = Path("runtime/certification/afip_v1_final_live_demo_certification.json")


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


def certify() -> dict[str, Any]:
    isolation = verify(CONFIG)
    _write(ISOLATION_OUTPUT, isolation)

    indexed = {
        str(row.get("profile_id", "")).upper(): row
        for row in isolation.get("profiles", [])
        if isinstance(row, dict)
    }
    profiles: list[dict[str, Any]] = []
    errors: list[str] = list(isolation.get("errors", []))

    for profile_id in PROFILES:
        row = indexed.get(profile_id, {})
        passed = row.get("status") == "PASS"
        profile = {
            "profile_id": profile_id,
            "binding_verified": passed,
            "isolation_status": row.get("status", "MISSING"),
            "reason": row.get("reason", "exact_terminal_account_binding_verified" if passed else "binding_not_verified"),
            "configured_login": row.get("configured_login", "UNKNOWN"),
            "actual_login": row.get("actual_login", "UNKNOWN"),
            "configured_server": row.get("configured_server", "UNKNOWN"),
            "actual_server": row.get("actual_server", "UNKNOWN"),
            "configured_terminal": row.get("configured_terminal", "UNKNOWN"),
            "actual_terminal": row.get("actual_terminal", "UNKNOWN"),
            "login_match": bool(row.get("login_match", False)),
            "server_match": bool(row.get("server_match", False)),
            "terminal_match": bool(row.get("terminal_match", False)),
        }
        profiles.append(profile)
        if not passed and not any(str(error).startswith(f"{profile_id}:") for error in errors):
            errors.append(f"{profile_id}:{profile['reason']}")

    passed = not errors and all(profile["binding_verified"] for profile in profiles)
    report = {
        "schema_version": "afip-v1-final-live-demo-certification.v1",
        "status": "PASS" if passed else "BLOCKED",
        "certification": "AFIP_V1_PRODUCTION_CERTIFIED" if passed else "LIVE_BINDING_CERTIFICATION_REQUIRED",
        "mode": "READ_ONLY_NO_ORDER_SENT",
        "order_check_called": False,
        "order_send_called": False,
        "source_authority": "EXISTING_ACCOUNT_ISOLATION_RUNTIME",
        "profiles": profiles,
        "errors": errors,
    }
    _write(OUTPUT, report)
    return report


def main() -> int:
    report = certify()
    print(json.dumps(report, indent=2, default=str))
    if report["status"] == "PASS":
        print("AFIP V1 Final Live Demo Certification: PASS")
        return 0
    print("AFIP V1 Final Live Demo Certification: BLOCKED")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
