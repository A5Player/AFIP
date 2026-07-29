from pathlib import Path
import json
from tools.afip_runtime_intelligence_role_audit import build_report


def test_reader_writer_roles_and_multiple_writer(tmp_path: Path):
    (tmp_path/'afip').mkdir()
    (tmp_path/'afip'/'a.py').write_text("from pathlib import Path\nPath('runtime/state.json').write_text('{}')\n",encoding='utf-8')
    (tmp_path/'afip'/'b.py').write_text("from pathlib import Path\nPath('runtime/state.json').write_text('{}')\n",encoding='utf-8')
    (tmp_path/'afip'/'c.py').write_text("from pathlib import Path\nPath('runtime/state.json').read_text()\n",encoding='utf-8')
    report=build_report(tmp_path)
    assert report['summary']['multiple_writer_targets']==1
    target=report['multiple_writer_targets'][0]
    assert target['writer_file_count']==2 and target['reader_file_count']==1


def test_reachability_and_legacy_candidate(tmp_path: Path):
    (tmp_path/'afip').mkdir()
    (tmp_path/'afip'/'main.py').write_text("from afip.engine import run\nif __name__ == '__main__': run()\n",encoding='utf-8')
    (tmp_path/'afip'/'engine.py').write_text("def run(): return 1\n",encoding='utf-8')
    (tmp_path/'afip'/'old_engine.py').write_text("def old_engine(): return 1\n",encoding='utf-8')
    report=build_report(tmp_path)
    by={x['path']:x for x in report['components']}
    assert by['afip/engine.py']['reachable_from_entrypoint'] is True
    assert by['afip/old_engine.py']['classification']=='LEGACY_CANDIDATE'


def test_empty_init_duplicates_are_benign(tmp_path: Path):
    (tmp_path/'afip'/'x').mkdir(parents=True); (tmp_path/'afip'/'y').mkdir(parents=True)
    (tmp_path/'afip'/'x'/'__init__.py').write_text('',encoding='utf-8')
    (tmp_path/'afip'/'y'/'__init__.py').write_text('',encoding='utf-8')
    report=build_report(tmp_path)
    assert report['exact_duplicate_files'][0]['classification']=='BENIGN_EMPTY_PACKAGE_FILES'


def test_historical_truth_finds_real_runtime_json_and_ignores_pytest(tmp_path: Path):
    fake=tmp_path/'runtime'/'pytest_temp_x'; fake.mkdir(parents=True)
    (fake/'dashboard.json').write_text(json.dumps({'coverage_start_utc':'2000','coverage_end_utc':'2001','next_start_utc':'2002','history_discovery':{'earliest_available_utc':'1999'}}),encoding='utf-8')
    real=tmp_path/'runtime'/'historical'/'p1'; real.mkdir(parents=True)
    (real/'status.json').write_text(json.dumps({'status':'PAUSED','quality_status':'PASS_WITH_GAPS','coverage_start_utc':'2026-04','coverage_end_utc':'2026-07','next_start_utc':'2026-08','timeframe':'M1','history_discovery':{'earliest_available_utc':'2026-03','bars_observed':100000}}),encoding='utf-8')
    truth=build_report(tmp_path)['historical_data_truth']
    assert truth['source']=='runtime/historical/p1/status.json'
    assert truth['boundaries_are_separated'] is True


def test_tests_and_runtime_source_are_excluded(tmp_path: Path):
    (tmp_path/'afip').mkdir(); (tmp_path/'tests').mkdir(); (tmp_path/'runtime').mkdir()
    (tmp_path/'afip'/'live.py').write_text('def live_engine(): return 1\n',encoding='utf-8')
    (tmp_path/'tests'/'test_x.py').write_text('def fake_engine(): return 1\n',encoding='utf-8')
    (tmp_path/'runtime'/'generated.py').write_text('def fake_engine(): return 1\n',encoding='utf-8')
    assert build_report(tmp_path)['summary']['python_files_scanned']==1
