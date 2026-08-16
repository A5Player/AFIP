import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "tools/afip_a33_multi_objective_ranking.py"
    spec = importlib.util.spec_from_file_location("a33", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_rr_win_rate_policy():
    module = _module()
    assert module.minimum_win_rate_for_rr(1.0) == 60.0
    assert module.minimum_win_rate_for_rr(2.0) == 42.0
    assert module.minimum_win_rate_for_rr(3.0) == 32.0
    assert module.minimum_win_rate_for_rr(4.0) == 27.0


def test_metric_pass_waits_for_walk_forward():
    module = _module()
    row = module.evaluate({"sl_points": 500, "tp_points": 1500, "win_rate_pct": 35,
                           "expectancy_r": .3, "profit_factor": 1.5, "samples": 120,
                           "max_drawdown_r": 5})
    assert row["metric_gate_pass"] is True
    assert row["eligibility"] == "PENDING_WALK_FORWARD"


def test_sl_below_500_is_not_eligible():
    module = _module()
    row = module.evaluate({"sl_points": 300, "tp_points": 1200, "win_rate_pct": 40,
                           "expectancy_r": .5, "profit_factor": 2, "samples": 200,
                           "max_drawdown_r": 4, "walk_forward_passes": 4, "walk_forward_windows": 4})
    assert row["eligibility"] == "NOT_ELIGIBLE"
    assert "SL_BELOW_500_POINTS" in row["eligibility_reasons"]


def test_no_execution_authority_in_source():
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "order_send" not in source
    assert "MetaTrader5" not in source
