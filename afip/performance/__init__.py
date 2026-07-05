"""Performance attribution components for AFIP production portfolio analysis."""

from afip.performance.benchmark_comparison import BenchmarkComparison, BenchmarkComparisonResult
from afip.performance.performance_attribution import PerformanceAttribution, PerformanceAttributionSummary
from afip.performance.performance_breakdown import PerformanceBreakdown, PerformanceBreakdownResult
from afip.performance.performance_summary import PerformanceSummary, PerformanceSummaryResult
from afip.performance.portfolio_return import PortfolioReturn, PortfolioReturnResult
from afip.performance.risk_adjusted_return import RiskAdjustedReturn, RiskAdjustedReturnResult

__all__ = [
    "BenchmarkComparison",
    "BenchmarkComparisonResult",
    "PerformanceAttribution",
    "PerformanceAttributionSummary",
    "PerformanceBreakdown",
    "PerformanceBreakdownResult",
    "PerformanceSummary",
    "PerformanceSummaryResult",
    "PortfolioReturn",
    "PortfolioReturnResult",
    "RiskAdjustedReturn",
    "RiskAdjustedReturnResult",
]
