"""Structured economic calendar intelligence for XM GOLD# simulation and demo runtime."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import EconomicCalendarReport, EconomicEventIntelligence

_GOLD_CATEGORIES = {
    "CPI": "INFLATION", "PPI": "INFLATION", "NFP": "EMPLOYMENT",
    "NONFARM PAYROLLS": "EMPLOYMENT", "FOMC": "CENTRAL_BANK",
    "FEDERAL RESERVE": "CENTRAL_BANK", "GDP": "GROWTH",
    "PMI": "ACTIVITY", "ISM": "ACTIVITY", "PCE": "INFLATION",
    "UNEMPLOYMENT": "EMPLOYMENT", "RETAIL SALES": "CONSUMPTION",
}

def _utc(value: Any, default: datetime | None = None) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif value:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else:
        dt = default or datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _category(title: str) -> str:
    up = title.upper()
    for key, value in _GOLD_CATEGORIES.items():
        if key in up:
            return value
    return "GENERAL_ECONOMIC"

def _gold_relevance(title: str, currency: str, impact: str) -> str:
    category = _category(title)
    if currency.upper() == "USD" and (impact == "HIGH" or category != "GENERAL_ECONOMIC"):
        return "HIGH"
    if currency.upper() == "USD" or category in {"CENTRAL_BANK", "INFLATION"}:
        return "MEDIUM"
    return "LOW"

class EconomicCalendarIntelligenceRuntime:
    """Convert supplied calendar records into explainable structured intelligence.

    This runtime never fetches news and never places orders. Providers can be wired
    later, while tests and replay remain deterministic through supplied event data.
    """
    def evaluate_one(self, record: Mapping[str, Any]) -> EconomicCalendarReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        before = max(0, int(record.get("economic_event_block_minutes_before", 30)))
        after = max(0, int(record.get("economic_event_block_minutes_after", 15)))
        raw_events: Iterable[Mapping[str, Any]] = record.get("economic_events", ()) or ()
        events: list[EconomicEventIntelligence] = []
        for index, item in enumerate(raw_events):
            scheduled = _utc(item.get("scheduled_time_utc"), now)
            minutes = int((scheduled - now).total_seconds() // 60)
            impact = str(item.get("impact", "LOW")).upper()
            if impact not in {"LOW", "MEDIUM", "HIGH"}: impact = "LOW"
            title = str(item.get("title", "Economic Event")).strip() or "Economic Event"
            currency = str(item.get("currency", "USD")).upper()
            relevance = _gold_relevance(title, currency, impact)
            in_window = -after <= minutes <= before
            blocks = impact == "HIGH" and relevance == "HIGH" and in_window
            window = "ACTIVE" if in_window else ("UPCOMING" if minutes > before else "PASSED")
            events.append(EconomicEventIntelligence(
                event_id=str(item.get("event_id", f"ECON-{index+1}")), title=title,
                country=str(item.get("country", "US")).upper(), currency=currency,
                scheduled_time_utc=scheduled.isoformat(), impact=impact,
                gold_relevance=relevance, event_category=_category(title),
                minutes_until_event=minutes, event_window=window,
                trading_allowed=not blocks,
                trading_block_reason="high_impact_gold_event_window" if blocks else "economic_calendar_pass",
                explanation_en=("Trading is paused around a high-impact USD event relevant to gold." if blocks else "Event is classified and visible; no calendar block is active."),
                explanation_th=("ระงับการเทรดชั่วคราวในช่วงข่าว USD ผลกระทบสูงที่เกี่ยวข้องกับทองคำ" if blocks else "จัดหมวดหมู่และแสดงเหตุการณ์แล้ว โดยยังไม่มีการบล็อกจากปฏิทินข่าว"),
            ))
        events.sort(key=lambda e: e.scheduled_time_utc)
        policy_errors=[]
        if broker != "XM": policy_errors.append("xm_only_required")
        if symbol != "GOLD#": policy_errors.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy_errors.append("live_execution_disabled")
        active_blocks=[e for e in events if not e.trading_allowed]
        trading_allowed=not policy_errors and not active_blocks
        if policy_errors: block_reason=",".join(policy_errors)
        elif active_blocks: block_reason=active_blocks[0].trading_block_reason
        else: block_reason="economic_calendar_pass"
        future=[e for e in events if e.minutes_until_event >= 0]
        next_time=future[0].scheduled_time_utc if future else "NONE"
        next_review=(now + timedelta(minutes=5)).isoformat()
        status="BLOCKED" if policy_errors else ("CAUTION" if active_blocks else "READY")
        return EconomicCalendarReport(
            status=status, reason=block_reason, current_time_utc=now.isoformat(),
            event_count=len(events), high_impact_count=sum(e.impact=="HIGH" for e in events),
            gold_relevant_count=sum(e.gold_relevance=="HIGH" for e in events),
            trading_allowed=trading_allowed, trading_block_reason=block_reason,
            next_event_time_utc=next_time, next_review_time_utc=next_review,
            events=tuple(events), live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any]) -> EconomicCalendarReport:
        return self.evaluate_one(record)
