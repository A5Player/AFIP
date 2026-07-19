from pathlib import Path
import pytest
from afip.research_standardization import (InitialStandardPolicy, ResearchDerivedStandardRegistry,
    ResearchLineage, StandardContext)
from afip.runtime_standard_adapter import *


def context():
    return StandardContext("PRECIOUS_METAL","TRENDING","BULLISH","NORMAL","UP","NORMAL","LONDON","BUY","BREAKOUT")

def standard(**overrides):
    data=dict(standard_id="STD1",standard_version="1.0",context=context(),policy_id="P",
      policy_parameters={"units":3,"lot_per_unit":0.01,"stop_points":3000,"target_points":5000,
      "break_even_trigger_points":1200,"trailing_stop_points":900,"hold_policy":"trend","close_policy":"evidence"},
      lineage=ResearchLineage("P","1","evidence",("dataset",),3,4,500,"2020-01-01","2026-01-01",("GOLD#",)),
      evidence_score=90,temporal_stability_score=85,resilience_score=88,owner_approved=True,approval_reference="OWNER")
    data.update(overrides); return InitialStandardPolicy(**data)

def registry():
    r=ResearchDerivedStandardRegistry(); r.register(standard()); return r

def test_selected_guidance_is_runtime_usable():
    g=RuntimeStandardAdapter(registry()).build_guidance(context(),"G1")
    assert g.runtime_usable and g.requested_units==3 and g.selected_standard_id=="STD1"

def test_guidance_preserves_all_safety_gates():
    g=RuntimeStandardAdapter(registry()).build_guidance(context(),"G2")
    assert set(g.safety_gate_requirements)=={"risk_approval","trading_cost_approval","profile_unit_capacity","execution_permission"}

def test_context_mismatch_is_not_usable():
    c=StandardContext("FOREX_MAJOR","TRENDING","BULLISH","NORMAL","UP","NORMAL","LONDON","BUY","BREAKOUT")
    assert not RuntimeStandardAdapter(registry()).build_guidance(c,"G3").runtime_usable

def test_units_are_bounded():
    r=ResearchDerivedStandardRegistry(); r.register(standard(policy_parameters={"units":99,"lot_per_unit":1,"stop_points":10,"target_points":10}))
    g=RuntimeStandardAdapter(r).build_guidance(context(),"G4")
    assert g.requested_units==3 and g.lot_per_unit==0.01

def test_dataset_persists_guidance(tmp_path):
    RuntimeStandardAdapter(registry(),str(tmp_path)).build_guidance(context(),"G5")
    assert (tmp_path/"runtime_standard_guidance.jsonl").exists()

def test_backfill_orders_and_deduplicates(tmp_path):
    rows=[{"timestamp_utc":"2024-01-02","open":2,"high":3,"low":1,"close":2},
          {"timestamp_utc":"2024-01-01","open":1,"high":2,"low":0,"close":1},
          {"timestamp_utc":"2024-01-01","open":1,"high":2,"low":0,"close":1}]
    result=HistoricalBackfillOrchestrator(str(tmp_path)).run(BackfillRequest("R","GOLD#","H1"),lambda _: rows,{"provider":"TEST"})
    assert result.bars_persisted==2 and result.duplicates_skipped==1 and result.earliest_available_utc=="2024-01-01"

def test_backfill_empty_provider(tmp_path):
    result=HistoricalBackfillOrchestrator(str(tmp_path)).run(BackfillRequest("R","GOLD#","H1"),lambda _: [],{"provider":"TEST"})
    assert result.status=="NO_DATA"

def test_backfill_rejects_missing_price_fields(tmp_path):
    with pytest.raises(KeyError):
        HistoricalBackfillOrchestrator(str(tmp_path)).run(BackfillRequest("R","GOLD#","H1"),lambda _: [{"timestamp_utc":"x"}],{})

def test_guidance_checksum_present():
    assert len(RuntimeStandardAdapter(registry()).build_guidance(context(),"G").as_dict()["guidance_checksum"])==64

def test_backfill_checksum_present(tmp_path):
    r=HistoricalBackfillOrchestrator(str(tmp_path)).run(BackfillRequest("R","GOLD#","H1"),lambda _: [],{})
    assert len(r.as_dict()["result_checksum"])==64
