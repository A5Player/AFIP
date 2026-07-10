from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import EntryValidation, EntryValidationReport


class EntryValidationRuntime:
    """Validate an allocated GOLD# opportunity without authorizing order execution."""

    LOT_PER_UNIT = 0.01

    @staticmethod
    def _bool(value: Any, default: bool = False) -> bool:
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip().upper() in {"TRUE", "1", "YES", "READY", "APPROVED", "ALLOWED", "PASS"}
        return bool(value)

    @staticmethod
    def _integer(value: Any, default: int = 0) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return default

    def evaluate_one(self, record: Mapping[str, Any]) -> EntryValidationReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))

        raw = record.get("unit_allocations") or record.get("allocations") or ()
        if not isinstance(raw, (list, tuple)):
            raw = ()

        market_regime_ready = self._bool(record.get("market_regime_ready", record.get("market_regime_status") == "READY"), False)
        conflict_allowed = self._bool(record.get("conflict_allowed", record.get("conflict_level", "LOW") != "HIGH"), True)
        risk_allowed = self._bool(record.get("risk_allowed", True), True)
        timing_allowed = self._bool(record.get("timing_allowed", record.get("trading_allowed", True)), True)
        spread_allowed = self._bool(record.get("spread_allowed", record.get("trading_cost_allowed", True)), True)

        validations: list[EntryValidation] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            opportunity_id = str(item.get("opportunity_id", f"OPPORTUNITY_{index + 1}"))
            symbol = str(item.get("symbol", "GOLD#")).upper()
            direction = str(item.get("direction", "WAIT")).upper()
            allocated_units = self._integer(item.get("allocated_units", item.get("units", 0)))
            lot_per_unit = self._number(item.get("lot_per_unit", self.LOT_PER_UNIT), self.LOT_PER_UNIT)
            upstream_eligible = self._bool(item.get("eligible", True), True)
            trade_score_allowed = self._bool(item.get("trade_score_allowed", item.get("trade_grade", "REJECT") not in {"REJECT", ""}), upstream_eligible)
            allocation_allowed = upstream_eligible and allocated_units > 0 and lot_per_unit == self.LOT_PER_UNIT

            blocks: list[str] = []
            if symbol != "GOLD#":
                blocks.append("version1_gold_only_required")
            if direction not in {"BUY", "SELL"}:
                blocks.append("entry_direction_not_actionable")
            if not market_regime_ready:
                blocks.append("market_regime_not_ready")
            if not conflict_allowed:
                blocks.append("unresolved_conflict_blocks_entry")
            if not trade_score_allowed:
                blocks.append("trade_score_not_approved")
            if not risk_allowed:
                blocks.append("risk_policy_blocks_entry")
            if not timing_allowed:
                blocks.append("market_timing_blocks_entry")
            if not spread_allowed:
                blocks.append("spread_or_trading_cost_blocks_entry")
            if not allocation_allowed:
                blocks.append("unit_allocation_not_approved")

            approved = not blocks
            total_lot = round(allocated_units * self.LOT_PER_UNIT, 2) if approved else 0.0
            if approved:
                en = f"Entry context approved for {allocated_units} fixed unit(s); approval does not send an order."
                th = f"อนุมัติบริบทจุดเข้าสำหรับ {allocated_units} Unit คงที่ โดยการอนุมัติไม่ส่งคำสั่งซื้อขาย"
            else:
                en = "Entry context is waiting because: " + ", ".join(blocks) + "."
                th = "บริบทจุดเข้ายังรอเนื่องจาก: " + ", ".join(blocks) + ""
            validations.append(EntryValidation(
                opportunity_id=opportunity_id,
                symbol=symbol,
                direction=direction,
                allocated_units=allocated_units if approved else 0,
                lot_per_unit=self.LOT_PER_UNIT,
                total_lot=total_lot,
                market_regime_ready=market_regime_ready,
                conflict_allowed=conflict_allowed,
                trade_score_allowed=trade_score_allowed,
                risk_allowed=risk_allowed,
                timing_allowed=timing_allowed,
                spread_allowed=spread_allowed,
                allocation_allowed=allocation_allowed,
                approved=approved,
                block_reasons=tuple(blocks),
                explanation_en=en,
                explanation_th=th,
            ))

        validations.sort(key=lambda x: (not x.approved, x.opportunity_id))
        selected = next((item for item in validations if item.approved), None)
        if selected:
            status, reason = "READY", "entry_validation_ready"
            wait_en = "No entry block is active."
            wait_th = "ไม่มีเงื่อนไขบล็อกจุดเข้า"
            next_en = "Pass the approved entry context to paper/demo execution review; do not send a live order."
            next_th = "ส่งบริบทจุดเข้าที่อนุมัติไปยังการตรวจสอบ paper/demo execution และห้ามส่งคำสั่งจริง"
        else:
            status, reason = "WAITING", "entry_validation_blocked_or_incomplete"
            unique = sorted({reason for item in validations for reason in item.block_reasons})
            wait_en = "Waiting for entry requirements: " + (", ".join(unique) if unique else "no allocation candidate") + "."
            wait_th = "รอเงื่อนไขจุดเข้า: " + (", ".join(unique) if unique else "ไม่มีผู้สมัครที่ได้รับการจัดสรร")
            next_en = "Review market regime, conflict, score, risk, timing, spread, and fixed-unit allocation."
            next_th = "ตรวจสอบ Market Regime ความขัดแย้ง คะแนน ความเสี่ยง เวลา Spread และการจัดสรร Unit คงที่"

        return EntryValidationReport(
            status=status,
            reason=reason,
            validations=tuple(validations),
            selected_opportunity_id=selected.opportunity_id if selected else "NONE",
            selected_direction=selected.direction if selected else "WAIT",
            approved_units=selected.allocated_units if selected else 0,
            lot_per_unit=self.LOT_PER_UNIT,
            total_lot=selected.total_lot if selected else 0.0,
            entry_approved=selected is not None,
            waiting_reason_en=wait_en,
            waiting_reason_th=wait_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=5)).isoformat(),
            direct_execution=False,
        )
