from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from afip.financial_data_lake import FinancialDataLake, canonical_json, classify_layer


def sample(lake):
    return lake.build_record(
        layer="raw", domain="gold", instrument="GOLD#", source_id="MT5_P1",
        observed_at_utc="2026-07-18T12:00:00+00:00",
        payload={"bid": 3333.10, "ask": 3333.42, "point": 0.01},
        provenance={"provider": "XM", "terminal": "P1", "future_data_used": False},
        quality={"status": "PASS", "freshness_ms": 50}, research_eligibility="ELIGIBLE")


def test_layers_are_strict():
    assert classify_layer("RAW") == "raw"
    with pytest.raises(ValueError): classify_layer("profile_data")


def test_timezone_is_required(tmp_path):
    lake=FinancialDataLake(tmp_path)
    with pytest.raises(ValueError):
        lake.build_record(layer="raw",domain="gold",instrument="GOLD#",source_id="x",observed_at_utc="2026-01-01T00:00:00",payload={},provenance={},quality={},research_eligibility="ELIGIBLE")


def test_record_id_is_deterministic(tmp_path):
    lake=FinancialDataLake(tmp_path)
    assert sample(lake).record_id == sample(lake).record_id


def test_append_creates_partition_manifest_and_index(tmp_path):
    lake=FinancialDataLake(tmp_path)
    result=lake.append(sample(lake))
    assert result.status == "APPENDED"
    path=tmp_path/result.relative_path
    assert path.exists()
    assert path.with_name("manifest.jsonl").exists()
    assert path.with_name("record_ids.txt").exists()


def test_duplicate_is_skipped(tmp_path):
    lake=FinancialDataLake(tmp_path); record=sample(lake)
    assert lake.append(record).duplicate is False
    assert lake.append(record).duplicate is True
    assert len((tmp_path/lake._relative_path(record)).read_text().splitlines()) == 1


def test_canonical_json_is_stable():
    assert canonical_json({"b":1,"a":2}) == canonical_json({"a":2,"b":1})


def test_catalog_is_profile_independent():
    catalog=json.loads(Path("config/financial_data_lake/source_catalog.json").read_text(encoding="utf-8"))
    assert catalog["policy"]["shared_across_profiles"] is True
    assert all(item["domain"] not in {"p1","p2","p3","p4"} for item in catalog["domains"])


def test_storage_is_append_only_and_execution_neutral():
    policy=json.loads(Path("config/financial_data_lake/storage_policy.json").read_text(encoding="utf-8"))
    assert policy["raw_mutability"] == "APPEND_ONLY"
    assert policy["execution_mode"] == "NO_EXECUTION_SIDE_EFFECT"


def test_formula_and_trace_contract():
    contract=json.loads(Path("config/financial_data_lake/normalization_contract.json").read_text(encoding="utf-8"))
    assert "derived" in contract["formula_version_required_for_layers"]
    assert "decision_context" in contract["decision_trace_required_for_layers"]


def test_no_execution_imports():
    source=Path("afip/financial_data_lake/runtime.py").read_text(encoding="utf-8")
    forbidden=("order_send", "MetaTrader5", "demo_execution_gateway", "live_execution")
    assert not any(token in source for token in forbidden)
