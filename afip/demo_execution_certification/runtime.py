"""Deterministic demo-execution certification for Milestone L Pack 8."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class DemoExecutionCertificationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    certification_readiness: str
    demo_certification_id: str
    performance_certification_id: str
    total_observations: int
    eligible_observations: int
    minimum_observations_required: int
    sample_sufficient: bool
    ready_observations: int
    readiness_rate_percent: float
    minimum_readiness_rate_percent: float
    spread_pass_rate_percent: float
    minimum_spread_pass_rate_percent: float
    latency_pass_rate_percent: float
    minimum_latency_pass_rate_percent: float
    market_quality_valid: bool
    risk_validation_valid: bool
    timing_validation_valid: bool
    market_structure_valid: bool
    independent_trade_plan_valid: bool
    protected_runner_exposure_included: bool
    chronological_integrity_valid: bool
    unique_observation_ids_valid: bool
    certification_lineage_valid: bool
    traditional_dca_disabled: bool
    averaging_down_disabled: bool
    certified_for_demo_observation: bool
    certified_for_demo_execution: bool
    broker_request_created: bool
    order_transmission_attempted: bool
    block_reasons: tuple[str, ...]
    certification_reason_en: str
    certification_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DemoExecutionCertificationRuntime:
    """Certify shadow evidence for controlled demo observation without order transmission."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DemoExecutionCertificationReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        performance_id = str(record.get("performance_certification_id", "")).strip()
        observations = tuple(self._mapping_items(record.get("shadow_observations", ())))
        minimum = max(1, self._integer(record.get("minimum_observations_required", 20)) or 20)
        minimum_ready = self._bounded_percent(record.get("minimum_readiness_rate_percent", 90.0), 90.0)
        minimum_spread = self._bounded_percent(record.get("minimum_spread_pass_rate_percent", 95.0), 95.0)
        minimum_latency = self._bounded_percent(record.get("minimum_latency_pass_rate_percent", 95.0), 95.0)

        eligible = tuple(item for item in observations if self._eligible(item))
        ready_count = sum(self._ready(item) for item in eligible)
        spread_count = sum(bool(item.get("spread_valid", False)) for item in eligible)
        latency_count = sum(bool(item.get("latency_valid", False)) for item in eligible)
        denominator = len(eligible)
        readiness_rate = self._rate(ready_count, denominator)
        spread_rate = self._rate(spread_count, denominator)
        latency_rate = self._rate(latency_count, denominator)
        sample_sufficient = denominator >= minimum

        market_quality = bool(eligible) and all(
            bool(item.get("market_data_fresh", False)) and bool(item.get("market_session_open", False))
            for item in eligible
        )
        risk_valid = bool(eligible) and all(bool(item.get("risk_validation_valid", False)) for item in eligible)
        timing_valid = bool(eligible) and all(bool(item.get("timing_validation_valid", False)) for item in eligible)
        structure_valid = bool(eligible) and all(bool(item.get("market_structure_confirmed", False)) for item in eligible)
        independent_plan = bool(eligible) and all(bool(item.get("independent_trade_plan_valid", False)) for item in eligible)
        runner_exposure = bool(eligible) and all(bool(item.get("protected_runner_exposure_included", False)) for item in eligible)
        observation_ids = tuple(str(item.get("shadow_observation_id", "")).strip() for item in eligible)
        unique_ids = bool(observation_ids) and all(observation_ids) and len(set(observation_ids)) == len(observation_ids)
        lineage = bool(performance_id) and bool(eligible) and all(
            str(item.get("performance_certification_id", "")).strip() == performance_id for item in eligible
        )
        chronological = self._chronological(eligible)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()

        checks = {
            "performance_certification_id_missing": bool(performance_id),
            "shadow_observation_sample_insufficient": sample_sufficient,
            "readiness_rate_below_minimum": readiness_rate >= minimum_ready,
            "spread_pass_rate_below_minimum": spread_rate >= minimum_spread,
            "latency_pass_rate_below_minimum": latency_rate >= minimum_latency,
            "market_quality_invalid": market_quality,
            "risk_validation_failed": risk_valid,
            "timing_validation_failed": timing_valid,
            "market_structure_unconfirmed": structure_valid,
            "independent_trade_plan_invalid": independent_plan,
            "protected_runner_exposure_excluded": runner_exposure,
            "chronological_integrity_invalid": chronological,
            "duplicate_or_missing_observation_id": unique_ids,
            "certification_lineage_invalid": lineage,
            "traditional_dca_enabled": not bool(record.get("traditional_dca_enabled", False)),
            "averaging_down_enabled": not bool(record.get("averaging_down_enabled", False)),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
            "broker_request_created": not bool(record.get("broker_request_created", False)),
            "order_transmission_attempted": not bool(record.get("order_transmission_attempted", False)),
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        payload = {
            "performance_certification_id": performance_id,
            "observation_ids": observation_ids,
            "rates": [readiness_rate, spread_rate, latency_rate],
            "thresholds": [minimum, minimum_ready, minimum_spread, minimum_latency],
            "checks": checks,
        }
        certification_id = "L08-" + sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason, readiness = "READY", "demo_observation_certified", "DEMO_OBSERVATION_CERTIFIED"
            en = "Shadow evidence passed sample, execution-quality, risk, timing, structure, lineage, and safety gates for controlled demo observation."
            th = "หลักฐาน Shadow ผ่านเกณฑ์จำนวนตัวอย่าง คุณภาพ Execution ความเสี่ยง เวลา โครงสร้าง Lineage และความปลอดภัย สำหรับการสังเกตแบบ Demo ที่ควบคุมไว้"
            next_en = "Continue to the Production Release Candidate review; demo order transmission remains disabled until Version 1.0 production certification."
            next_th = "ดำเนินการต่อสู่การทบทวน Production Release Candidate โดยการส่งคำสั่ง Demo ยังคงปิดจนกว่าจะผ่าน Production Certification ของ Version 1.0"
        else:
            status, reason, readiness = "BLOCKED", blocks[0], "DEMO_CERTIFICATION_BLOCKED"
            en = "Demo certification was blocked because shadow evidence, policy, data integrity, or execution-safety requirements failed."
            th = "บล็อกการรับรอง Demo เพราะหลักฐาน Shadow นโยบาย ความสมบูรณ์ของข้อมูล หรือข้อกำหนดความปลอดภัยของ Execution ไม่ผ่าน"
            next_en = "Correct every block reason, collect additional chronological shadow evidence, and re-run certification without transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมด เก็บหลักฐาน Shadow ตามลำดับเวลาเพิ่ม และรับรองใหม่โดยไม่ส่งคำสั่งซื้อขาย"

        return DemoExecutionCertificationReport(
            status=status, reason=reason, milestone="MILESTONE_L", pack="PACK_8",
            certification_readiness=readiness, demo_certification_id=certification_id,
            performance_certification_id=performance_id, total_observations=len(observations),
            eligible_observations=denominator, minimum_observations_required=minimum,
            sample_sufficient=sample_sufficient, ready_observations=ready_count,
            readiness_rate_percent=readiness_rate, minimum_readiness_rate_percent=minimum_ready,
            spread_pass_rate_percent=spread_rate, minimum_spread_pass_rate_percent=minimum_spread,
            latency_pass_rate_percent=latency_rate, minimum_latency_pass_rate_percent=minimum_latency,
            market_quality_valid=market_quality, risk_validation_valid=risk_valid,
            timing_validation_valid=timing_valid, market_structure_valid=structure_valid,
            independent_trade_plan_valid=independent_plan,
            protected_runner_exposure_included=runner_exposure,
            chronological_integrity_valid=chronological, unique_observation_ids_valid=unique_ids,
            certification_lineage_valid=lineage,
            traditional_dca_disabled=not bool(record.get("traditional_dca_enabled", False)),
            averaging_down_disabled=not bool(record.get("averaging_down_enabled", False)),
            certified_for_demo_observation=ready, certified_for_demo_execution=False,
            broker_request_created=False, order_transmission_attempted=False,
            block_reasons=blocks, certification_reason_en=en, certification_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status,
            direct_execution=False, live_execution_enabled=False, order_status=order_status,
        )

    @staticmethod
    def _mapping_items(value: Any) -> Iterable[Mapping[str, Any]]:
        if isinstance(value, Mapping):
            return (value,)
        if isinstance(value, (str, bytes)) or value is None:
            return ()
        try:
            return tuple(item for item in value if isinstance(item, Mapping))
        except TypeError:
            return ()

    @staticmethod
    def _eligible(item: Mapping[str, Any]) -> bool:
        return (
            str(item.get("observation_readiness", "")).strip().upper() in {"SHADOW_OBSERVATION_READY", "SHADOW_OBSERVATION_BLOCKED"}
            and str(item.get("execution_status", "")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(item.get("order_status", "")).strip().upper() == "NO_ORDER_SENT"
            and not bool(item.get("broker_request_created", False))
            and not bool(item.get("order_transmission_attempted", False))
        )

    @staticmethod
    def _ready(item: Mapping[str, Any]) -> bool:
        return str(item.get("status", "")).strip().upper() == "READY" and not tuple(item.get("block_reasons", ()))

    @staticmethod
    def _chronological(items: tuple[Mapping[str, Any], ...]) -> bool:
        if not items:
            return False
        stamps = [str(item.get("observed_at_utc", item.get("next_review_time_utc", ""))).strip() for item in items]
        return all(stamps) and stamps == sorted(stamps)

    @staticmethod
    def _rate(numerator: int, denominator: int) -> float:
        return round((numerator / denominator * 100.0) if denominator else 0.0, 6)

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _bounded_percent(cls, value: Any, default: float) -> float:
        number = cls._number(value)
        if number <= 0.0:
            number = default
        return round(min(100.0, max(0.0, number)), 6)

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
