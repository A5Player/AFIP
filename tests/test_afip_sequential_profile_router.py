from pathlib import Path


def test_control_uses_single_router_not_per_profile_workers():
    text = Path('tools/afip_demo_execution_control.py').read_text(encoding='utf-8')
    assert 'afip_profile_sequential_execution_router' in text
    assert 'concurrent_profile_workers' in text
    assert 'demo_runner.pid' in text  # removed only as legacy cleanup
    assert 'DemoExecutionRunner(' not in text


def test_router_processes_profiles_sequentially():
    text = Path('tools/afip_profile_sequential_execution_router.py').read_text(encoding='utf-8')
    assert 'for profile in profiles' in text
    assert 'tools.afip_profile_execution_once' in text
    assert 'time.sleep(1.0)' in text
    assert 'SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5' in text


def test_isolation_probes_research_profile_too():
    text = Path('tools/afip_verify_account_isolation.py').read_text(encoding='utf-8')
    assert "if not p.enabled" in text
    assert "execution_disabled" not in text
    assert "'RESEARCH_ONLY'" in text


def test_gateway_always_shutdowns_mt5():
    text = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'finally:' in text
    assert 'mt5.shutdown()' in text
