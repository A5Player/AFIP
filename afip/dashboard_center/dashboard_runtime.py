"""Dashboard Foundation runtime for Milestone H Pack 1.

This runtime prepares presentation metadata only. It never opens orders, never
changes risk decisions, and never updates strategy behavior.
"""

from __future__ import annotations

from typing import Any, Mapping

from .dashboard_report import DashboardFoundationReport
from .engine_catalog import default_engine_catalog
from .intelligence_catalog import default_intelligence_catalog
from .top10_summary import build_top_rankings


class DashboardFoundationRuntime:
    """Build dashboard foundation reports deterministically."""

    def evaluate_one(self, record: Mapping[str, Any]) -> DashboardFoundationReport:
        market_regime = str(record.get("market_regime", "")).strip().upper()
        signal_context = str(record.get("signal_context", record.get("context", "UNKNOWN"))).strip().upper() or "UNKNOWN"
        execution_mode = str(record.get("execution_mode", "LOCKED_SIMULATION_ONLY")).strip().upper()

        intelligence_cards = tuple(default_intelligence_catalog(record.get("intelligence_records")))
        engine_cards = tuple(default_engine_catalog(record.get("engine_records")))
        top_rankings = tuple(build_top_rankings(record.get("top_rank_records", _default_top_records())))

        bilingual_ready = all(card.name_en and card.name_th and card.function_en and card.function_th for card in intelligence_cards) and all(
            card.name_en and card.name_th and card.function_en and card.function_th for card in engine_cards
        )

        if not market_regime:
            return _report("BLOCKED", "market_regime_required", "BLOCKED", market_regime, signal_context, intelligence_cards, engine_cards, top_rankings, bilingual_ready)
        if execution_mode not in {"SIMULATION", "PAPER", "PAPER_TRADING", "LOCKED_SIMULATION_ONLY"}:
            return _report("BLOCKED", "live_execution_not_allowed_for_dashboard_foundation", "BLOCKED", market_regime, signal_context, intelligence_cards, engine_cards, top_rankings, bilingual_ready)
        if not bilingual_ready:
            return _report("REVIEW", "bilingual_dashboard_metadata_review_required", "REVIEW", market_regime, signal_context, intelligence_cards, engine_cards, top_rankings, bilingual_ready)
        if len(top_rankings) == 0:
            return _report("REVIEW", "top_ranking_sections_required", "REVIEW", market_regime, signal_context, intelligence_cards, engine_cards, top_rankings, bilingual_ready)
        return _report("READY", "dashboard_foundation_ready", "DASHBOARD_FOUNDATION_READY", market_regime, signal_context, intelligence_cards, engine_cards, top_rankings, bilingual_ready)

    def explain_one(self, record: Mapping[str, Any]) -> DashboardFoundationReport:
        return self.evaluate_one(record)


def _report(
    status: str,
    reason: str,
    gate: str,
    market_regime: str,
    signal_context: str,
    intelligence_cards: tuple,
    engine_cards: tuple,
    top_rankings: tuple,
    bilingual_ready: bool,
) -> DashboardFoundationReport:
    return DashboardFoundationReport(
        status=status,
        reason=reason,
        dashboard_gate=gate,
        market_regime=market_regime,
        signal_context=signal_context,
        intelligence_cards=intelligence_cards,
        engine_cards=engine_cards,
        top_rankings=top_rankings,
        bilingual_ready=bilingual_ready,
    )


def _default_top_records() -> list[dict[str, Any]]:
    return [
        {"category": "Trading Hour", "label_en": "London session", "label_th": "ช่วงตลาดลอนดอน", "metric_name": "win_rate", "metric_value": 74, "sample_size": 120},
        {"category": "Trading Pattern", "label_en": "Bearish order block", "label_th": "โซนคำสั่งราคาฝั่งขาย", "metric_name": "win_rate", "metric_value": 72, "sample_size": 96},
        {"category": "Market Regime", "label_en": "Trending market", "label_th": "ตลาดมีแนวโน้ม", "metric_name": "expectancy", "metric_value": 69, "sample_size": 180},
        {"category": "No Trade Reason", "label_en": "Spread near limit", "label_th": "Spread ใกล้ขอบเขต", "metric_name": "avoidance_value", "metric_value": 65, "sample_size": 80},
    ]
