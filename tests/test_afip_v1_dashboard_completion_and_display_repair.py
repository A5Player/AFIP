from pathlib import Path
import json
from afip.dashboard_data_contract import build_dashboard_contract
from afip.live_mt5_dashboard import write as write_mt5
from afip.research_observability_dashboard import write as write_research
from afip.dashboard_audit import write as write_audit
from afip.unified_dashboard import write as write_unified

def _root(tmp_path:Path)->Path:
    (tmp_path/'config').mkdir()
    (tmp_path/'runtime/profiles/p1').mkdir(parents=True)
    (tmp_path/'runtime/dashboard').mkdir(parents=True)
    (tmp_path/'runtime/research').mkdir(parents=True)
    (tmp_path/'runtime/execution').mkdir(parents=True)
    (tmp_path/'config/four_profile_demo.json').write_text(json.dumps({'profiles':[{'profile_id':'P1','runtime_directory':'runtime/profiles/p1'}]}))
    (tmp_path/'runtime/profiles/p1/mt5_health.json').write_text(json.dumps({'connection_status':'CONNECTED','balance':1000}))
    (tmp_path/'runtime/profiles/p1/status.json').write_text(json.dumps({'runtime_state':'RUNNING'}))
    (tmp_path/'runtime/profiles/p1/demo_execution_state.json').write_text(json.dumps({'decision':'WAIT','order_status':'ORDER_NOT_SENT'}))
    (tmp_path/'runtime/research/automatic_research_status.json').write_text(json.dumps({'status':'READY','accepted_events':12}))
    return tmp_path

def test_phase4_live_mt5(tmp_path):
    c=build_dashboard_contract(_root(tmp_path)); p=write_mt5(c,tmp_path/'runtime/dashboard'); h=p.read_text(); assert 'Live MT5 Dashboard' in h and 'CONNECTED' in h

def test_phase5_research(tmp_path):
    c=build_dashboard_contract(_root(tmp_path)); p=write_research(c,tmp_path/'runtime/dashboard'); h=p.read_text(); assert 'Research Observability' in h and 'accepted_events' in h

def test_phase6_audit(tmp_path):
    c=build_dashboard_contract(_root(tmp_path)); p=write_audit(c,tmp_path/'runtime/dashboard'); h=p.read_text(); assert 'Dashboard Audit Mode' in h and 'configuration' in h

def test_unified_display_is_iframe_free(tmp_path):
    c=build_dashboard_contract(_root(tmp_path)); p=write_unified(c,tmp_path/'runtime/dashboard'); h=p.read_text(); assert 'AFIP Unified Runtime Dashboard' in h and '<iframe' not in h and 'P1' in h
