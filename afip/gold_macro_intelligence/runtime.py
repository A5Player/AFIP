"""Deterministic macro classification for XM GOLD# research and paper runtime."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import GoldMacroIntelligenceReport, MacroIndicatorIntelligence

_CATEGORIES = {
    "CPI":"INFLATION", "CORE CPI":"INFLATION", "PPI":"INFLATION", "PCE":"INFLATION",
    "NFP":"EMPLOYMENT", "NONFARM PAYROLLS":"EMPLOYMENT", "UNEMPLOYMENT":"EMPLOYMENT", "JOBLESS CLAIMS":"EMPLOYMENT",
    "GDP":"GROWTH", "RETAIL SALES":"GROWTH",
    "PMI":"ACTIVITY", "ISM":"ACTIVITY", "MANUFACTURING PMI":"ACTIVITY", "SERVICES PMI":"ACTIVITY",
}

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt=value
    elif value: dt=datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt=datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _number(value: Any) -> float | None:
    if value is None or value == "": return None
    try: return float(value)
    except (TypeError, ValueError): return None

def _category(name: str) -> str:
    up=name.upper()
    for key, value in _CATEGORIES.items():
        if key in up: return value
    return "OTHER"

def _effect(category: str, name: str, surprise: float) -> tuple[str, float]:
    if abs(surprise) < 1e-12: return "NEUTRAL", 0.0
    up=name.upper()
    # Higher inflation often supports gold inflation demand but can lift yields; keep deterministic cautious weighting.
    if category == "INFLATION": score = 0.55 if surprise > 0 else -0.55
    elif category == "EMPLOYMENT":
        score = (0.65 if surprise > 0 else -0.65) if "UNEMPLOYMENT" in up or "JOBLESS" in up else (-0.65 if surprise > 0 else 0.65)
    elif category in {"GROWTH", "ACTIVITY"}: score = -0.50 if surprise > 0 else 0.50
    else: score = 0.20 if surprise > 0 else -0.20
    return ("BULLISH" if score > 0 else "BEARISH", score)

class GoldMacroIntelligenceRuntime:
    """Convert supplied macro releases into structured intelligence; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> GoldMacroIntelligenceReport:
        broker=str(record.get("broker", "XM")).upper(); symbol=str(record.get("symbol", "GOLD#")).upper()
        now=_utc(record.get("current_time_utc")); raw: Iterable[Mapping[str, Any]]=record.get("macro_indicators", ()) or ()
        rows=[]
        for index, item in enumerate(raw):
            name=str(item.get("indicator", "Macro Indicator")).strip() or "Macro Indicator"
            category=_category(name); actual=_number(item.get("actual")); forecast=_number(item.get("forecast")); previous=_number(item.get("previous"))
            reference=forecast if forecast is not None else previous
            surprise=round((actual-reference), 6) if actual is not None and reference is not None else 0.0
            effect, score=_effect(category, name, surprise)
            direction="ABOVE_EXPECTATION" if surprise>0 else "BELOW_EXPECTATION" if surprise<0 else "IN_LINE_OR_PENDING"
            confidence=0.85 if actual is not None and forecast is not None else 0.60 if actual is not None and previous is not None else 0.25
            rows.append(MacroIndicatorIntelligence(
                indicator_id=str(item.get("indicator_id", f"MACRO-{index+1}")), indicator=name, category=category,
                actual=actual, forecast=forecast, previous=previous, surprise=surprise, direction=direction,
                gold_effect=effect, confidence=confidence,
                explanation_en=f"{name} classified as {category}; surprise versus available reference is {surprise}. This is context only and cannot execute orders.",
                explanation_th=f"จัด {name} อยู่ในหมวด {category} โดยค่าความแตกต่างจากข้อมูลอ้างอิงเท่ากับ {surprise} ข้อมูลนี้ใช้เป็นบริบทเท่านั้นและไม่สามารถส่งคำสั่งซื้อขายได้",
            ))
        valid=[r for r in rows if r.confidence>=0.60]
        total=sum((0.55 if r.gold_effect=="BULLISH" else -0.55 if r.gold_effect=="BEARISH" else 0.0)*r.confidence for r in valid)
        denom=sum(r.confidence for r in valid) or 1.0; aggregate=round(total/denom,4) if valid else 0.0
        bias="BULLISH" if aggregate>0.10 else "BEARISH" if aggregate<-0.10 else "NEUTRAL"
        policy=[]
        if broker!="XM": policy.append("xm_only_required")
        if symbol!="GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        status="BLOCKED" if policy else "READY" if valid else "WAITING"
        reason=",".join(policy) if policy else "gold_macro_intelligence_ready" if valid else "waiting_for_macro_indicators"
        return GoldMacroIntelligenceReport(
            status=status, reason=reason, indicator_count=len(rows), inflation_count=sum(r.category=="INFLATION" for r in rows),
            employment_count=sum(r.category=="EMPLOYMENT" for r in rows), growth_count=sum(r.category=="GROWTH" for r in rows),
            activity_count=sum(r.category=="ACTIVITY" for r in rows), bullish_count=sum(r.gold_effect=="BULLISH" for r in rows),
            bearish_count=sum(r.gold_effect=="BEARISH" for r in rows), neutral_count=sum(r.gold_effect=="NEUTRAL" for r in rows),
            aggregate_bias=bias, aggregate_score=aggregate, confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1),4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now+timedelta(minutes=15)).isoformat(), indicators=tuple(rows), live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> GoldMacroIntelligenceReport: return self.evaluate_one(record)
