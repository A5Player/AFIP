from dataclasses import FrozenInstanceError
import pytest
from afip.market_behaviour_sequence_analysis import MarketBehaviourSequenceAnalysisRuntime

def _state(i, **kw):
    x={"state_id":f"PBNS-{i:016X}","status":"READY","schema_version":"AFIP_MARKET_BEHAVIOUR_STATE_V1","normalized_timestamp":2000+i*100,"market_regime":"TREND","behaviour_state":"DIRECTIONAL_PERSISTENCE","direction":"BUY","data_quality_certified":True,"future_safe":True,"future_leakage_detected":False,"market_regime_before_behaviour":True,"broker":"XM","symbol":"GOLD#","base_lot_per_unit":0.01,"execution_status":"LOCKED_SIMULATION_ONLY","order_status":"NO_ORDER_SENT","direct_execution":False,"live_execution_enabled":False,"automatic_parameter_update_allowed":False,"trading_logic_change_allowed":False,"production_knowledge_allowed":False}; x.update(kw); return x

def _states(): return [_state(1),_state(2),_state(3,market_regime="TRANSITION",behaviour_state="REGIME_TRANSITION",direction="FLAT"),_state(4,market_regime="RANGE",behaviour_state="RANGE_ROTATION",direction="FLAT")]

def test_ready_sequence_report_contains_transition_metrics():
    r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(_states(),analysis_timestamp=2500)
    assert r.status=="READY" and r.schema_version=="AFIP_MARKET_BEHAVIOUR_SEQUENCE_V1" and r.state_count==4 and r.transition_count==3 and r.regime_change_count==2 and r.behaviour_change_count==2 and r.report_id.startswith("PBSQ-")

def test_sequence_analysis_is_deterministic_and_immutable():
    rt=MarketBehaviourSequenceAnalysisRuntime(); a=rt.evaluate_many(_states(),analysis_timestamp=2500); b=rt.evaluate_many(_states(),analysis_timestamp=2500); assert a==b
    with pytest.raises(FrozenInstanceError): a.status="BLOCKED"

def test_blocks_invalid_pack_2_lineage_and_duplicate_ids():
    rows=_states(); rows[0]["schema_version"]="OTHER"; rows[1]["state_id"]=rows[0]["state_id"]; r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(rows,analysis_timestamp=2500); assert "pack_2_state_lineage_invalid" in r.block_reasons and "duplicate_state_id_detected" in r.block_reasons

def test_blocks_insufficient_sequence_and_invalid_chronology():
    r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many([_state(2),_state(1)],analysis_timestamp=2050); assert "insufficient_sequence_length" in r.block_reasons and "sequence_chronology_invalid" in r.block_reasons

def test_blocks_future_leakage_and_uncertified_data():
    rows=_states(); rows[1]["future_leakage_detected"]=True; rows[2]["data_quality_certified"]=False; r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(rows,analysis_timestamp=2500); assert "future_leakage_detected" in r.block_reasons and "data_quality_not_certified" in r.block_reasons

def test_dominant_state_and_persistence_are_deterministic():
    r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(_states(),analysis_timestamp=2500); assert r.dominant_market_regime=="TREND" and r.dominant_behaviour_state=="DIRECTIONAL_PERSISTENCE" and r.persistence_ratio==pytest.approx(1/3,abs=1e-6)

def test_blocks_regime_order_and_policy_violation():
    rows=_states(); rows[0]["market_regime_before_behaviour"]=False; rows[1]["broker"]="OTHER"; r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(rows,analysis_timestamp=2500); assert "market_regime_not_evaluated_before_behaviour" in r.block_reasons and "feature_freeze_or_execution_policy_violation" in r.block_reasons

def test_adaptive_production_and_execution_authority_remain_disabled():
    r=MarketBehaviourSequenceAnalysisRuntime().evaluate_many(_states(),analysis_timestamp=2500); assert r.research_only and not r.automatic_parameter_update_allowed and not r.trading_logic_change_allowed and not r.production_knowledge_allowed and not r.production_certification_granted and r.execution_status=="LOCKED_SIMULATION_ONLY" and not r.direct_execution and not r.live_execution_enabled and r.order_status=="NO_ORDER_SENT" and not r.broker_request_created and not r.order_transmission_attempted and not r.position_modification_attempted
