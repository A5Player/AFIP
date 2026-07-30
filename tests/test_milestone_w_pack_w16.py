from pathlib import Path
import json

from afip.advisory_integration_certification import (
    BLOCKED,
    CERTIFIED,
    AdvisoryIntegrationCertificationRuntime,
)


def test_complete_milestone_w_chain_certifies():
    root = Path(__file__).resolve().parents[1]
    result = AdvisoryIntegrationCertificationRuntime(root).certify()
    assert result.status == CERTIFIED
    assert result.reason == "integration_certification_passed"
    assert result.certification_id.startswith("AFIP-W16-")


def test_certification_is_deterministic():
    root = Path(__file__).resolve().parents[1]
    runtime = AdvisoryIntegrationCertificationRuntime(root)
    first = runtime.certify()
    second = runtime.certify()
    assert first.certification_id == second.certification_id
    assert first.source_digest == second.source_digest


def test_missing_contract_blocks(tmp_path):
    result = AdvisoryIntegrationCertificationRuntime(tmp_path).certify()
    assert result.status == BLOCKED
    assert any(check.reason == "contract_missing" for check in result.checks)


def test_all_required_modules_and_contracts_are_checked():
    root = Path(__file__).resolve().parents[1]
    result = AdvisoryIntegrationCertificationRuntime(root).certify()
    names = {check.name for check in result.checks}
    assert "afip.advisory_dashboard_runtime" in names
    assert "config/advisory_dashboard_runtime_contract.json" in names
    assert len(result.checks) >= 14


def test_no_execution_authority_and_contract():
    root = Path(__file__).resolve().parents[1]
    result = AdvisoryIntegrationCertificationRuntime(root).certify()
    assert result.execution_authority is False
    assert result.order_send_called is False
    assert result.order_modify_called is False
    assert result.order_close_called is False

    contract = json.loads(
        (root / "config" / "advisory_integration_certification_contract.json").read_text(encoding="utf-8")
    )
    assert contract["authority"] == "READ_ONLY_CERTIFICATION"
    assert contract["fail_closed"] is True
