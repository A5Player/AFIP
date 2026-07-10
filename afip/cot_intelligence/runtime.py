"""Deterministic Commitments of Traders intelligence for GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import COTIntelligenceReport, COTObservation

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _integer(value: Any) -> int:
    try: return int(float(value))
    except (TypeError, ValueError): return 0

class COTIntelligenceRuntime:
    """Convert supplied COT observations into positioning context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> COTIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("cot_observations", ()) or ()
        rows: list[COTObservation] = []
        weighted = 0.0
        total_weight = 0.0
        for index, item in enumerate(raw):
            cl = _integer(item.get("commercial_long")); cs = _integer(item.get("commercial_short"))
            nl = _integer(item.get("noncommercial_long")); ns = _integer(item.get("noncommercial_short"))
            previous_net = _integer(item.get("previous_noncommercial_net", nl - ns))
            commercial_net = cl - cs
            noncommercial_net = nl - ns
            change = noncommercial_net - previous_net
            threshold = max(500, int(max(abs(noncommercial_net), 1) * 0.03))
            if change > threshold:
                trend, effect, score = "ACCUMULATING_LONG", "BULLISH", 1.0
            elif change < -threshold:
                trend, effect, score = "REDUCING_LONG_OR_ADDING_SHORT", "BEARISH", -1.0
            else:
                trend, effect, score = "STABLE", "NEUTRAL", 0.0
            complete = any((cl, cs, nl, ns))
            confidence = 0.88 if complete else 0.25
            weighted += score * confidence
            total_weight += confidence
            rows.append(COTObservation(
                report_id=str(item.get("report_id", f"COT-{index+1}")),
                market=str(item.get("market", "COMEX_GOLD")).upper(),
                commercial_long=cl, commercial_short=cs,
                noncommercial_long=nl, noncommercial_short=ns,
                commercial_net=commercial_net, noncommercial_net=noncommercial_net,
                noncommercial_net_change=change, positioning_trend=trend,
                gold_effect=effect, confidence=confidence,
                explanation_en=f"Non-commercial net positioning changed by {change}. The observation is classified as {trend} and supplies structured GOLD# context only.",
                explanation_th=f"สถานะสุทธิของกลุ่ม Non-Commercial เปลี่ยนแปลง {change} สัญญา จัดประเภทเป็น {trend} และใช้เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# เท่านั้น",
            ))
        aggregate = round(weighted / (total_weight or 1.0), 4) if rows else 0.0
        bias = "BULLISH" if aggregate > 0.15 else "BEARISH" if aggregate < -0.15 else "NEUTRAL"
        policy: list[str] = []
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid = [row for row in rows if row.confidence >= 0.60]
        status = "BLOCKED" if policy else "READY" if valid else "WAITING"
        reason = ",".join(policy) if policy else "cot_intelligence_ready" if valid else "waiting_for_cot_observations"
        return COTIntelligenceReport(
            status=status, reason=reason, observation_count=len(rows),
            bullish_count=sum(r.gold_effect == "BULLISH" for r in rows),
            bearish_count=sum(r.gold_effect == "BEARISH" for r in rows),
            neutral_count=sum(r.gold_effect == "NEUTRAL" for r in rows),
            aggregate_positioning_bias=bias, aggregate_score=aggregate,
            confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1), 4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now + timedelta(hours=24)).isoformat(),
            observations=tuple(rows), live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> COTIntelligenceReport:
        return self.evaluate_one(record)
