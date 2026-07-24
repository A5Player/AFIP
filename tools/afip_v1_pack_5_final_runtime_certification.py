"""Read-only final runtime certification for AFIP V1 Pack 5."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

PROFILES = ("P1", "P2", "P3", "P4")

def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}

def certify(root: Path = Path(".")) -> dict[str, Any]:
    config = load(root / "config/four_profile_demo.json")
    rows = {str(x.get("profile_id", "")).upper(): x for x in config.get("profiles", []) if isinstance(x, dict)}
    errors: list[str] = []
    terminals: set[str] = set(); accounts: set[tuple[str, str]] = set()
    for pid in PROFILES:
        row = rows.get(pid)
        if not row:
            errors.append(f"{pid}:missing_profile"); continue
        terminal = str(row.get("mt5_terminal", "")).replace("/", "\\").rstrip("\\").casefold()
        account = (str(row.get("server", "")).casefold(), str(row.get("login_env", "")).casefold())
        if not terminal: errors.append(f"{pid}:missing_terminal")
        if terminal in terminals: errors.append(f"{pid}:duplicate_terminal")
        if account in accounts: errors.append(f"{pid}:duplicate_account_authority")
        terminals.add(terminal); accounts.add(account)
    isolation = load(root / "runtime/account_isolation_status.json")
    iso_rows = {str(x.get("profile_id", "")).upper(): x for x in isolation.get("profiles", []) if isinstance(x, dict)}
    live = []
    for pid in PROFILES:
        state = load(root / f"runtime/profiles/{pid.lower()}/demo_execution_state.json")
        iso = iso_rows.get(pid, {})
        verified = bool(state.get("binding_verified", False)) or iso.get("status") == "PASS"
        live.append({"profile_id": pid, "binding_verified": verified, "isolation_status": iso.get("status", "NOT_RUN")})
    source = (root / "afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    protection = (root / "afip/protection/sl_tp_planner.py").read_text(encoding="utf-8")
    if "exact_profile_binding_mismatch" not in source: errors.append("missing_exact_binding_authority")
    if "binding_verified=True" not in source: errors.append("missing_binding_verified_success_state")
    if "legacy_sl_points" in protection or "legacy_tp_points" in protection: errors.append("legacy_sl_tp_execution_authority_present")
    live_pass = all(x["binding_verified"] for x in live)
    status = "PASS" if not errors and live_pass else ("READY_FOR_LIVE_CERTIFICATION" if not errors else "FAIL")
    report = {"status": status, "source_certification": "PASS" if not errors else "FAIL", "live_binding_certification": "PASS" if live_pass else "PENDING", "profiles": live, "errors": errors}
    out = root / "runtime/certification/afip_v1_pack_5_final_runtime_certification.json"
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

def main() -> int:
    report = certify()
    print(json.dumps(report, indent=2))
    return 1 if report["status"] == "FAIL" else 0

if __name__ == "__main__": raise SystemExit(main())
