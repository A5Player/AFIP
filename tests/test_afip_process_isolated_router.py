from pathlib import Path


def test_router_does_not_import_demo_gateway_or_mt5():
    text = Path('tools/afip_profile_sequential_execution_router.py').read_text(encoding='utf-8')
    assert 'DemoExecutionGateway' not in text
    assert 'import MetaTrader5' not in text
    assert 'tools.afip_profile_execution_once' in text
    assert '.wait()' in text


def test_single_profile_worker_runs_exactly_one_gateway_cycle():
    text = Path('tools/afip_profile_execution_once.py').read_text(encoding='utf-8')
    assert 'DemoExecutionGateway(profile, policy).run_cycle()' in text
    assert 'while ' not in text


def test_status_exposes_process_isolated_mode():
    text = Path('tools/afip_demo_execution_control.py').read_text(encoding='utf-8')
    assert 'SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5' in text
    assert 'NOT_APPLICABLE' in text
