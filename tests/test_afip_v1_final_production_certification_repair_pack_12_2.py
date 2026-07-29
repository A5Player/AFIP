from pathlib import Path


def test_pack_12_2_sources_exist():
    required = [
        'afip/live_mt5_snapshot_authority.py',
        'afip/dashboard_state_machine.py',
        'afip/dashboard_data_contract.py',
        'afip/demo_execution_gateway/runtime.py',
        'afip/dashboard_ui/split_runtime.py',
        'afip/final_integration/runtime.py',
    ]
    assert all(Path(p).is_file() for p in required)


def test_gateway_report_exposes_capital_authority_contract():
    source = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    for token in ('available_capital', 'capital_basis', 'capital_authority_policy', 'account_equity'):
        assert token in source


def test_live_snapshot_is_read_only_and_backward_compatible():
    source = Path('afip/live_mt5_snapshot_authority.py').read_text(encoding='utf-8')
    assert 'order_send_called": False' in source
    assert 'orders_get = getattr' in source
    assert '"type_code"' in source
    assert '"sl"' in source and '"tp"' in source


def test_final_runtime_keeps_legacy_spawn_and_dashboard_cadence():
    source = Path('afip/final_integration/runtime.py').read_text(encoding='utf-8')
    assert 'Backward compatibility: _spawn(pid_path, command, log_name)' in source
    assert "'--fast-interval','10'" in source
    assert "'--full-interval','60'" in source
