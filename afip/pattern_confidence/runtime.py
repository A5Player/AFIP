"""Milestone M Pack 9: deterministic pattern confidence controls."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import exp
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternConfidenceEntry:
    confidence_id: str
    scope_id: str
    scope_type: str
    market_regime: str
    sample_count: int
    expectancy_r: float
    profit_factor: float
    dispersion_r: float
    validation_status: str
    confidence_score: float
    confidence_tier: str
    confidence_reasons: tuple[str, ...]
    source_lineages: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternConfidenceReport:
    status: str
    reason: str
    milestone: str
    pack: str
    evaluation_id: str
    knowledge_version: str
    source_scope_count: int
    eligible_scope_count: int
    scored_scope_count: int
    high_confidence_count: int
    medium_confidence_count: int
    low_confidence_count: int
    confidence_bounds_valid: bool
    lineage_integrity_valid: bool
    deterministic_scoring_valid: bool
    market_regime_context_valid: bool
    future_safe: bool
    research_only: bool
    pattern_confidence_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    entries: tuple[PatternConfidenceEntry, ...]
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
        payload["entries"] = [entry.as_dict() for entry in self.entries]
        return payload


class PatternConfidenceRuntime:
    """Scores validated research patterns without granting production authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternConfidenceReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.9.0-RESEARCH")).strip() or "M1.9.0-RESEARCH"
        raw_scopes = self._records(record.get("confidence_scopes", ()))

        lineage_valid = True
        regime_valid = True
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in raw_scopes:
            scope_id = str(item.get("scope_id", "")).strip()
            scope_type = str(item.get("scope_type", "")).strip().upper()
            regime = str(item.get("market_regime", "")).strip().upper()
            lineages = tuple(sorted(set(str(v).strip() for v in item.get("source_lineages", ()) if str(v).strip())))
            if not lineages:
                lineage_valid = False
            if not regime or regime == "UNKNOWN":
                regime_valid = False
            if not scope_id or scope_id in seen or scope_type not in {"PATTERN", "CLUSTER"}:
                continue
            seen.add(scope_id)
            sample_count = max(0, int(self._number(item.get("sample_count", 0), 0)))
            expectancy = self._number(item.get("expectancy_r", 0.0), 0.0)
            profit_factor = max(0.0, self._number(item.get("profit_factor", 0.0), 0.0))
            dispersion = max(0.0, self._number(item.get("dispersion_r", 0.0), 0.0))
            validation_status = str(item.get("validation_status", "REJECTED")).strip().upper()
            normalized.append({
                "scope_id": scope_id, "scope_type": scope_type, "market_regime": regime,
                "sample_count": sample_count, "expectancy_r": expectancy,
                "profit_factor": profit_factor, "dispersion_r": dispersion,
                "validation_status": validation_status, "source_lineages": lineages,
            })

        blocked: list[str] = []
        if not bool(record.get("historical_pattern_database_ready", False)):
            blocked.append("historical_pattern_database_not_ready")
        if not bool(record.get("research_knowledge_approved", False)):
            blocked.append("research_knowledge_not_approved")
        if not bool(record.get("data_quality_certified", False)):
            blocked.append("data_quality_not_certified")
        if not lineage_valid:
            blocked.append("lineage_integrity_invalid")
        if not regime_valid:
            blocked.append("market_regime_context_invalid")
        if bool(record.get("future_leakage_detected", False)):
            blocked.append("future_leakage_detected")
        if broker != "XM": blocked.append("broker_policy_violation")
        if symbol != "GOLD#": blocked.append("symbol_policy_violation")
        if abs(lot - 0.01) > 1e-12: blocked.append("base_unit_policy_violation")
        if execution_status != "LOCKED_SIMULATION_ONLY": blocked.append("execution_lock_invalid")
        if order_status != "NO_ORDER_SENT": blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        entries: list[PatternConfidenceEntry] = []
        if not blocked:
            for item in sorted(normalized, key=lambda x: (x["market_regime"], x["scope_type"], x["scope_id"])):
                sample_component = min(1.0, item["sample_count"] / 100.0)
                expectancy_component = 1.0 / (1.0 + exp(-3.0 * item["expectancy_r"]))
                pf_component = min(1.0, item["profit_factor"] / 2.0)
                stability_component = 1.0 / (1.0 + item["dispersion_r"])
                validation_component = 1.0 if item["validation_status"] == "VALIDATED" else 0.0
                score = round(100.0 * (
                    0.25 * sample_component + 0.25 * expectancy_component +
                    0.20 * pf_component + 0.15 * stability_component +
                    0.15 * validation_component
                ), 2)
                score = max(0.0, min(100.0, score))
                tier = "HIGH" if score >= 75.0 else "MEDIUM" if score >= 50.0 else "LOW"
                reasons = (
                    f"sample_count={item['sample_count']}",
                    f"expectancy_r={item['expectancy_r']:.4f}",
                    f"profit_factor={item['profit_factor']:.4f}",
                    f"dispersion_r={item['dispersion_r']:.4f}",
                    f"validation_status={item['validation_status']}",
                )
                identity = {**item, "knowledge_version": knowledge_version, "confidence_score": score}
                cid = "PCONF-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
                entries.append(PatternConfidenceEntry(confidence_id=cid, confidence_score=score,
                    confidence_tier=tier, confidence_reasons=reasons, **item))

        identity = {"knowledge_version": knowledge_version, "entries": [e.as_dict() for e in entries]}
        evaluation_id = "PCEVAL-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocked
        return PatternConfidenceReport(
            status="READY" if ready else "BLOCKED",
            reason="Pattern confidence calibrated under research-only controls." if ready else "Pattern confidence blocked by integrity or safety controls.",
            milestone="M", pack="9", evaluation_id=evaluation_id, knowledge_version=knowledge_version,
            source_scope_count=len(raw_scopes), eligible_scope_count=len(normalized), scored_scope_count=len(entries),
            high_confidence_count=sum(e.confidence_tier == "HIGH" for e in entries),
            medium_confidence_count=sum(e.confidence_tier == "MEDIUM" for e in entries),
            low_confidence_count=sum(e.confidence_tier == "LOW" for e in entries),
            confidence_bounds_valid=all(0.0 <= e.confidence_score <= 100.0 for e in entries),
            lineage_integrity_valid=lineage_valid, deterministic_scoring_valid=True,
            market_regime_context_valid=regime_valid, future_safe="future_leakage_detected" not in blocked,
            research_only=True, pattern_confidence_enabled=ready,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            entries=tuple(entries), block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Calibrates bounded confidence from sample strength, expectancy, profit factor, stability and validation status." if ready else "Confidence scoring is blocked until integrity and safety controls pass.",
            explanation_reason_th="ปรับเทียบค่าความเชื่อมั่นแบบมีขอบเขตจากจำนวนตัวอย่าง Expectancy, Profit Factor, Stability และสถานะ Validation" if ready else "การคำนวณความเชื่อมั่นถูกบล็อกจนกว่าการตรวจความสมบูรณ์และความปลอดภัยจะผ่าน",
            expected_next_action_en="Continue to Milestone M Pack 10 — Knowledge Intelligence Complete." if ready else "Correct blocked inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone M Pack 10 — Knowledge Intelligence Complete" if ready else "แก้ข้อมูลที่ถูกบล็อกแล้วประเมินใหม่",
            broker=broker, symbol=symbol, lot_per_unit=lot,
        )

    @staticmethod
    def _records(value: Any) -> list[Mapping[str, Any]]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [v for v in value if isinstance(v, Mapping)]
        return []

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
            return number if number == number else default
        except (TypeError, ValueError):
            return default
