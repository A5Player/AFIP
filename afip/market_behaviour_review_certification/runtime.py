"""Milestone P Pack 9: deterministic Market Behaviour Review Certification.

Certifies that accepted Pack 8 market-behaviour governance reports received documented manual
research review. Certification remains research-only and cannot tune parameters,
change trading logic, promote production knowledge, modify positions, or send orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourReviewCertificationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    review_certification_id: str
    governance_validation_ids: tuple[str, ...]
    governance_report_count: int
    total_transition_count: int
    mean_governance_confidence: float
    minimum_governance_confidence: float
    reviewer_id: str
    review_record_id: str
    review_timestamp: int
    review_outcome: str
    review_notes_present: bool
    pack_8_governance_accepted: bool
    unique_governance_lineage: bool
    chronology_valid: bool
    reviewer_identity_valid: bool
    review_record_valid: bool
    review_outcome_valid: bool
    minimum_report_count_met: bool
    minimum_transition_count_met: bool
    confidence_threshold_met: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_behaviour: bool
    finite_metrics: bool
    locked_policy_valid: bool
    review_certified: bool
    manual_review_completed: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    production_certification_granted: bool
    research_only: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
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


class MarketBehaviourReviewCertificationRuntime:
    """Certify documented manual review of accepted Pack 8 market-behaviour governance reports."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        reviewer_id: str,
        review_record_id: str,
        review_timestamp: int,
        review_outcome: str,
        review_notes: str,
        minimum_report_count: int = 3,
        minimum_total_transition_count: int = 120,
        minimum_mean_confidence: float = 60.0,
    ) -> MarketBehaviourReviewCertificationReport:
        rows = [dict(row) for row in records]
        ids = tuple(str(row.get("governance_validation_id", "")).strip().upper() for row in rows)
        timestamps = [self._integer(row.get("governance_timestamp", 0)) for row in rows]
        reviewer = str(reviewer_id).strip().upper()
        record_id = str(review_record_id).strip().upper()
        outcome = str(review_outcome).strip().upper()
        notes_present = bool(str(review_notes).strip())
        review_ts = self._integer(review_timestamp)

        unique = bool(ids) and all(identifier.startswith("PBGV-") for identifier in ids) and len(ids) == len(set(ids))
        accepted_pack_8 = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and bool(row.get("governance_accepted", False))
            and bool(row.get("manual_review_required", False))
            for row in rows
        )
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps) and review_ts > max(timestamps)
        reviewer_valid = len(reviewer) >= 3 and reviewer not in {"SYSTEM", "AUTO", "AUTOMATION"}
        review_record_valid = record_id.startswith("PBREV-") and len(record_id) >= 10 and notes_present and review_ts > 0
        outcome_valid = outcome == "APPROVED_FOR_RESEARCH_CONTINUATION"
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) and not bool(row.get("future_leakage_detected", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)

        metric_keys = ("total_transition_count", "mean_calibrated_confidence", "minimum_calibrated_confidence")
        finite = all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in metric_keys)
        total_transitions = sum(max(0, self._integer(row.get("total_transition_count", 0))) for row in rows)
        mean_confidence = self._weighted_mean(rows, "mean_calibrated_confidence", "total_transition_count")
        min_confidence = min((self._number(row.get("minimum_calibrated_confidence", 0.0)) for row in rows), default=0.0)
        report_count_met = len(rows) >= int(minimum_report_count)
        transition_count_met = total_transitions >= int(minimum_total_transition_count)
        confidence_met = mean_confidence >= float(minimum_mean_confidence) and min_confidence >= 60.0

        policies_valid = bool(rows) and all(
            str(row.get("policy_version", "")).strip().upper() == "AFIP_V1_FEATURE_FREEZE"
            and str(row.get("broker", "XM")).strip().upper() == "XM"
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
            for row in rows
        )

        checks = (
            (not rows, "review_governance_evidence_missing"),
            (not unique, "duplicate_or_invalid_behaviour_governance_validation_id"),
            (not accepted_pack_8, "pack_8_behaviour_governance_not_accepted"),
            (not chronology, "behaviour_review_chronology_invalid"),
            (not reviewer_valid, "manual_reviewer_identity_invalid"),
            (not review_record_valid, "manual_behaviour_review_record_invalid"),
            (not outcome_valid, "manual_behaviour_review_outcome_not_approved"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not finite, "non_finite_behaviour_review_metric"),
            (not report_count_met, "minimum_behaviour_governance_report_count_not_met"),
            (not transition_count_met, "minimum_transition_count_not_met"),
            (not confidence_met, "minimum_behaviour_review_confidence_not_met"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        certified = not blocked

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "reviewer": reviewer,
            "review_record_id": record_id,
            "review_timestamp": review_ts,
            "review_outcome": outcome,
            "blocked": blocked,
        }
        certification_id = "PBCERT-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if certified:
            reason = "MARKET_BEHAVIOUR_REVIEW_CERTIFIED_FOR_RESEARCH_CONTINUATION"
            en = "Accepted Pack 8 market-behaviour governance reports received documented manual review and are certified only for continued Milestone P research validation."
            th = "รายงาน Governance จาก Pack 8 ได้รับการทบทวนด้วยมนุษย์พร้อมเอกสาร และได้รับการรับรองเฉพาะสำหรับการตรวจงานวิจัยต่อใน Milestone P"
            next_en = "Proceed to Milestone P Pack 10 certification; keep parameter updates, production promotion, and execution disabled."
            next_th = "ดำเนินการต่อไปยัง Milestone P Pack 10 โดยคงการปรับ Parameter การเลื่อนสู่ Production และ Execution ไว้ที่ปิด"
        else:
            reason = "MARKET_BEHAVIOUR_REVIEW_CERTIFICATION_BLOCKED"
            en = "Review certification was blocked because governance lineage, documented manual review, chronology, quality, coverage, confidence, future safety, or locked controls failed."
            th = "การรับรอง Review ถูกระงับเนื่องจาก Governance lineage เอกสารการทบทวนด้วยมนุษย์ ลำดับเวลา คุณภาพ Coverage Confidence Future Safety หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Correct the blocked review evidence and retain all adaptive and execution authority as disabled."
            next_th = "แก้ไขหลักฐาน Review ที่ถูกระงับ และคง Adaptive กับ Execution authority ไว้ที่ปิด"

        return MarketBehaviourReviewCertificationReport(
            status="READY" if certified else "BLOCKED", reason=reason, milestone="P", pack="9",
            review_certification_id=certification_id, governance_validation_ids=ids,
            governance_report_count=len(rows), total_transition_count=total_transitions,
            mean_governance_confidence=mean_confidence, minimum_governance_confidence=round(min_confidence, 8),
            reviewer_id=reviewer, review_record_id=record_id, review_timestamp=review_ts,
            review_outcome=outcome, review_notes_present=notes_present,
            pack_8_governance_accepted=accepted_pack_8, unique_governance_lineage=unique,
            chronology_valid=chronology, reviewer_identity_valid=reviewer_valid,
            review_record_valid=review_record_valid, review_outcome_valid=outcome_valid,
            minimum_report_count_met=report_count_met, minimum_transition_count_met=transition_count_met,
            confidence_threshold_met=confidence_met, data_quality_certified=quality,
            future_safe=future_safe, market_regime_before_behaviour=regime_first, finite_metrics=finite, locked_policy_valid=policies_valid,
            review_certified=certified, manual_review_completed=certified,
            automatic_parameter_update_allowed=False, trading_logic_change_allowed=False,
            production_knowledge_allowed=False, production_certification_granted=False, research_only=True, block_reasons=blocked,
            explanation_reason_en=en, explanation_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
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

    def _weighted_mean(self, rows: list[dict[str, Any]], value_key: str, weight_key: str) -> float:
        weighted = 0.0
        total = 0.0
        for row in rows:
            value = self._number(row.get(value_key, 0.0))
            weight = max(0.0, self._number(row.get(weight_key, 0.0)))
            weighted += value * weight
            total += weight
        return round(weighted / total, 8) if total > 0 else 0.0
