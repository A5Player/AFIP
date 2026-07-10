"""Deterministic central-bank policy and speech classification for GOLD#."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from .models import CentralBankIntelligenceReport, CentralBankObservation

_SUPPORTED = {"FOMC", "FED", "ECB", "BOE", "BOJ", "PBOC"}
_HAWKISH = ("hawkish", "higher for longer", "raise rates", "rate hike", "inflation remains high", "tightening", "restrictive")
_DOVISH = ("dovish", "rate cut", "lower rates", "easing", "accommodative", "growth risk", "disinflation")

def _utc(value: Any) -> datetime:
    if isinstance(value, datetime): dt = value
    elif value: dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    else: dt = datetime.now(timezone.utc)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

def _institution(value: Any) -> str:
    text = str(value or "FOMC").upper().strip()
    return "FOMC" if text == "FED" else text

def _bias(item: Mapping[str, Any]) -> tuple[str, float]:
    explicit = str(item.get("policy_bias", "")).upper().strip()
    if explicit in {"HAWKISH", "DOVISH", "NEUTRAL"}:
        return explicit, 1.0 if explicit == "HAWKISH" else -1.0 if explicit == "DOVISH" else 0.0
    text = " ".join(str(item.get(k, "")) for k in ("headline", "statement", "summary", "title")).lower()
    hawkish = sum(term in text for term in _HAWKISH)
    dovish = sum(term in text for term in _DOVISH)
    if hawkish > dovish: return "HAWKISH", 1.0
    if dovish > hawkish: return "DOVISH", -1.0
    return "NEUTRAL", 0.0

class CentralBankIntelligenceRuntime:
    """Convert supplied central-bank communications into context; never place orders."""
    def evaluate_one(self, record: Mapping[str, Any]) -> CentralBankIntelligenceReport:
        broker = str(record.get("broker", "XM")).upper()
        symbol = str(record.get("symbol", "GOLD#")).upper()
        now = _utc(record.get("current_time_utc"))
        raw: Iterable[Mapping[str, Any]] = record.get("central_bank_observations", ()) or ()
        rows: list[CentralBankObservation] = []
        weighted = 0.0
        weight_total = 0.0
        for index, item in enumerate(raw):
            institution = _institution(item.get("institution"))
            bias, score = _bias(item)
            communication_type = str(item.get("communication_type", "STATEMENT")).upper().strip() or "STATEMENT"
            speaker = str(item.get("speaker", institution)).strip() or institution
            confidence = 0.90 if str(item.get("policy_bias", "")).upper() in {"HAWKISH", "DOVISH", "NEUTRAL"} else 0.72
            if institution not in _SUPPORTED:
                confidence = min(confidence, 0.35)
            # Hawkish USD policy is generally adverse for non-yielding gold; dovish is generally supportive.
            gold_effect = "BEARISH" if bias == "HAWKISH" else "BULLISH" if bias == "DOVISH" else "NEUTRAL"
            weighted += score * confidence
            weight_total += confidence
            rows.append(CentralBankObservation(
                observation_id=str(item.get("observation_id", f"CB-{index+1}")), institution=institution,
                communication_type=communication_type, speaker=speaker, policy_bias=bias,
                gold_effect=gold_effect, confidence=confidence,
                explanation_en=f"{institution} {communication_type} from {speaker} is classified as {bias}. It provides structured GOLD# context only and cannot execute orders.",
                explanation_th=f"ข้อมูล {communication_type} ของ {institution} จาก {speaker} ถูกจัดเป็น {bias} ใช้เป็นบริบทแบบมีโครงสร้างสำหรับ GOLD# เท่านั้นและไม่สามารถส่งคำสั่งซื้อขายได้",
            ))
        aggregate = round(weighted / (weight_total or 1.0), 4) if rows else 0.0
        policy_bias = "HAWKISH" if aggregate > 0.15 else "DOVISH" if aggregate < -0.15 else "NEUTRAL"
        gold_effect = "BEARISH" if policy_bias == "HAWKISH" else "BULLISH" if policy_bias == "DOVISH" else "NEUTRAL"
        policy: list[str] = []
        if broker != "XM": policy.append("xm_only_required")
        if symbol != "GOLD#": policy.append("gold_symbol_only_required")
        if bool(record.get("live_execution_enabled", False)): policy.append("live_execution_disabled")
        valid = [r for r in rows if r.confidence >= 0.60]
        status = "BLOCKED" if policy else "READY" if valid else "WAITING"
        reason = ",".join(policy) if policy else "central_bank_intelligence_ready" if valid else "waiting_for_central_bank_observations"
        return CentralBankIntelligenceReport(
            status=status, reason=reason, observation_count=len(rows),
            hawkish_count=sum(r.policy_bias == "HAWKISH" for r in rows),
            dovish_count=sum(r.policy_bias == "DOVISH" for r in rows),
            neutral_count=sum(r.policy_bias == "NEUTRAL" for r in rows),
            aggregate_policy_bias=policy_bias, aggregate_gold_effect=gold_effect,
            aggregate_score=aggregate,
            confidence=round(sum(r.confidence for r in valid)/(len(valid) or 1), 4),
            intelligence_ready=not policy and bool(valid), execution_allowed=False,
            next_review_time_utc=(now + timedelta(minutes=15)).isoformat(), observations=tuple(rows),
            live_execution_enabled=False,
        )
    def explain_one(self, record: Mapping[str, Any]) -> CentralBankIntelligenceReport:
        return self.evaluate_one(record)
