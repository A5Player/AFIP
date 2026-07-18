from __future__ import annotations
import json, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = Path(__file__).resolve().parents[1] / "patch_payload"
BACKUP = ROOT / "runtime" / "patch_backups" / "milestone_s_cleanup_pack_4_1"


def backup(path: Path) -> None:
    if path.exists():
        target = BACKUP / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one source match, found {count}")
    return text.replace(old, new, 1)


def tiers_p1(max_cents: int) -> list[dict]:
    rows = [{"minimum_balance": 0, "lots": [0.01]}, {"minimum_balance": 100, "lots": [0.01, 0.01]}, {"minimum_balance": 300, "lots": [0.01, 0.01, 0.01]}]
    for cents in range(2, max_cents + 1):
        threshold = 150 * cents * (cents + 1)
        lot = round(cents / 100, 2)
        rows.append({"minimum_balance": threshold, "lots": [lot, lot, lot]})
    return rows


def tiers_p3(max_cents: int) -> list[dict]:
    rows = [{"minimum_balance": 0, "lots": [0.01]}, {"minimum_balance": 100, "lots": [0.01, 0.01]}, {"minimum_balance": 300, "lots": [0.01, 0.01, 0.01]}]
    for cents in range(2, max_cents + 1):
        threshold = 450 * cents
        lot = round(cents / 100, 2)
        rows.append({"minimum_balance": threshold, "lots": [lot, lot, lot]})
    return rows


def main() -> int:
    required = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
    if not required.exists():
        print(f"ERROR: AFIP root not detected: {ROOT}")
        return 2
    BACKUP.mkdir(parents=True, exist_ok=True)

    for rel in [
        Path("afip/protection/adaptive_rr_portfolio.py"),
        Path("afip/execution/protected_simulation_order_builder.py"),
        Path("tests/test_milestone_s_cleanup_pack_4_1.py"),
    ]:
        target = ROOT / rel
        backup(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PAYLOAD / rel, target)

    gateway_path = required
    backup(gateway_path)
    text = gateway_path.read_text(encoding="utf-8")

    old = '            protection = order.get("protection", {})\n'
    new = '            protection = order.get("protection", {})\n            protection_portfolio = order.get("protection_portfolio", {})\n'
    text = replace_once(text, old, new, "portfolio_read")

    old = '''            allocation_lots = growth.available_lots
            units = sum(max(1, int(round(lot / 0.01))) for lot in allocation_lots)
'''
    new = '''            confidence_unit_cap = 0 if confidence < 98.0 else 1 if confidence < 98.5 else 2 if confidence < 99.5 else 3
            allocation_lots = tuple(growth.available_lots[:confidence_unit_cap])
            units = len(allocation_lots)
'''
    text = replace_once(text, old, new, "confidence_allocation_cap")

    old = '''            fingerprint = hashlib.sha256(f"{action}|{confidence:.4f}|{sl_points:.2f}|{tp_points:.2f}".encode()).hexdigest()
'''
    new = '''            rr_plans = tuple(protection_portfolio.get("unit_plans", ()))
            if rr_plans and len(rr_plans) < len(allocation_lots):
                return self._report("BLOCKED", "rr_protection_plan_count_insufficient", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, **allocation_diagnostics)
            fingerprint = hashlib.sha256(f"{self.profile.profile_id}|{action}|{confidence:.4f}|{sl_points:.2f}|{tp_points:.2f}".encode()).hexdigest()
'''
    text = replace_once(text, old, new, "profile_isolated_fingerprint")

    old = '''            tickets: list[int] = []
            for volume in allocation_lots:
                request = self._request(mt5, action, sl_points, tp_points, volume)
'''
    new = '''            tickets: list[int] = []
            for order_index, volume in enumerate(allocation_lots):
                unit_plan = rr_plans[order_index] if rr_plans else protection
                unit_sl_points = float(unit_plan.get("stop_loss_points", sl_points) or sl_points)
                unit_tp_points = float(unit_plan.get("take_profit_points", tp_points) or tp_points)
                if unit_sl_points <= 0 or unit_tp_points <= 0:
                    return self._report("BLOCKED", "rr_unit_protection_missing", account_trade_mode="DEMO", demo_verified=True, decision_action=action, decision_confidence=confidence, sent_units=len(tickets), **allocation_diagnostics, tickets=tuple(tickets), **execution_diagnostics)
                request = self._request(mt5, action, unit_sl_points, unit_tp_points, volume)
                request["comment"] = f"AFIP {self.profile.profile_id} {unit_plan.get('role', 'RR')}"
'''
    text = replace_once(text, old, new, "per_order_rr_plan")
    gateway_path.write_text(text, encoding="utf-8", newline="\n")

    config_path = ROOT / "config" / "four_profile_demo.json"
    backup(config_path)
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    config["version"] = "AFIP-1.0-MILESTONE-S-CLEANUP-PACK-4.1"
    for profile in config["profiles"]:
        pid = str(profile["profile_id"]).upper()
        profile["minimum_confidence"] = 98.0
        profile["lot_per_unit"] = 0.01
        if pid == "P1":
            profile.update(allocation_mode="CAPITAL_TIER_TABLE", maximum_units=3, maximum_concurrent_orders=3, maximum_lot_per_order=0.10, capital_tiers=tiers_p1(10))
        elif pid == "P2":
            profile.update(allocation_mode="CAPITAL_TIER_TABLE", maximum_units=3, maximum_concurrent_orders=3, maximum_lot_per_order=1.00, capital_tiers=tiers_p1(100))
        elif pid == "P3":
            profile.update(allocation_mode="CAPITAL_TIER_TABLE", maximum_units=3, maximum_concurrent_orders=3, maximum_lot_per_order=10.00, capital_tiers=tiers_p3(1000))
        elif pid == "P4":
            profile.update(allocation_mode="RESEARCH_FIXED_001", maximum_units=0, maximum_concurrent_orders=0, maximum_lot_per_order=0.01, capital_tiers=[])
            profile["research_unit_policy"] = {
                "lot_growth_enabled": False,
                "lot_per_order": 0.01,
                "scenario_units_unlimited": True,
                "distinct_rr_and_sl_plans": True,
                "operational_emergency_ceiling_env": "AFIP_P4_RESEARCH_ORDER_CEILING",
            }
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    marker = ROOT / "runtime" / "architecture_cleanup_pack_4_1" / "patch_result.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({
        "status": "PATCH_APPLIED_EXECUTION_REMAINS_STOPPED",
        "pack": "MILESTONE_S_CLEANUP_PACK_4_1",
        "rr_definition": "reward_distance / initial_risk_distance",
        "profiles_can_share_entry": ["P1", "P2", "P3"],
        "cross_profile_duplicate_blocking": False,
        "per_unit_rr_roles": ["RR_NEAR", "RR_CORE", "RR_RUNNER"],
    }, indent=2), encoding="utf-8")
    print("AFIP Milestone S Cleanup Pack 4.1 applied.")
    print("Execution remains stopped. Run focused and full regression tests before arming demo execution.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
