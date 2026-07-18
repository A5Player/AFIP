import json
from pathlib import Path

import pytest

from afip.research_data_foundation import (
    DataFoundationRegistry,
    DecisionTraceEnvelope,
    RegistryValidationError,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_ROOT = ROOT / "config" / "research_data"


def test_all_machine_readable_registries_validate():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    assert registry.versions == {
        "data": "AFIP_DATA_DICTIONARY_V1",
        "score": "AFIP_SCORE_DICTIONARY_V1",
        "formula": "AFIP_FORMULA_REGISTRY_V1",
        "quality": "AFIP_DATA_QUALITY_RULES_V1",
        "eligibility": "AFIP_RESEARCH_ELIGIBILITY_V1",
    }


def test_all_registries_lock_immutable_raw_data():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    assert all(payload["immutable_raw_data"] is True for payload in registry.payloads.values())


def test_research_fields_are_profile_independent_and_traceable():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    fields = registry.payloads["data"]["fields"]
    assert fields
    assert all(not item["field_id"].lower().startswith(("p1.", "p2.", "p3.", "p4.")) for item in fields)
    assert all(item["lineage"]["layer"] in {"raw", "normalized", "derived", "decision", "outcome", "knowledge"} for item in fields)


def test_scores_reference_registered_formulas_and_keep_gates_separate():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    formulas = {x["formula_id"] for x in registry.payloads["formula"]["formulas"]}
    for score in registry.payloads["score"]["scores"]:
        assert score["formula_id"] in formulas
        assert isinstance(score["hard_gates"], list)
        assert score["hard_gates"]


def test_clean_observation_is_research_eligible():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    result = registry.evaluate_research_eligibility(
        data_quality_status="PASS",
        execution_incident=False,
        configuration_incident=False,
        lookahead_detected=False,
    )
    assert result.eligible is True
    assert result.classification == "RESEARCH_ELIGIBLE"


@pytest.mark.parametrize(
    "kwargs,reason",
    [
        ({"lookahead_detected": True}, "lookahead_detected"),
        ({"execution_incident": True}, "execution_incident"),
        ({"configuration_incident": True}, "configuration_incident"),
        ({"data_quality_status": "BLOCK"}, "data_quality_not_acceptable"),
    ],
)
def test_incident_or_invalid_data_is_quarantined(kwargs, reason):
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    arguments = {
        "data_quality_status": "PASS",
        "execution_incident": False,
        "configuration_incident": False,
        "lookahead_detected": False,
    }
    arguments.update(kwargs)
    result = registry.evaluate_research_eligibility(**arguments)
    assert result.eligible is False
    assert result.classification == "QUARANTINED"
    assert reason in result.reasons


def test_decision_trace_preserves_versions_gates_and_eligibility():
    registry = DataFoundationRegistry(REGISTRY_ROOT)
    eligibility = registry.evaluate_research_eligibility(
        data_quality_status="PASS",
        execution_incident=False,
        configuration_incident=False,
        lookahead_detected=False,
    )
    trace = DecisionTraceEnvelope.create(
        trace_id="trace-001",
        observed_at_utc="2026-07-18T12:00:00+00:00",
        formula_version=registry.versions["formula"],
        data_dictionary_version=registry.versions["data"],
        score_dictionary_version=registry.versions["score"],
        market_context={"symbol": "GOLD#", "regime": "TREND"},
        score_components={"decision.confidence": 99.5},
        gates={"trading_cost": {"status": "PASS"}},
        decision={"action": "BUY", "maximum_units": 3},
        research_eligibility=eligibility,
        source_timestamps={"gold_tick": "2026-07-18T11:59:59+00:00"},
    ).as_dict()
    assert trace["formula_version"] == "AFIP_FORMULA_REGISTRY_V1"
    assert trace["gates"]["trading_cost"]["status"] == "PASS"
    assert trace["research_eligibility"]["eligible"] is True


def test_empty_trace_id_and_non_utc_timestamp_are_rejected():
    eligibility = DataFoundationRegistry(REGISTRY_ROOT).evaluate_research_eligibility(
        data_quality_status="PASS", execution_incident=False,
        configuration_incident=False, lookahead_detected=False,
    )
    base = dict(
        formula_version="f", data_dictionary_version="d", score_dictionary_version="s",
        market_context={}, score_components={}, gates={}, decision={}, research_eligibility=eligibility,
    )
    with pytest.raises(RegistryValidationError):
        DecisionTraceEnvelope.create(trace_id="", **base)
    with pytest.raises(RegistryValidationError):
        DecisionTraceEnvelope.create(trace_id="x", observed_at_utc="2026-07-18T12:00:00", **base)


def test_documentation_set_exists():
    required = {
        "AFIP_DATA_ARCHITECTURE.md", "AFIP_DATA_DICTIONARY.md",
        "AFIP_SCORE_DICTIONARY.md", "AFIP_SCORE_CALCULATION_GUIDE.md",
        "AFIP_DATA_QUALITY_GUIDE.md", "AFIP_DECISION_TRACE_GUIDE.md",
        "AFIP_RESEARCH_DATA_USAGE_GUIDE.md", "AFIP_CROSS_MARKET_DATA_GUIDE.md",
    }
    assert required <= {path.name for path in (ROOT / "docs" / "research").glob("*.md")}
