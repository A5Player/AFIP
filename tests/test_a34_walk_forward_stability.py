import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "tools/afip_a32_real_backtest_campaign.py"
    spec = importlib.util.spec_from_file_location("a32_a34", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_walk_forward_gate_requires_stability():
    module = _module()
    result = {"samples": 30, "win_rate_pct": 35, "expectancy_r": .3,
              "profit_factor": 1.5, "max_drawdown_r": 5}
    assert module._walk_forward_pass(result, tp_points=1500, sl_points=500) is True
    result["max_drawdown_r"] = 11
    assert module._walk_forward_pass(result, tp_points=1500, sl_points=500) is False


def test_rr_thresholds_are_explicit():
    module = _module()
    assert module._minimum_win_rate_for_rr(1) == 60
    assert module._minimum_win_rate_for_rr(3) == 32
    assert module._minimum_win_rate_for_rr(4) == 27


def test_no_execution_authority():
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "order_send" not in source
    assert "MetaTrader5" not in source
