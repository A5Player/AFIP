from pathlib import Path
from types import SimpleNamespace

from afip.production_activation_runtime import ProductionActivationRuntime


def runtime(tmp_path: Path) -> ProductionActivationRuntime:
    profile = SimpleNamespace(profile_id="P1", symbol="GOLD#")
    policy = SimpleNamespace(magic=1001)
    return ProductionActivationRuntime(profile=profile, policy=policy, runtime_root=tmp_path)


def simulation(action="BUY", confidence=78.0, structure="BUY"):
    return {
        "data_status": "REAL_MARKET_DATA_READY",
        "data_source": "MT5",
        "decision": {
            "action": action,
            "confidence": confidence,
            "reason": "weighted_intelligence",
            "conflict_resolution_reason": "weighted_edge",
            "selected_scenario": f"{action}_WEIGHTED_INTELLIGENCE",
            "blocking_intelligence": [],
            "explain": [
                {"name": "MarketStructureIntelligence", "status": "READY", "direction": structure},
                {"name": "LiquidityIntelligence", "status": "READY", "direction": action},
                {"name": "VolatilityRiskIntelligence", "status": "READY", "direction": "FLAT"},
            ],
        },
    }


def test_position_care_context_uses_current_intelligence(tmp_path):
    ctx = runtime(tmp_path)._position_intelligence_context(simulation())
    assert ctx["decision_action"] == "BUY"
    assert ctx["market_data_fresh"] is True
    assert ctx["liquidity_acceptable"] is True
    assert ctx["selected_scenario"] == "BUY_WEIGHTED_INTELLIGENCE"


def test_opposite_high_confidence_invalidates_holding_thesis(tmp_path):
    ctx = runtime(tmp_path)._position_intelligence_context(simulation(action="SELL", confidence=80.0))
    assert runtime(tmp_path)._thesis_valid_for_position(position_direction="BUY", context=ctx) is False


def test_wait_does_not_invent_thesis_failure(tmp_path):
    ctx = runtime(tmp_path)._position_intelligence_context(simulation(action="WAIT", confidence=40.0, structure="FLAT"))
    assert runtime(tmp_path)._thesis_valid_for_position(position_direction="BUY", context=ctx) is True


def test_structure_opposition_is_not_valid_for_position(tmp_path):
    ctx = runtime(tmp_path)._position_intelligence_context(simulation(action="BUY", structure="SELL"))
    assert runtime(tmp_path)._module_supports_position("MarketStructureIntelligence", "BUY", ctx) is False


def test_stale_or_fallback_market_data_blocks_freshness(tmp_path):
    data = simulation()
    data["data_status"] = "FALLBACK_DATA"
    ctx = runtime(tmp_path)._position_intelligence_context(data)
    assert ctx["market_data_fresh"] is False


def test_gateway_evaluates_current_intelligence_before_position_care():
    source = Path("afip/demo_execution_gateway/runtime.py").read_text(encoding="utf-8")
    simulate_at = source.index('result = self._simulate()')
    care_at = source.index('self._production_activation.observe_positions(', simulate_at)
    assert simulate_at < care_at
    assert 'current_intelligence=result' in source
    assert 'execution_trace_id=self._active_trace_id' in source


def test_no_hardcoded_position_intelligence_validity_flags():
    source = Path("afip/production_activation_runtime/runtime.py").read_text(encoding="utf-8")
    assert "market_regime_valid=True, thesis_valid=True, structure_valid=True" not in source
    assert '"intelligence_context": intelligence_context' in source

def test_dashboard_exposes_position_care_intelligence_fields():
    runtime_source = Path("afip/control_center_runtime.py").read_text(encoding="utf-8")
    dashboard_source = Path("afip/dashboard_ui/control_center.py").read_text(encoding="utf-8")
    for key in ("position_care_action", "position_care_reason", "care_intelligence_scenario", "care_intelligence_confidence"):
        assert key in runtime_source
        assert key in dashboard_source
