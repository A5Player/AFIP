"""Milestone Q Pack 10: deterministic Market Intent Intelligence completion.

Closes Milestone Q from accepted Pack 9 research-review certificates. Completion
is research-only and cannot grant Production Certification, Release Candidate
status, execution authority, parameter updates, or trading-logic changes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentIntelligenceCompletionReport:
    completion_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_review_certification_ids: tuple[str, ...]
    completion_timestamp: int
    review_certificate_count: int
    total_governance_report_count: int
    total_calibration_report_count: int
    total_validation_window_count: int
    minimum_research_review_score: float
    average_research_review_score: float
    completion_score: float
    completion_band: str
    pack_9_lineage_valid: bool
    unique_review_certificates: bool
    chronology_valid: bool
    review_metrics_valid: bool
    minimum_certificate_count_met: bool
    all_reviews_certified: bool
    all_completion_candidates: bool
    no_pending_review: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_intent: bool
    market_behaviour_before_intent: bool
    locked_policy_valid: bool
    milestone_q_complete: bool
    next_milestone: str
    review_required: bool
    immutable_record: bool
    research_only: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    production_certification_granted: bool
    release_candidate_granted: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    position_modification_attempted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketIntentIntelligenceCompletionRuntime:
    """Complete Milestone Q without escalating production or execution authority."""

    def complete_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        completion_timestamp: int,
        minimum_certificate_count: int = 3,
        minimum_review_score: float = 75.0,
    ) -> MarketIntentIntelligenceCompletionReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("review_certification_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("certification_timestamp", 0)) for row in rows)
        complete_ts = self._integer(completion_timestamp)

        lineage = bool(rows) and all(
            str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "9")).strip() == "9"
            for row in rows
        )
        unique = bool(rows) and all(item.startswith("QREV-") for item in ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(timestamp > 0 for timestamp in timestamps)
            and tuple(sorted(timestamps)) == timestamps
            and len(set(timestamps)) == len(timestamps)
            and complete_ts >= max(timestamps)
        )

        scores = tuple(self._number(row.get("research_review_score", 0.0)) for row in rows)
        metrics_valid = bool(rows) and all(isfinite(value) and 0.0 <= value <= 100.0 for value in scores)
        minimum_score = round(min(scores), 8) if metrics_valid else 0.0
        average_score = round(sum(scores) / len(scores), 8) if metrics_valid else 0.0
        count_met = len(rows) >= max(1, self._integer(minimum_certificate_count))
        all_certified = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and bool(row.get("market_intent_review_certified", False))
            for row in rows
        )
        all_candidates = bool(rows) and all(bool(row.get("milestone_q_completion_candidate", False)) for row in rows)
        no_pending = bool(rows) and all(not bool(row.get("review_required", True)) for row in rows)
        score_met = metrics_valid and minimum_score >= self._number(minimum_review_score)
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = bool(rows) and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        total_governance = sum(max(0, self._integer(row.get("governance_report_count", 0))) for row in rows)
        total_calibrations = sum(max(0, self._integer(row.get("total_calibration_report_count", 0))) for row in rows)
        total_windows = sum(max(0, self._integer(row.get("total_validation_window_count", 0))) for row in rows)
        completion_score = round(
            0.60 * average_score
            + (10.0 if all_certified else 0.0)
            + (10.0 if all_candidates else 0.0)
            + (5.0 if no_pending else 0.0)
            + (5.0 if quality else 0.0)
            + (5.0 if future_safe else 0.0)
            + (5.0 if policy_valid else 0.0),
            8,
        )
        completion_score = min(100.0, completion_score)

        checks = (
            (not rows, "market_intent_completion_evidence_missing"),
            (not lineage, "pack_9_lineage_invalid"),
            (not unique, "duplicate_or_invalid_pack_9_review_certification_id"),
            (not chronology, "market_intent_completion_chronology_invalid"),
            (not metrics_valid, "market_intent_completion_metrics_invalid"),
            (not count_met, "minimum_review_certificate_count_not_met"),
            (not all_certified, "pack_9_review_not_certified"),
            (not all_candidates, "pack_9_completion_candidate_missing"),
            (not no_pending, "market_intent_review_pending"),
            (not score_met, "minimum_research_review_score_not_met"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        complete = not blocked

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "completion_timestamp": complete_ts,
            "minimum_certificate_count": minimum_certificate_count,
            "minimum_review_score": minimum_review_score,
            "completion_score": completion_score,
            "blocked": blocked,
        }
        completion_id = "QCOMP-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if complete:
            reason = "MARKET_INTENT_INTELLIGENCE_COMPLETE_RESEARCH_ONLY"
            en = "Milestone Q Market Intent Intelligence completed deterministic research validation without Production Certification, Release Candidate status, or execution authority."
            th = "Milestone Q Market Intent Intelligence เสร็จสมบูรณ์ด้านการตรวจสอบงานวิจัยแบบ deterministic โดยไม่ให้ Production Certification สถานะ Release Candidate หรือสิทธิ์ execution"
        else:
            reason = "MARKET_INTENT_INTELLIGENCE_COMPLETION_BLOCKED"
            en = "Milestone Q completion was blocked by lineage, chronology, review, quality, prerequisite, or frozen-policy controls."
            th = "การปิด Milestone Q ถูกระงับจาก lineage ลำดับเวลา การทบทวน คุณภาพข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentIntelligenceCompletionReport(
            completion_id=completion_id,
            status="COMPLETE" if complete else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="10",
            source_review_certification_ids=ids,
            completion_timestamp=complete_ts,
            review_certificate_count=len(rows),
            total_governance_report_count=total_governance,
            total_calibration_report_count=total_calibrations,
            total_validation_window_count=total_windows,
            minimum_research_review_score=minimum_score,
            average_research_review_score=average_score,
            completion_score=completion_score,
            completion_band=self._band(completion_score),
            pack_9_lineage_valid=lineage,
            unique_review_certificates=unique,
            chronology_valid=chronology,
            review_metrics_valid=metrics_valid,
            minimum_certificate_count_met=count_met,
            all_reviews_certified=all_certified,
            all_completion_candidates=all_candidates,
            no_pending_review=no_pending,
            data_quality_certified=quality,
            future_safe=future_safe,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
            locked_policy_valid=policy_valid,
            milestone_q_complete=complete,
            next_milestone="R_PRODUCTION_CERTIFICATION" if complete else "Q_REVIEW_REQUIRED",
            review_required=not complete,
            immutable_record=True,
            research_only=True,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            production_certification_granted=False,
            release_candidate_granted=False,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _band(score: float) -> str:
        if score >= 90.0:
            return "COMPLETE_STRONG"
        if score >= 75.0:
            return "COMPLETE_ACCEPTABLE"
        if score >= 60.0:
            return "REVIEW_REQUIRED"
        return "INSUFFICIENT"

    @staticmethod
    def _policy_valid(row: Mapping[str, Any]) -> bool:
        try:
            base_lot = float(row.get("base_lot_per_unit", 0.0))
        except (TypeError, ValueError):
            return False
        return (
            str(row.get("broker", "")).strip().upper() == "XM"
            and str(row.get("symbol", "")).strip().upper() == "GOLD#"
            and abs(base_lot - 0.01) < 1e-12
            and str(row.get("execution_status", "")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", True))
            and not bool(row.get("live_execution_enabled", True))
            and not bool(row.get("automatic_parameter_update_allowed", True))
            and not bool(row.get("trading_logic_change_allowed", True))
            and not bool(row.get("production_knowledge_allowed", True))
            and not bool(row.get("production_certification_granted", True))
            and not bool(row.get("release_candidate_granted", True))
        )
