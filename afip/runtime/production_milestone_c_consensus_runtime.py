"""Production Milestone C Pack 5 integrated macro market consensus runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.macro.economic_calendar_runtime import EconomicCalendarRuntime
from afip.macro.macro_event_engine import MacroEventEngine
from afip.macro.macro_market_consensus import MacroMarketConsensusEngine
from afip.macro.macro_market_decision_profile import MacroMarketDecisionProfileEngine
from afip.runtime.production_milestone_c_market_factor_runtime import ProductionMilestoneCMarketFactorRuntime
from afip.runtime.production_milestone_c_news_runtime import ProductionMilestoneCNewsRuntime


class ProductionMilestoneCConsensusRuntime:
    """Integrate calendar, news, and macro market factors into one financial runtime state."""

    def __init__(self) -> None:
        self.calendar_runtime = EconomicCalendarRuntime()
        self.event_engine = MacroEventEngine()
        self.news_runtime = ProductionMilestoneCNewsRuntime()
        self.market_factor_runtime = ProductionMilestoneCMarketFactorRuntime()
        self.consensus_engine = MacroMarketConsensusEngine()
        self.decision_profile_engine = MacroMarketDecisionProfileEngine()

    def run_dict(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        news_articles: Iterable[Mapping[str, object]] | None = None,
        market_factors: Mapping[str, object] | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        current = self._ensure_timezone(now or datetime.now(timezone.utc))
        calendar_state = self.calendar_runtime.runtime_state(economic_events or (), current)
        event_assessment = self.event_engine.assess_dict(calendar_state)
        news_state = self.news_runtime.run_dict(news_articles or (), current)
        market_factor_state = self.market_factor_runtime.run(current_time=current, raw_factors=market_factors or {})
        consensus = self.consensus_engine.combine_dict(calendar_state, event_assessment, news_state, market_factor_state)
        profile = self.decision_profile_engine.build(consensus).as_dict()
        return {
            "runtime": "PRODUCTION_MILESTONE_C_CONSENSUS_RUNTIME",
            "package": "Production Milestone C Pack 5",
            "status": "MACRO_MARKET_CONSENSUS_RUNTIME_READY",
            "ready": True,
            "calendar_state": calendar_state,
            "event_assessment": event_assessment,
            "news_state": news_state,
            "market_factor_state": market_factor_state,
            "consensus": consensus,
            "decision_profile": profile,
            "exposure_instruction": profile["exposure_instruction"],
            "position_horizon": profile["position_horizon"],
            "reason": profile["reason"],
        }

    @staticmethod
    def _ensure_timezone(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
