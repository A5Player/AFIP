import json
from pathlib import Path

from afip.production_runtime_authority import build_dashboard_snapshot, clean_stale_runtime


def test_all_profiles_share_execution_pipeline():
    data = json.loads(Path('config/four_profile_demo.json').read_text(encoding='utf-8'))
    assert [p['profile_name'] for p in data['profiles']] == ['Conservative','Balanced','Aggressive','Experimental']
    assert all(p['execution_enabled'] for p in data['profiles'])
    assert all(p['allocation_mode'] == 'CAPITAL_TIER_TABLE' for p in data['profiles'])
    assert all(p['sizing_authority'] == 'CAPITAL_TIER_FORMULA_ONLY' for p in data['profiles'])


def test_dashboard_snapshot_is_single_read_only_authority(tmp_path):
    (tmp_path/'config').mkdir()
    (tmp_path/'runtime/profiles/p1').mkdir(parents=True)
    (tmp_path/'config/four_profile_demo.json').write_text(json.dumps({'profiles':[{'profile_id':'P1','runtime_directory':'runtime/profiles/p1','execution_enabled':True}]}),encoding='utf-8')
    (tmp_path/'runtime/profiles/p1/mt5_health.json').write_text(json.dumps({'balance':123.45}),encoding='utf-8')
    snap=build_dashboard_snapshot([],tmp_path)
    assert snap['profiles'][0]['balance']==123.45
    assert snap['profiles'][0]['execution_pipeline']=='UNIFIED_PROCESS_ISOLATED_MT5'
    assert (tmp_path/'runtime/dashboard/production_authority_snapshot.json').exists()


def test_cleanup_preserves_evidence_and_removes_dead_pid(tmp_path):
    control=tmp_path/'runtime/execution'
    control.mkdir(parents=True)
    (control/'sequential_router.pid').write_text('99999999',encoding='utf-8')
    evidence=tmp_path/'runtime/research/evidence.json'
    evidence.parent.mkdir(parents=True)
    evidence.write_text('{}',encoding='utf-8')
    report=clean_stale_runtime(tmp_path)
    assert not (control/'sequential_router.pid').exists()
    assert evidence.exists()
    assert report['status']=='READY'


def test_gateway_uses_pid_aware_stale_lock_reclaim():
    text=Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'reclaim_stale_lock(path, maximum_age_seconds=180.0)' in text
    assert 'exact_profile_binding_mismatch' in text


def test_router_bootstraps_runtime_cleanup():
    text=Path('tools/afip_profile_sequential_execution_router.py').read_text(encoding='utf-8')
    assert 'clean_stale_runtime(Path.cwd())' in text
    assert 'tools.afip_profile_execution_once' in text
