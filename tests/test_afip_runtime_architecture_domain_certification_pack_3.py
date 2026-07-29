from pathlib import Path
from tools.afip_runtime_architecture_domain_audit import build_report, domain_for_path


def test_domain_classification():
    assert domain_for_path('INSTALL_PATCH.ps1') == 'INSTALLER_MIGRATION'
    assert domain_for_path('tools/afip_historical_mt5_backfill.py') == 'HISTORICAL_DATA'
    assert domain_for_path('afip/demo_execution_gateway/runtime.py') == 'LIVE_EXECUTION'
    assert domain_for_path('afip/dashboard_ui/runtime.py') == 'DASHBOARD'


def test_production_entrypoints_exclude_milestone_scripts(tmp_path: Path):
    (tmp_path/'afip').mkdir(); (tmp_path/'tools').mkdir()
    (tmp_path/'START_AFIP.ps1').write_text('python -m tools.afip_operational_runtime\n')
    (tmp_path/'RUN_MILESTONE_S_PACK_1.ps1').write_text('python -m pytest\n')
    (tmp_path/'tools'/'afip_operational_runtime.py').write_text("if __name__ == '__main__': pass\n")
    report=build_report(tmp_path)
    assert 'START_AFIP.ps1' in report['production_entrypoints']
    assert 'RUN_MILESTONE_S_PACK_1.ps1' not in report['production_entrypoints']
    assert report['summary']['all_detected_entrypoints'] > report['summary']['production_entrypoints']


def test_authority_map_and_heat_map(tmp_path: Path):
    (tmp_path/'afip'/'execution_supervisor').mkdir(parents=True)
    (tmp_path/'afip'/'execution_supervisor'/'runtime.py').write_text('def execution_runtime(): return 1\n')
    (tmp_path/'START_AFIP.ps1').write_text('python -m afip.execution_supervisor.runtime\n')
    report=build_report(tmp_path)
    names={x['authority'] for x in report['authority_map']}
    assert 'EXECUTION_AUTHORITY' in names
    assert report['runtime_heat_map']


def test_legacy_confidence_is_reported(tmp_path: Path):
    (tmp_path/'afip').mkdir()
    (tmp_path/'afip'/'unused_execution_engine.py').write_text('def execution_engine(): return 1\n')
    report=build_report(tmp_path)
    item=next(x for x in report['components'] if x['path'].endswith('unused_execution_engine.py'))
    assert item['classification']=='LEGACY_CANDIDATE'
    assert item['legacy_confidence'] in {'HIGH','MEDIUM','LOW'}
