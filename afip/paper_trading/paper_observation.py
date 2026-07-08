"""Paper trading observation contract for Production Milestone G Pack 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PaperTradingObservation:
    """Normalized paper trading evidence for deterministic production simulation review."""

    market_regime: str
    signal_context: str
    runtime_component: str
    execution_mode: str
    configuration_version: str
    decision_action: str
    decision_confidence: float
    production_hardening_score: float
    risk_allowed: bool
    trading_cost_score: float
    paper_account_equity: float
    simulated_lot: float
    max_drawdown: float
    source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PaperTradingObservation":
        market_regime = str(value.get("market_regime", "")).strip().upper()
        signal_context = str(value.get("signal_context", value.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        runtime_component = str(value.get("runtime_component", value.get("component", "AFIP_RUNTIME"))).strip().upper() or "AFIP_RUNTIME"
        execution_mode = _mode(value.get("execution_mode", value.get("mode", "SIMULATION")))
        configuration_version = str(value.get("configuration_version", value.get("config_version", "v1"))).strip() or "v1"
        decision_action = _action(value.get("decision_action", value.get("action", "FLAT")))
        decision_confidence = _ratio(value.get("decision_confidence", value.get("confidence", 0.0)))
        production_hardening_score = _ratio(value.get("production_hardening_score", value.get("hardening_score", 0.0)))
        risk_allowed = _bool(value.get("risk_allowed", value.get("risk_pass", False)))
        trading_cost_score = _ratio(value.get("trading_cost_score", value.get("cost_score", 0.0)))
        paper_account_equity = _money(value.get("paper_account_equity", value.get("account_equity", 0.0)))
        simulated_lot = _money(value.get("simulated_lot", value.get("lot", 0.0)))
        max_drawdown = _ratio(value.get("max_drawdown", value.get("drawdown", 0.0)))
        source = str(value.get("source", "PAPER_TRADING")).strip().upper() or "PAPER_TRADING"
        return cls(
            market_regime=market_regime,
            signal_context=signal_context,
            runtime_component=runtime_component,
            execution_mode=execution_mode,
            configuration_version=configuration_version,
            decision_action=decision_action,
            decision_confidence=decision_confidence,
            production_hardening_score=production_hardening_score,
            risk_allowed=risk_allowed,
            trading_cost_score=trading_cost_score,
            paper_account_equity=paper_account_equity,
            simulated_lot=simulated_lot,
            max_drawdown=max_drawdown,
            source=source,
        )

    @property
    def has_market_regime(self) -> bool:
        return bool(self.market_regime)

    @property
    def simulation_only(self) -> bool:
        return self.execution_mode in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}

    @property
    def actionable_decision(self) -> bool:
        return self.decision_action in {"BUY", "SELL", "FLAT"}

    @property
    def account_ready(self) -> bool:
        return self.paper_account_equity > 0.0 and self.simulated_lot > 0.0

    @property
    def paper_quality(self) -> float:
        value = (
            self.decision_confidence * 0.22
            + self.production_hardening_score * 0.26
            + self.trading_cost_score * 0.18
            + (1.0 if self.risk_allowed else 0.0) * 0.22
            + (1.0 - self.max_drawdown) * 0.12
        )
        return round(min(max(value, 0.0), 1.0), 6)

    @property
    def continuity_score(self) -> float:
        account_score = 1.0 if self.account_ready else 0.0
        value = self.paper_quality * 0.72 + account_score * 0.16 + (1.0 if self.simulation_only else 0.0) * 0.12
        return round(min(max(value, 0.0), 1.0), 6)


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return min(max(number, 0.0), 1.0)


def _money(value: Any) -> float:
    return round(max(float(value), 0.0), 6)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().upper()
    return text in {"1", "TRUE", "YES", "PASS", "PASSED", "ALLOW", "ALLOWED", "READY"}


def _mode(value: Any) -> str:
    text = str(value).strip().upper().replace("-", "_").replace(" ", "_")
    return text or "SIMULATION"


def _action(value: Any) -> str:
    text = str(value).strip().upper()
    return text if text in {"BUY", "SELL", "FLAT"} else "FLAT"
