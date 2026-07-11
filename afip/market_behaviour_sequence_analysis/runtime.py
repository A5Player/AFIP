from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

@dataclass(frozen=True)
class MarketBehaviourSequenceReport:
    report_id: str; status: str; reason: str; milestone: str; pack: str
    sequence_start_timestamp: int; sequence_end_timestamp: int
    state_count: int; transition_count: int; unique_state_count: int
    regime_change_count: int; behaviour_change_count: int; direction_change_count: int
    persistence_ratio: float; dominant_market_regime: str; dominant_behaviour_state: str
    transition_signature: tuple[str, ...]; source_state_ids: tuple[str, ...]
    schema_version: str; data_quality_certified: bool; future_safe: bool
    chronology_valid: bool; market_regime_before_behaviour: bool
    immutable_record: bool; research_only: bool
    automatic_parameter_update_allowed: bool; trading_logic_change_allowed: bool
    production_knowledge_allowed: bool; production_certification_granted: bool
    block_reasons: tuple[str, ...]; explanation_reason_en: str; explanation_reason_th: str
    broker: str = "XM"; symbol: str = "GOLD#"; base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"; direct_execution: bool = False
    live_execution_enabled: bool = False; order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False; order_transmission_attempted: bool = False
    position_modification_attempted: bool = False
    def as_dict(self) -> dict[str, Any]: return asdict(self)

class MarketBehaviourSequenceAnalysisRuntime:
    def evaluate_many(self, states: Iterable[Mapping[str, Any]], *, analysis_timestamp: int) -> MarketBehaviourSequenceReport:
        rows = [dict(x) for x in states]
        ids = tuple(str(x.get("state_id", "")).strip().upper() for x in rows)
        ts = tuple(self._int(x.get("normalized_timestamp", 0)) for x in rows)
        regimes = tuple(str(x.get("market_regime", "")).strip().upper() for x in rows)
        behaviours = tuple(str(x.get("behaviour_state", "")).strip().upper() for x in rows)
        directions = tuple(str(x.get("direction", "FLAT")).strip().upper() for x in rows)
        analysis_ts = self._int(analysis_timestamp)
        source_ready = bool(rows) and all(str(x.get("status", "")).upper()=="READY" and str(x.get("schema_version", "")).upper()=="AFIP_MARKET_BEHAVIOUR_STATE_V1" and i.startswith("PBNS-") for x,i in zip(rows,ids))
        unique = len(ids)==len(set(ids))
        chronology = bool(ts) and all(t>0 for t in ts) and tuple(sorted(ts))==ts and analysis_ts>=ts[-1]
        quality = bool(rows) and all(bool(x.get("data_quality_certified", False)) for x in rows)
        future_safe = bool(rows) and all(bool(x.get("future_safe", False)) and not bool(x.get("future_leakage_detected", False)) for x in rows)
        regime_first = bool(rows) and all(bool(x.get("market_regime_before_behaviour", False)) for x in rows)
        policy = bool(rows) and all(str(x.get("broker","XM")).upper()=="XM" and str(x.get("symbol","GOLD#")).upper()=="GOLD#" and abs(self._num(x.get("base_lot_per_unit",0.01))-0.01)<=1e-12 and str(x.get("execution_status","LOCKED_SIMULATION_ONLY")).upper()=="LOCKED_SIMULATION_ONLY" and str(x.get("order_status","NO_ORDER_SENT")).upper()=="NO_ORDER_SENT" and not bool(x.get("direct_execution",False)) and not bool(x.get("live_execution_enabled",False)) and not bool(x.get("automatic_parameter_update_allowed",False)) and not bool(x.get("trading_logic_change_allowed",False)) and not bool(x.get("production_knowledge_allowed",False)) for x in rows)
        checks=((not source_ready,"pack_2_state_lineage_invalid"),(not unique,"duplicate_state_id_detected"),(len(rows)<3,"insufficient_sequence_length"),(not chronology,"sequence_chronology_invalid"),(not quality,"data_quality_not_certified"),(not future_safe,"future_leakage_detected"),(not regime_first,"market_regime_not_evaluated_before_behaviour"),(not policy,"feature_freeze_or_execution_policy_violation"))
        blocked=tuple(sorted({r for c,r in checks if c})); ready=not blocked
        transitions=tuple(f"{regimes[i]}:{behaviours[i]}:{directions[i]}->{regimes[i+1]}:{behaviours[i+1]}:{directions[i+1]}" for i in range(max(0,len(rows)-1)))
        rc=sum(regimes[i]!=regimes[i-1] for i in range(1,len(regimes))); bc=sum(behaviours[i]!=behaviours[i-1] for i in range(1,len(behaviours))); dc=sum(directions[i]!=directions[i-1] for i in range(1,len(directions)))
        persistence=round(sum(behaviours[i]==behaviours[i-1] for i in range(1,len(behaviours)))/max(1,len(behaviours)-1),6) if rows else 0.0
        ident={"ids":ids,"ts":ts,"analysis":analysis_ts,"transitions":transitions,"blocked":blocked}
        report_id="PBSQ-"+sha256(json.dumps(ident,sort_keys=True,separators=(",",":")).encode()).hexdigest()[:16].upper()
        en="Certified Pack 2 states were analyzed into an immutable deterministic market-behaviour sequence report." if ready else "Sequence analysis was blocked by lineage, duplication, coverage, chronology, data, or frozen-policy validation."
        th="State จาก Pack 2 ที่ผ่านการรับรองถูกวิเคราะห์เป็นรายงานลำดับพฤติกรรมตลาดแบบ immutable และ deterministic" if ready else "การวิเคราะห์ลำดับพฤติกรรมตลาดถูกระงับจากการตรวจ lineage ข้อมูลซ้ำ ความครอบคลุม ลำดับเวลา ข้อมูล หรือนโยบายล็อก"
        return MarketBehaviourSequenceReport(report_id,"READY" if ready else "BLOCKED","MARKET_BEHAVIOUR_SEQUENCE_ANALYZED" if ready else "MARKET_BEHAVIOUR_SEQUENCE_ANALYSIS_BLOCKED","P","3",ts[0] if ts else 0,ts[-1] if ts else 0,len(rows),max(0,len(rows)-1),len(set(ids)),rc,bc,dc,persistence,self._dominant(regimes),self._dominant(behaviours),transitions,ids,"AFIP_MARKET_BEHAVIOUR_SEQUENCE_V1",quality,future_safe,chronology,regime_first,True,True,False,False,False,False,blocked,en,th)
    @staticmethod
    def _dominant(values: tuple[str,...]) -> str:
        if not values: return "UNAVAILABLE"
        counts={v:values.count(v) for v in set(values)}
        return sorted(counts,key=lambda v:(-counts[v],v))[0]
    @staticmethod
    def _int(v: Any) -> int:
        try: return int(v)
        except (TypeError,ValueError): return 0
    @staticmethod
    def _num(v: Any) -> float:
        try: return float(v)
        except (TypeError,ValueError): return float("nan")
