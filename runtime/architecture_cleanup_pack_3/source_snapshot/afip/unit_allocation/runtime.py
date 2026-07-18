from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import UnitAllocation, UnitAllocationReport


class UnitAllocationRuntime:
    """Allocate fixed 0.01-lot units after trade scoring without authorizing execution."""

    LOT_PER_UNIT = 0.01
    PROFILE_DEFAULTS = {
        "CONSERVATIVE": (1000.0, 3),
        "BALANCED": (500.0, 3),
        "GROWTH": (200.0, 3),
        "RESEARCH": (200.0, 3),
    }
    GRADE_CAPS = {"A+": 3, "A": 2, "B": 1, "C": 1, "REJECT": 0}

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _integer(value: Any, default: int = 0) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def evaluate_one(self, record: Mapping[str, Any]) -> UnitAllocationReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))

        profile_name = str(record.get("profile_name", "Balanced")).strip() or "Balanced"
        profile_key = profile_name.upper()
        default_capital_per_unit, default_max_units = self.PROFILE_DEFAULTS.get(profile_key, (500.0, 3))
        capital_per_unit = self._number(record.get("capital_per_unit", default_capital_per_unit), default_capital_per_unit)
        profile_max_units = self._integer(record.get("maximum_units", record.get("profile_max_units", default_max_units)), default_max_units)
        available_capital = self._number(record.get("available_capital", record.get("equity", record.get("balance", 0.0))), 0.0)
        risk_allowed = bool(record.get("risk_allowed", True))

        raw = record.get("trade_scores") or record.get("scores") or ()
        if not isinstance(raw, (list, tuple)):
            raw = ()
        allocations: list[UnitAllocation] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            opportunity_id = str(item.get("opportunity_id", f"OPPORTUNITY_{index + 1}"))
            symbol = str(item.get("symbol", "GOLD#")).upper()
            direction = str(item.get("direction", "WAIT")).upper()
            grade = str(item.get("grade", "REJECT")).upper()
            trade_score = self._number(item.get("final_score", item.get("trade_score", 0.0)))
            upstream_eligible = bool(item.get("eligible", True))
            score_max_units = self.GRADE_CAPS.get(grade, 0)
            capital_max_units = int(available_capital // capital_per_unit) if capital_per_unit > 0 else 0
            units = min(profile_max_units, score_max_units, capital_max_units)
            eligible = symbol == "GOLD#" and direction in {"BUY", "SELL"} and upstream_eligible and risk_allowed and units > 0
            if not eligible:
                units = 0
            if symbol != "GOLD#":
                en, th = "Version 1 supports GOLD# only.", "เวอร์ชัน 1 รองรับเฉพาะ GOLD#"
            elif direction not in {"BUY", "SELL"}:
                en, th = "Direction is not actionable.", "ทิศทางยังไม่พร้อมใช้งาน"
            elif not upstream_eligible:
                en, th = "Trade scoring did not approve this candidate.", "การให้คะแนนการซื้อขายยังไม่อนุมัติผู้สมัครนี้"
            elif not risk_allowed:
                en, th = "Risk policy blocks unit allocation.", "นโยบายความเสี่ยงบล็อกการจัดสรร Unit"
            elif capital_per_unit <= 0:
                en, th = "Capital per unit must be positive.", "เงินทุนต่อ Unit ต้องมากกว่าศูนย์"
            elif capital_max_units <= 0:
                en, th = "Available capital is below one unit requirement.", "เงินทุนที่มีต่ำกว่าข้อกำหนดสำหรับ 1 Unit"
            elif score_max_units <= 0:
                en, th = "Trade grade does not permit any unit.", "เกรดการซื้อขายไม่อนุญาต Unit"
            else:
                en = f"Allocated {units} unit(s) at fixed 0.01 lot per unit; allocation does not authorize execution."
                th = f"จัดสรร {units} Unit โดยแต่ละ Unit คงที่ 0.01 lot และการจัดสรรไม่ใช่การอนุญาตให้ส่งคำสั่ง"
            allocations.append(UnitAllocation(
                opportunity_id=opportunity_id, symbol=symbol, direction=direction,
                trade_grade=grade, trade_score=round(trade_score, 4), profile_name=profile_name,
                capital_per_unit=round(capital_per_unit, 2), available_capital=round(available_capital, 2),
                profile_max_units=profile_max_units, score_max_units=score_max_units,
                capital_max_units=capital_max_units, allocated_units=units,
                lot_per_unit=self.LOT_PER_UNIT, total_lot=round(units * self.LOT_PER_UNIT, 2),
                eligible=eligible, explanation_en=en, explanation_th=th,
            ))
        allocations.sort(key=lambda x: (not x.eligible, -x.trade_score, x.opportunity_id))
        selected = next((x for x in allocations if x.eligible), None)
        if selected:
            status, reason = "READY", "unit_allocation_ready"
            next_en = f"Pass {selected.opportunity_id} with {selected.allocated_units} fixed unit(s) to Entry Validation; allocation does not authorize execution."
            next_th = f"ส่ง {selected.opportunity_id} พร้อม {selected.allocated_units} Unit คงที่ไปยังการตรวจสอบจุดเข้า โดยการจัดสรรไม่ใช่การอนุญาตให้ส่งคำสั่ง"
        else:
            status, reason = "WAITING", "no_eligible_unit_allocation"
            next_en = "Wait for sufficient score, risk approval, profile capacity, and capital for at least one fixed unit."
            next_th = "รอคะแนน การอนุมัติความเสี่ยง ความจุโปรไฟล์ และเงินทุนที่เพียงพอสำหรับอย่างน้อย 1 Unit คงที่"
        return UnitAllocationReport(
            status=status, reason=reason, allocations=tuple(allocations),
            selected_opportunity_id=selected.opportunity_id if selected else "NONE",
            selected_direction=selected.direction if selected else "WAIT",
            allocated_units=selected.allocated_units if selected else 0,
            lot_per_unit=self.LOT_PER_UNIT, total_lot=selected.total_lot if selected else 0.0,
            profile_name=profile_name, expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=10)).isoformat(),
            direct_execution=False,
        )
