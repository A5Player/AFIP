"""Pre-trade compliance checks for production financial execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PreTradeComplianceResult:
    """Result of deterministic pre-trade compliance evaluation."""

    status: str
    approved: bool
    score: float
    failed_rules: tuple[str, ...]
    reason: str


class PreTradeCompliance:
    """Validate an execution plan against financial operating limits."""

    def evaluate(
        self,
        execution_plan: Mapping[str, object] | None = None,
        account_state: Mapping[str, object] | None = None,
        market_state: Mapping[str, object] | None = None,
    ) -> PreTradeComplianceResult:
        plan = dict(execution_plan or {})
        account = dict(account_state or {})
        market = dict(market_state or {})

        failures: list[str] = []
        action = str(plan.get("action", "WAIT")).upper()
        readiness = str(plan.get("readiness", "NOT_READY")).upper()
        lot_size = self._float(plan.get("lot_size", plan.get("lot", 0.0)))
        exposure_ratio = self._ratio(plan.get("exposure_ratio", 0.0))
        margin_level = self._float(account.get("margin_level", 1000.0))
        daily_drawdown = self._ratio(account.get("daily_drawdown_ratio", 0.0))
        spread_points = self._float(market.get("spread_points", 0.0))
        spread_limit = self._float(market.get("spread_limit", 35.0))
        session_status = str(market.get("session_status", "OPEN")).upper()

        if action not in {"BUY", "SELL", "REDUCE"}:
            failures.append("action_not_executable")
        if readiness not in {"READY", "SELECTIVE"}:
            failures.append("execution_readiness_not_met")
        if lot_size <= 0.0:
            failures.append("lot_size_not_positive")
        if exposure_ratio > self._ratio(account.get("maximum_exposure_ratio", 0.80)):
            failures.append("exposure_limit_exceeded")
        if margin_level < self._float(account.get("minimum_margin_level", 250.0)):
            failures.append("margin_level_below_limit")
        if daily_drawdown >= self._ratio(account.get("maximum_daily_drawdown_ratio", 0.10)):
            failures.append("daily_drawdown_limit_reached")
        if spread_points > spread_limit:
            failures.append("spread_limit_exceeded")
        if session_status in {"CLOSED", "PAUSED", "RESTRICTED"}:
            failures.append("market_session_not_open")

        total_rules = 8
        score = round(((total_rules - len(failures)) / total_rules) * 100.0, 2)
        approved = not failures
        status = "PRE_TRADE_COMPLIANCE_APPROVED" if approved else "PRE_TRADE_COMPLIANCE_REVIEW"
        reason = "all_pre_trade_rules_approved" if approved else "pre_trade_rules_require_review"
        return PreTradeComplianceResult(status, approved, score, tuple(failures), reason)

    @staticmethod
    def _float(value: object) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @classmethod
    def _ratio(cls, value: object) -> float:
        number = cls._float(value)
        if number > 1.0:
            number = number / 100.0
        return max(0.0, min(number, 1.0))
