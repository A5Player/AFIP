import json, os
from pathlib import Path
from afip.dashboard_data_contract import build_dashboard_contract
from afip.dashboard_ui.split_runtime import ThreeDashboardRuntime


def write(path: Path, data, age=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding='utf-8')
    if age:
        import time
        t=time.time()-age; os.utime(path,(t,t))


def test_fresh_mt5_wins_over_stale_integration(tmp_path):
    write(tmp_path/'config/four_profile_demo.json', {'profiles':[{'profile_id':'P1','runtime_directory':'runtime/profiles/p1'}]})
    write(tmp_path/'runtime/final_integration_status.json', {'trading_runtime':{'profiles':[{'profile_id':'P1','balance':100000,'runtime_state':'STOPPED'}]}}, age=500)
    write(tmp_path/'runtime/profiles/p1/mt5_health.json', {'balance':90,'connection_status':'CONNECTED'})
    write(tmp_path/'runtime/profiles/p1/status.json', {'runtime_state':'RUNNING'})
    c=build_dashboard_contract(tmp_path); p=c['profiles'][0]
    assert p['balance']==90
    assert p['current_mt5_status']=='CONNECTED'


def test_stale_gateway_is_last_event_not_current(tmp_path):
    write(tmp_path/'config/four_profile_demo.json', {'profiles':[{'profile_id':'P1','runtime_directory':'runtime/profiles/p1'}]})
    write(tmp_path/'runtime/profiles/p1/status.json', {'runtime_state':'RUNNING'}, age=500)
    write(tmp_path/'runtime/profiles/p1/demo_execution_state.json', {'gateway_status':'ORDER_SENT','waiting_reason':'old'}, age=500)
    c=build_dashboard_contract(tmp_path); p=c['profiles'][0]
    assert p['current_gateway_status']=='INACTIVE'
    assert p['last_gateway_event']=='ORDER_SENT'


def test_research_empty_ranking_is_not_generated():
    html=ThreeDashboardRuntime._ranking_card('Patterns', [])
    assert 'NOT_GENERATED' in html and 'DATA_UNAVAILABLE' not in html
