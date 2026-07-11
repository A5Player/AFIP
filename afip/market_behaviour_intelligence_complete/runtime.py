"""Milestone P Pack 10: deterministic Market Behaviour Intelligence completion certification.

Closes Milestone P by validating capability lineage for Packs 1-9 and accepted
manual review certification. This runtime is research-only and grants no adaptive,
production, position-management, broker, or order-transmission authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketBehaviourIntelligenceCompleteReport:
    status: str
    reason: str
    milestone: str
    pack: str
    completion_id: str
    completed_pack_ids: tuple[str, ...]
    completed_pack_count: int
    review_certification_id: str
    pack_1_to_9_complete: bool
    unique_capability_lineage: bool
    pack_9_review_certified: bool
    data_quality_certified: bool
    future_safe: bool
    deterministic_runtime: bool
    market_regime_before_behaviour: bool
    chronology_valid: bool
    feature_freeze_valid: bool
    market_behaviour_intelligence_complete: bool
    ready_for_milestone_q: bool
    production_certification_granted: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
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


class MarketBehaviourIntelligenceCompleteRuntime:
    """Certify Milestone P completion without granting adaptive or execution authority."""

    REQUIRED_PACKS = tuple(range(1, 10))

    def evaluate_one(self, payload: Mapping[str, Any]) -> MarketBehaviourIntelligenceCompleteReport:
        data = dict(payload)
        capability_rows = [dict(row) for row in data.get("capabilities", ())]
        pack_ids = tuple(str(row.get("capability_id", "")).strip().upper() for row in capability_rows)
        pack_numbers = tuple(self._integer(row.get("pack", 0)) for row in capability_rows)
        unique_lineage = bool(pack_ids) and len(pack_ids) == len(set(pack_ids)) and all(
            identifier.startswith("PBEHAV-") for identifier in pack_ids
        )
        packs_complete = set(pack_numbers) == set(self.REQUIRED_PACKS) and len(pack_numbers) == len(self.REQUIRED_PACKS) and all(
            str(row.get("status", "")).strip().upper() == "COMPLETE" for row in capability_rows
        )

        review = dict(data.get("pack_9_review", {}))
        review_id = str(review.get("review_certification_id", "")).strip().upper()
        review_certified = (
            review_id.startswith("PBCERT-")
            and str(review.get("status", "")).strip().upper() == "READY"
            and bool(review.get("review_certified", False))
            and bool(review.get("manual_review_completed", False))
        )
        quality = bool(data.get("data_quality_certified", False)) and all(
            bool(row.get("data_quality_certified", False)) for row in capability_rows
        )
        future_safe = bool(data.get("future_safe", False)) and not bool(data.get("future_leakage_detected", False)) and all(
            bool(row.get("future_safe", False)) and not bool(row.get("future_leakage_detected", False))
            for row in capability_rows
        )
        deterministic = bool(data.get("deterministic_runtime", False)) and all(
            bool(row.get("deterministic_runtime", False)) for row in capability_rows
        )
        regime_first = bool(data.get("market_regime_before_behaviour", False)) and all(
            bool(row.get("market_regime_before_behaviour", False)) for row in capability_rows
        )
        timestamps = [self._integer(row.get("completed_timestamp", 0)) for row in capability_rows]
        chronology = bool(timestamps) and all(ts > 0 for ts in timestamps) and timestamps == sorted(timestamps)

        policy_valid = (
            str(data.get("policy_version", "")).strip().upper() == "AFIP_V1_FEATURE_FREEZE"
            and str(data.get("broker", "XM")).strip().upper() == "XM"
            and str(data.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(data.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(data.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(data.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(data.get("direct_execution", False))
            and not bool(data.get("live_execution_enabled", False))
            and not bool(data.get("automatic_parameter_update_allowed", False))
            and not bool(data.get("trading_logic_change_allowed", False))
            and not bool(data.get("production_knowledge_allowed", False))
            and not bool(data.get("production_certification_granted", False))
        )

        checks = (
            (not packs_complete, "milestone_p_pack_1_to_9_incomplete"),
            (not unique_lineage, "duplicate_or_invalid_market_behaviour_capability_lineage"),
            (not review_certified, "pack_9_market_behaviour_review_certification_not_accepted"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not deterministic, "deterministic_runtime_not_certified"),
            (not regime_first, "market_regime_before_behaviour_not_certified"),
            (not chronology, "market_behaviour_completion_chronology_invalid"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        complete = not blocked

        identity = {
            "pack_ids": pack_ids,
            "pack_numbers": pack_numbers,
            "review_id": review_id,
            "blocked": blocked,
        }
        completion_id = "PCOMP-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        if complete:
            reason = "MARKET_BEHAVIOUR_INTELLIGENCE_COMPLETE"
            en = "Milestone P Packs 1-9 and documented manual review were certified as complete for research-only progression."
            th = "Milestone P Pack 1-9 และการทบทวนด้วยมนุษย์ที่มีเอกสารได้รับการรับรองว่าครบถ้วนสำหรับการดำเนินงานวิจัยต่อเท่านั้น"
            next_en = "Proceed to Milestone Q Pack 1 — Market Intent Intelligence Foundation; production certification remains pending Milestone R."
            next_th = "ดำเนินการต่อไปยัง Milestone Q Pack 1 — Market Intent Intelligence Foundation โดย Production Certification ยังคงรอ Milestone R"
        else:
            reason = "MARKET_BEHAVIOUR_INTELLIGENCE_COMPLETION_BLOCKED"
            en = "Milestone P completion was blocked because capability lineage, review certification, chronology, data integrity, future safety, deterministic controls, market-regime ordering, or frozen policy failed."
            th = "การปิด Milestone P ถูกระงับเนื่องจาก Capability lineage, Review certification, ลำดับเวลา, Data Integrity, Future Safety, Deterministic Control, ลำดับ Market Regime หรือนโยบายล็อกไม่ผ่าน"
            next_en = "Correct only the blocked certification evidence and keep all adaptive, production, and execution authority disabled."
            next_th = "แก้ไขเฉพาะหลักฐานการรับรองที่ถูกระงับ และคง Adaptive, Production และ Execution authority ไว้ที่ปิด"

        return MarketBehaviourIntelligenceCompleteReport(
            status="READY" if complete else "BLOCKED",
            reason=reason,
            milestone="P",
            pack="10",
            completion_id=completion_id,
            completed_pack_ids=pack_ids,
            completed_pack_count=len(pack_numbers),
            review_certification_id=review_id,
            pack_1_to_9_complete=packs_complete,
            unique_capability_lineage=unique_lineage,
            pack_9_review_certified=review_certified,
            data_quality_certified=quality,
            future_safe=future_safe,
            deterministic_runtime=deterministic,
            market_regime_before_behaviour=regime_first,
            chronology_valid=chronology,
            feature_freeze_valid=policy_valid,
            market_behaviour_intelligence_complete=complete,
            ready_for_milestone_q=complete,
            production_certification_granted=False,
            automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False,
            production_knowledge_allowed=False,
            research_only=True,
            block_reasons=blocked,
            explanation_reason_en=en,
            explanation_reason_th=th,
            expected_next_action_en=next_en,
            expected_next_action_th=next_th,
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
            return float("nan")
