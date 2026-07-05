from afip.cli.simulate import _find_intelligence
from afip.pipeline.modular_intelligence_pipeline import ModularIntelligencePipeline
from afip.registry.intelligence_catalog import IntelligenceCatalog
from afip.runtime.runtime_v1 import RuntimeV1


INSTITUTIONAL_NAMES = {
    "FairValueGapIntelligence",
    "ImbalanceIntelligence",
    "OrderBlockIntelligence",
    "LiquiditySweepIntelligence",
    "SmartMoneyConceptIntelligence",
}


def sample_snapshot():
    return {
        "symbol": "XAUUSD",
        "opens": [100.0, 100.2, 100.1, 100.0, 100.4, 101.0, 101.5, 102.0, 102.8, 103.4],
        "highs": [100.5, 100.6, 100.4, 100.8, 101.4, 101.9, 102.4, 103.1, 103.8, 104.5],
        "lows": [99.7, 99.9, 99.8, 99.6, 100.9, 101.2, 101.7, 102.2, 102.9, 103.5],
        "closes": [100.1, 100.0, 99.95, 100.6, 101.2, 101.7, 102.2, 102.9, 103.6, 104.2],
        "volumes": [100, 120, 125, 150, 180, 190, 200, 220, 230, 250],
        "spread": 25.0,
    }


def test_default_catalog_loads_institutional_intelligence():
    modules = IntelligenceCatalog().load_default()
    module_names = {module.__class__.__name__ for module in modules}
    assert INSTITUTIONAL_NAMES.issubset(module_names)
    assert len(modules) >= 20


def test_modular_pipeline_runs_institutional_intelligence():
    result = ModularIntelligencePipeline().run(sample_snapshot())
    names = {item["name"] for item in result["intelligence"]}
    assert INSTITUTIONAL_NAMES.issubset(names)
    assert result["module_count"] >= 20
    assert result["decision"]["action"] in {"BUY", "SELL", "WAIT"}


def test_runtime_exposes_institutional_intelligence_results():
    result = RuntimeV1().simulate()
    modular = result["modular_intelligence"]
    names = {item["name"] for item in modular["intelligence"]}
    assert INSTITUTIONAL_NAMES.issubset(names)
    assert modular["module_count"] >= 20
    assert result["status"] == "OK"


def test_cli_find_intelligence_supports_institutional_modules():
    result = ModularIntelligencePipeline().run(sample_snapshot())
    smart_money = _find_intelligence(result, "SmartMoneyConceptIntelligence")
    assert smart_money["name"] == "SmartMoneyConceptIntelligence"
    assert smart_money["status"] in {"READY", "INSUFFICIENT_DATA"}


def test_batch15_1_keeps_financial_terminology_only():
    banned_terms = ("military", "commander", "sniper", "scout", "ranger")
    catalog_source_names = {module.__class__.__name__ for module in IntelligenceCatalog().load_default()}
    assert not any(term in name.lower() for term in banned_terms for name in catalog_source_names)
