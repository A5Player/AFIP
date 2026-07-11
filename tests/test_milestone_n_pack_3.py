from afip.portfolio_risk_engine import PortfolioRiskEngineRuntime

def _record():
    return {"foundation_id":"NPF-1234567890ABCDEF","portfolio_intelligence_foundation_ready":True,
    "sizing_id":"APS-1234567890ABCDEF","adaptive_position_sizing_ready":True,"profile_id":"PROFILE-1",
    "market_regime":"TRENDING_BULLISH","equity":3000.0,"free_margin":2500.0,"proposed_risk_amount":10.0,
    "proposed_units":1,"maximum_portfolio_risk_percent":3.0,"current_drawdown_percent":2.0,"maximum_drawdown_percent":10.0,
    "margin_level_percent":800.0,"minimum_margin_level_percent":300.0,"maximum_portfolio_units":3,
    "market_regime_before_signal":True,"protected_runner_exposure_included":True,"traditional_dca_disabled":True,
    "averaging_down_disabled":True,"martingale_disabled":True,"grid_trading_disabled":True,"recovery_trading_disabled":True,
    "data_quality_certified":True,"broker":"XM","symbol":"GOLD#","execution_status":"LOCKED_SIMULATION_ONLY","order_status":"NO_ORDER_SENT"}

def _positions():
    return [{"position_id":"P-1","trade_plan_id":"TP-1","risk_amount":20.0,"units":1,"protected_runner":True,"independent_position_lifecycle":True}]

def test_ready_portfolio_risk_engine():
    r=PortfolioRiskEngineRuntime().evaluate(_record(),_positions()); assert r.status=="READY"; assert r.total_portfolio_risk_amount==30.0; assert r.portfolio_risk_approved

def test_risk_budget_blocks():
    x=_record(); x["proposed_risk_amount"]=100.0; r=PortfolioRiskEngineRuntime().evaluate(x,_positions()); assert "portfolio_risk_budget_exceeded" in r.block_reasons

def test_drawdown_and_margin_blocks():
    x=_record(); x["current_drawdown_percent"]=12; x["margin_level_percent"]=200
    r=PortfolioRiskEngineRuntime().evaluate(x,_positions()); assert "drawdown_limit_exceeded" in r.block_reasons; assert "margin_level_below_minimum" in r.block_reasons

def test_exposure_and_position_lineage_blocks():
    x=_record(); x["proposed_units"]=3; p=_positions()+[{"position_id":"P-1","trade_plan_id":"","risk_amount":1,"units":0}]
    r=PortfolioRiskEngineRuntime().evaluate(x,p); assert "portfolio_exposure_limit_exceeded" in r.block_reasons; assert "position_lineage_invalid" in r.block_reasons

def test_independent_lifecycle_runner_and_forbidden_policy():
    x=_record(); x["protected_runner_exposure_included"]=False; x["martingale_disabled"]=False
    p=_positions(); p[0]["independent_position_lifecycle"]=False
    r=PortfolioRiskEngineRuntime().evaluate(x,p); assert "independent_position_lifecycle_required" in r.block_reasons; assert "protected_runner_exposure_missing" in r.block_reasons; assert "forbidden_trading_method_enabled" in r.block_reasons

def test_deterministic_identity_is_order_independent():
    p=_positions()+[{"position_id":"P-2","trade_plan_id":"TP-2","risk_amount":5,"units":0,"independent_position_lifecycle":True}]
    a=PortfolioRiskEngineRuntime().evaluate(_record(),p); b=PortfolioRiskEngineRuntime().evaluate(dict(reversed(list(_record().items()))),reversed(p)); assert a.risk_evaluation_id==b.risk_evaluation_id

def test_execution_remains_locked_and_serializes():
    x=_record(); x["direct_execution"]=True; x["broker_request_created"]=True
    r=PortfolioRiskEngineRuntime().evaluate(x,_positions()); assert r.status=="BLOCKED"; assert r.execution_status=="LOCKED_SIMULATION_ONLY"; assert r.order_status=="NO_ORDER_SENT"; assert r.as_dict()["trading_logic_changed"] is False
