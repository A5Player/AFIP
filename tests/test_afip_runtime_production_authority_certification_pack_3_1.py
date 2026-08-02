from pathlib import Path
import importlib.util
import json

MODULE_PATH = Path(__file__).parents[1] / 'tools' / 'afip_runtime_production_authority_audit.py'
spec = importlib.util.spec_from_file_location('audit31', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mod)


def test_operational_role_contract():
    assert mod.operational_role('START_AFIP.ps1', True, True) == 'PRIMARY_RUNTIME_ROOT'
    assert mod.operational_role('STATUS_AFIP.ps1', False, True) == 'CONTROL_COMMAND'
    assert mod.operational_role('BUILD_AFIP_DASHBOARD_4_ONCE.ps1', True, True) == 'DASHBOARD_BUILDER'
    assert mod.operational_role('INSTALL_X.ps1', False, True) == 'NON_RUNTIME_TOOL'


def test_script_python_module_invocation(tmp_path: Path):
    p = tmp_path / 'START_AFIP.ps1'
    p.write_text('python -m tools.afip_operational_runtime\n', encoding='utf-8')
    item = mod.inspect_script(p, tmp_path)
    assert any(x['kind'] == 'python_module' and x['target'] == 'tools.afip_operational_runtime' for x in item['invocation_targets'])


def test_authority_chain_from_primary_root(tmp_path: Path):
    (tmp_path / 'tools').mkdir()
    (tmp_path / 'START_AFIP.ps1').write_text('python -m tools.worker\n', encoding='utf-8')
    (tmp_path / 'tools' / 'worker.py').write_text('def main(): pass\nif __name__ == "__main__": main()\n', encoding='utf-8')
    report = mod.build_report(tmp_path)
    assert report['summary']['primary_runtime_roots'] == 1
    assert report['primary_runtime_roots'] == ['START_AFIP.ps1']
    chain = report['authority_chains'][0]
    assert 'tools/worker.py' in chain['reachable_targets']


def test_read_only_output_contract(tmp_path: Path):
    (tmp_path / 'afip.py').write_text('if __name__ == "__main__": pass\n', encoding='utf-8')
    report = mod.build_report(tmp_path)
    assert report['schema_version'].endswith('v3.1')
    assert 'entrypoint_classification' in report
    assert 'invocation_edges' in report


def test_historical_truth_reads_partitioned_financial_lake_records(tmp_path: Path):
    records = (
        tmp_path / 'runtime' / 'research' / 'historical_data_lake'
        / 'layer=normalized' / 'domain=market_ohlc' / 'instrument=GOLD_'
        / 'year=2026' / 'month=08' / 'day=02' / 'records.jsonl'
    )
    records.parent.mkdir(parents=True)
    records.write_text(json.dumps({
        'schema_version': 'financial-data-lake.v1',
        'layer': 'normalized',
        'domain': 'market_ohlc',
        'observed_at_utc': '2026-08-02T00:00:00+00:00',
        'payload': {'timeframe': 'D1'},
    }) + '\n', encoding='utf-8')

    truth = mod.find_historical_truth(tmp_path)

    assert truth['source'] == 'runtime/research/historical_data_lake'
    assert truth['status'] == 'AVAILABLE'
    assert truth['dataset_start_utc'] == '2026-08-02T00:00:00+00:00'
    assert truth['dataset_end_utc'] == '2026-08-02T00:00:00+00:00'
    assert truth['bars_observed'] == 1
    assert truth['timeframes'] == ['D1']
    assert truth['boundaries_are_separated'] is False
