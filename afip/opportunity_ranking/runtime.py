from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import OpportunityCandidate, OpportunityRankingReport


class OpportunityRankingRuntime:
    """Ranks review candidates after regime, consensus, conflict, risk, and cost gates."""

    WEIGHTS = {
        "regime": 0.25,
        "consensus": 0.25,
        "structure": 0.20,
        "timing": 0.10,
        "risk": 0.10,
        "cost": 0.10,
    }

    @staticmethod
    def _score(value: Any) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return 0.0
        if number > 1.0:
            number /= 100.0
        return round(max(0.0, min(1.0, number)), 4)

    def evaluate_one(self, record: Mapping[str, Any]) -> OpportunityRankingReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        raw_items = record.get("opportunities")
        if not isinstance(raw_items, (list, tuple)) or not raw_items:
            raw_items = ({
                "opportunity_id": str(record.get("opportunity_id", "GOLD_PRIMARY")),
                "symbol": str(record.get("symbol", "GOLD#")),
                "direction": str(record.get("resolved_consensus", record.get("consensus", "WAIT"))),
                "regime_score": record.get("market_regime_confidence", record.get("regime_score", 0.0)),
                "consensus_score": record.get("consensus_confidence", record.get("consensus_score", 0.0)),
                "structure_score": record.get("market_structure_confidence", 0.0),
                "timing_score": record.get("timing_confidence", 0.0),
                "risk_score": 1.0 if bool(record.get("risk_allowed", True)) else 0.0,
                "cost_score": 1.0 if bool(record.get("trading_cost_allowed", True)) else 0.0,
                "conflict_level": record.get("conflict_level", "LOW"),
            },)

        provisional: list[dict[str, Any]] = []
        for index, item in enumerate(raw_items):
            if not isinstance(item, Mapping):
                continue
            symbol = str(item.get("symbol", "GOLD#")).upper()
            direction = str(item.get("direction", "WAIT")).upper()
            direction = {"BULLISH": "BUY", "BEARISH": "SELL", "NEUTRAL": "WAIT"}.get(direction, direction)
            parts = {f"{key}_score": self._score(item.get(f"{key}_score", 0.0)) for key in self.WEIGHTS}
            total = round(sum(parts[f"{key}_score"] * weight for key, weight in self.WEIGHTS.items()), 4)
            conflict = str(item.get("conflict_level", "LOW")).upper()
            risk_ok = parts["risk_score"] >= 0.5
            cost_ok = parts["cost_score"] >= 0.5
            eligible = symbol == "GOLD#" and direction in {"BUY", "SELL"} and conflict != "HIGH" and risk_ok and cost_ok
            if symbol != "GOLD#":
                block_en, block_th = "Version 1 supports GOLD# only.", "เวอร์ชัน 1 รองรับเฉพาะ GOLD#"
            elif direction not in {"BUY", "SELL"}:
                block_en, block_th = "Directional evidence is not actionable.", "หลักฐานด้านทิศทางยังไม่พร้อมใช้งาน"
            elif conflict == "HIGH":
                block_en, block_th = "High unresolved conflict blocks ranking eligibility.", "ความขัดแย้งสูงที่ยังไม่แก้ขัดขวางการจัดอันดับ"
            elif not risk_ok:
                block_en, block_th = "Risk gate is not satisfied.", "ยังไม่ผ่านเงื่อนไขความเสี่ยง"
            elif not cost_ok:
                block_en, block_th = "Trading-cost gate is not satisfied.", "ยังไม่ผ่านเงื่อนไขต้นทุนการซื้อขาย"
            else:
                block_en, block_th = "No blocking condition.", "ไม่มีเงื่อนไขที่ขัดขวาง"
            provisional.append({
                "opportunity_id": str(item.get("opportunity_id", f"OPPORTUNITY_{index + 1}")),
                "symbol": symbol,
                "direction": direction,
                **parts,
                "total_score": total,
                "eligible": eligible,
                "block_reason_en": block_en,
                "block_reason_th": block_th,
            })

        provisional.sort(key=lambda value: (not value["eligible"], -value["total_score"], value["opportunity_id"]))
        ranked = tuple(OpportunityCandidate(rank=i + 1, **value) for i, value in enumerate(provisional))
        eligible = tuple(item for item in ranked if item.eligible)
        if eligible:
            top = eligible[0]
            status, reason = "READY", "opportunity_ranking_ready"
            next_en = f"Validate entry conditions for {top.opportunity_id}; ranking does not authorize execution."
            next_th = f"ตรวจสอบเงื่อนไขเข้าออเดอร์สำหรับ {top.opportunity_id} โดยการจัดอันดับไม่ใช่การอนุญาตให้ส่งคำสั่ง"
        else:
            top = None
            status, reason = "WAITING", "no_eligible_opportunity"
            next_en = "Wait for an eligible GOLD# opportunity with aligned direction, acceptable risk, cost, and conflict."
            next_th = "รอโอกาส GOLD# ที่มีทิศทางสอดคล้อง ความเสี่ยงและต้นทุนยอมรับได้ และไม่มีความขัดแย้งสูง"
        return OpportunityRankingReport(
            status=status,
            reason=reason,
            ranked_opportunities=ranked,
            top_opportunity_id=top.opportunity_id if top else "NONE",
            top_direction=top.direction if top else "WAIT",
            top_score=top.total_score if top else 0.0,
            opportunity_count=len(ranked),
            eligible_count=len(eligible),
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=10)).isoformat(),
            direct_execution=False,
        )
