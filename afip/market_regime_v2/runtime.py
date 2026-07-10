"""Deterministic Market Regime V2 aggregation for XM GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from .models import MarketRegimeComponent, MarketRegimeV2Report

def _utc(v: Any) -> datetime:
    if isinstance(v, datetime): dt=v
    elif v: dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    else: dt=datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _effect(value: Any) -> str:
    text=str(value or "NEUTRAL").upper()
    return text if text in {"BULLISH","BEARISH","NEUTRAL"} else "NEUTRAL"

def _score(effect: str, raw: Any) -> float:
    try: s=float(raw)
    except (TypeError,ValueError): s=0.0
    if s == 0.0: s=1.0 if effect=="BULLISH" else -1.0 if effect=="BEARISH" else 0.0
    return max(-1.0,min(1.0,s))

class MarketRegimeV2Runtime:
    """Aggregate structured intelligence only; never place or modify orders."""
    COMPONENTS=(
        ("economic_calendar","economic_calendar_status","economic_calendar_effect","economic_calendar_score"),
        ("news","news_status","news_effect","news_score"),
        ("gold_macro","gold_macro_status","gold_macro_effect","gold_macro_score"),
        ("central_bank","central_bank_status","central_bank_effect","central_bank_score"),
        ("cot","cot_status","cot_effect","cot_score"),
        ("open_interest","open_interest_status","open_interest_effect","open_interest_score"),
        ("etf_flow","etf_flow_status","etf_flow_effect","etf_flow_score"),
        ("usd_index","usd_index_status","usd_index_effect","usd_index_score"),
        ("bond_yield","bond_yield_status","bond_yield_effect","bond_yield_score"),
    )
    def evaluate_one(self, record: Mapping[str, Any]) -> MarketRegimeV2Report:
        now=_utc(record.get("current_time_utc"))
        policy=[]
        if str(record.get("broker","XM")).upper()!="XM": policy.append("xm_only_required")
        if str(record.get("symbol","GOLD#")).upper()!="GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled",False)): policy.append("live_execution_disabled")
        rows=[]; weighted=0.0; total_weight=0.0
        for name,status_key,effect_key,score_key in self.COMPONENTS:
            status=str(record.get(status_key,"WAITING")).upper()
            effect=_effect(record.get(effect_key))
            confidence=max(0.0,min(1.0,float(record.get(f"{name}_confidence", 0.8 if status=="READY" else 0.0) or 0.0)))
            score=_score(effect,record.get(score_key,0.0))
            if status=="READY" and confidence>0:
                weighted+=score*confidence; total_weight+=confidence
            rows.append(MarketRegimeComponent(name,status,effect,round(score,4),round(confidence,4),f"{name} contributes {effect} structured context with score {score:.2f}.",f"{name} ให้บริบทแบบมีโครงสร้างเป็น {effect} ด้วยคะแนน {score:.2f}"))
        agg=round(weighted/(total_weight or 1.0),4)
        ready=sum(r.status=="READY" for r in rows)
        bullish=sum(r.status=="READY" and r.effect=="BULLISH" for r in rows); bearish=sum(r.status=="READY" and r.effect=="BEARISH" for r in rows)
        bias="BULLISH" if agg>0.20 else "BEARISH" if agg<-0.20 else "NEUTRAL"
        alignment="ALIGNED" if max(bullish,bearish)>=max(3,ready-1) and ready>0 else "MIXED" if bullish and bearish else "NEUTRAL"
        if ready<3: regime="INSUFFICIENT_DATA"
        elif alignment=="MIXED": regime="TRANSITION"
        elif abs(agg)>=0.60: regime="DIRECTIONAL_STRONG"
        elif abs(agg)>=0.25: regime="DIRECTIONAL_MODERATE"
        else: regime="BALANCED"
        risk="HIGH" if alignment=="MIXED" or ready<5 else "MODERATE" if abs(agg)<0.60 else "CONTROLLED"
        status="BLOCKED" if policy else "READY" if ready>=5 else "WAITING"
        reason=",".join(policy) if policy else "market_regime_v2_ready" if status=="READY" else "waiting_for_minimum_structured_intelligence"
        confidence=round(total_weight/len(rows),4)
        return MarketRegimeV2Report(status,reason,regime,bias,risk,agg,confidence,ready,len(rows),alignment,status=="READY",False,(now+timedelta(minutes=30)).isoformat(),tuple(rows),False)
    def explain_one(self, record: Mapping[str, Any]) -> MarketRegimeV2Report:
        return self.evaluate_one(record)
