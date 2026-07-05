"""Benchmark comparison for production performance attribution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class BenchmarkComparisonResult:
    """Portfolio versus benchmark comparison output."""

    status: str
    ready: bool
    portfolio_return_ratio: float
    benchmark_return_ratio: float
    excess_return_ratio: float
    excess_return_percent: float
    reason: str


class BenchmarkComparison:
    """Compare portfolio return with an external or internal benchmark."""

    def compare(self, portfolio_return: Mapping[str, object] | object, benchmark_return_ratio: float) -> BenchmarkComparisonResult:
        status = str(_read_value(portfolio_return, "status", ""))
        portfolio_return_ratio = float(_read_value(portfolio_return, "return_ratio", 0.0) or 0.0)
        if status != "PORTFOLIO_RETURN_READY":
            return BenchmarkComparisonResult("BENCHMARK_COMPARISON_REVIEW", False, portfolio_return_ratio, float(benchmark_return_ratio), 0.0, 0.0, "portfolio_return_not_ready")
        excess = portfolio_return_ratio - float(benchmark_return_ratio)
        return BenchmarkComparisonResult(
            status="BENCHMARK_COMPARISON_READY",
            ready=True,
            portfolio_return_ratio=portfolio_return_ratio,
            benchmark_return_ratio=float(benchmark_return_ratio),
            excess_return_ratio=round(excess, 6),
            excess_return_percent=round(excess * 100.0, 4),
            reason="benchmark_comparison_calculated",
        )


def _read_value(source: Mapping[str, object] | object, name: str, default: object = None) -> object:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)
