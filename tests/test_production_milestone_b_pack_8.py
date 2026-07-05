from afip.learning.adaptive_learning_loop import AdaptiveLearningLoop
from afip.learning.execution_feedback_record import ExecutionFeedbackRecord
from afip.learning.learning_weight_update import LearningWeightUpdate
from afip.learning.performance_attribution_model import PerformanceAttributionModel
from afip.runtime.production_milestone_b_learning_runtime import ProductionMilestoneBLearningRuntime, run_production_milestone_b_learning_runtime


def test_execution_feedback_record_normalizes_payload() -> None:
    record = ExecutionFeedbackRecord.from_mapping({"action": "buy", "entry_confidence": 1.5, "exit_confidence": -1, "realized_profit": 10, "spread_cost": 1, "slippage_cost": 2})
    assert record.action == "BUY"
    assert record.entry_confidence == 1.0
    assert record.exit_confidence == 0.0
    assert record.net_execution_result == 7.0


def test_performance_attribution_positive_feedback() -> None:
    result = PerformanceAttributionModel().evaluate([
        {"action": "BUY", "entry_confidence": 0.8, "exit_confidence": 0.9, "realized_profit": 12, "drawdown": 2, "spread_cost": 1, "slippage_cost": 0.2},
        {"action": "BUY", "entry_confidence": 0.7, "exit_confidence": 0.8, "realized_profit": 9, "drawdown": 3, "spread_cost": 0.8, "slippage_cost": 0.2},
    ])
    assert result.status == "ATTRIBUTION_POSITIVE"
    assert result.contribution_score >= 60.0


def test_performance_attribution_empty_feedback() -> None:
    result = PerformanceAttributionModel().evaluate([])
    assert result.status == "ATTRIBUTION_EMPTY"
    assert result.contribution_score == 0.0


def test_learning_weight_update_normalizes_weights() -> None:
    result = LearningWeightUpdate().update({"trend": 0.4, "risk": 0.6}, 80.0)
    assert result.status == "WEIGHT_UPDATE_READY"
    assert round(sum(result.updated_weights.values()), 6) == 1.0


def test_adaptive_learning_loop_ready() -> None:
    result = AdaptiveLearningLoop().process([
        {"action": "SELL", "entry_confidence": 0.75, "exit_confidence": 0.84, "realized_profit": 11, "drawdown": 2, "spread_cost": 0.5, "slippage_cost": 0.2},
    ])
    assert result.status == "LEARNING_LOOP_READY"
    assert result.records_processed == 1


def test_adaptive_learning_loop_empty_review() -> None:
    result = AdaptiveLearningLoop().process([])
    assert result.status == "LEARNING_LOOP_EMPTY"
    assert result.records_processed == 0


def test_learning_runtime_integration() -> None:
    result = ProductionMilestoneBLearningRuntime().run([
        {"action": "BUY", "entry_confidence": 0.8, "exit_confidence": 0.9, "realized_profit": 10, "drawdown": 2, "spread_cost": 1, "slippage_cost": 0.1},
    ])
    assert result.status == "LEARNING_RUNTIME_READY"
    assert result.execution_mode == "LOCKED_SIMULATION_ONLY"


def test_learning_runtime_sample_function_backward_compatible() -> None:
    result = run_production_milestone_b_learning_runtime()
    assert result.status == "LEARNING_RUNTIME_READY"
    assert result.records_processed == 2
