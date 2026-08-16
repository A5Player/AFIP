import importlib.util
import json
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "tools/afip_a35_atr_buffer_campaign.py"
    spec = importlib.util.spec_from_file_location("a35", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_a35_grid_and_minimum_stop_are_explicit():
    module = _module()
    assert module.ATR_PERIOD == 14
    assert module.MINIMUM_SL_POINTS == 500
    assert module.SL_ATR_MULTIPLIERS == (1.0, 1.5, 2.0)
    assert module.TP_ATR_MULTIPLIERS == (1.0, 2.0, 3.0)
    assert module.BUFFER_POINTS == (-200, 0, 200)


def test_a35_policy_is_research_only():
    root = Path(__file__).resolve().parents[1]
    policy = json.loads((root / "config/research_metrics/atr_buffer_research_policy.json").read_text(encoding="utf-8"))
    assert policy["research_only"] is True
    assert policy["execution_authority"] == "NONE"
    assert policy["automatic_production_promotion_allowed"] is False
    assert policy["candidate_grid"]["minimum_effective_sl_points"] == 500


def test_a35_has_no_order_authority():
    module = _module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "order_send" not in source
    assert "MetaTrader5" not in source


def test_walk_forward_gate_keeps_rr_safety():
    module = _module()
    result = {"samples": 30, "win_rate_pct": 35, "expectancy_r": .3,
              "profit_factor": 1.5, "max_drawdown_r": 5}
    assert module._walk_forward_pass(result, tp_points=1500, sl_points=500)
