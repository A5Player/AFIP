"""Milestone Q Pack 9: deterministic Market Intent review certification.

Certifies the completeness of accepted Pack 8 governance evidence for research
review only. It cannot grant Production Certification, alter trading logic,
change parameters, modify positions, contact a broker, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentReviewCertificationReport:
    review_certification_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_governance_ids: tuple[str, ...]
    certification_timestamp: int
    governance_report_count: int
    total_calibration_report_count: int
    total_validation_window_count: int
    minimum_governance_score: float
    average_governance_score: float
    accepted_governance_ratio: float
    research_review_score: float
    research_review_band: str
    pack_8_lineage_valid: bool
    unique_governance_reports: bool
    chronology_valid: bool
    governance_metrics_valid: bool
    minimum_report_count_met: bool
    minimum_governance_score_met: bool
    all_governance_reports_accepted: bool
    no_pending_governance_review: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_intent: bool
    market_behaviour_before_intent: bool
    locked_policy_valid: bool
    market_intent_review_certified: bool
    milestone_q_completion_candidate: bool
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


class MarketIntentReviewCertificationRuntime:
    """Certify Pack 8 evidence for research review without authority escalation."""

    def certify_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        certification_timestamp: int,
        minimum_report_count: int = 3,
        minimum_governance_score: float = 75.0,
    ) -> MarketIntentReviewCertificationReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("governance_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("governance_timestamp", 0)) for row in rows)
        cert_ts = self._integer(certification_timestamp)

        lineage = bool(rows) and all(
            str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "8")).strip() == "8"
            for row in rows
        )
        unique = bool(rows) and all(item.startswith("QGOV-") for item in ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(timestamp > 0 for timestamp in timestamps)
            and tuple(sorted(timestamps)) == timestamps
            and len(set(timestamps)) == len(timestamps)
            and cert_ts >= max(timestamps)
        )

        scores = tuple(self._number(row.get("governance_score", 0.0)) for row in rows)
        metrics_valid = bool(rows) and all(isfinite(value) and 0.0 <= value <= 100.0 for value in scores)
        min_score = round(min(scores), 8) if metrics_valid else 0.0
        avg_score = round(sum(scores) / len(scores), 8) if metrics_valid else 0.0

        accepted_rows = tuple(
            str(row.get("status", "")).strip().upper() == "READY"
            and bool(row.get("validation_governance_accepted", False))
            for row in rows
        )
        accepted_ratio = round(sum(1 for item in accepted_rows if item) / len(rows), 8) if rows else 0.0
        all_accepted = bool(rows) and all(accepted_rows)
        no_pending_review = bool(rows) and all(not bool(row.get("review_required", True)) for row in rows)
        count_met = len(rows) >= max(1, self._integer(minimum_report_count))
        score_met = metrics_valid and min_score >= self._number(minimum_governance_score)

        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = bool(rows) and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        total_calibrations = sum(max(0, self._integer(row.get("calibration_report_count", 0))) for row in rows)
        total_windows = sum(max(0, self._integer(row.get("total_validation_window_count", 0))) for row in rows)
        review_score = round(
            0.55 * avg_score
            + 25.0 * accepted_ratio
            + (10.0 if no_pending_review else 0.0)
            + (5.0 if quality else 0.0)
            + (5.0 if future_safe else 0.0),
            8,
        )
        review_score = min(100.0, review_score)
        review_band = self._band(review_score)

        checks = (
            (not rows, "market_intent_review_evidence_missing"),
            (not lineage, "pack_8_lineage_invalid"),
            (not unique, "duplicate_or_invalid_pack_8_governance_id"),
            (not chronology, "market_intent_review_chronology_invalid"),
            (not metrics_valid, "market_intent_review_metrics_invalid"),
            (not count_met, "minimum_governance_report_count_not_met"),
            (not all_accepted, "pack_8_governance_not_accepted"),
            (not no_pending_review, "pack_8_governance_review_pending"),
            (not score_met, "minimum_governance_score_not_met"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        certified = not blocked

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "certification_timestamp": cert_ts,
            "minimum_report_count": minimum_report_count,
            "minimum_governance_score": minimum_governance_score,
            "research_review_score": review_score,
            "blocked": blocked,
        }
        certification_id = "QREV-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if certified:
            reason = "MARKET_INTENT_REVIEW_CERTIFIED_RESEARCH_ONLY"
            en = "Pack 8 governance evidence passed deterministic Market Intent research review certification without Production Certification or execution authority."
            th = "หลักฐานการกำกับจาก Pack 8 ผ่านการรับรองการทบทวน Market Intent แบบ deterministic สำหรับงานวิจัย โดยไม่ให้สิทธิ์ Production Certification หรือ execution"
        else:
            reason = "MARKET_INTENT_REVIEW_CERTIFICATION_BLOCKED"
            en = "Market Intent research review certification was blocked by lineage, chronology, governance, quality, prerequisite, or frozen-policy controls."
            th = "การรับรองการทบทวน Market Intent สำหรับงานวิจัยถูกระงับจาก lineage ลำดับเวลา การกำกับ คุณภาพข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentReviewCertificationReport(
            review_certification_id=certification_id,
            status="READY" if certified else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="9",
            source_governance_ids=ids,
            certification_timestamp=cert_ts,
            governance_report_count=len(rows),
            total_calibration_report_count=total_calibrations,
            total_validation_window_count=total_windows,
            minimum_governance_score=min_score,
            average_governance_score=avg_score,
            accepted_governance_ratio=accepted_ratio,
            research_review_score=review_score,
            research_review_band=review_band,
            pack_8_lineage_valid=lineage,
            unique_governance_reports=unique,
            chronology_valid=chronology,
            governance_metrics_valid=metrics_valid,
            minimum_report_count_met=count_met,
            minimum_governance_score_met=score_met,
            all_governance_reports_accepted=all_accepted,
            no_pending_governance_review=no_pending_review,
            data_quality_certified=quality,
            future_safe=future_safe,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
            locked_policy_valid=policy_valid,
            market_intent_review_certified=certified,
            milestone_q_completion_candidate=certified,
            review_required=not certified,
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
            return "STRONG"
        if score >= 75.0:
            return "ACCEPTABLE"
        if score >= 60.0:
            return "CAUTIOUS"
        return "INSUFFICIENT"

    @staticmethod
    def _policy_valid(row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "")).strip().upper() == "XM"
            and str(row.get("symbol", "")).strip().upper() == "GOLD#"
            and abs(float(row.get("base_lot_per_unit", 0.0)) - 0.01) < 1e-12
            and str(row.get("execution_status", "")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", True))
            and not bool(row.get("live_execution_enabled", True))
            and not bool(row.get("automatic_parameter_update_allowed", True))
            and not bool(row.get("trading_logic_change_allowed", True))
            and not bool(row.get("production_knowledge_allowed", True))
            and not bool(row.get("production_certification_granted", True))
        )
