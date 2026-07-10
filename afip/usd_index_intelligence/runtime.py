"""Deterministic USD index intelligence for XM GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import USDIndexIntelligenceReport, USDIndexObservation

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _number(value: Any) -> float:
    try: return float(value)
    except (TypeError, ValueError): return 0.0

class USDIndexIntelligenceRuntime:
    """Transform supplied DXY observations into structured context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> USDIndexIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("usd_index_observations", ()) or ()
        rows: list[USDIndexObservation] = []
        weighted = total_weight = 0.0
        for index, item in enumerate(raw):
            current = _number(item.get("current_value"))
            previous = _number(item.get("previous_value"))
            change = _number(item.get("change_pct"))
            if change == 0.0 and previous != 0.0:
                change = ((current - previous) / abs(previous)) * 100.0
            threshold = abs(_number(item.get("material_change_pct", 0.15))) or 0.15
            if change > threshold:
                trend, effect, score = "RISING", "BEARISH", -min(1.0, abs(change) / max(threshold * 4.0, 0.01))
            elif change < -threshold:
                trend, effect, score = "FALLING", "BULLISH", min(1.0, abs(change) / max(threshold * 4.0, 0.01))
            else:
                trend, effect, score = "STABLE", "NEUTRAL", 0.0
            gold_change = _number(item.get("gold_change_pct"))
            if change > threshold and gold_change > threshold:
                divergence = "POSITIVE_DIVERGENCE"
            elif change < -threshold and gold_change < -threshold:
                divergence = "NEGATIVE_DIVERGENCE"
            else:
                divergence = "NONE"
            correlation = "INVERSE" if change * gold_change < 0 else "DIRECT" if change * gold_change > 0 else "UNCONFIRMED"
            complete = bool(item.get("index_name", "DXY")) and (current != 0.0 or previous != 0.0 or change != 0.0)
            confidence = 0.9 if complete else 0.25
            weighted += score * confidence; total_weight += confidence
            rows.append(USDIndexObservation(
                observation_id=str(item.get("observation_id", f"DXY-{index+1}")),
                index_name=str(item.get("index_name", "DXY")).upper(),
                current_value=round(current, 6), previous_value=round(previous, 6),
                change_pct=round(change, 4), trend=trend, gold_correlation=correlation,
                divergence=divergence, gold_effect=effect, confidence=confidence,
                explanation_en=f"USD index change is {change:.4f}% and is classified as {trend}. Gold relationship: {correlation}; divergence: {divergence}. This is structured GOLD# context only.",
                explanation_th=f"ดัชนีดอลลาร์เปลี่ยนแปลง {change:.4f}% และจัดเป็น {trend} ความสัมพันธ์กับทองคือ {correlation} และ divergence คือ {divergence} ใช้เป็นบริบทสำหรับ GOLD# เท่านั้น",
            ))
        aggregate = round(weighted / (total_weight or 1.0), 4) if rows else 0.0
        effect = "BULLISH" if aggregate > 0.20 else "BEARISH" if aggregate < -0.20 else "NEUTRAL"
        rising = sum(r.trend == "RISING" for r in rows)
        falling = sum(r.trend == "FALLING" for r in rows)
        trend = "RISING" if rising > falling else "FALLING" if falling > rising else "STABLE"
        policy: list[str] = []
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid = [r for r in rows if r.confidence >= 0.60]
        status = "BLOCKED" if policy else "READY" if valid else "WAITING"
        reason = ",".join(policy) if policy else "usd_index_intelligence_ready" if valid else "waiting_for_usd_index_observations"
        return USDIndexIntelligenceReport(
            status=status, reason=reason, observation_count=len(rows), rising_count=rising,
            falling_count=falling, stable_count=sum(r.trend == "STABLE" for r in rows),
            divergence_count=sum(r.divergence != "NONE" for r in rows), aggregate_usd_trend=trend,
            aggregate_gold_effect=effect, aggregate_score=aggregate,
            confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1), 4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now + timedelta(hours=1)).isoformat(), observations=tuple(rows),
            live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> USDIndexIntelligenceReport:
        return self.evaluate_one(record)
