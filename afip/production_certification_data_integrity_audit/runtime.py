"""Milestone R Pack 8: deterministic production data integrity audit."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class ProductionDataIntegrityAuditReport:
    audit_id: str; status: str; reason: str; milestone: str; pack: str; audit_timestamp: int
    security_audit_id: str; control_count: int; reviewed_control_count: int; passed_control_count: int
    failed_control_count: int; accepted_exception_count: int; critical_failure_count: int
    source_integrity_control_count: int; schema_integrity_control_count: int; chronology_integrity_control_count: int
    lineage_integrity_control_count: int; reconciliation_integrity_control_count: int
    persistence_integrity_control_count: int; replay_integrity_control_count: int
    security_lineage_valid: bool; control_ids_unique: bool; chronology_valid: bool; control_schema_valid: bool
    all_controls_reviewed: bool; no_unaccepted_failure: bool; no_critical_failure: bool
    mandatory_domains_covered: bool; locked_policy_valid: bool; data_integrity_score: float
    data_integrity_audit_passed: bool; next_audit: str; review_required: bool; immutable_record: bool
    production_certification_granted: bool; release_candidate_granted: bool
    block_reasons: tuple[str, ...]; control_ids: tuple[str, ...]; failed_control_ids: tuple[str, ...]
    accepted_exception_ids: tuple[str, ...]; explanation_reason_en: str; explanation_reason_th: str
    broker: str = "XM"; symbol: str = "GOLD#"; base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"; direct_execution: bool = False
    live_execution_enabled: bool = False; order_status: str = "NO_ORDER_SENT"
    source_data_changed: bool = False; schema_changed: bool = False; historical_data_rewritten: bool = False
    future_data_used: bool = False; broker_request_created: bool = False; order_transmission_attempted: bool = False
    position_modification_attempted: bool = False; trading_logic_changed: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class ProductionDataIntegrityAuditRuntime:
    ALLOWED_DOMAINS = frozenset({"SOURCE_INTEGRITY","SCHEMA_INTEGRITY","CHRONOLOGY_INTEGRITY","LINEAGE_INTEGRITY","RECONCILIATION_INTEGRITY","PERSISTENCE_INTEGRITY","REPLAY_INTEGRITY"})
    MANDATORY_DOMAINS = ALLOWED_DOMAINS
    ALLOWED_RESULTS = frozenset({"PASS","FAIL","ACCEPTED_EXCEPTION"})
    ALLOWED_SEVERITIES = frozenset({"LOW","MEDIUM","HIGH","CRITICAL"})
    ALLOWED_REVIEW_STATUSES = frozenset({"REVIEWED","ACCEPTED","REJECTED"})

    def validate(self, security_report: Mapping[str, Any], controls: Iterable[Mapping[str, Any]], *, audit_timestamp: int, minimum_data_integrity_score: float = 0.95) -> ProductionDataIntegrityAuditReport:
        rows=tuple(dict(x) for x in controls); audit_ts=self._integer(audit_timestamp)
        ids=tuple(str(r.get("control_id","")).strip().upper() for r in rows)
        ts=tuple(self._integer(r.get("timestamp",0)) for r in rows)
        lineage=(str(security_report.get("milestone","")).upper()=="R" and str(security_report.get("pack",""))=="7" and str(security_report.get("status","")).upper()=="PASS" and bool(security_report.get("security_audit_passed",False)) and str(security_report.get("audit_id","")).upper().startswith("RSEC-"))
        unique=all(i.startswith("DATA-") for i in ids) and len(ids)==len(set(ids))
        chronology=all(t>0 and t<=audit_ts for t in ts)
        schema_valid=all(self._schema(r) for r in rows)
        reviewed=sum(1 for r in rows if self._reviewed(r)); all_reviewed=reviewed==len(rows)
        passed=tuple(r for r in rows if self._result(r)=="PASS"); failed=tuple(r for r in rows if self._result(r)=="FAIL"); exc=tuple(r for r in rows if self._result(r)=="ACCEPTED_EXCEPTION")
        unaccepted=tuple(r for r in failed if not bool(r.get("exception_accepted",False)))
        critical=tuple(r for r in failed if str(r.get("severity","")).upper()=="CRITICAL")
        domains={str(r.get("control_domain","")).upper() for r in rows}; covered=self.MANDATORY_DOMAINS.issubset(domains)
        policy=self._policy(security_report) and all(self._policy(r) for r in rows)
        score=round((len(passed)+0.5*len(exc))/max(len(rows),1),6); threshold=self._score(minimum_data_integrity_score)
        checks=((not lineage,"security_audit_lineage_invalid"),(not unique,"duplicate_or_invalid_data_integrity_control_id"),(not chronology,"data_integrity_audit_chronology_invalid"),(not schema_valid,"data_integrity_control_schema_invalid"),(not all_reviewed,"data_integrity_control_review_incomplete"),(bool(unaccepted),"unaccepted_data_integrity_control_failure"),(bool(critical),"critical_data_integrity_control_failure"),(not covered,"mandatory_data_integrity_domain_missing"),(score<threshold,"data_integrity_score_below_threshold"),(not policy,"feature_freeze_or_execution_policy_violation"))
        blocked=tuple(sorted({r for c,r in checks if c})); ok=not blocked
        identity={"security_audit_id":str(security_report.get("audit_id","")),"control_ids":ids,"audit_timestamp":audit_ts,"score":score,"blocked":blocked}
        aid="RDATA-"+sha256(json.dumps(identity,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16].upper()
        return ProductionDataIntegrityAuditReport(audit_id=aid,status="PASS" if ok else "BLOCKED",reason="DATA_INTEGRITY_AUDIT_PASSED" if ok else "DATA_INTEGRITY_AUDIT_BLOCKED",milestone="R",pack="8",audit_timestamp=audit_ts,security_audit_id=str(security_report.get("audit_id","")).upper(),control_count=len(rows),reviewed_control_count=reviewed,passed_control_count=len(passed),failed_control_count=len(failed),accepted_exception_count=len(exc),critical_failure_count=len(critical),source_integrity_control_count=self._count(rows,"SOURCE_INTEGRITY"),schema_integrity_control_count=self._count(rows,"SCHEMA_INTEGRITY"),chronology_integrity_control_count=self._count(rows,"CHRONOLOGY_INTEGRITY"),lineage_integrity_control_count=self._count(rows,"LINEAGE_INTEGRITY"),reconciliation_integrity_control_count=self._count(rows,"RECONCILIATION_INTEGRITY"),persistence_integrity_control_count=self._count(rows,"PERSISTENCE_INTEGRITY"),replay_integrity_control_count=self._count(rows,"REPLAY_INTEGRITY"),security_lineage_valid=lineage,control_ids_unique=unique,chronology_valid=chronology,control_schema_valid=schema_valid,all_controls_reviewed=all_reviewed,no_unaccepted_failure=not bool(unaccepted),no_critical_failure=not bool(critical),mandatory_domains_covered=covered,locked_policy_valid=policy,data_integrity_score=score,data_integrity_audit_passed=ok,next_audit="R_PERFORMANCE_AUDIT" if ok else "R_DATA_INTEGRITY_REVIEW_REQUIRED",review_required=not ok,immutable_record=True,production_certification_granted=False,release_candidate_granted=False,block_reasons=blocked,control_ids=ids,failed_control_ids=tuple(str(r.get("control_id","")).upper() for r in failed),accepted_exception_ids=tuple(str(r.get("control_id","")).upper() for r in exc),explanation_reason_en="Reviewed data-integrity controls passed deterministic validation. Execution remains locked." if ok else "Data Integrity Audit was blocked by lineage, evidence, chronology, review, coverage, score, failure, or frozen-policy controls.",explanation_reason_th="มาตรการความสมบูรณ์ของข้อมูลผ่านการตรวจสอบ deterministic และ execution ยังคงถูกล็อก" if ok else "Data Integrity Audit ถูกระงับจาก lineage หลักฐาน ลำดับเวลา การทบทวน ความครอบคลุม คะแนน ความล้มเหลว หรือนโยบายล็อก")
    def _schema(self,r):
        fp=str(r.get("fingerprint","")).lower(); return (str(r.get("control_domain","")).upper() in self.ALLOWED_DOMAINS and self._result(r) in self.ALLOWED_RESULTS and str(r.get("severity","")).upper() in self.ALLOWED_SEVERITIES and str(r.get("review_status","")).upper() in self.ALLOWED_REVIEW_STATUSES and len(fp)==64 and all(c in "0123456789abcdef" for c in fp))
    def _reviewed(self,r): return str(r.get("review_status","")).upper() in {"REVIEWED","ACCEPTED"}
    def _result(self,r): return str(r.get("result","")).upper()
    def _count(self,rows,d): return sum(1 for r in rows if str(r.get("control_domain","")).upper()==d)
    def _policy(self,r):
        return (str(r.get("broker","XM"))=="XM" and str(r.get("symbol","GOLD#"))=="GOLD#" and float(r.get("base_lot_per_unit",0.01))==0.01 and str(r.get("execution_status","LOCKED_SIMULATION_ONLY"))=="LOCKED_SIMULATION_ONLY" and not bool(r.get("direct_execution",False)) and not bool(r.get("live_execution_enabled",False)) and str(r.get("order_status","NO_ORDER_SENT"))=="NO_ORDER_SENT" and not any(bool(r.get(k,False)) for k in ("source_data_changed","schema_changed","historical_data_rewritten","future_data_used","broker_request_created","order_transmission_attempted","position_modification_attempted","trading_logic_changed")))
    def _score(self,v):
        try: return min(max(float(v),0.0),1.0)
        except (TypeError,ValueError): return 1.0
    def _integer(self,v):
        try: return int(v)
        except (TypeError,ValueError): return 0
