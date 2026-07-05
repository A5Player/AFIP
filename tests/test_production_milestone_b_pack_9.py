from afip.memory.confidence_memory_tracker import ConfidenceMemoryTracker
from afip.memory.execution_memory_snapshot import ExecutionMemorySnapshot
from afip.memory.intelligence_memory_bank import IntelligenceMemoryBank
from afip.memory.market_memory_profile import MarketMemoryProfile
from afip.memory.signal_history_repository import SignalHistoryRepository
from afip.runtime.production_milestone_b_memory_runtime import ProductionMilestoneBMemoryRuntime, run_production_milestone_b_memory_runtime


def test_signal_history_repository_ready() -> None:
    result = SignalHistoryRepository().build([
        {"signal_name": "trend", "direction": "buy", "confidence": 0.9, "market_regime": "trending"},
        {"signal_name": "liquidity", "direction": "buy", "confidence": 75, "market_regime": "trending"},
    ])
    assert result.status == "SIGNAL_HISTORY_READY"
    assert result.buy_count == 2
    assert result.average_confidence >= 75.0


def test_signal_history_repository_empty() -> None:
    result = SignalHistoryRepository().build([])
    assert result.status == "SIGNAL_HISTORY_EMPTY"
    assert result.average_confidence == 0.0


def test_market_memory_profile_ready() -> None:
    result = MarketMemoryProfile().evaluate({"market_regime": "trending", "volatility_state": "normal", "liquidity_state": "expanding", "confidence": 0.85})
    assert result.status == "MARKET_MEMORY_READY"
    assert result.dominant_regime == "TRENDING"
    assert result.profile_score >= 70.0


def test_confidence_memory_tracker_stable() -> None:
    result = ConfidenceMemoryTracker().evaluate([0.78, 0.8, 0.82, 0.83])
    assert result.status == "CONFIDENCE_MEMORY_READY"
    assert result.current_confidence == 83.0
    assert result.stability_score >= 95.0


def test_execution_memory_snapshot_positive() -> None:
    result = ExecutionMemorySnapshot().evaluate([
        {"realized_profit": 10, "spread_cost": 1, "slippage_cost": 0.2},
        {"realized_profit": 8, "spread_cost": 0.8, "slippage_cost": 0.2},
    ])
    assert result.status == "EXECUTION_MEMORY_READY"
    assert result.execution_count == 2
    assert result.execution_score >= 60.0


def test_intelligence_memory_bank_ready() -> None:
    result = IntelligenceMemoryBank().build(
        [{"signal_name": "trend", "direction": "BUY", "confidence": 0.86, "market_regime": "TRENDING"}],
        {"market_regime": "TRENDING", "volatility_state": "NORMAL", "liquidity_state": "HIGH", "confidence": 0.84},
        [0.8, 0.82, 0.84],
        [{"realized_profit": 12, "spread_cost": 0.6, "slippage_cost": 0.2}],
    )
    assert result.status == "INTELLIGENCE_MEMORY_READY"
    assert result.memory_score >= 60.0


def test_memory_runtime_integration() -> None:
    result = ProductionMilestoneBMemoryRuntime().run(
        [{"signal_name": "trend", "direction": "BUY", "confidence": 0.86, "market_regime": "TRENDING"}],
        {"market_regime": "TRENDING", "volatility_state": "NORMAL", "liquidity_state": "EXPANDING", "confidence": 0.84},
        [0.8, 0.82, 0.84],
        [{"realized_profit": 11, "spread_cost": 0.7, "slippage_cost": 0.2}],
    )
    assert result.status == "MEMORY_RUNTIME_READY"
    assert result.execution_mode == "LOCKED_SIMULATION_ONLY"


def test_memory_runtime_sample_backward_compatible() -> None:
    result = run_production_milestone_b_memory_runtime()
    assert result.status == "MEMORY_RUNTIME_READY"
    assert result.memory_score >= 60.0
