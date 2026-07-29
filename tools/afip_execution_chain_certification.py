from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any

# Ensure the installed project root is importable when this file is executed
# directly (for example: python tools\afip_execution_chain_certification.py).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from afip.lot_authority import calculate_lot_authority

BALANCES = {"P1": 70.19, "P2": 272.10, "P3": 875.37, "P4": 17.26}


def run(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "config" / "four_profile_demo.json"
    raw = json.loads(config_path.read_text(encoding="utf-8-sig"))
    rows: list[dict[str, Any]] = []
    failures: list[str] = []

    scenarios = (
        ("DEFAULT_ONE_AT_99_7", 99.7, {}, None, None),
        ("REQUEST_THREE_AT_98_7", 98.7, {"requested_units": 3}, None, None),
        ("REQUEST_THREE_AT_99_7", 99.7, {"requested_units": 3}, None, None),
        ("RISK_CAP_ONE", 99.7, {"requested_units": 3}, 1, None),
        ("EXECUTION_CAP_ONE", 99.7, {"requested_units": 3}, None, 1),
    )

    for profile in raw["profiles"]:
        pid = str(profile["profile_id"]).upper()
        balance = BALANCES[pid]
        for name, confidence, decision, risk_units, execution_units in scenarios:
            result = calculate_lot_authority(
                profile=profile,
                decision=decision,
                confidence=confidence,
                balance=balance,
                equity=balance,
                current_orders=0,
                risk_units=risk_units,
                execution_safety_units=execution_units,
            )
            row = {"scenario": name, **result.as_dict()}
            rows.append(row)
            if result.approved_units > 3:
                failures.append(f"{pid}:{name}:approved_units_above_three")
            if any(abs(lot - 0.01) > 1e-12 for lot in result.approved_lots):
                failures.append(f"{pid}:{name}:non_001_unit_lot")
            if name == "DEFAULT_ONE_AT_99_7" and result.approved_units != 1:
                failures.append(f"{pid}:{name}:confidence_ceiling_became_target")
            if name in {"RISK_CAP_ONE", "EXECUTION_CAP_ONE"} and result.approved_units > 1:
                failures.append(f"{pid}:{name}:safety_cap_not_honored")

    zero_equity = calculate_lot_authority(
        profile=next(p for p in raw["profiles"] if p["profile_id"] == "P3"),
        decision={"requested_units": 3},
        confidence=100.0,
        balance=875.37,
        equity=0.0,
        current_orders=0,
    )
    if zero_equity.approved_units != 0 or zero_equity.available_capital != 0.0:
        failures.append("P3:ZERO_EQUITY:capital_not_fail_closed")

    report = {
        "schema_version": "afip-execution-chain-certification.v1",
        "status": "PASS" if not failures else "FAIL",
        "purpose": "Prove confidence is a ceiling, capital/risk/profile/execution gates reduce units, and no scenario automatically expands to three orders.",
        "order_send_called": False,
        "profiles": [p["profile_id"] for p in raw["profiles"]],
        "rows": rows,
        "zero_equity_case": zero_equity.as_dict(),
        "failures": failures,
    }
    output = project_root / "runtime" / "control" / "execution_chain_certification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    result = run(root)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
