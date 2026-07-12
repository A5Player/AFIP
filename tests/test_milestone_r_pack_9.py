from dataclasses import FrozenInstanceError
from hashlib import sha256
import pytest
from afip.production_certification_performance_audit import ProductionPerformanceAuditRuntime

def data_report(**o):
 r={"milestone":"R","pack":"8","status":"PASS","data_integrity_audit_passed":True,"audit_id":"RDATA-1234567890ABCDEF","broker":"XM","symbol":"GOLD#","base_lot_per_unit":.01,"execution_status":"LOCKED_SIMULATION_ONLY","direct_execution":False,"live_execution_enabled":False,"order_status":"NO_ORDER_SENT"};r.update(o);return r
def bench(i,d,**o):
 r={"benchmark_id":i,"benchmark_domain":d,"result":"PASS","severity":"HIGH","review_status":"REVIEWED","timestamp":100,"fingerprint":sha256(f"{i}:{d}".encode()).hexdigest(),"observed_value":1.0,"limit_value":2.0,"exception_accepted":False,"broker":"XM","symbol":"GOLD#","base_lot_per_unit":.01,"execution_status":"LOCKED_SIMULATION_ONLY","direct_execution":False,"live_execution_enabled":False,"order_status":"NO_ORDER_SENT","benchmark_changed_runtime":False,"production_traffic_used":False,"broker_request_created":False,"order_transmission_attempted":False,"position_modification_attempted":False,"trading_logic_changed":False};r.update(o);return r
def benches():
 ds=("LATENCY","THROUGHPUT","MEMORY","CPU","STARTUP","DASHBOARD","REGRESSION");return [bench(f"PERF-{n:03d}",d) for n,d in enumerate(ds,1)]
def test_passes():
 x=ProductionPerformanceAuditRuntime().validate(data_report(),benches(),audit_timestamp=200);assert x.status=="PASS" and x.performance_score==1.0 and x.next_audit=="R_PRODUCTION_CERTIFICATION"
def test_deterministic_immutable():
 r=ProductionPerformanceAuditRuntime();a=r.validate(data_report(),benches(),audit_timestamp=200);assert a==r.validate(data_report(),benches(),audit_timestamp=200)
 with pytest.raises(FrozenInstanceError):a.status="BLOCKED"
def test_bad_lineage():
 x=ProductionPerformanceAuditRuntime().validate(data_report(data_integrity_audit_passed=False),benches(),audit_timestamp=200);assert "data_integrity_audit_lineage_invalid" in x.block_reasons
def test_duplicate_future():
 rows=benches();rows[1]["benchmark_id"]=rows[0]["benchmark_id"];rows[2]["timestamp"]=300;x=ProductionPerformanceAuditRuntime().validate(data_report(),rows,audit_timestamp=200);assert "duplicate_or_invalid_performance_benchmark_id" in x.block_reasons and "performance_audit_chronology_invalid" in x.block_reasons
def test_missing_domain_schema():
 rows=benches()[:-1];rows[0]["observed_value"]="bad";x=ProductionPerformanceAuditRuntime().validate(data_report(),rows,audit_timestamp=200);assert "mandatory_performance_domain_missing" in x.block_reasons and "performance_benchmark_schema_invalid" in x.block_reasons
def test_unreviewed_failure():
 rows=benches();rows[0]["review_status"]="REJECTED";rows[1]["result"]="FAIL";x=ProductionPerformanceAuditRuntime().validate(data_report(),rows,audit_timestamp=200);assert "performance_benchmark_review_incomplete" in x.block_reasons and "unaccepted_performance_benchmark_failure" in x.block_reasons
def test_critical_low_score():
 rows=benches();rows[0].update(result="FAIL",severity="CRITICAL",exception_accepted=True);x=ProductionPerformanceAuditRuntime().validate(data_report(),rows,audit_timestamp=200,minimum_performance_score=.95);assert "critical_performance_benchmark_failure" in x.block_reasons and "performance_score_below_threshold" in x.block_reasons
def test_policy_boundaries():
 rows=benches();rows[0]["production_traffic_used"]=True;x=ProductionPerformanceAuditRuntime().validate(data_report(),rows,audit_timestamp=200);assert "feature_freeze_or_execution_policy_violation" in x.block_reasons and x.execution_status=="LOCKED_SIMULATION_ONLY" and x.production_certification_granted is False
