from types import SimpleNamespace
from afip.demo_execution_gateway.runtime import DemoExecutionGateway


def test_execution_request_evidence_records_fill_and_slippage():
    request = {"symbol":"GOLD#","volume":0.01,"price":2400.00,"sl":2397.00,"tp":2405.00,"deviation":20,"type_filling":1,"type":0}
    result = SimpleNamespace(price=2400.05, order=123, deal=456, volume=0.01)
    evidence = DemoExecutionGateway._execution_request_evidence(request, result, point_size=0.01)
    assert evidence["request_price"] == 2400.0
    assert evidence["fill_price"] == 2400.05
    assert evidence["slippage_points"] == 5.0
    assert evidence["broker_order"] == 123
    assert evidence["broker_deal"] == 456
    assert evidence["deviation_points_allowed"] == 20


def test_execution_request_evidence_does_not_invent_fill():
    evidence = DemoExecutionGateway._execution_request_evidence({"symbol":"GOLD#","volume":0.01,"price":2400.0}, None, point_size=0.01)
    assert evidence["fill_price"] is None
    assert evidence["slippage_points"] is None


def test_live_execution_certification_is_observational_only():
    import inspect
    source = inspect.getsource(DemoExecutionGateway._execution_request_evidence)
    assert "order_send" not in source
    assert "order_check" not in source
