"""Deterministic ETF flow intelligence for XM GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import ETFFlowIntelligenceReport, ETFFlowObservation

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _number(value: Any) -> float:
    try: return float(value)
    except (TypeError, ValueError): return 0.0

class ETFFlowIntelligenceRuntime:
    """Transform supplied gold ETF flows into structured context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> ETFFlowIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("etf_flow_observations", ()) or ()
        rows: list[ETFFlowObservation] = []
        weighted = total_weight = total_daily = total_weekly = 0.0
        for index, item in enumerate(raw):
            daily = _number(item.get("daily_flow_usd"))
            weekly = _number(item.get("weekly_flow_usd"))
            holdings = _number(item.get("holdings_change_tonnes"))
            total_daily += daily; total_weekly += weekly
            scale = max(abs(_number(item.get("material_flow_usd", 10_000_000))), 1.0)
            composite = (daily + weekly * 0.35) / scale + holdings * 0.12
            if composite > 0.25:
                trend, effect, score = "NET_INFLOW", "BULLISH", min(1.0, composite)
            elif composite < -0.25:
                trend, effect, score = "NET_OUTFLOW", "BEARISH", max(-1.0, composite)
            else:
                trend, effect, score = "BALANCED", "NEUTRAL", 0.0
            complete = bool(item.get("fund")) and (daily != 0.0 or weekly != 0.0 or holdings != 0.0)
            confidence = 0.9 if complete else 0.25
            weighted += score * confidence; total_weight += confidence
            rows.append(ETFFlowObservation(
                observation_id=str(item.get("observation_id", f"ETF-{index+1}")),
                fund=str(item.get("fund", "GOLD_ETF")).upper(),
                daily_flow_usd=round(daily, 2), weekly_flow_usd=round(weekly, 2),
                holdings_change_tonnes=round(holdings, 4), flow_trend=trend,
                gold_effect=effect, confidence=confidence,
                explanation_en=f"{str(item.get('fund', 'Gold ETF')).upper()} daily flow is {daily:.2f} USD and weekly flow is {weekly:.2f} USD. Classification: {trend}. This is structured GOLD# context only.",
                explanation_th=f"กระแสเงินรายวันของ {str(item.get('fund', 'Gold ETF')).upper()} เท่ากับ {daily:.2f} USD และรายสัปดาห์เท่ากับ {weekly:.2f} USD จัดประเภทเป็น {trend} และใช้เป็นบริบทสำหรับ GOLD# เท่านั้น",
            ))
        aggregate = round(weighted / (total_weight or 1.0), 4) if rows else 0.0
        effect = "BULLISH" if aggregate > 0.20 else "BEARISH" if aggregate < -0.20 else "NEUTRAL"
        inflows = sum(r.flow_trend == "NET_INFLOW" for r in rows)
        outflows = sum(r.flow_trend == "NET_OUTFLOW" for r in rows)
        trend = "NET_INFLOW" if inflows > outflows else "NET_OUTFLOW" if outflows > inflows else "BALANCED"
        policy: list[str] = []
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid = [r for r in rows if r.confidence >= 0.60]
        status = "BLOCKED" if policy else "READY" if valid else "WAITING"
        reason = ",".join(policy) if policy else "etf_flow_intelligence_ready" if valid else "waiting_for_etf_flow_observations"
        return ETFFlowIntelligenceReport(
            status=status, reason=reason, observation_count=len(rows), inflow_count=inflows,
            outflow_count=outflows, neutral_count=sum(r.flow_trend == "BALANCED" for r in rows),
            aggregate_flow_trend=trend, aggregate_gold_effect=effect, aggregate_score=aggregate,
            total_daily_flow_usd=round(total_daily, 2), total_weekly_flow_usd=round(total_weekly, 2),
            confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1), 4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now + timedelta(hours=6)).isoformat(), observations=tuple(rows),
            live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> ETFFlowIntelligenceReport:
        return self.evaluate_one(record)
