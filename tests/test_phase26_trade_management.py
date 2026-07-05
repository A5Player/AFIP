from afip.pipeline.trade_management_workflow import TradeManagementWorkflow
def test_trade_management():
    r=TradeManagementWorkflow().run(1000,75)
    assert r["state"]=="PROTECTED"
    assert r["trailing"]["status"]=="ACTIVE"
