"""Deterministic news classification for XM GOLD# research and paper runtime."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import re
from typing import Any, Iterable, Mapping
from .models import NewsIntelligenceReport, NewsItemIntelligence

_POSITIVE = {"dovish", "rate cut", "lower yields", "safe haven", "gold demand", "weak dollar", "geopolitical risk", "inflation rises"}
_NEGATIVE = {"hawkish", "rate hike", "higher yields", "strong dollar", "gold selling", "risk-on", "inflation falls"}
_CATEGORIES = {
    "FOMC": "CENTRAL_BANK", "FED": "CENTRAL_BANK", "ECB": "CENTRAL_BANK", "BOE": "CENTRAL_BANK",
    "CPI": "INFLATION", "PCE": "INFLATION", "PPI": "INFLATION", "INFLATION": "INFLATION",
    "NFP": "EMPLOYMENT", "PAYROLL": "EMPLOYMENT", "UNEMPLOYMENT": "EMPLOYMENT",
    "YIELD": "BOND_YIELD", "TREASURY": "BOND_YIELD", "DOLLAR": "USD", "DXY": "USD",
    "WAR": "GEOPOLITICAL", "CONFLICT": "GEOPOLITICAL", "SANCTION": "GEOPOLITICAL",
    "GOLD": "GOLD_MARKET", "BULLION": "GOLD_MARKET", "ETF": "ETF_FLOW",
}
_SOURCE_RELIABILITY = {"OFFICIAL": 0.98, "CENTRAL_BANK": 0.97, "GOVERNMENT": 0.96, "REUTERS": 0.93, "BLOOMBERG": 0.92, "AP": 0.91, "EXCHANGE": 0.90, "BROKER": 0.78, "MEDIA": 0.70, "SOCIAL": 0.35, "UNKNOWN": 0.50}

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

def _fingerprint(headline: str) -> str:
    return sha256(_normalise(headline).encode("utf-8")).hexdigest()[:16]

def _category(headline: str) -> str:
    up = headline.upper()
    for key, value in _CATEGORIES.items():
        if key in up: return value
    return "GENERAL_MARKET"

def _sentiment(headline: str) -> tuple[str, float]:
    low = headline.lower()
    score = sum(1 for x in _POSITIVE if x in low) - sum(1 for x in _NEGATIVE if x in low)
    bounded = max(-1.0, min(1.0, score / 2.0))
    return ("BULLISH" if bounded > 0 else "BEARISH" if bounded < 0 else "NEUTRAL", bounded)

def _gold_relevance(category: str, headline: str) -> str:
    if category in {"CENTRAL_BANK", "INFLATION", "EMPLOYMENT", "BOND_YIELD", "USD", "GEOPOLITICAL", "GOLD_MARKET", "ETF_FLOW"}: return "HIGH"
    return "MEDIUM" if "gold" in headline.lower() else "LOW"

def _reliability(source: str, supplied: Any) -> float:
    if supplied is not None:
        try: return max(0.0, min(1.0, float(supplied)))
        except (TypeError, ValueError): pass
    up = source.upper()
    for key, value in _SOURCE_RELIABILITY.items():
        if key in up: return value
    return _SOURCE_RELIABILITY["UNKNOWN"]

class NewsIntelligenceRuntime:
    """Convert supplied news into structured intelligence; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> NewsIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("news_items", ()) or ()
        seen: dict[str, str] = {}
        items: list[NewsItemIntelligence] = []
        for index, item in enumerate(raw):
            headline = str(item.get("headline", "Market update")).strip() or "Market update"
            source = str(item.get("source", "UNKNOWN")).strip() or "UNKNOWN"
            news_id = str(item.get("news_id", f"NEWS-{index+1}"))
            fp = _fingerprint(headline)
            duplicate_of = seen.get(fp, "")
            duplicate = bool(duplicate_of)
            if not duplicate: seen[fp] = news_id
            category = _category(headline)
            sentiment, sentiment_score = _sentiment(headline)
            reliability = _reliability(source, item.get("reliability_score"))
            relevance = _gold_relevance(category, headline)
            structured_signal = "IGNORE_DUPLICATE" if duplicate else ("REVIEW" if reliability < 0.60 else "STRUCTURED_INTELLIGENCE_READY")
            items.append(NewsItemIntelligence(
                news_id=news_id, headline=headline, source=source,
                published_time_utc=_utc(item.get("published_time_utc") or now).isoformat(),
                category=category, sentiment=sentiment, sentiment_score=round(sentiment_score, 4),
                reliability_score=round(reliability, 4), gold_relevance=relevance,
                duplicate=duplicate, duplicate_of=duplicate_of, structured_signal=structured_signal,
                explanation_en=("Duplicate headline excluded from aggregate intelligence." if duplicate else "News classified by category, sentiment, reliability, and gold relevance; it cannot execute orders directly."),
                explanation_th=("ตัดข่าวซ้ำออกจากการรวมผลข้อมูลอัจฉริยะ" if duplicate else "จัดหมวดหมู่ข่าวตามประเภท อารมณ์ตลาด ความน่าเชื่อถือ และความเกี่ยวข้องกับทองคำ โดยข่าวไม่สามารถส่งคำสั่งซื้อขายโดยตรง"),
            ))
        unique = [x for x in items if not x.duplicate]
        weighted = sum(x.sentiment_score * x.reliability_score for x in unique)
        denominator = sum(x.reliability_score for x in unique) or 1.0
        score = round(weighted / denominator, 4) if unique else 0.0
        aggregate = "BULLISH" if score > 0.10 else "BEARISH" if score < -0.10 else "NEUTRAL"
        policy_errors=[]
        if broker != "XM": policy_errors.append("xm_only_required")
        if symbol != "GOLD#": policy_errors.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy_errors.append("live_execution_disabled")
        status = "BLOCKED" if policy_errors else ("READY" if unique else "WAITING")
        reason = ",".join(policy_errors) if policy_errors else ("news_intelligence_ready" if unique else "waiting_for_news_items")
        return NewsIntelligenceReport(
            status=status, reason=reason, item_count=len(items), unique_item_count=len(unique),
            duplicate_count=sum(x.duplicate for x in items),
            high_reliability_count=sum((not x.duplicate) and x.reliability_score >= 0.80 for x in items),
            gold_relevant_count=sum((not x.duplicate) and x.gold_relevance == "HIGH" for x in items),
            aggregate_sentiment=aggregate, aggregate_sentiment_score=score,
            intelligence_ready=not policy_errors and bool(unique), execution_allowed=False,
            next_review_time_utc=(now + timedelta(minutes=5)).isoformat(), items=tuple(items), live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any]) -> NewsIntelligenceReport:
        return self.evaluate_one(record)
