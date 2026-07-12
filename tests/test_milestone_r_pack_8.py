from dataclasses import FrozenInstanceError
from hashlib import sha256
import pytest
from afip.production_certification_data_integrity_audit import ProductionDataIntegrityAuditRuntime

def security_report(**o):
 r={"milestone":"R","pack":"7","status":"PASS","security_audit_passed":True,"audit_id":"RSEC-1234567890ABCDEF","broker":"XM","symbol":"GOLD#","base_lot_per_unit":0.01,"execution_status":"LOCKED_SIMULATION_ONLY","direct_execution":False,"live_execution_enabled":False,"order_status":"NO_ORDER_SENT"}; r.update(o); return r

def control(i,d,**o):
 r={"control_id":i,"control_domain":d,"result":"PASS","severity":"HIGH","review_status":"REVIEWED","timestamp":100,"fingerprint":sha256(f"{i}:{d}".encode()).hexdigest(),"exception_accepted":False,"broker":"XM","symbol":"GOLD#","base_lot_per_unit":0.01,"execution_status":"LOCKED_SIMULATION_ONLY","direct_execution":False,"live_execution_enabled":False,"order_status":"NO_ORDER_SENT","source_data_changed":False,"schema_changed":False,"historical_data_rewritten":False,"future_data_used":False,"broker_request_created":False,"order_transmission_attempted":False,"position_modification_attempted":False,"trading_logic_changed":False}; r.update(o); return r

def controls():
 ds=("SOURCE_INTEGRITY","SCHEMA_INTEGRITY","CHRONOLOGY_INTEGRITY","LINEAGE_INTEGRITY","RECONCILIATION_INTEGRITY","PERSISTENCE_INTEGRITY","REPLAY_INTEGRITY"); return [control(f"DATA-{n:03d}",d) for n,d in enumerate(ds,1)]

def test_passes():
 x=ProductionDataIntegrityAuditRuntime().validate(security_report(),controls(),audit_timestamp=200); assert x.status=="PASS" and x.data_integrity_score==1.0 and x.next_audit=="R_PERFORMANCE_AUDIT"
def test_deterministic_immutable():
 r=ProductionDataIntegrityAuditRuntime(); a=r.validate(security_report(),controls(),audit_timestamp=200); assert a==r.validate(security_report(),controls(),audit_timestamp=200)
 with pytest.raises(FrozenInstanceError): a.status="BLOCKED"
def test_bad_lineage():
 x=ProductionDataIntegrityAuditRuntime().validate(security_report(security_audit_passed=False),controls(),audit_timestamp=200); assert "security_audit_lineage_invalid" in x.block_reasons
def test_duplicate_future():
 rows=controls(); rows[1]["control_id"]=rows[0]["control_id"]; rows[2]["timestamp"]=300; x=ProductionDataIntegrityAuditRuntime().validate(security_report(),rows,audit_timestamp=200); assert "duplicate_or_invalid_data_integrity_control_id" in x.block_reasons and "data_integrity_audit_chronology_invalid" in x.block_reasons
def test_missing_domain_schema():
 rows=controls()[:-1]; rows[0]["fingerprint"]="bad"; x=ProductionDataIntegrityAuditRuntime().validate(security_report(),rows,audit_timestamp=200); assert "mandatory_data_integrity_domain_missing" in x.block_reasons and "data_integrity_control_schema_invalid" in x.block_reasons
def test_unreviewed_failure():
 rows=controls(); rows[0]["review_status"]="REJECTED"; rows[1]["result"]="FAIL"; x=ProductionDataIntegrityAuditRuntime().validate(security_report(),rows,audit_timestamp=200); assert "data_integrity_control_review_incomplete" in x.block_reasons and "unaccepted_data_integrity_control_failure" in x.block_reasons
def test_critical_low_score():
 rows=controls(); rows[0].update(result="FAIL",severity="CRITICAL",exception_accepted=True); x=ProductionDataIntegrityAuditRuntime().validate(security_report(),rows,audit_timestamp=200,minimum_data_integrity_score=.95); assert "critical_data_integrity_control_failure" in x.block_reasons and "data_integrity_score_below_threshold" in x.block_reasons
def test_policy_boundaries():
 rows=controls(); rows[0]["future_data_used"]=True; x=ProductionDataIntegrityAuditRuntime().validate(security_report(),rows,audit_timestamp=200); assert "feature_freeze_or_execution_policy_violation" in x.block_reasons and x.execution_status=="LOCKED_SIMULATION_ONLY" and x.production_certification_granted is False
