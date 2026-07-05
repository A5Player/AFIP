from afip.backtest.backtest_metrics_engine import BacktestMetricsEngine
from afip.backtest.scenario_stress_engine import ScenarioStressEngine
from afip.backtest.walk_forward_engine import WalkForwardEngine


def test_backtest_metrics_engine_reports_survival():
    trades = [{"profit": 10.0}, {"profit": -3.0}, {"profit": 7.0}]
    result = BacktestMetricsEngine().evaluate(trades, [100.0, 110.0, 106.0, 120.0])
    assert result["status"] == "READY"
    assert result["survival"] is True
    assert result["score"] > 50


def test_walk_forward_engine_detects_stability():
    result = WalkForwardEngine().evaluate([
        {"train_score": 75.0, "test_score": 68.0},
        {"train_score": 70.0, "test_score": 63.0},
    ])
    assert result["status"] == "READY"
    assert result["pass_rate"] == 100.0


def test_walk_forward_engine_warns_on_degradation():
    result = WalkForwardEngine().evaluate([{"train_score": 90.0, "test_score": 50.0}])
    assert result["status"] == "CAUTION"
    assert result["windows"][0]["stable"] is False


def test_scenario_stress_engine_blocks_high_drawdown():
    result = ScenarioStressEngine().evaluate([{"name": "spread shock", "net_profit": 4.0, "drawdown_percent": 40.0, "recovery_factor": 0.5}])
    assert result["status"] == "CAUTION"
    assert result["blockers"] == 1
