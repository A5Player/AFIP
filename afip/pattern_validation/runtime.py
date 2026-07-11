"""Milestone M Pack 6: deterministic research pattern validation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternValidationResult:
    scope_id: str
    scope_type: str
    market_regime: str
    sample_count: int
    expectancy_r: float
    profit_factor: float
    win_rate: float
    r_standard_deviation: float
    sample_gate_passed: bool
    expectancy_gate_passed: bool
    profit_factor_gate_passed: bool
    dispersion_gate_passed: bool
    lineage_gate_passed: bool
    validated: bool
    confidence_tier: str
    source_lineages: tuple[str, ...]
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternValidationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    validation_id: str
    knowledge_version: str
    source_statistics_count: int
    eligible_statistics_count: int
    validated_pattern_count: int
    validated_cluster_count: int
    rejected_scope_count: int
    minimum_sample_size: int
    minimum_expectancy_r: float
    minimum_profit_factor: float
    maximum_r_standard_deviation: float
    statistics_lineage_valid: bool
    threshold_configuration_valid: bool
    deterministic_validation_valid: bool
    future_safe: bool
    research_only: bool
    pattern_statistics_enabled: bool
    pattern_validation_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    validations: tuple[PatternValidationResult, ...]
    block_reasons: tuple[str, ...]
    validation_reason_en: str
    validation_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["validations"] = [item.as_dict() for item in self.validations]
        return payload


class PatternValidationRuntime:
    """Validates research pattern statistics without granting execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternValidationReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.6.0-RESEARCH")).strip() or "M1.6.0-RESEARCH"
        statistics = self._records(record.get("statistics", ()))
        minimum_sample_size = max(1, int(self._number(record.get("minimum_sample_size", 20)) or 20))
        minimum_expectancy_r = float(self._number(record.get("minimum_expectancy_r", 0.05)) or 0.05)
        minimum_profit_factor = float(self._number(record.get("minimum_profit_factor", 1.05)) or 1.05)
        maximum_r_standard_deviation = float(self._number(record.get("maximum_r_standard_deviation", 3.0)) or 3.0)

        threshold_configuration_valid = (
            minimum_sample_size > 0
            and minimum_profit_factor >= 1.0
            and maximum_r_standard_deviation > 0.0
        )
        scope_ids = [str(item.get("scope_id", "")).strip() for item in statistics]
        statistics_lineage_valid = bool(statistics) and len(scope_ids) == len(set(scope_ids)) and all(scope_ids)
        normalized: list[dict[str, Any]] = []
        for item in statistics:
            lineages = tuple(sorted(set(str(value).strip() for value in item.get("source_lineages", ()) if str(value).strip())))
            sample_count = self._integer(item.get("sample_count"))
            expectancy = self._number(item.get("expectancy_r"))
            profit_factor = self._number(item.get("profit_factor"))
            win_rate = self._number(item.get("win_rate"))
            dispersion = self._number(item.get("r_standard_deviation"))
            scope_id = str(item.get("scope_id", "")).strip()
            scope_type = str(item.get("scope_type", "")).strip().upper()
            regime = str(item.get("market_regime", "UNKNOWN")).strip().upper()
            if (
                not scope_id or scope_type not in {"PATTERN", "CLUSTER"} or not regime
                or sample_count is None or sample_count < 0
                or expectancy is None or profit_factor is None or win_rate is None or dispersion is None
                or not 0.0 <= win_rate <= 1.0 or dispersion < 0.0 or not lineages
            ):
                statistics_lineage_valid = False
                continue
            normalized.append({
                "scope_id": scope_id,
                "scope_type": scope_type,
                "market_regime": regime,
                "sample_count": sample_count,
                "expectancy_r": float(expectancy),
                "profit_factor": float(profit_factor),
                "win_rate": float(win_rate),
                "r_standard_deviation": float(dispersion),
                "confidence_tier": str(item.get("confidence_tier", "LOW_SAMPLE")).strip().upper(),
                "source_lineages": lineages,
            })

        blocked: list[str] = []
        if not bool(record.get("pattern_statistics_ready", False)):
            blocked.append("pattern_statistics_not_ready")
        if not bool(record.get("research_knowledge_approved", False)):
            blocked.append("research_knowledge_not_approved")
        if not statistics_lineage_valid or len(normalized) != len(statistics):
            blocked.append("statistics_lineage_invalid")
        if not threshold_configuration_valid:
            blocked.append("threshold_configuration_invalid")
        if bool(record.get("future_leakage_detected", False)):
            blocked.append("future_leakage_detected")
        if not bool(record.get("data_quality_certified", False)):
            blocked.append("data_quality_not_certified")
        if broker != "XM":
            blocked.append("broker_policy_violation")
        if symbol != "GOLD#":
            blocked.append("symbol_policy_violation")
        if abs(lot - 0.01) > 1e-12:
            blocked.append("base_unit_policy_violation")
        if execution_status != "LOCKED_SIMULATION_ONLY":
            blocked.append("execution_lock_invalid")
        if order_status != "NO_ORDER_SENT":
            blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        validations: tuple[PatternValidationResult, ...] = ()
        if not blocked:
            built: list[PatternValidationResult] = []
            for item in normalized:
                sample_gate = item["sample_count"] >= minimum_sample_size
                expectancy_gate = item["expectancy_r"] >= minimum_expectancy_r
                profit_gate = item["profit_factor"] >= minimum_profit_factor
                dispersion_gate = item["r_standard_deviation"] <= maximum_r_standard_deviation
                lineage_gate = bool(item["source_lineages"])
                reasons = []
                if not sample_gate:
                    reasons.append("insufficient_sample")
                if not expectancy_gate:
                    reasons.append("expectancy_below_threshold")
                if not profit_gate:
                    reasons.append("profit_factor_below_threshold")
                if not dispersion_gate:
                    reasons.append("dispersion_above_threshold")
                if not lineage_gate:
                    reasons.append("lineage_invalid")
                validated = not reasons
                built.append(PatternValidationResult(
                    scope_id=item["scope_id"], scope_type=item["scope_type"], market_regime=item["market_regime"],
                    sample_count=item["sample_count"], expectancy_r=round(item["expectancy_r"], 6),
                    profit_factor=round(item["profit_factor"], 6), win_rate=round(item["win_rate"], 6),
                    r_standard_deviation=round(item["r_standard_deviation"], 6),
                    sample_gate_passed=sample_gate, expectancy_gate_passed=expectancy_gate,
                    profit_factor_gate_passed=profit_gate, dispersion_gate_passed=dispersion_gate,
                    lineage_gate_passed=lineage_gate, validated=validated,
                    confidence_tier=item["confidence_tier"], source_lineages=item["source_lineages"],
                    reasons=tuple(reasons),
                ))
            validations = tuple(sorted(built, key=lambda item: (item.scope_type, item.market_regime, item.scope_id)))

        identity = {
            "knowledge_version": knowledge_version,
            "thresholds": [minimum_sample_size, minimum_expectancy_r, minimum_profit_factor, maximum_r_standard_deviation],
            "validations": [item.as_dict() for item in validations],
        }
        validation_id = "PVAL-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocked
        validated_patterns = sum(item.validated and item.scope_type == "PATTERN" for item in validations)
        validated_clusters = sum(item.validated and item.scope_type == "CLUSTER" for item in validations)
        rejected = sum(not item.validated for item in validations)
        return PatternValidationReport(
            status="READY" if ready else "BLOCKED",
            reason="Pattern validation completed under research-only controls." if ready else "Pattern validation blocked by integrity or safety controls.",
            milestone="M", pack="6", validation_id=validation_id, knowledge_version=knowledge_version,
            source_statistics_count=len(statistics), eligible_statistics_count=len(normalized),
            validated_pattern_count=validated_patterns, validated_cluster_count=validated_clusters,
            rejected_scope_count=rejected, minimum_sample_size=minimum_sample_size,
            minimum_expectancy_r=minimum_expectancy_r, minimum_profit_factor=minimum_profit_factor,
            maximum_r_standard_deviation=maximum_r_standard_deviation,
            statistics_lineage_valid=statistics_lineage_valid,
            threshold_configuration_valid=threshold_configuration_valid,
            deterministic_validation_valid=ready, future_safe=not bool(record.get("future_leakage_detected", False)),
            research_only=True, pattern_statistics_enabled=ready, pattern_validation_enabled=ready,
            production_knowledge_approved=False,
            research_knowledge_approved=ready and bool(record.get("research_knowledge_approved", False)),
            validations=validations, block_reasons=tuple(sorted(set(blocked))),
            validation_reason_en="Applies explicit sample, expectancy, profit-factor, dispersion, and lineage gates to research statistics." if ready else "Validation remains blocked until statistics, lineage, thresholds, data quality, and safety controls pass.",
            validation_reason_th="ใช้เกณฑ์ Sample, Expectancy, Profit Factor, Dispersion และ Lineage ที่ชัดเจนกับสถิติสำหรับงานวิจัย" if ready else "การตรวจสอบยังถูกบล็อกจนกว่าสถิติ Lineage Threshold คุณภาพข้อมูล และ Safety Control จะผ่านครบ",
            expected_next_action_en="Continue to Milestone M Pack 7 — Pattern Explainability." if ready else "Correct blocked inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone M Pack 7 — Pattern Explainability" if ready else "แก้ข้อมูลที่ถูกบล็อกแล้วประเมินใหม่",
        )

    @staticmethod
    def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return None
        return number
