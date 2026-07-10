"""Deterministic, explainable decision context for XM GOLD#.

This module creates decision intelligence only. It cannot place, modify, or
close orders and cannot enable live execution.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from .models import DecisionEvidence, DecisionIntelligenceReport

_ALLOWED_DIRECTIONS={"BUY","SELL","WAIT"}

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt=value
    elif value: dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    else: dt=datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _clamp(value: Any, low: float=0.0, high: float=1.0) -> float:
    try: number=float(value)
    except (TypeError,ValueError): number=0.0
    return max(low,min(high,number))

def _direction(value: Any) -> str:
    text=str(value or "WAIT").upper()
    if text in {"BULLISH","LONG"}: text="BUY"
    if text in {"BEARISH","SHORT"}: text="SELL"
    return text if text in _ALLOWED_DIRECTIONS else "WAIT"

class DecisionIntelligenceFoundationRuntime:
    """Resolve consensus and conflicts without authorising execution."""
    SOURCES=(
        ("market_regime",1.00),
        ("market_structure",0.90),
        ("multi_timeframe",0.85),
        ("liquidity",0.70),
        ("trading_cost",0.55),
        ("risk",1.00),
    )

    def evaluate_one(self, record: Mapping[str, Any]) -> DecisionIntelligenceReport:
        now=_utc(record.get("current_time_utc"))
        policy=[]
        if str(record.get("broker","XM")).upper()!="XM": policy.append("xm_only_required")
        if str(record.get("symbol","GOLD#")).upper()!="GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled",False)): policy.append("live_execution_disabled")

        evidence=[]; total=0.0; total_weight=0.0
        for source,base_weight in self.SOURCES:
            status=str(record.get(f"{source}_status","WAITING")).upper()
            direction=_direction(record.get(f"{source}_direction",record.get(f"{source}_bias","WAIT")))
            confidence=_clamp(record.get(f"{source}_confidence",0.0))
            weight=_clamp(record.get(f"{source}_weight",base_weight),0.0,2.0)
            sign=1.0 if direction=="BUY" else -1.0 if direction=="SELL" else 0.0
            weighted=sign*confidence*weight if status=="READY" else 0.0
            if status=="READY": total+=weighted; total_weight+=confidence*weight
            evidence.append(DecisionEvidence(source,status,direction,round(sign,4),round(confidence,4),round(weight,4),round(weighted,4),f"{source} contributes {direction} decision context with confidence {confidence:.2f}.",f"{source} ให้บริบทการตัดสินใจเป็น {direction} ด้วยความมั่นใจ {confidence:.2f}"))

        aggregate=round(total/(total_weight or 1.0),4)
        ready=[e for e in evidence if e.status=="READY"]
        buy=sum(e.direction=="BUY" for e in ready); sell=sum(e.direction=="SELL" for e in ready); neutral=sum(e.direction=="WAIT" for e in ready)
        consensus="BUY" if aggregate>=0.25 else "SELL" if aggregate<=-0.25 else "WAIT"
        support=buy if consensus=="BUY" else sell if consensus=="SELL" else neutral
        oppose=sell if consensus=="BUY" else buy if consensus=="SELL" else buy+sell
        conflict="HIGH" if buy>=2 and sell>=2 else "MODERATE" if buy and sell else "LOW"

        regime=str(record.get("market_regime","UNKNOWN")).upper()
        regime_bias=_direction(record.get("market_regime_bias",record.get("market_regime_direction","WAIT")))
        risk_allowed=bool(record.get("risk_allowed",True))
        trading_cost_allowed=bool(record.get("trading_cost_allowed",True))
        if not risk_allowed: policy.append("risk_not_allowed")
        if not trading_cost_allowed: policy.append("trading_cost_not_allowed")
        minimum_ready=int(record.get("minimum_ready_evidence",3) or 3)
        if len(ready)<minimum_ready: opportunity="INSUFFICIENT_EVIDENCE"
        elif conflict=="HIGH": opportunity="CONFLICT_REVIEW"
        elif consensus=="WAIT": opportunity="WAIT"
        elif abs(aggregate)>=0.65 and conflict=="LOW": opportunity="HIGH_QUALITY_CONTEXT"
        else: opportunity="QUALIFIED_CONTEXT"
        decision_ready=not policy and len(ready)>=minimum_ready and consensus in {"BUY","SELL"} and conflict!="HIGH"
        status="BLOCKED" if policy else "READY" if decision_ready else "WAITING"
        reason=",".join(policy) if policy else "decision_intelligence_context_ready" if decision_ready else "waiting_for_consensus_or_evidence"
        if decision_ready:
            next_en=f"Validate {consensus} entry conditions; execution remains disabled."
            next_th=f"ตรวจสอบเงื่อนไขเข้า {consensus}; ระบบส่งคำสั่งจริงยังปิดอยู่"
        elif conflict=="HIGH":
            next_en="Wait for conflict reduction and review the strongest opposing evidence."
            next_th="รอให้ความขัดแย้งลดลงและตรวจสอบหลักฐานฝั่งตรงข้ามที่มีน้ำหนักสูงสุด"
        else:
            next_en="Wait for additional structured evidence."
            next_th="รอหลักฐานแบบมีโครงสร้างเพิ่มเติม"
        confidence=round(abs(aggregate)*min(1.0,len(ready)/len(evidence)),4)
        return DecisionIntelligenceReport(status,reason,consensus,conflict,opportunity,aggregate,confidence,support,oppose,neutral,len(ready),len(evidence),regime,regime_bias,next_en,next_th,(now+timedelta(minutes=15)).isoformat(),tuple(evidence),decision_ready,False,False)

    def explain_one(self, record: Mapping[str, Any]) -> DecisionIntelligenceReport:
        return self.evaluate_one(record)
