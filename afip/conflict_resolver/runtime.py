from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from afip.consensus_engine import ConsensusEngineRuntime
from .models import ConflictResolutionReport

class ConflictResolverRuntime:
    """Resolves material disagreement without bypassing market-regime or risk gates."""

    PRIORITY = ("market_regime", "market_structure", "multi_timeframe", "gold_macro", "central_bank")

    def evaluate_one(self, record: Mapping[str, Any]) -> ConflictResolutionReport:
        now = record.get("current_time_utc") or datetime.now(timezone.utc)
        if not isinstance(now, datetime):
            now = datetime.fromisoformat(str(now).replace("Z", "+00:00"))
        consensus = ConsensusEngineRuntime().evaluate_one(record)
        conflicting = list(consensus.contradicting_sources)
        score = round(consensus.conflict_ratio, 4)
        level = "HIGH" if score >= 0.35 else "MODERATE" if score >= 0.20 else "LOW"
        resolved = consensus.consensus
        method = "WEIGHTED_CONSENSUS"
        resolved_sources: list[str] = []
        unresolved_sources: list[str] = conflicting
        status = "READY"

        if consensus.status != "READY":
            status = "WAITING"
            resolved = "WAIT"
            method = "INSUFFICIENT_EVIDENCE"
        elif level == "HIGH":
            priority_direction = None
            for source in self.PRIORITY:
                source_status = str(record.get(f"{source}_status", "WAITING")).upper()
                source_direction = str(record.get(f"{source}_direction", record.get(f"{source}_bias", "WAIT"))).upper()
                source_direction = {"BULLISH":"BUY", "BEARISH":"SELL", "NEUTRAL":"WAIT"}.get(source_direction, source_direction)
                try:
                    confidence = float(record.get(f"{source}_confidence", 0.0))
                except (TypeError, ValueError):
                    confidence = 0.0
                if source_status == "READY" and source_direction in {"BUY", "SELL"} and confidence >= 0.75:
                    priority_direction = source_direction
                    resolved_sources.append(source)
                    break
            if priority_direction and priority_direction == consensus.consensus:
                method = "PRIORITY_EVIDENCE_CONFIRMATION"
                unresolved_sources = [s for s in conflicting if s not in resolved_sources]
            else:
                status = "WAITING"
                resolved = "WAIT"
                method = "CONFLICT_HOLD"
        elif level == "MODERATE":
            method = "WEIGHTED_CONSENSUS_WITH_REVIEW"

        if status == "READY":
            waiting_en = "No material unresolved conflict blocks decision review."
            waiting_th = "ไม่มีความขัดแย้งสาระสำคัญที่ยังไม่ได้แก้และขัดขวางการทบทวนการตัดสินใจ"
            next_en = f"Continue with {resolved} decision validation; verify risk, cost, and entry conditions."
            next_th = f"ดำเนินการตรวจสอบการตัดสินใจ {resolved} ต่อ โดยยืนยันความเสี่ยง ต้นทุน และเงื่อนไขเข้าออเดอร์"
        else:
            waiting_en = "Material evidence conflict remains unresolved; decision must wait."
            waiting_th = "หลักฐานสำคัญยังขัดแย้งกันและยังแก้ไม่ได้ จึงต้องรอการตัดสินใจ"
            next_en = "Wait for market-regime confirmation or stronger aligned evidence."
            next_th = "รอการยืนยัน Market Regime หรือหลักฐานที่สอดคล้องและแข็งแรงกว่า"

        return ConflictResolutionReport(
            status=status,
            original_consensus=consensus.consensus,
            resolved_consensus=resolved,
            conflict_level=level,
            conflict_score=score,
            resolution_method=method,
            unresolved_sources=tuple(unresolved_sources),
            resolved_sources=tuple(resolved_sources),
            waiting_reason_en=waiting_en,
            waiting_reason_th=waiting_th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
            next_review_time_utc=(now.astimezone(timezone.utc)+timedelta(minutes=10)).isoformat(),
            direct_execution=False,
        )
