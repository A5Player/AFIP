from pathlib import Path
from afip.final_production_certification.runtime import REQUIRED_COMPONENTS, REQUIRED_SAFETY_INVARIANTS, build_final_certification


def _source(tmp_path: Path) -> None:
    for paths in REQUIRED_COMPONENTS.values():
        for relative in paths:
            path=tmp_path/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("# certified source\n", encoding="utf-8")


def _runtime():
    return {name:{"status":"PASS"} for name in ("runtime","execution","position","research","financial","portfolio","dashboard","mt5")}


def test_missing_source_blocks(tmp_path):
    result=build_final_certification(tmp_path)
    assert result["status"] == "CERTIFICATION_BLOCKED"
    assert result["production_certified"] is False


def test_source_only_is_not_live_certified(tmp_path):
    _source(tmp_path)
    result=build_final_certification(tmp_path)
    assert result["source_contract_certification"]["status"] == "PASS"
    assert result["status"] == "READY_FOR_OPERATIONAL_CERTIFICATION"


def test_complete_evidence_certifies(tmp_path):
    _source(tmp_path)
    result=build_final_certification(tmp_path, runtime_evidence=_runtime())
    assert result["status"] == "PRODUCTION_CERTIFIED"
    assert result["production_certified"] is True


def test_blocked_execution_prevents_certification(tmp_path):
    _source(tmp_path); runtime=_runtime(); runtime["execution"]={"status":"BLOCKED"}
    result=build_final_certification(tmp_path, runtime_evidence=runtime)
    assert result["production_certified"] is False
    assert any("execution:BLOCKED" in x for x in result["certification_blockers"])


def test_missing_mt5_evidence_is_not_pass(tmp_path):
    _source(tmp_path); runtime=_runtime(); runtime.pop("mt5")
    result=build_final_certification(tmp_path, runtime_evidence=runtime)
    assert "runtime_evidence_missing:mt5" in result["certification_blockers"]


def test_safety_invariant_failure_blocks(tmp_path):
    _source(tmp_path)
    result=build_final_certification(tmp_path, runtime_evidence=_runtime(), safety_invariants={"automatic_order_retry_allowed": True})
    assert result["source_contract_certification"]["status"] == "FAILED"


def test_default_safety_contract_is_strict(tmp_path):
    _source(tmp_path)
    result=build_final_certification(tmp_path)
    assert result["safety_certification"]["effective_invariants"] == REQUIRED_SAFETY_INVARIANTS


def test_certification_is_read_only(tmp_path):
    _source(tmp_path)
    result=build_final_certification(tmp_path, runtime_evidence=_runtime())
    assert result["truth_policy"]["read_only_certification"] is True
    assert result["truth_policy"]["execution_permission"] is False
    assert result["truth_policy"]["affects_trading"] is False


def test_unrecognized_status_does_not_pass(tmp_path):
    _source(tmp_path); runtime=_runtime(); runtime["financial"]={"status":"UNKNOWN"}
    result=build_final_certification(tmp_path, runtime_evidence=runtime)
    assert result["production_certified"] is False


def test_all_required_components_are_explicit():
    assert set(REQUIRED_COMPONENTS) == {"execution","position","research_dataset","research_ranking","financial","portfolio","dashboard"}
