from dataclasses import FrozenInstanceError
from hashlib import sha256
import pytest
from afip.production_certification_safety_audit import ProductionSafetyAuditRuntime

def _cleanup(**overrides):
    payload={"cleanup_id":"RCLEAN-1234567890ABCDEF","status":"PASS","milestone":"R","pack":"5","repository_cleanup_passed":True,"broker":"XM","symbol":"GOLD#","base_lot_per_unit":0.01,"execution_status":"LOCKED_SIMULATION_ONLY","order_status":"NO_ORDER_SENT","direct_execution":False,"live_execution_enabled":False,"production_certification_granted":False,"release_candidate_granted":False}
    payload.update(overrides); return payload

def _policy():
    return {"broker":"XM","symbol":"GOLD#","base_lot_per_unit":0.01,"execution_status":"LOCKED_SIMULATION_ONLY","order_status":"NO_ORDER_SENT","direct_execution":False,"live_execution_enabled":False,"production_certification_granted":False,"release_candidate_granted":False}

def _fp(v): return sha256(v.encode()).hexdigest()

def _controls():
    domains=["RISK_BOUNDARY","ORDER_SAFETY","POSITION_SAFETY","DATA_SAFETY","OPERATIONAL_SAFETY","FAIL_SAFE"]
    return [{"control_id":f"SAFE-{i:03d}","timestamp":1000+i,"control_domain":d,"control_name":f"{d} verified","fingerprint":_fp(d),"result":"PASS","severity":"CRITICAL" if d in {"ORDER_SAFETY","FAIL_SAFE"} else "HIGH","review_status":"REVIEWED","exception_accepted":False,**_policy()} for i,d in enumerate(domains,1)]

def test_safety_audit_passes_deterministically():
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),_controls(),audit_timestamp=2000)
    assert r.status=="PASS" and r.safety_audit_passed and r.safety_score==1.0 and r.mandatory_domains_covered and r.next_audit=="R_SECURITY_AUDIT"

def test_report_is_immutable_and_repeatable():
    rt=ProductionSafetyAuditRuntime(); a=rt.validate(_cleanup(),_controls(),audit_timestamp=2000); b=rt.validate(_cleanup(),_controls(),audit_timestamp=2000); assert a==b
    with pytest.raises(FrozenInstanceError): a.status="BLOCKED"

def test_blocks_invalid_cleanup_lineage():
    r=ProductionSafetyAuditRuntime().validate(_cleanup(pack="4",repository_cleanup_passed=False),_controls(),audit_timestamp=2000); assert "repository_cleanup_lineage_invalid" in r.block_reasons

def test_blocks_duplicate_ids_and_bad_chronology():
    rows=_controls(); rows[1]["control_id"]=rows[0]["control_id"]; rows[2]["timestamp"]=9999
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),rows,audit_timestamp=2000); assert "duplicate_or_invalid_safety_control_id" in r.block_reasons and "safety_audit_chronology_invalid" in r.block_reasons

def test_blocks_invalid_schema_and_incomplete_review():
    rows=_controls(); rows[0]["fingerprint"]="invalid"; rows[1]["review_status"]="PENDING"
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),rows,audit_timestamp=2000); assert "safety_control_schema_invalid" in r.block_reasons and "safety_control_review_incomplete" in r.block_reasons

def test_blocks_failed_and_critical_controls():
    rows=_controls(); rows[1]["result"]="FAIL"; rows[1]["severity"]="CRITICAL"
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),rows,audit_timestamp=2000); assert "unaccepted_safety_control_failure" in r.block_reasons and "critical_safety_control_failure" in r.block_reasons and "SAFE-002" in r.failed_control_ids

def test_blocks_missing_domain_and_low_score():
    rows=_controls()[:-1]; rows[0]["result"]="ACCEPTED_EXCEPTION"; rows[0]["exception_accepted"]=True
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),rows,audit_timestamp=2000,minimum_safety_score=0.95); assert "mandatory_safety_domain_missing" in r.block_reasons and "safety_score_below_threshold" in r.block_reasons

def test_certification_and_execution_remain_locked():
    r=ProductionSafetyAuditRuntime().validate(_cleanup(),_controls(),audit_timestamp=2000)
    assert not r.production_certification_granted and not r.release_candidate_granted and not r.trading_logic_changed and not r.safety_control_bypassed
    assert r.execution_status=="LOCKED_SIMULATION_ONLY" and not r.direct_execution and not r.live_execution_enabled and r.order_status=="NO_ORDER_SENT"
    assert not r.broker_request_created and not r.order_transmission_attempted and not r.position_modification_attempted
