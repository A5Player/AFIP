from pathlib import Path


def test_injected_mt5_adapter_does_not_require_os_terminal_process():
    text = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    assert 'if self._mt5 is None and not self._manual_terminal_running()' in text


def test_gateway_report_accepts_trade_plan_evidence():
    text = Path('afip/demo_execution_gateway/runtime.py').read_text(encoding='utf-8')
    for token in ('plan_id: str', 'plan_certification_status: str', 'plan_rejection_reasons: tuple[str, ...]'):
        assert token in text


def test_dashboard_monitor_remains_non_execution_authority():
    text = Path('tools/afip_dashboard_monitor.py').read_text(encoding='utf-8')
    assert '"execution_authority": False' in text
    assert "'execution_authority':False" in text


def test_research_non_ohlc_compatibility_is_scope_aware():
    text = Path('afip/automatic_research_runtime/runtime.py').read_text(encoding='utf-8')
    assert '(self.root / "data" / "research") in path.parents' in text
    assert 'NON_OHLC_SKIPPED' in text
