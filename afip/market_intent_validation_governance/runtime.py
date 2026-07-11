"""Milestone Q Pack 8: deterministic Market Intent validation governance.

Applies immutable governance controls to accepted Pack 7 confidence calibration
reports. This research-only runtime cannot alter parameters, trading logic,
execution, positions, broker state, or production certification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketIntentValidationGovernanceReport:
    governance_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    source_calibration_ids: tuple[str, ...]
    governance_timestamp: int
    calibration_report_count: int
    total_validation_window_count: int
    minimum_confidence_score: float
    average_confidence_score: float
    minimum_evidence_coverage_score: float
    average_evidence_coverage_score: float
    accepted_calibration_ratio: float
    governance_score: float
    governance_band: str
    pack_7_lineage_valid: bool
    unique_calibration_reports: bool
    chronology_valid: bool
    confidence_metrics_valid: bool
    confidence_threshold_met: bool
    evidence_threshold_met: bool
    minimum_report_count_met: bool
    all_calibrations_accepted: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_intent: bool
    market_behaviour_before_intent: bool
    locked_policy_valid: bool
    validation_governance_accepted: bool
    review_required: bool
    immutable_record: bool
    research_only: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    production_certification_granted: bool
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


class MarketIntentValidationGovernanceRuntime:
    """Govern accepted Market Intent confidence evidence without authority escalation."""

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        governance_timestamp: int,
        minimum_report_count: int = 3,
        minimum_confidence_score: float = 60.0,
        minimum_evidence_coverage_score: float = 70.0,
    ) -> MarketIntentValidationGovernanceReport:
        rows = tuple(dict(item) for item in reports)
        ids = tuple(str(row.get("calibration_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("calibration_timestamp", 0)) for row in rows)
        governance_ts = self._integer(governance_timestamp)

        unique = bool(rows) and all(item.startswith("QCNF-") for item in ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(timestamp > 0 for timestamp in timestamps)
            and tuple(sorted(timestamps)) == timestamps
            and len(set(timestamps)) == len(timestamps)
            and governance_ts >= max(timestamps)
        )
        lineage = bool(rows) and all(
            str(row.get("milestone", "Q")).strip().upper() == "Q"
            and str(row.get("pack", "7")).strip() == "7"
            for row in rows
        )
        accepted_rows = tuple(
            str(row.get("status", "")).strip().upper() == "READY"
            and bool(row.get("calibration_accepted", False))
            for row in rows
        )
        all_accepted = bool(rows) and all(accepted_rows)
        accepted_ratio = round(sum(1 for item in accepted_rows if item) / len(rows), 8) if rows else 0.0

        confidence_values = tuple(self._number(row.get("calibrated_confidence_score", 0.0)) for row in rows)
        coverage_values = tuple(self._number(row.get("evidence_coverage_score", 0.0)) for row in rows)
        metrics_valid = bool(rows) and all(
            isfinite(value) and 0.0 <= value <= 100.0
            for value in confidence_values + coverage_values
        )
        min_confidence = round(min(confidence_values), 8) if metrics_valid else 0.0
        avg_confidence = round(sum(confidence_values) / len(confidence_values), 8) if metrics_valid else 0.0
        min_coverage = round(min(coverage_values), 8) if metrics_valid else 0.0
        avg_coverage = round(sum(coverage_values) / len(coverage_values), 8) if metrics_valid else 0.0
        total_windows = sum(max(0, self._integer(row.get("total_validation_window_count", 0))) for row in rows)

        report_count_met = len(rows) >= max(1, self._integer(minimum_report_count))
        confidence_met = metrics_valid and min_confidence >= self._number(minimum_confidence_score)
        evidence_met = metrics_valid and min_coverage >= self._number(minimum_evidence_coverage_score)
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_intent", False)) for row in rows)
        behaviour_first = bool(rows) and all(bool(row.get("market_behaviour_before_intent", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        governance_score = round(
            0.35 * avg_confidence
            + 0.25 * avg_coverage
            + 20.0 * accepted_ratio
            + (10.0 if quality else 0.0)
            + (10.0 if future_safe else 0.0),
            8,
        )
        governance_score = min(100.0, governance_score)
        governance_band = self._band(governance_score)

        checks = (
            (not rows, "market_intent_governance_evidence_missing"),
            (not lineage, "pack_7_lineage_invalid"),
            (not unique, "duplicate_or_invalid_pack_7_calibration_id"),
            (not chronology, "market_intent_governance_chronology_invalid"),
            (not metrics_valid, "market_intent_governance_metrics_invalid"),
            (not report_count_met, "minimum_calibration_report_count_not_met"),
            (not all_accepted, "pack_7_calibration_not_accepted"),
            (not confidence_met, "minimum_confidence_threshold_not_met"),
            (not evidence_met, "minimum_evidence_coverage_threshold_not_met"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_intent"),
            (not behaviour_first, "market_behaviour_not_evaluated_before_intent"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked
        review_required = not accepted

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "governance_timestamp": governance_ts,
            "minimum_report_count": minimum_report_count,
            "minimum_confidence_score": minimum_confidence_score,
            "minimum_evidence_coverage_score": minimum_evidence_coverage_score,
            "governance_score": governance_score,
            "blocked": blocked,
        }
        governance_id = "QGOV-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if accepted:
            reason = "MARKET_INTENT_VALIDATION_GOVERNANCE_ACCEPTED_RESEARCH_ONLY"
            en = "Pack 7 confidence evidence passed deterministic Market Intent validation governance without production or execution authority."
            th = "หลักฐานความเชื่อมั่นจาก Pack 7 ผ่านการกำกับการตรวจสอบ Market Intent แบบ deterministic โดยไม่มีสิทธิ์ production หรือ execution"
        else:
            reason = "MARKET_INTENT_VALIDATION_GOVERNANCE_BLOCKED"
            en = "Market Intent validation governance was blocked by lineage, chronology, evidence, confidence, quality, prerequisite, or frozen-policy controls."
            th = "การกำกับการตรวจสอบ Market Intent ถูกระงับจาก lineage ลำดับเวลา หลักฐาน ความเชื่อมั่น คุณภาพข้อมูล เงื่อนไขก่อนหน้า หรือนโยบายล็อก"

        return MarketIntentValidationGovernanceReport(
            governance_id=governance_id,
            status="READY" if accepted else "BLOCKED",
            reason=reason,
            milestone="Q",
            pack="8",
            source_calibration_ids=ids,
            governance_timestamp=governance_ts,
            calibration_report_count=len(rows),
            total_validation_window_count=total_windows,
            minimum_confidence_score=min_confidence,
            average_confidence_score=avg_confidence,
            minimum_evidence_coverage_score=min_coverage,
            average_evidence_coverage_score=avg_coverage,
            accepted_calibration_ratio=accepted_ratio,
            governance_score=governance_score,
            governance_band=governance_band,
            pack_7_lineage_valid=lineage,
            unique_calibration_reports=unique,
            chronology_valid=chronology,
            confidence_metrics_valid=metrics_valid,
            confidence_threshold_met=confidence_met,
            evidence_threshold_met=evidence_met,
            minimum_report_count_met=report_count_met,
            all_calibrations_accepted=all_accepted,
            data_quality_certified=quality,
            future_safe=future_safe,
            market_regime_before_intent=regime_first,
            market_behaviour_before_intent=behaviour_first,
            locked_policy_valid=policy_valid,
            validation_governance_accepted=accepted,
            review_required=review_required,
            immutable_record=True,
            research_only=True,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            production_certification_granted=False,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
        )

    @staticmethod
    def _band(score: float) -> str:
        if score >= 90.0:
            return "STRONG"
        if score >= 75.0:
            return "ACCEPTABLE"
        if score >= 60.0:
            return "CAUTIOUS"
        return "INSUFFICIENT"

    def _policy_valid(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(row.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("automatic_parameter_update_allowed", False))
            and not bool(row.get("trading_logic_change_allowed", False))
            and not bool(row.get("production_knowledge_allowed", False))
            and not bool(row.get("production_certification_granted", False))
        )

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
