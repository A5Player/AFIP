from pathlib import Path
from afip.four_profile_operations.mt5_connection import MT5ProfileHealth
from afip.dashboard_ui.split_runtime import _profile_rows

def test_mt5_health_has_live_financial_fields():
    names=set(MT5ProfileHealth.__dataclass_fields__)
    assert {'currency','balance','equity','margin','margin_free','profit','positions_total','orders_total','bid','ask','spread_points'} <= names

def test_dashboard_rows_render_live_mt5_fields_without_fake_zero():
    rows={label:value for _icon,label,value in _profile_rows({'account_balance':1234.5,'account_equity':1250.0,'positions_total':2,'orders_total':1,'bid':2400.1,'ask':2400.3,'spread_points':20,'trade_allowed':True})}
    assert rows['Balance']=='1,234.50'
    assert rows['Equity']=='1,250.00'
    assert rows['Positions / Orders']=='2 / 1'
    assert rows['Spread points']=='20'

def test_live_scripts_exist():
    assert Path('START_AFIP_PRODUCTION_DASHBOARD.ps1').exists()
    assert Path('BUILD_AFIP_PRODUCTION_DASHBOARD_ONCE.ps1').exists()
