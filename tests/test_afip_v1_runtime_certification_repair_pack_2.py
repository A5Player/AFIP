from pathlib import Path


def test_gateway_imports_stale_lock_authority():
    text = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'from afip.production_runtime_authority import reclaim_stale_lock' in text
    assert 'reclaim_stale_lock(path, maximum_age_seconds=180.0)' in text


def test_injected_mt5_uses_profile_local_test_lock():
    text = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'if self._mt5 is not None:' in text
    assert 'self.profile.runtime_directory / "account_routing.lock"' in text
    assert 'Path("runtime/execution/account_routing.lock")' in text


def test_router_uses_existing_sequential_one_shot_authority():
    text = Path('tools/afip_profile_sequential_execution_router.py').read_text(encoding='utf-8')
    assert 'tools.afip_profile_execution_once' in text
    assert '.wait()' in text
    assert 'SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5' in text
    assert 'tools.afip_profile_execution_worker' not in text


def test_control_reports_existing_sequential_authority():
    text = Path('tools/afip_demo_execution_control.py').read_text(encoding='utf-8')
    assert 'SINGLE_SUPERVISOR_PROCESS_ISOLATED_MT5' in text
    assert 'concurrent_profile_workers": 0' in text
    assert 'ONE_PROCESS_PER_PROFILE' not in text
