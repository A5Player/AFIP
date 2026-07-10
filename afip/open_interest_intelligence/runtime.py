"""Deterministic open-interest intelligence for XM GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import OpenInterestIntelligenceReport, OpenInterestObservation

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _number(value: Any) -> float:
    try: return float(value)
    except (TypeError, ValueError): return 0.0

class OpenInterestIntelligenceRuntime:
    """Transform supplied futures OI observations into context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> OpenInterestIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("open_interest_observations", ()) or ()
        rows: list[OpenInterestObservation] = []
        weighted = 0.0
        total_weight = 0.0
        for index, item in enumerate(raw):
            current = max(0, int(_number(item.get("open_interest"))))
            previous = max(0, int(_number(item.get("previous_open_interest"))))
            price_change = _number(item.get("price_change_pct"))
            change = current - previous
            change_pct = (change / previous * 100.0) if previous else 0.0
            threshold = max(0.5, abs(_number(item.get("stability_threshold_pct", 1.0))))
            if change_pct > threshold:
                participation = "RISING"
            elif change_pct < -threshold:
                participation = "FALLING"
            else:
                participation = "STABLE"
            if participation == "RISING" and price_change > 0:
                interpretation, effect, score = "LONG_PARTICIPATION_EXPANDING", "BULLISH", 1.0
            elif participation == "RISING" and price_change < 0:
                interpretation, effect, score = "SHORT_PARTICIPATION_EXPANDING", "BEARISH", -1.0
            elif participation == "FALLING" and price_change > 0:
                interpretation, effect, score = "SHORT_COVERING_OR_REDUCED_PARTICIPATION", "NEUTRAL", 0.15
            elif participation == "FALLING" and price_change < 0:
                interpretation, effect, score = "LONG_LIQUIDATION_OR_REDUCED_PARTICIPATION", "NEUTRAL", -0.15
            else:
                interpretation, effect, score = "PARTICIPATION_STABLE", "NEUTRAL", 0.0
            complete = current > 0 and previous > 0
            confidence = 0.88 if complete else 0.25
            weighted += score * confidence
            total_weight += confidence
            rows.append(OpenInterestObservation(
                observation_id=str(item.get("observation_id", f"OI-{index+1}")),
                market=str(item.get("market", "COMEX_GOLD")).upper(),
                price_change_pct=round(price_change, 4), open_interest=current,
                previous_open_interest=previous, open_interest_change=change,
                open_interest_change_pct=round(change_pct, 4), participation_trend=participation,
                market_interpretation=interpretation, gold_effect=effect, confidence=confidence,
                explanation_en=f"Open interest changed {change_pct:.2f}% while price changed {price_change:.2f}%. Classification: {interpretation}. This is structured GOLD# context only.",
                explanation_th=f"Open Interest เปลี่ยนแปลง {change_pct:.2f}% ขณะที่ราคาเปลี่ยนแปลง {price_change:.2f}% จัดประเภทเป็น {interpretation} และใช้เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# เท่านั้น",
            ))
        aggregate = round(weighted / (total_weight or 1.0), 4) if rows else 0.0
        effect = "BULLISH" if aggregate > 0.20 else "BEARISH" if aggregate < -0.20 else "NEUTRAL"
        rising = sum(r.participation_trend == "RISING" for r in rows)
        falling = sum(r.participation_trend == "FALLING" for r in rows)
        participation = "EXPANDING" if rising > falling else "CONTRACTING" if falling > rising else "STABLE"
        policy: list[str] = []
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid = [r for r in rows if r.confidence >= 0.60]
        status = "BLOCKED" if policy else "READY" if valid else "WAITING"
        reason = ",".join(policy) if policy else "open_interest_intelligence_ready" if valid else "waiting_for_open_interest_observations"
        return OpenInterestIntelligenceReport(
            status=status, reason=reason, observation_count=len(rows), rising_count=rising,
            falling_count=falling, stable_count=sum(r.participation_trend == "STABLE" for r in rows),
            aggregate_participation=participation, aggregate_gold_effect=effect,
            aggregate_score=aggregate, confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1), 4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now + timedelta(hours=4)).isoformat(), observations=tuple(rows),
            live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> OpenInterestIntelligenceReport:
        return self.evaluate_one(record)
