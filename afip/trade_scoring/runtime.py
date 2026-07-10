from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .models import TradeScore, TradeScoringReport


class TradeScoringRuntime:
    """Produces deterministic, explainable trade-quality scores after opportunity ranking."""

    WEIGHTS = {
        "opportunity": 0.35,
        "quality": 0.25,
        "risk_adjusted": 0.25,
        "execution_readiness": 0.15,
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

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 0.90:
            return "A+"
        if score >= 0.80:
            return "A"
        if score >= 0.70:
            return "B"
        if score >= 0.60:
            return "C"
        return "REJECT"

    def evaluate_one(self, record: Mapping[str, Any]) -> TradeScoringReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        raw = record.get("ranked_opportunities") or record.get("opportunities") or ()
        if not isinstance(raw, (list, tuple)):
            raw = ()
        scores: list[TradeScore] = []
        for index, item in enumerate(raw):
            if not isinstance(item, Mapping):
                continue
            symbol = str(item.get("symbol", "GOLD#")).upper()
            direction = str(item.get("direction", "WAIT")).upper()
            opportunity = self._score(item.get("total_score", item.get("opportunity_score", 0.0)))
            quality = self._score(item.get("quality_score", item.get("structure_score", 0.0)))
            risk_adjusted = self._score(item.get("risk_adjusted_score", item.get("risk_score", 0.0)))
            execution_readiness = self._score(item.get("execution_readiness_score", item.get("cost_score", 0.0)))
            final = round(
                opportunity * self.WEIGHTS["opportunity"]
                + quality * self.WEIGHTS["quality"]
                + risk_adjusted * self.WEIGHTS["risk_adjusted"]
                + execution_readiness * self.WEIGHTS["execution_readiness"],
                4,
            )
            grade = self._grade(final)
            upstream_eligible = bool(item.get("eligible", True))
            eligible = symbol == "GOLD#" and direction in {"BUY", "SELL"} and upstream_eligible and grade != "REJECT"
            if symbol != "GOLD#":
                en, th = "Version 1 supports GOLD# only.", "เวอร์ชัน 1 รองรับเฉพาะ GOLD#"
            elif direction not in {"BUY", "SELL"}:
                en, th = "Direction is not actionable.", "ทิศทางยังไม่พร้อมใช้งาน"
            elif not upstream_eligible:
                en, th = "Opportunity ranking did not approve this candidate.", "การจัดอันดับโอกาสยังไม่อนุมัติผู้สมัครนี้"
            elif grade == "REJECT":
                en, th = "Final score is below the minimum review threshold.", "คะแนนสุดท้ายต่ำกว่าเกณฑ์ขั้นต่ำสำหรับการทบทวน"
            else:
                en = f"Candidate passed deterministic scoring with grade {grade}; scoring does not authorize execution."
                th = f"ผู้สมัครผ่านการให้คะแนนแบบกำหนดแน่นอนด้วยเกรด {grade} โดยคะแนนไม่ใช่การอนุญาตให้ส่งคำสั่ง"
            scores.append(TradeScore(
                opportunity_id=str(item.get("opportunity_id", f"OPPORTUNITY_{index + 1}")),
                symbol=symbol,
                direction=direction,
                opportunity_score=opportunity,
                quality_score=quality,
                risk_adjusted_score=risk_adjusted,
                execution_readiness_score=execution_readiness,
                final_score=final,
                grade=grade,
                eligible=eligible,
                explanation_en=en,
                explanation_th=th,
            ))
        scores.sort(key=lambda x: (not x.eligible, -x.final_score, x.opportunity_id))
        eligible_scores = [x for x in scores if x.eligible]
        top = eligible_scores[0] if eligible_scores else None
        if top:
            status, reason = "READY", "trade_scoring_ready"
            next_en = f"Pass {top.opportunity_id} to Unit Allocation review; scoring does not authorize execution."
            next_th = f"ส่ง {top.opportunity_id} ไปทบทวนการจัดสรร Unit โดยคะแนนไม่ใช่การอนุญาตให้ส่งคำสั่ง"
        else:
            status, reason = "WAITING", "no_eligible_trade_score"
            next_en = "Wait for a candidate with sufficient opportunity, quality, risk-adjusted, and execution-readiness scores."
            next_th = "รอผู้สมัครที่มีคะแนนโอกาส คุณภาพ ปรับตามความเสี่ยง และความพร้อมในการดำเนินการเพียงพอ"
        return TradeScoringReport(
            status=status,
            reason=reason,
            scores=tuple(scores),
            top_opportunity_id=top.opportunity_id if top else "NONE",
            top_direction=top.direction if top else "WAIT",
            top_final_score=top.final_score if top else 0.0,
            top_grade=top.grade if top else "REJECT",
            eligible_count=len(eligible_scores),
            score_count=len(scores),
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc) + timedelta(minutes=10)).isoformat(),
            direct_execution=False,
        )
