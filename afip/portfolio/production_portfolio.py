"""Production portfolio aggregation for Milestone B runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from afip.capital.capital_allocator import CapitalAllocator
from afip.portfolio.equity_calculator import EquityCalculator
from afip.portfolio.portfolio_equity import PortfolioEquity
from afip.portfolio.portfolio_risk import PortfolioRisk
from afip.portfolio_analytics.portfolio_analytics import PortfolioAnalytics


@dataclass(frozen=True)
class ProductionPortfolioResult:
    """Integrated portfolio state across equity, risk, capital, and analytics."""

    status: str
    ready: bool
    equity_status: str
    risk_status: str
    capital_status: str
    analytics_status: str
    account_count: int
    position_count: int
    total_balance: float
    total_equity: float
    total_net_asset_value: float
    proposed_risk_amount: float
    proposed_allocation: float
    gross_exposure: float
    risk_ratio: float
    exposure_ratio: float
    concentration_ratio: float
    available_capital: float
    allocation_ratio: float
    utilization_ratio: float
    trend_direction: str
    trend_strength_percent: float
    risk_efficiency_ratio: float
    capital_utilization_percent: float
    failed_rules: tuple[str, ...]
    reason: str


class ProductionPortfolio:
    """Build a production-ready portfolio runtime state from financial inputs."""

    def __init__(self) -> None:
        self.equity_calculator = EquityCalculator()
        self.portfolio_equity = PortfolioEquity()
        self.portfolio_risk = PortfolioRisk()
        self.capital_allocator = CapitalAllocator()
        self.portfolio_analytics = PortfolioAnalytics()

    def build(
        self,
        account_snapshots: Iterable[Mapping[str, object]],
        positions: Iterable[Mapping[str, object]],
        proposed_risk_amount: float,
        proposed_allocation: float,
        position_requests: Iterable[Mapping[str, object]],
        equity_observations: Iterable[Mapping[str, object]] | None = None,
        runtime_policy: Mapping[str, object] | None = None,
    ) -> ProductionPortfolioResult:
        """Return a deterministic integrated portfolio state."""
        policy = dict(runtime_policy or {})
        account_list = list(account_snapshots)
        position_list = list(positions)
        request_list = list(position_requests)
        equity_snapshots = [self.equity_calculator.calculate(account) for account in account_list]
        equity_summary = self.portfolio_equity.summarize(equity_snapshots)
        risk_summary = self.portfolio_risk.evaluate(equity_summary, proposed_risk_amount, position_list, policy)
        capital_summary = self.capital_allocator.allocate(equity_summary, proposed_allocation, request_list, policy)
        analytics_summary = self.portfolio_analytics.calculate(
            tuple(equity_observations or self._equity_observations(equity_summary)),
            self._performance_summary(equity_summary),
            self._risk_snapshot(risk_summary),
            self._capital_snapshot(capital_summary),
        )

        failed = self._failed_rules(equity_summary, risk_summary, capital_summary, analytics_summary)
        ready = not failed
        return ProductionPortfolioResult(
            status="PRODUCTION_PORTFOLIO_READY" if ready else "PRODUCTION_PORTFOLIO_REVIEW",
            ready=ready,
            equity_status=equity_summary.status,
            risk_status=risk_summary.status,
            capital_status=capital_summary.status,
            analytics_status=analytics_summary.status,
            account_count=equity_summary.account_count,
            position_count=len(position_list),
            total_balance=equity_summary.total_balance,
            total_equity=equity_summary.total_equity,
            total_net_asset_value=equity_summary.total_net_asset_value,
            proposed_risk_amount=risk_summary.proposed_risk_amount,
            proposed_allocation=capital_summary.proposed_allocation,
            gross_exposure=risk_summary.gross_exposure,
            risk_ratio=risk_summary.risk_ratio,
            exposure_ratio=risk_summary.exposure_ratio,
            concentration_ratio=risk_summary.concentration_ratio,
            available_capital=capital_summary.available_capital,
            allocation_ratio=capital_summary.allocation_ratio,
            utilization_ratio=capital_summary.utilization_ratio,
            trend_direction=analytics_summary.trend_direction,
            trend_strength_percent=analytics_summary.trend_strength_percent,
            risk_efficiency_ratio=analytics_summary.risk_efficiency_ratio,
            capital_utilization_percent=analytics_summary.capital_utilization_percent,
            failed_rules=failed,
            reason="production_portfolio_ready" if ready else "production_portfolio_requires_review",
        )

    @staticmethod
    def _equity_observations(equity_summary: Mapping[str, object] | object) -> tuple[dict[str, object], ...]:
        total_equity = _read_float(equity_summary, "total_equity")
        opening_equity = _read_float(equity_summary, "total_balance", total_equity)
        if opening_equity <= 0.0:
            opening_equity = total_equity
        return (
            {"timestamp": "runtime_open", "equity": round(opening_equity, 8)},
            {"timestamp": "runtime_close", "equity": round(total_equity, 8)},
        )

    @staticmethod
    def _performance_summary(equity_summary: Mapping[str, object] | object) -> dict[str, object]:
        opening_equity = _read_float(equity_summary, "total_balance")
        closing_equity = _read_float(equity_summary, "total_equity")
        return_ratio = 0.0 if opening_equity <= 0.0 else (closing_equity - opening_equity) / opening_equity
        return {"status": "PERFORMANCE_ATTRIBUTION_READY", "return_percent": round(return_ratio * 100.0, 4)}

    @staticmethod
    def _risk_snapshot(risk_summary: Mapping[str, object] | object) -> dict[str, object]:
        return {
            "status": _read_value(risk_summary, "status", ""),
            "maximum_drawdown_ratio": max(_read_float(risk_summary, "risk_ratio"), 0.0001),
        }

    @staticmethod
    def _capital_snapshot(capital_summary: Mapping[str, object] | object) -> dict[str, object]:
        return {
            "status": _read_value(capital_summary, "status", ""),
            "allocated_capital": _read_float(capital_summary, "distributed_capital"),
            "available_capital": _read_float(capital_summary, "available_capital"),
        }

    @staticmethod
    def _failed_rules(
        equity_summary: Mapping[str, object] | object,
        risk_summary: Mapping[str, object] | object,
        capital_summary: Mapping[str, object] | object,
        analytics_summary: Mapping[str, object] | object,
    ) -> tuple[str, ...]:
        failed: list[str] = []
        if _read_value(equity_summary, "status") != "PORTFOLIO_EQUITY_READY":
            failed.append("portfolio_equity_not_ready")
        if _read_value(risk_summary, "status") != "PORTFOLIO_RISK_READY":
            failed.extend(_read_tuple(risk_summary, "failed_rules") or ("portfolio_risk_not_ready",))
        if _read_value(capital_summary, "status") != "CAPITAL_ALLOCATION_READY":
            failed.extend(_read_tuple(capital_summary, "failed_rules") or ("capital_allocation_not_ready",))
        if _read_value(analytics_summary, "status") != "PORTFOLIO_ANALYTICS_READY":
            failed.extend(_read_tuple(analytics_summary, "failed_rules") or ("portfolio_analytics_not_ready",))
        return tuple(dict.fromkeys(failed))


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _read_float(source: Mapping[str, object] | object, name: str, default: float = 0.0) -> float:
    try:
        return float(_read_value(source, name, default) or 0.0)
    except (TypeError, ValueError):
        return default


def _read_tuple(source: Mapping[str, object] | object, name: str) -> tuple[str, ...]:
    raw = _read_value(source, name, ())
    if raw is None:
        return ()
    return tuple(str(item) for item in raw)
