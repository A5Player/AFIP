from pathlib import Path

def test_unified_dashboard_delegates_to_production_authority():
    text=Path('afip/final_integration/dashboard.py').read_text(encoding='utf-8')
    assert 'DashboardAuthority' in text
    assert 'build_all' in text

def test_gateway_blocks_wrong_terminal_binding():
    text=Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'mt5_terminal_path_mismatch' in text
    assert 'configured_terminal_folder' in text

def test_start_blocks_duplicate_accounts():
    text=Path('tools/afip_demo_execution_control.py').read_text(encoding='utf-8')
    assert 'profile_isolation_validation_failed' in text
    assert 'duplicate_account' in text

def test_dashboard_monitor_is_non_execution_authority():
    text=Path('tools/afip_dashboard_monitor.py').read_text(encoding='utf-8')
    assert "'execution_authority':False" in text
    assert "default=2.0" in text
