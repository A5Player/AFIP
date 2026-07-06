"""Production Milestone C Pack 6 macro dashboard runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.macro.macro_market_dashboard import MacroMarketDashboardBuilder
from afip.runtime.production_milestone_c_consensus_runtime import ProductionMilestoneCConsensusRuntime


class ProductionMilestoneCMacroDashboardRuntime:
    """Build dashboard-ready macro market intelligence from integrated consensus inputs."""

    def __init__(self) -> None:
        self.consensus_runtime = ProductionMilestoneCConsensusRuntime()
        self.dashboard_builder = MacroMarketDashboardBuilder()

    def run_dict(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        news_articles: Iterable[Mapping[str, object]] | None = None,
        market_factors: Mapping[str, object] | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        current = self._ensure_timezone(now or datetime.now(timezone.utc))
        consensus_state = self.consensus_runtime.run_dict(
            economic_events=economic_events or (),
            news_articles=news_articles or (),
            market_factors=market_factors or {},
            now=current,
        )
        dashboard = self.dashboard_builder.build_dict(consensus_state)
        return {
            "runtime": "PRODUCTION_MILESTONE_C_MACRO_DASHBOARD_RUNTIME",
            "package": "Production Milestone C Pack 6",
            "status": "MACRO_DASHBOARD_RUNTIME_READY",
            "ready": True,
            "consensus_state": consensus_state,
            "dashboard": dashboard,
            "headline": dashboard["headline"],
            "summary_line": dashboard["summary_line"],
            "exposure_instruction": dashboard["exposure_instruction"],
            "position_horizon": dashboard["position_horizon"],
        }

    @staticmethod
    def _ensure_timezone(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
