from pathlib import Path

ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "afip" / "demo_execution_gateway" / "runtime.py"
RESEARCH_TEST = ROOT / "tests" / "test_afip_pro_v1_dashboard_final_completion.py"

def test_verified_context_is_created_after_preflight():
    text = RUNTIME.read_text(encoding="utf-8")
    assert "verified_context = {" in text
    assert '"binding_verified": bool(binding_ok)' in text
    assert '"available_capital": min(account_balance, account_equity)' in text
    assert '"capital_basis": "MIN_BALANCE_EQUITY"' in text

def test_confidence_waiting_preserves_verified_context():
    text = RUNTIME.read_text(encoding="utf-8")
    line = next(
        line for line in text.splitlines()
        if '"profile_confidence_below_threshold"' in line and "return self._report" in line
    )
    assert "**verified_context" in line

def test_other_post_preflight_waiting_states_preserve_context():
    text = RUNTIME.read_text(encoding="utf-8")
    for reason in (
        "simulation_fallback_data_blocked",
        "decision_not_actionable",
        "risk_not_approved",
        "trading_cost_not_approved",
        "protected_order_not_ready",
    ):
        line = next(
            line for line in text.splitlines()
            if f'"{reason}"' in line and "return self._report" in line
        )
        assert "**verified_context" in line

def test_research_test_requires_current_eligible_feedback_contract():
    text = RESEARCH_TEST.read_text(encoding="utf-8")
    assert "INSUFFICIENT_ELIGIBLE_COMPLETED_TRADES" in text
    assert '"research_feedback_status":"ELIGIBLE"' in text
    assert '"net_realized_profit_usd":5' in text
    assert '"net_profit":5' not in text
