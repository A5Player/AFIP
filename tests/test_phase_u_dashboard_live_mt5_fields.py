from afip.four_profile_operations.mt5_connection import MT5ProfileHealth
from afip.dashboard_ui.split_runtime import _profile_rows

def test_live_health_contract_has_financial_market_fields():
    h=MT5ProfileHealth('P1',True,'CONNECTED',True,True,True,True,True,True,True,1.0,0,'****0001','XM','x','ok','now',balance=123.0,equity=124.0,bid=3300.1,ask=3300.2,spread_points=10.0)
    d=h.as_dict()
    assert d['balance']==123.0 and d['spread_points']==10.0

def test_profile_rows_surface_live_values():
    rows={label:value for _,label,value in _profile_rows({'account_balance':123,'account_equity':124,'bid':1,'ask':2,'spread_points':10,'positions_total':2,'orders_total':1})}
    assert rows['Balance']=='123.00'
    assert rows['Positions / Orders']=='2 / 1'
    assert rows['Spread']=='10 points'
