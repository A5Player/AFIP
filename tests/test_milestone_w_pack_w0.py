from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_w0_contract_locks_authorities() -> None:
    contract = json.loads(_text("config/milestone_w_authority_contract.json"))
    assert contract["schema_version"] == "afip-milestone-w-authority-contract.v1"
    assert contract["status"] == "LOCKED"
    assert contract["authorities"]["research"]["execution_authority"] is False
    assert contract["authorities"]["research"]["order_send_allowed"] is False
    assert contract["authorities"]["execution"]["research_may_submit_orders"] is False
    assert contract["integration_contract"]["new_execution_path_forbidden"] is True
    assert contract["integration_contract"]["new_runtime_authority_forbidden"] is True
    assert contract["integration_contract"]["automatic_policy_change_forbidden"] is True


def test_locked_source_owners_exist() -> None:
    required = (
        "afip/final_integration/runtime.py",
        "afip/final_integration/research_engine.py",
        "afip/research_data_foundation/runtime.py",
        "afip/research_data_foundation/intelligence.py",
        "afip/research_replay_engine/runtime.py",
        "afip/research_ranking/runtime.py",
        "afip/research_governance/runtime.py",
        "afip/demo_execution_gateway/runtime.py",
        "afip/dashboard_ui/truth_v2.py",
    )
    assert all((ROOT / path).is_file() for path in required)


def test_research_authority_is_non_executing() -> None:
    source = _text("afip/final_integration/research_engine.py")
    assert "class UnifiedResearchEngine" in source
    assert '"execution_authority": False' in source
    assert '"order_send_called": False' in source
    assert ".order_send(" not in source
    assert ".order_check(" not in source


def test_execution_gateway_remains_order_send_owner() -> None:
    source = _text("afip/demo_execution_gateway/runtime.py")
    assert "class DemoExecutionGateway" in source
    assert "mt5.order_send(request)" in source
    contract = json.loads(_text("config/milestone_w_authority_contract.json"))
    assert contract["authorities"]["execution"]["mt5_order_send_source"] == "afip/demo_execution_gateway/runtime.py"


def test_dashboard_truth_is_read_only() -> None:
    source = _text("afip/dashboard_ui/truth_v2.py")
    assert "passive truth, lineage, and consistency viewer" in source
    assert "does" in source and "not start MT5, research, execution" in source
    assert ".order_send(" not in source
    assert ".order_check(" not in source
