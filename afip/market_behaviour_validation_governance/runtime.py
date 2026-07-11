"""Milestone P Pack 8: deterministic Market Behaviour Validation Governance.

Applies research governance to accepted Pack 7 behaviour-confidence calibrations.
The runtime records a review gate only; it cannot tune parameters, change trading
logic, promote production knowledge, modify positions, or transmit orders.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourValidationGovernanceReport:
    status: str
    reason: str
    milestone: str
    pack: str
    governance_validation_id: str
    confidence_calibration_ids: tuple[str, ...]
    calibration_count: int
    total_transition_count: int
    mean_calibrated_confidence: float
    minimum_calibrated_confidence: float
    policy_version: str
    review_role: str
    approval_role: str
    pack_7_calibrations_accepted: bool
    unique_calibration_lineage: bool
    chronology_valid: bool
    reviewer_separation_valid: bool
    policy_version_valid: bool
    minimum_calibration_count_met: bool
    minimum_transition_count_met: bool
    confidence_threshold_met: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_behaviour: bool
    finite_metrics: bool
    locked_policy_valid: bool
    governance_accepted: bool
    manual_review_required: bool
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


class MarketBehaviourValidationGovernanceRuntime:
    """Validate Pack 7 behaviour calibrations under frozen governance policy."""

    def evaluate_many(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        policy_version: str = "AFIP_V1_FEATURE_FREEZE",
        review_role: str = "MARKET_BEHAVIOUR_RESEARCH_REVIEW",
        approval_role: str = "PRODUCTION_CERTIFICATION",
        minimum_calibration_count: int = 3,
        minimum_total_transition_count: int = 300,
        minimum_mean_confidence: float = 60.0,
    ) -> MarketBehaviourValidationGovernanceReport:
        rows = [dict(row) for row in records]
        ids = tuple(str(row.get("calibration_id", "")).strip().upper() for row in rows)
        timestamps = [self._integer(row.get("governance_timestamp", row.get("calibration_timestamp", 0))) for row in rows]
        policy = str(policy_version).strip().upper()
        reviewer = str(review_role).strip().upper()
        approver = str(approval_role).strip().upper()

        unique = bool(ids) and all(identifier.startswith("PBCF-") for identifier in ids) and len(ids) == len(set(ids))
        chronology = bool(rows) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)
        accepted_pack_7 = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and bool(row.get("calibration_accepted", False))
            and str(row.get("confidence_band", "")).strip().upper() in {"CAUTIOUS", "MODERATE", "HIGH"}
            for row in rows
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) and not bool(row.get("future_leakage_detected", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)
        separation = bool(reviewer and approver and reviewer != approver)
        policy_valid = policy == "AFIP_V1_FEATURE_FREEZE"

        metric_keys = ("total_transition_count", "calibrated_confidence_score")
        finite = bool(rows) and all(isfinite(self._number(row.get(key, 0.0))) for row in rows for key in metric_keys)
        total_transitions = sum(max(0, self._integer(row.get("total_transition_count", 0))) for row in rows)
        mean_confidence = self._weighted_mean(rows, "calibrated_confidence_score", "total_transition_count")
        min_confidence = min((self._number(row.get("calibrated_confidence_score", 0.0)) for row in rows), default=0.0)
        calibration_count_met = len(rows) >= max(1, int(minimum_calibration_count))
        transition_count_met = total_transitions >= max(1, int(minimum_total_transition_count))
        confidence_met = mean_confidence >= float(minimum_mean_confidence) and min_confidence >= 60.0
        policies_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        checks = (
            (not rows, "behaviour_governance_evidence_missing"),
            (not unique, "duplicate_or_invalid_behaviour_confidence_calibration_id"),
            (not chronology, "market_behaviour_governance_chronology_invalid"),
            (not accepted_pack_7, "pack_7_behaviour_calibration_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not finite, "non_finite_behaviour_governance_metric"),
            (not separation, "reviewer_approval_role_separation_invalid"),
            (not policy_valid, "feature_freeze_policy_version_invalid"),
            (not calibration_count_met, "minimum_calibration_count_not_met"),
            (not transition_count_met, "minimum_transition_count_not_met"),
            (not confidence_met, "minimum_behaviour_governance_confidence_not_met"),
            (not policies_valid, "locked_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        accepted = not blocked

        identity = {
            "ids": ids, "timestamps": timestamps, "policy": policy,
            "reviewer": reviewer, "approver": approver, "blocked": blocked,
            "minimum_calibration_count": int(minimum_calibration_count),
            "minimum_total_transition_count": int(minimum_total_transition_count),
            "minimum_mean_confidence": float(minimum_mean_confidence),
        }
        governance_id = "PBGV-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()

        if accepted:
            reason = "MARKET_BEHAVIOUR_VALIDATION_GOVERNANCE_READY_FOR_MANUAL_REVIEW"
            en = "Accepted Pack 7 market-behaviour calibrations passed deterministic governance checks and are retained for manual research review only."
            th = "ผล Calibration พฤติกรรมตลาดจาก Pack 7 ผ่านการตรวจ Governance แบบ Deterministic และถูกเก็บไว้เพื่อการทบทวนงานวิจัยด้วยมนุษย์เท่านั้น"
            next_en = "Perform documented manual review in Milestone P Pack 9; do not tune parameters or promote knowledge automatically."
            next_th = "ดำเนินการทบทวนแบบมีเอกสารใน Milestone P Pack 9 และห้ามปรับ Parameter หรือเลื่อน Knowledge อัตโนมัติ"
        else:
            reason = "MARKET_BEHAVIOUR_VALIDATION_GOVERNANCE_BLOCKED"
            en = "Governance validation was blocked because lineage, chronology, role separation, policy, quality, coverage, confidence, regime order, future safety, or locked controls failed."
            th = "การตรวจ Governance ถูกระงับเนื่องจาก Lineage, ลำดับเวลา, การแยกหน้าที่, Policy, คุณภาพ, Coverage, Confidence, ลำดับ Market Regime, Future Safety หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Investigate blocked governance evidence and retain all adaptive and execution authority as disabled."
            next_th = "ตรวจสอบหลักฐาน Governance ที่ถูกระงับ และคง Adaptive กับ Execution authority ไว้ที่ปิด"

        return MarketBehaviourValidationGovernanceReport(
            status="READY" if accepted else "BLOCKED", reason=reason, milestone="P", pack="8",
            governance_validation_id=governance_id, confidence_calibration_ids=ids,
            calibration_count=len(rows), total_transition_count=total_transitions,
            mean_calibrated_confidence=mean_confidence, minimum_calibrated_confidence=round(min_confidence, 8),
            policy_version=policy, review_role=reviewer, approval_role=approver,
            pack_7_calibrations_accepted=accepted_pack_7, unique_calibration_lineage=unique,
            chronology_valid=chronology, reviewer_separation_valid=separation,
            policy_version_valid=policy_valid, minimum_calibration_count_met=calibration_count_met,
            minimum_transition_count_met=transition_count_met, confidence_threshold_met=confidence_met,
            data_quality_certified=quality, future_safe=future_safe,
            market_regime_before_behaviour=regime_first, finite_metrics=finite,
            locked_policy_valid=policies_valid, governance_accepted=accepted,
            manual_review_required=True, automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False, production_knowledge_allowed=False,
            production_certification_granted=False, research_only=True,
            block_reasons=blocked, explanation_reason_en=en, explanation_reason_th=th,
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
        )
