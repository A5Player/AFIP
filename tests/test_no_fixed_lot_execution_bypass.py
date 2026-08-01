import pytest

from afip.position.position_sizer import PositionSizer


def test_position_sizer_rejects_missing_authority_inputs():
    with pytest.raises(ValueError, match="approved risk_usd and stop_loss_points are required"):
        PositionSizer().calculate(balance=1000.0)


def test_position_sizer_uses_explicit_dynamic_stop_without_fixed_fallback():
    result = PositionSizer().calculate(balance=1000.0, risk_usd=8.12, stop_loss_points=812.0)
    assert result["stop_loss_points"] == 812.0
    assert result["risk_usd"] == 8.12
    assert result["method"] == "approved_risk_stop_sizing"
