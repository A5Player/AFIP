"""Milestone R Pack 9: deterministic production performance audit."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class ProductionPerformanceAuditReport:
    audit_id: str; status: str; reason: str; milestone: str; pack: str; audit_timestamp: int
    data_integrity_audit_id: str; benchmark_count: int; reviewed_benchmark_count: int; passed_benchmark_count: int
    failed_benchmark_count: int; accepted_exception_count: int; critical_failure_count: int
    latency_benchmark_count: int; throughput_benchmark_count: int; memory_benchmark_count: int
    cpu_benchmark_count: int; startup_benchmark_count: int; dashboard_benchmark_count: int; regression_benchmark_count: int
    data_integrity_lineage_valid: bool; benchmark_ids_unique: bool; chronology_valid: bool; benchmark_schema_valid: bool
    all_benchmarks_reviewed: bool; no_unaccepted_failure: bool; no_critical_failure: bool; mandatory_domains_covered: bool
    locked_policy_valid: bool; performance_score: float; performance_audit_passed: bool; next_audit: str
    review_required: bool; immutable_record: bool; production_certification_granted: bool; release_candidate_granted: bool
    block_reasons: tuple[str, ...]; benchmark_ids: tuple[str, ...]; failed_benchmark_ids: tuple[str, ...]
    accepted_exception_ids: tuple[str, ...]; explanation_reason_en: str; explanation_reason_th: str
    broker: str = "XM"; symbol: str = "GOLD#"; base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"; direct_execution: bool = False
    live_execution_enabled: bool = False; order_status: str = "NO_ORDER_SENT"
    benchmark_changed_runtime: bool = False; production_traffic_used: bool = False; broker_request_created: bool = False
    order_transmission_attempted: bool = False; position_modification_attempted: bool = False; trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class ProductionPerformanceAuditRuntime:
    ALLOWED_DOMAINS=frozenset({"LATENCY","THROUGHPUT","MEMORY","CPU","STARTUP","DASHBOARD","REGRESSION"})
    MANDATORY_DOMAINS=ALLOWED_DOMAINS
    ALLOWED_RESULTS=frozenset({"PASS","FAIL","ACCEPTED_EXCEPTION"})
    ALLOWED_SEVERITIES=frozenset({"LOW","MEDIUM","HIGH","CRITICAL"})
    ALLOWED_REVIEW_STATUSES=frozenset({"REVIEWED","ACCEPTED","REJECTED"})
    def validate(self, data_integrity_report: Mapping[str,Any], benchmarks: Iterable[Mapping[str,Any]], *, audit_timestamp:int, minimum_performance_score:float=.95)->ProductionPerformanceAuditReport:
        rows=tuple(dict(x) for x in benchmarks); ts_a=self._int(audit_timestamp)
        ids=tuple(str(r.get("benchmark_id","")).strip().upper() for r in rows); ts=tuple(self._int(r.get("timestamp",0)) for r in rows)
        lineage=(str(data_integrity_report.get("milestone","")).upper()=="R" and str(data_integrity_report.get("pack",""))=="8" and str(data_integrity_report.get("status","")).upper()=="PASS" and bool(data_integrity_report.get("data_integrity_audit_passed",False)) and str(data_integrity_report.get("audit_id","")).upper().startswith("RDATA-"))
        unique=all(i.startswith("PERF-") for i in ids) and len(ids)==len(set(ids)); chronology=all(t>0 and t<=ts_a for t in ts)
        schema=all(self._schema(r) for r in rows); reviewed=sum(1 for r in rows if self._reviewed(r)); all_reviewed=reviewed==len(rows)
        passed=tuple(r for r in rows if self._result(r)=="PASS"); failed=tuple(r for r in rows if self._result(r)=="FAIL"); exc=tuple(r for r in rows if self._result(r)=="ACCEPTED_EXCEPTION")
        unaccepted=tuple(r for r in failed if not bool(r.get("exception_accepted",False))); critical=tuple(r for r in failed if str(r.get("severity","")).upper()=="CRITICAL")
        covered=self.MANDATORY_DOMAINS.issubset({str(r.get("benchmark_domain","")).upper() for r in rows}); policy=self._policy(data_integrity_report) and all(self._policy(r) for r in rows)
        score=round((len(passed)+.5*len(exc))/max(len(rows),1),6); threshold=self._score(minimum_performance_score)
        checks=((not lineage,"data_integrity_audit_lineage_invalid"),(not unique,"duplicate_or_invalid_performance_benchmark_id"),(not chronology,"performance_audit_chronology_invalid"),(not schema,"performance_benchmark_schema_invalid"),(not all_reviewed,"performance_benchmark_review_incomplete"),(bool(unaccepted),"unaccepted_performance_benchmark_failure"),(bool(critical),"critical_performance_benchmark_failure"),(not covered,"mandatory_performance_domain_missing"),(score<threshold,"performance_score_below_threshold"),(not policy,"feature_freeze_or_execution_policy_violation"))
        blocked=tuple(sorted({r for c,r in checks if c})); ok=not blocked
        ident={"data_integrity_audit_id":str(data_integrity_report.get("audit_id","")),"benchmark_ids":ids,"audit_timestamp":ts_a,"score":score,"blocked":blocked}
        aid="RPERF-"+sha256(json.dumps(ident,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16].upper()
        count=lambda d:sum(1 for r in rows if str(r.get("benchmark_domain","")).upper()==d)
        return ProductionPerformanceAuditReport(audit_id=aid,status="PASS" if ok else "BLOCKED",reason="PERFORMANCE_AUDIT_PASSED" if ok else "PERFORMANCE_AUDIT_BLOCKED",milestone="R",pack="9",audit_timestamp=ts_a,data_integrity_audit_id=str(data_integrity_report.get("audit_id","")).upper(),benchmark_count=len(rows),reviewed_benchmark_count=reviewed,passed_benchmark_count=len(passed),failed_benchmark_count=len(failed),accepted_exception_count=len(exc),critical_failure_count=len(critical),latency_benchmark_count=count("LATENCY"),throughput_benchmark_count=count("THROUGHPUT"),memory_benchmark_count=count("MEMORY"),cpu_benchmark_count=count("CPU"),startup_benchmark_count=count("STARTUP"),dashboard_benchmark_count=count("DASHBOARD"),regression_benchmark_count=count("REGRESSION"),data_integrity_lineage_valid=lineage,benchmark_ids_unique=unique,chronology_valid=chronology,benchmark_schema_valid=schema,all_benchmarks_reviewed=all_reviewed,no_unaccepted_failure=not bool(unaccepted),no_critical_failure=not bool(critical),mandatory_domains_covered=covered,locked_policy_valid=policy,performance_score=score,performance_audit_passed=ok,next_audit="R_PRODUCTION_CERTIFICATION" if ok else "R_PERFORMANCE_REVIEW_REQUIRED",review_required=not ok,immutable_record=True,production_certification_granted=False,release_candidate_granted=False,block_reasons=blocked,benchmark_ids=ids,failed_benchmark_ids=tuple(str(r.get("benchmark_id","")).upper() for r in failed),accepted_exception_ids=tuple(str(r.get("benchmark_id","")).upper() for r in exc),explanation_reason_en="Performance evidence passed deterministic validation. Execution remains locked." if ok else "Performance Audit was blocked by lineage, evidence, chronology, review, coverage, score, failure, or frozen-policy controls.",explanation_reason_th="หลักฐานประสิทธิภาพผ่านการตรวจสอบแบบ deterministic และ execution ยังคงถูกล็อก" if ok else "Performance Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน ความครอบคลุม คะแนน ความล้มเหลว หรือนโยบายล็อก")
    def _schema(self,r):
        fp=str(r.get("fingerprint","")).lower(); return str(r.get("benchmark_domain","")).upper() in self.ALLOWED_DOMAINS and self._result(r) in self.ALLOWED_RESULTS and str(r.get("severity","")).upper() in self.ALLOWED_SEVERITIES and str(r.get("review_status","")).upper() in self.ALLOWED_REVIEW_STATUSES and len(fp)==64 and all(c in "0123456789abcdef" for c in fp) and self._number(r.get("observed_value")) and self._number(r.get("limit_value"))
    def _reviewed(self,r): return str(r.get("review_status","")).upper() in {"REVIEWED","ACCEPTED"}
    def _result(self,r): return str(r.get("result","")).upper()
    def _number(self,v):
        try: float(v); return True
        except (TypeError,ValueError): return False
    def _policy(self,r):
        return str(r.get("broker","XM"))=="XM" and str(r.get("symbol","GOLD#"))=="GOLD#" and float(r.get("base_lot_per_unit",.01))==.01 and str(r.get("execution_status","LOCKED_SIMULATION_ONLY"))=="LOCKED_SIMULATION_ONLY" and not bool(r.get("direct_execution",False)) and not bool(r.get("live_execution_enabled",False)) and str(r.get("order_status","NO_ORDER_SENT"))=="NO_ORDER_SENT" and not any(bool(r.get(k,False)) for k in ("benchmark_changed_runtime","production_traffic_used","broker_request_created","order_transmission_attempted","position_modification_attempted","trading_logic_changed"))
    def _score(self,v):
        try:return min(max(float(v),0.0),1.0)
        except (TypeError,ValueError):return 1.0
    def _int(self,v):
        try:return int(v)
        except (TypeError,ValueError):return 0
