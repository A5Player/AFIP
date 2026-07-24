from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "four_profile_demo.json"
GATEWAY = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
PLANNER = ROOT / "afip" / "protection" / "sl_tp_planner.py"


def main() -> int:
    errors: list[str] = []
    raw = json.loads(CONFIG.read_text(encoding="utf-8-sig"))
    profiles = [p for p in raw.get("profiles", []) if p.get("enabled") and p.get("execution_enabled")]
    seen_terminal: set[str] = set()
    seen_account: set[tuple[str, str]] = set()
    for p in profiles:
        pid = str(p.get("profile_id", "")).upper()
        terminal = str(p.get("mt5_terminal", "")).replace("/", "\\").rstrip("\\").casefold()
        account = (str(p.get("server", "")).casefold(), str(p.get("login_env", "")).casefold())
        if pid not in {"P1", "P2", "P3", "P4"}: errors.append(f"invalid_profile:{pid}")
        if terminal in seen_terminal: errors.append(f"duplicate_terminal:{pid}")
        if account in seen_account: errors.append(f"duplicate_account_binding:{pid}")
        seen_terminal.add(terminal); seen_account.add(account)
        if not p.get("demo_execution_enabled"): errors.append(f"demo_disabled:{pid}")
        if p.get("live_execution") is True: errors.append(f"live_execution_true:{pid}")
        if float(p.get("lot_per_unit", 0)) != 0.01: errors.append(f"lot_per_unit_invalid:{pid}")
    gateway = GATEWAY.read_text(encoding="utf-8")
    planner = PLANNER.read_text(encoding="utf-8")
    required = ["account_routing.lock", "_repair_exact_binding(mt5)", "binding_verified=True", "exact_profile_binding_mismatch"]
    errors.extend(f"missing_gateway_contract:{x}" for x in required if x not in gateway)
    if "stop_loss_points: float | None = None" not in planner or "take_profit_points: float | None = None" not in planner:
        errors.append("legacy_sl_tp_defaults_reachable")
    result = {"status": "PASS" if not errors else "FAIL", "profiles": [p.get("profile_id") for p in profiles], "errors": errors}
    out = ROOT / "runtime" / "certification" / "afip_v1_pack_4_demo_execution_certification.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
