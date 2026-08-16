import importlib.util
from pathlib import Path


def _module():
    path = Path(__file__).resolve().parents[1] / "tools" / "afip_a32_real_backtest_campaign.py"
    spec = importlib.util.spec_from_file_location("a32", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_a32_contract_is_research_only():
    module = _module()
    assert module.SCHEMA == "afip.a32.real_backtest_campaign.v1"
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "order_send" not in source
    assert "MetaTrader5" not in source


def test_metrics_use_explicit_units():
    module = _module()
    result = module._metrics([
        ("1", 1.0, "TP", 2),
        ("2", -1.0, "SL", 1),
        ("3", 0.5, "TIME", 4),
    ])
    assert result["win_rate_pct"] == 66.6667
    assert result["expectancy_r"] == 0.166667
    assert result["max_drawdown_r"] == 1.0
