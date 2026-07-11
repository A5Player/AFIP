"""Milestone N Pack 1: deterministic Portfolio Intelligence foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


_FORBIDDEN_METHODS = {
    "TRADITIONAL_DCA", "AVERAGING_DOWN", "MARTINGALE", "GRID_TRADING", "RECOVERY_TRADING"
}
_ALLOWED_LIFECYCLE = {
    "INDEPENDENT_TRADE_PLAN", "PROTECTED_RUNNER", "INDEPENDENT_POSITION_LIFECYCLE",
    "MULTI_DAY_POSITION_MANAGEMENT", "TRAILING_STOP", "PARTIAL_CLOSE",
    "DYNAMIC_STOP_LOSS", "DYNAMIC_TAKE_PROFIT",
}


@dataclass(frozen=True)
class PortfolioIntelligenceFoundationReport:
    status: str
    reason: str
    milestone: str
    pack: str
    foundation_id: str
    portfolio_version: str
    knowledge_completion_id: str
    milestone_m_complete: bool
    research_knowledge_approved: bool
    production_knowledge_approved: bool
    profile_count: int
    enabled_profile_count: int
    total_equity: float
    total_margin_used: float
    total_free_margin: float
    aggregate_risk_budget_percent: float
    exposure_snapshot_valid: bool
    capital_snapshot_valid: bool
    independent_position_lifecycle_valid: bool
    protected_runner_policy_valid: bool
    forbidden_methods_disabled: bool
    market_regime_before_signal: bool
    deterministic_runtime_valid: bool
    data_quality_certified: bool
    future_safe: bool
    portfolio_intelligence_foundation_ready: bool
    adaptive_position_sizing_enabled: bool
    portfolio_risk_engine_enabled: bool
    capital_allocation_enabled: bool
    feature_flags: tuple[tuple[str, bool], ...]
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
        payload["feature_flags"] = dict(self.feature_flags)
        return payload


class PortfolioIntelligenceFoundationRuntime:
    """Builds a read-only portfolio evidence boundary without execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PortfolioIntelligenceFoundationReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01), 0.01)
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        version = str(record.get("portfolio_version", "N1.1.0-RESEARCH")).strip() or "N1.1.0-RESEARCH"
        knowledge_completion_id = str(record.get("knowledge_completion_id", "")).strip()

        milestone_m_complete = bool(record.get("milestone_m_complete", False))
        research_approved = bool(record.get("research_knowledge_approved", False))
        production_approved = bool(record.get("production_knowledge_approved", False))
        profiles = self._mappings(record.get("profiles", ()))
        enabled_profiles = tuple(profile for profile in profiles if bool(profile.get("enabled", True)))

        equity_values = tuple(self._number(p.get("equity", 0.0), 0.0) for p in enabled_profiles)
        margin_values = tuple(self._number(p.get("margin_used", 0.0), 0.0) for p in enabled_profiles)
        free_margin_values = tuple(self._number(p.get("free_margin", 0.0), 0.0) for p in enabled_profiles)
        risk_values = tuple(self._number(p.get("risk_budget_percent", 0.0), 0.0) for p in enabled_profiles)
        position_ids = [str(pos.get("position_id", "")).strip() for p in enabled_profiles for pos in self._mappings(p.get("positions", ()))]

        exposure_valid = all(position_ids) and len(position_ids) == len(set(position_ids)) if position_ids else True
        capital_valid = bool(enabled_profiles) and all(
            equity >= 0.0 and margin >= 0.0 and free >= 0.0 and margin <= equity + 1e-9
            for equity, margin, free in zip(equity_values, margin_values, free_margin_values)
        )
        lifecycle = {str(v).strip().upper() for v in self._strings(record.get("allowed_position_lifecycle", ())) }
        independent_valid = "INDEPENDENT_TRADE_PLAN" in lifecycle and "INDEPENDENT_POSITION_LIFECYCLE" in lifecycle
        runner_valid = "PROTECTED_RUNNER" in lifecycle
        disabled = {str(v).strip().upper() for v in self._strings(record.get("disabled_methods", ())) }
        forbidden_disabled = _FORBIDDEN_METHODS.issubset(disabled)
        regime_first = bool(record.get("market_regime_before_signal", True))
        deterministic = bool(record.get("deterministic_runtime_valid", True))
        data_quality = bool(record.get("data_quality_certified", False))
        future_safe = not bool(record.get("future_leakage_detected", False))

        blocked: list[str] = []
        if not milestone_m_complete: blocked.append("milestone_m_incomplete")
        if not research_approved: blocked.append("research_knowledge_not_approved")
        if production_approved: blocked.append("production_knowledge_authority_forbidden")
        if not knowledge_completion_id: blocked.append("knowledge_completion_lineage_missing")
        if not enabled_profiles: blocked.append("enabled_profile_missing")
        if not exposure_valid: blocked.append("exposure_snapshot_invalid")
        if not capital_valid: blocked.append("capital_snapshot_invalid")
        if any(risk < 0.0 or risk > 100.0 for risk in risk_values): blocked.append("risk_budget_out_of_bounds")
        if not independent_valid: blocked.append("independent_position_lifecycle_missing")
        if not runner_valid: blocked.append("protected_runner_policy_missing")
        if not forbidden_disabled: blocked.append("forbidden_portfolio_method_enabled")
        if not regime_first: blocked.append("market_regime_sequence_invalid")
        if not deterministic: blocked.append("deterministic_runtime_invalid")
        if not data_quality: blocked.append("data_quality_not_certified")
        if not future_safe: blocked.append("future_leakage_detected")
        if broker != "XM": blocked.append("broker_policy_violation")
        if symbol != "GOLD#": blocked.append("symbol_policy_violation")
        if abs(lot - 0.01) > 1e-12: blocked.append("base_unit_policy_violation")
        if execution_status != "LOCKED_SIMULATION_ONLY": blocked.append("execution_lock_invalid")
        if order_status != "NO_ORDER_SENT": blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        ready = not blocked
        flags = tuple(sorted({
            "portfolio_intelligence_foundation": ready,
            "adaptive_position_sizing_enabled": False,
            "portfolio_risk_engine_enabled": False,
            "capital_allocation_enabled": False,
            "direct_execution_enabled": False,
            "live_execution_enabled": False,
        }.items()))
        identity = {
            "version": version,
            "knowledge_completion_id": knowledge_completion_id,
            "profiles": [
                {
                    "profile_id": str(p.get("profile_id", "")).strip(),
                    "enabled": bool(p.get("enabled", True)),
                    "equity": self._number(p.get("equity", 0.0), 0.0),
                    "margin_used": self._number(p.get("margin_used", 0.0), 0.0),
                    "free_margin": self._number(p.get("free_margin", 0.0), 0.0),
                    "risk_budget_percent": self._number(p.get("risk_budget_percent", 0.0), 0.0),
                }
                for p in sorted(profiles, key=lambda item: str(item.get("profile_id", "")))
            ],
            "blocked": sorted(set(blocked)),
        }
        foundation_id = "NPF-" + sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16].upper()

        return PortfolioIntelligenceFoundationReport(
            status="READY" if ready else "BLOCKED",
            reason="Portfolio Intelligence foundation is ready under research-only authority." if ready else "Portfolio Intelligence foundation is blocked by lineage, data, policy or safety controls.",
            milestone="N", pack="1", foundation_id=foundation_id,
            portfolio_version=version, knowledge_completion_id=knowledge_completion_id,
            milestone_m_complete=milestone_m_complete,
            research_knowledge_approved=research_approved,
            production_knowledge_approved=False,
            profile_count=len(profiles), enabled_profile_count=len(enabled_profiles),
            total_equity=round(sum(equity_values), 8),
            total_margin_used=round(sum(margin_values), 8),
            total_free_margin=round(sum(free_margin_values), 8),
            aggregate_risk_budget_percent=round(sum(risk_values), 8),
            exposure_snapshot_valid=exposure_valid,
            capital_snapshot_valid=capital_valid,
            independent_position_lifecycle_valid=independent_valid,
            protected_runner_policy_valid=runner_valid,
            forbidden_methods_disabled=forbidden_disabled,
            market_regime_before_signal=regime_first,
            deterministic_runtime_valid=deterministic,
            data_quality_certified=data_quality,
            future_safe=future_safe,
            portfolio_intelligence_foundation_ready=ready,
            adaptive_position_sizing_enabled=False,
            portfolio_risk_engine_enabled=False,
            capital_allocation_enabled=False,
            feature_flags=flags,
            block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Establishes a deterministic, read-only portfolio evidence boundary over profiles, capital, exposure and position lifecycle policies." if ready else "Foundation remains blocked until portfolio lineage, capital, exposure, policy and safety evidence is complete.",
            explanation_reason_th="สร้างขอบเขตหลักฐาน Portfolio แบบอ่านอย่างเดียวและ Deterministic ครอบคลุม Profile, Capital, Exposure และนโยบายวงจรชีวิต Position" if ready else "รากฐานยังถูกบล็อกจนกว่าหลักฐาน Lineage, Capital, Exposure, Policy และ Safety จะครบถ้วน",
            expected_next_action_en="Continue to Milestone N Pack 2 — Adaptive Position Sizing." if ready else "Correct blocked portfolio inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone N Pack 2 — Adaptive Position Sizing" if ready else "แก้ข้อมูล Portfolio ที่ถูกบล็อกแล้วประเมินใหม่",
            broker=broker, symbol=symbol, lot_per_unit=lot,
        )

    @staticmethod
    def _mappings(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return ()

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            number = float(value)
            return number if number == number else default
        except (TypeError, ValueError):
            return default
