"""Tests for AFIP Production Milestone A Pack 12."""

from afip.intelligence.portfolio_quality_assessment import PortfolioQualityAssessment
from afip.intelligence.production_readiness_assessment import ProductionReadinessAssessment
from afip.intelligence.runtime_health_assessment import RuntimeHealthAssessment
from afip.learning.adaptive_integration_summary import AdaptiveIntegrationSummary
from afip.runtime.production_milestone_a_readiness_runtime import ProductionMilestoneAReadinessRuntime


def test_production_readiness_assessment_ready_status() -> None:
    result = ProductionReadinessAssessment().assess(
        {
            "decision_quality": 0.88,
            "optimization_quality": 0.84,
            "execution_quality": 0.86,
            "portfolio_quality": 0.82,
            "data_completeness": 0.90,
            "drawdown_pressure": 0.18,
        }
    )
    assert result.status == "PRODUCTION_READY"
    assert result.action == "ENABLE_CONTROLLED_PRODUCTION_MODE"
    assert result.readiness_score >= 0.78


def test_production_readiness_assessment_keeps_simulation_under_pressure() -> None:
    result = ProductionReadinessAssessment().assess(
        {
            "decision_quality": 0.45,
            "optimization_quality": 0.40,
            "execution_quality": 0.42,
            "portfolio_quality": 0.38,
            "data_completeness": 0.50,
            "drawdown_pressure": 0.86,
        }
    )
    assert result.status == "SIMULATION_ONLY"
    assert result.action == "KEEP_SIMULATION_ONLY"


def test_runtime_health_assessment_healthy_status() -> None:
    result = RuntimeHealthAssessment().assess(
        {
            "data_availability": 0.92,
            "latency_quality": 0.86,
            "execution_continuity": 0.90,
            "cost_stability": 0.82,
            "error_pressure": 0.08,
        }
    )
    assert result.status == "RUNTIME_HEALTHY"
    assert result.health_score >= 0.80


def test_runtime_health_assessment_review_required_status() -> None:
    result = RuntimeHealthAssessment().assess(
        {
            "data_availability": 0.32,
            "latency_quality": 0.30,
            "execution_continuity": 0.28,
            "cost_stability": 0.35,
            "error_pressure": 0.80,
        }
    )
    assert result.status == "RUNTIME_REVIEW_REQUIRED"
    assert result.action == "PAUSE_PRODUCTION_READINESS"


def test_portfolio_quality_assessment_ready_status() -> None:
    result = PortfolioQualityAssessment().assess(
        {
            "capital_efficiency": 0.86,
            "exposure_balance": 0.84,
            "liquidity_quality": 0.88,
            "return_consistency": 0.82,
            "concentration_pressure": 0.14,
        }
    )
    assert result.status == "PORTFOLIO_QUALITY_READY"
    assert result.allocation_policy == "BALANCED_ALLOCATION_ELIGIBLE"


def test_adaptive_integration_summary_release_ready_status() -> None:
    result = AdaptiveIntegrationSummary().summarize(
        {
            "readiness_score": 0.86,
            "runtime_health_score": 0.88,
            "portfolio_quality_score": 0.84,
            "learning_quality_score": 0.82,
            "compatibility_score": 1.00,
        }
    )
    assert result.status == "MILESTONE_A_READY"
    assert result.action == "PREPARE_MILESTONE_A_RELEASE"


def test_readiness_runtime_prepares_controlled_release() -> None:
    result = ProductionMilestoneAReadinessRuntime().evaluate(
        readiness_metrics={
            "decision_quality": 0.90,
            "optimization_quality": 0.88,
            "execution_quality": 0.86,
            "data_completeness": 0.92,
            "drawdown_pressure": 0.12,
        },
        runtime_metrics={
            "data_availability": 0.94,
            "latency_quality": 0.88,
            "execution_continuity": 0.92,
            "cost_stability": 0.86,
            "error_pressure": 0.06,
        },
        portfolio_metrics={
            "capital_efficiency": 0.88,
            "exposure_balance": 0.86,
            "liquidity_quality": 0.90,
            "return_consistency": 0.84,
            "concentration_pressure": 0.12,
        },
        learning_metrics={"learning_quality_score": 0.86, "compatibility_score": 1.00},
    )
    assert result.status == "MILESTONE_A_PRODUCTION_READY"
    assert result.action == "PREPARE_CONTROLLED_PRODUCTION_RELEASE"


def test_readiness_runtime_preserves_backward_safe_simulation_mode() -> None:
    result = ProductionMilestoneAReadinessRuntime().evaluate(
        readiness_metrics={
            "decision_quality": 0.42,
            "optimization_quality": 0.38,
            "execution_quality": 0.40,
            "data_completeness": 0.45,
            "drawdown_pressure": 0.78,
        },
        runtime_metrics={
            "data_availability": 0.34,
            "latency_quality": 0.32,
            "execution_continuity": 0.30,
            "cost_stability": 0.35,
            "error_pressure": 0.84,
        },
        portfolio_metrics={
            "capital_efficiency": 0.36,
            "exposure_balance": 0.34,
            "liquidity_quality": 0.38,
            "return_consistency": 0.30,
            "concentration_pressure": 0.78,
        },
        learning_metrics={"learning_quality_score": 0.30, "compatibility_score": 1.00},
    )
    assert result.status == "MILESTONE_A_REVIEW_REQUIRED"
    assert result.action == "KEEP_SIMULATION_ONLY"
