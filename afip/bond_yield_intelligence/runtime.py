"""Deterministic US bond-yield intelligence for XM GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import BondYieldIntelligenceReport, BondYieldObservation

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _number(value: Any) -> float:
    try: return float(value)
    except (TypeError, ValueError): return 0.0

def _trend(current: float, previous: float, threshold: float) -> str:
    change = current - previous
    return "RISING" if change > threshold else "FALLING" if change < -threshold else "STABLE"

class BondYieldIntelligenceRuntime:
    """Transform supplied US yield observations into structured context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> BondYieldIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("bond_yield_observations", ()) or ()
        rows: list[BondYieldObservation] = []
        weighted = total_weight = 0.0
        for index, item in enumerate(raw):
            us2y = _number(item.get("us2y_yield")); prev2 = _number(item.get("previous_us2y_yield"))
            us10y = _number(item.get("us10y_yield")); prev10 = _number(item.get("previous_us10y_yield"))
            real = _number(item.get("real_yield")); prev_real = _number(item.get("previous_real_yield"))
            threshold = abs(_number(item.get("material_change_pct_points", 0.03))) or 0.03
            nominal_change = ((us2y-prev2)+(us10y-prev10))/2.0
            nominal_trend = "RISING" if nominal_change > threshold else "FALLING" if nominal_change < -threshold else "STABLE"
            real_trend = _trend(real, prev_real, threshold)
            spread = (us10y-us2y)*100.0
            curve = "INVERTED" if spread < -5.0 else "STEEP" if spread > 75.0 else "FLAT" if abs(spread) <= 15.0 else "NORMAL"
            score = 0.0
            if nominal_trend == "RISING": score -= 0.35
            elif nominal_trend == "FALLING": score += 0.35
            if real_trend == "RISING": score -= 0.65
            elif real_trend == "FALLING": score += 0.65
            score = max(-1.0, min(1.0, score))
            effect = "BULLISH" if score > 0.20 else "BEARISH" if score < -0.20 else "NEUTRAL"
            complete = any(v != 0.0 for v in (us2y, us10y, real, prev2, prev10, prev_real))
            confidence = 0.92 if complete else 0.25
            weighted += score * confidence; total_weight += confidence
            rows.append(BondYieldObservation(
                observation_id=str(item.get("observation_id", f"YIELD-{index+1}")),
                us2y_yield=round(us2y,6), us10y_yield=round(us10y,6), real_yield=round(real,6),
                previous_us2y_yield=round(prev2,6), previous_us10y_yield=round(prev10,6), previous_real_yield=round(prev_real,6),
                curve_spread_bps=round(spread,2), curve_shape=curve, nominal_yield_trend=nominal_trend,
                real_yield_trend=real_trend, gold_effect=effect, confidence=confidence,
                explanation_en=f"US2Y={us2y:.3f}%, US10Y={us10y:.3f}%, real yield={real:.3f}%. Nominal trend={nominal_trend}, real-yield trend={real_trend}, curve={curve}. This is structured GOLD# context only.",
                explanation_th=f"US2Y={us2y:.3f}% US10Y={us10y:.3f}% และ real yield={real:.3f}% แนวโน้มผลตอบแทนทั่วไป={nominal_trend} แนวโน้ม real yield={real_trend} และเส้นอัตราผลตอบแทน={curve} ใช้เป็นบริบทสำหรับ GOLD# เท่านั้น",
            ))
        aggregate = round(weighted/(total_weight or 1.0),4) if rows else 0.0
        effect = "BULLISH" if aggregate > 0.20 else "BEARISH" if aggregate < -0.20 else "NEUTRAL"
        def majority(values: list[str], rising: str, falling: str, stable: str) -> str:
            return rising if values.count(rising)>values.count(falling) and values.count(rising)>values.count(stable) else falling if values.count(falling)>values.count(rising) and values.count(falling)>values.count(stable) else stable
        nominal = majority([r.nominal_yield_trend for r in rows], "RISING","FALLING","STABLE")
        real_t = majority([r.real_yield_trend for r in rows], "RISING","FALLING","STABLE")
        shapes=[r.curve_shape for r in rows]; curve=max(set(shapes), key=shapes.count) if shapes else "UNAVAILABLE"
        policy=[]
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid=[r for r in rows if r.confidence>=0.60]
        status="BLOCKED" if policy else "READY" if valid else "WAITING"
        reason=",".join(policy) if policy else "bond_yield_intelligence_ready" if valid else "waiting_for_bond_yield_observations"
        return BondYieldIntelligenceReport(status,reason,len(rows),sum(r.nominal_yield_trend=="RISING" for r in rows),sum(r.nominal_yield_trend=="FALLING" for r in rows),sum(r.real_yield_trend=="RISING" for r in rows),sum(r.real_yield_trend=="FALLING" for r in rows),sum(r.curve_shape=="INVERTED" for r in rows),nominal,real_t,curve,effect,aggregate,round(sum(r.confidence for r in valid)/(len(valid) or 1),4),not policy and bool(valid),False,(now+timedelta(hours=1)).isoformat(),tuple(rows),False)
    def explain_one(self, record: Mapping[str, Any]) -> BondYieldIntelligenceReport:
        return self.evaluate_one(record)
