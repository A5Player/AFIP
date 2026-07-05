"""Performance summary controls for production reporting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class PerformanceSummaryResult:
    """Performance summary readiness output."""

    status: str
    ready: bool
    return_status: str
    risk_adjusted_status: str
    breakdown_status: str
    comparison_status: str
    return_percent: float
    risk_adjusted_ratio: float
    excess_return_percent: float
    failed_rules: tuple[str, ...]


class PerformanceSummary:
    """Summarize performance outputs and produce a production-ready status."""

    def summarize(
        self,
        portfolio_return: Mapping[str, object] | object,
        risk_adjusted_return: Mapping[str, object] | object,
        performance_breakdown: Mapping[str, object] | object,
        benchmark_comparison: Mapping[str, object] | object,
    ) -> PerformanceSummaryResult:
        return_status = str(_read_value(portfolio_return, "status", ""))
        risk_status = str(_read_value(risk_adjusted_return, "status", ""))
        breakdown_status = str(_read_value(performance_breakdown, "status", ""))
        comparison_status = str(_read_value(benchmark_comparison, "status", ""))
        failed: list[str] = []
        if return_status != "PORTFOLIO_RETURN_READY":
            failed.append("portfolio_return_not_ready")
        if risk_status != "RISK_ADJUSTED_RETURN_READY":
            failed.append("risk_adjusted_return_not_ready")
        if breakdown_status != "PERFORMANCE_BREAKDOWN_READY":
            failed.append("performance_breakdown_not_ready")
        if comparison_status != "BENCHMARK_COMPARISON_READY":
            failed.append("benchmark_comparison_not_ready")
        ready = not failed
        return PerformanceSummaryResult(
            status="PERFORMANCE_SUMMARY_READY" if ready else "PERFORMANCE_SUMMARY_REVIEW",
            ready=ready,
            return_status=return_status,
            risk_adjusted_status=risk_status,
            breakdown_status=breakdown_status,
            comparison_status=comparison_status,
            return_percent=float(_read_value(portfolio_return, "return_percent", 0.0) or 0.0),
            risk_adjusted_ratio=float(_read_value(risk_adjusted_return, "risk_adjusted_ratio", 0.0) or 0.0),
            excess_return_percent=float(_read_value(benchmark_comparison, "excess_return_percent", 0.0) or 0.0),
            failed_rules=tuple(failed),
        )


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
