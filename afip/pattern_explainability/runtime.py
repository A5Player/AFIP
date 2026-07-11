"""Milestone M Pack 7: deterministic research pattern explainability."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternExplanation:
    scope_id: str
    scope_type: str
    market_regime: str
    validated: bool
    explanation_status: str
    primary_reason: str
    supporting_reasons: tuple[str, ...]
    risk_notes: tuple[str, ...]
    feature_contributions: tuple[tuple[str, float], ...]
    source_lineages: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternExplainabilityReport:
    status: str
    reason: str
    milestone: str
    pack: str
    explainability_id: str
    knowledge_version: str
    source_validation_count: int
    eligible_validation_count: int
    explained_scope_count: int
    validated_scope_count: int
    rejected_scope_count: int
    explanation_coverage: float
    validation_lineage_valid: bool
    feature_contribution_schema_valid: bool
    deterministic_explainability_valid: bool
    future_safe: bool
    research_only: bool
    pattern_validation_enabled: bool
    pattern_explainability_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    explanations: tuple[PatternExplanation, ...]
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
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
        payload["explanations"] = [item.as_dict() for item in self.explanations]
        return payload


class PatternExplainabilityRuntime:
    """Builds auditable explanations for validated and rejected research scopes."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternExplainabilityReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.7.0-RESEARCH")).strip() or "M1.7.0-RESEARCH"
        validations = self._records(record.get("validations", ()))

        scope_ids = [str(item.get("scope_id", "")).strip() for item in validations]
        validation_lineage_valid = bool(validations) and len(scope_ids) == len(set(scope_ids)) and all(scope_ids)
        feature_contribution_schema_valid = True
        normalized: list[dict[str, Any]] = []
        for item in validations:
            scope_id = str(item.get("scope_id", "")).strip()
            scope_type = str(item.get("scope_type", "")).strip().upper()
            regime = str(item.get("market_regime", "UNKNOWN")).strip().upper()
            lineages = tuple(sorted(set(str(v).strip() for v in item.get("source_lineages", ()) if str(v).strip())))
            reasons = tuple(sorted(set(str(v).strip() for v in item.get("reasons", ()) if str(v).strip())))
            validated = bool(item.get("validated", False))
            metrics = {
                "sample_count": self._number(item.get("sample_count")),
                "expectancy_r": self._number(item.get("expectancy_r")),
                "profit_factor": self._number(item.get("profit_factor")),
                "win_rate": self._number(item.get("win_rate")),
                "r_standard_deviation": self._number(item.get("r_standard_deviation")),
            }
            if (
                not scope_id or scope_type not in {"PATTERN", "CLUSTER"} or not regime or not lineages
                or any(value is None for value in metrics.values())
                or not 0.0 <= float(metrics["win_rate"]) <= 1.0
                or float(metrics["r_standard_deviation"]) < 0.0
            ):
                validation_lineage_valid = False
                feature_contribution_schema_valid = False
                continue
            normalized.append({
                "scope_id": scope_id,
                "scope_type": scope_type,
                "market_regime": regime,
                "validated": validated,
                "reasons": reasons,
                "source_lineages": lineages,
                **{key: float(value) for key, value in metrics.items()},
            })

        blocked: list[str] = []
        if not bool(record.get("pattern_validation_ready", False)):
            blocked.append("pattern_validation_not_ready")
        if not bool(record.get("research_knowledge_approved", False)):
            blocked.append("research_knowledge_not_approved")
        if not validation_lineage_valid or len(normalized) != len(validations):
            blocked.append("validation_lineage_invalid")
        if not feature_contribution_schema_valid:
            blocked.append("feature_contribution_schema_invalid")
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

        explanations: tuple[PatternExplanation, ...] = ()
        if not blocked:
            built: list[PatternExplanation] = []
            for item in normalized:
                contributions = (
                    ("expectancy_r", round(item["expectancy_r"], 6)),
                    ("profit_factor", round(item["profit_factor"] - 1.0, 6)),
                    ("win_rate", round(item["win_rate"] - 0.5, 6)),
                    ("sample_strength", round(min(item["sample_count"] / 100.0, 1.0), 6)),
                    ("dispersion_penalty", round(-min(item["r_standard_deviation"] / 10.0, 1.0), 6)),
                )
                ordered = tuple(sorted(contributions, key=lambda pair: (-abs(pair[1]), pair[0])))
                if item["validated"]:
                    primary = "validated_by_statistical_and_lineage_gates"
                    supporting = (
                        "sample_expectancy_profit_factor_and_dispersion_gates_passed",
                        "market_regime_context_preserved",
                        "source_lineage_verified",
                    )
                    risk_notes = ("research_only_not_production_authority",)
                    status = "EXPLAINED_VALIDATED"
                else:
                    primary = item["reasons"][0] if item["reasons"] else "validation_rejected"
                    supporting = item["reasons"] or ("validation_rejected_without_additional_reason",)
                    risk_notes = ("scope_not_eligible_for_knowledge_promotion", "research_only_not_production_authority")
                    status = "EXPLAINED_REJECTED"
                built.append(PatternExplanation(
                    scope_id=item["scope_id"], scope_type=item["scope_type"], market_regime=item["market_regime"],
                    validated=item["validated"], explanation_status=status, primary_reason=primary,
                    supporting_reasons=tuple(supporting), risk_notes=tuple(risk_notes),
                    feature_contributions=ordered, source_lineages=item["source_lineages"],
                ))
            explanations = tuple(sorted(built, key=lambda x: (x.scope_type, x.market_regime, x.scope_id)))

        identity = {
            "knowledge_version": knowledge_version,
            "explanations": [item.as_dict() for item in explanations],
        }
        explainability_id = "PEXP-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocked
        validated_count = sum(item.validated for item in explanations)
        rejected_count = sum(not item.validated for item in explanations)
        coverage = round(len(explanations) / len(validations), 6) if validations else 0.0
        return PatternExplainabilityReport(
            status="READY" if ready else "BLOCKED",
            reason="Pattern explainability completed under research-only controls." if ready else "Pattern explainability blocked by integrity or safety controls.",
            milestone="M", pack="7", explainability_id=explainability_id, knowledge_version=knowledge_version,
            source_validation_count=len(validations), eligible_validation_count=len(normalized),
            explained_scope_count=len(explanations), validated_scope_count=validated_count,
            rejected_scope_count=rejected_count, explanation_coverage=coverage,
            validation_lineage_valid=validation_lineage_valid,
            feature_contribution_schema_valid=feature_contribution_schema_valid,
            deterministic_explainability_valid=ready,
            future_safe=not bool(record.get("future_leakage_detected", False)),
            research_only=True, pattern_validation_enabled=ready, pattern_explainability_enabled=ready,
            production_knowledge_approved=False,
            research_knowledge_approved=ready and bool(record.get("research_knowledge_approved", False)),
            explanations=explanations, block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Provides auditable reasons, risk notes, and bounded feature contributions for every validated or rejected research scope." if ready else "Explainability remains blocked until validation lineage, data quality, and safety controls pass.",
            explanation_reason_th="แสดงเหตุผล Risk Note และ Feature Contribution ที่ตรวจสอบย้อนหลังได้สำหรับทุก Scope ที่ผ่านหรือไม่ผ่านการตรวจสอบ" if ready else "Explainability ยังถูกบล็อกจนกว่า Validation Lineage คุณภาพข้อมูล และ Safety Control จะผ่านครบ",
            expected_next_action_en="Continue to Milestone M Pack 8 — Historical Pattern Database." if ready else "Correct blocked inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone M Pack 8 — Historical Pattern Database" if ready else "แก้ข้อมูลที่ถูกบล็อกแล้วประเมินใหม่",
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
