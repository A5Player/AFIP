"""Production Milestone C Pack 1 macro intelligence runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.macro.economic_calendar_runtime import EconomicCalendarRuntime
from afip.macro.macro_consensus_engine import MacroConsensusEngine
from afip.macro.macro_event_engine import MacroEventEngine
from afip.macro.market_factor_runtime import MarketFactorRuntime
from afip.macro.macro_dashboard_report import MacroDashboardReport
from afip.macro.macro_snapshot import MacroSnapshot


@dataclass(frozen=True)
class ProductionMilestoneCMacroRuntimeResult:
    """Pack 1 macro runtime result."""

    status: str
    ready: bool
    next_event: str | None
    event_risk_state: str
    event_impact_score: float
    event_urgency_score: float
    event_confidence_score: float
    market_factor_status: str
    market_factor_score: float
    macro_score: float
    gold_bias: str
    trade_instruction: str
    dashboard_line: str
    reason: str


class ProductionMilestoneCMacroRuntime:
    """Run the first production macro intelligence layer."""

    def __init__(self) -> None:
        self.calendar_runtime = EconomicCalendarRuntime()
        self.event_engine = MacroEventEngine()
        self.market_factor_runtime = MarketFactorRuntime()
        self.consensus_engine = MacroConsensusEngine()
        self.dashboard_report = MacroDashboardReport()

    def run(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        market_factors: Mapping[str, object] | None = None,
        now: datetime | None = None,
    ) -> ProductionMilestoneCMacroRuntimeResult:
        current_time = now or datetime.now(timezone.utc)
        calendar_state = self.calendar_runtime.runtime_state(economic_events or (), current_time)
        event_assessment = self.event_engine.assess_dict(calendar_state)
        factor_state = self.market_factor_runtime.evaluate(market_factors or {})
        consensus = self.consensus_engine.combine_dict(calendar_state, event_assessment, factor_state)
        snapshot = MacroSnapshot(
            status=consensus["status"],
            next_event=calendar_state.get("next_event"),
            event_risk_state=str(calendar_state.get("event_risk_state", "CLEAR")),
            macro_score=float(consensus["macro_score"]),
            gold_bias=str(consensus["gold_bias"]),
            trade_instruction=str(consensus["trade_instruction"]),
            reason=str(consensus["reason"]),
        )
        dashboard_line = self.dashboard_report.build(asdict(snapshot))
        return ProductionMilestoneCMacroRuntimeResult(
            status="PRODUCTION_MILESTONE_C_MACRO_READY",
            ready=True,
            next_event=snapshot.next_event,
            event_risk_state=snapshot.event_risk_state,
            event_impact_score=float(event_assessment["impact_score"]),
            event_urgency_score=float(event_assessment["urgency_score"]),
            event_confidence_score=float(event_assessment["confidence_score"]),
            market_factor_status=str(factor_state["status"]),
            market_factor_score=float(factor_state["gold_macro_score"]),
            macro_score=snapshot.macro_score,
            gold_bias=snapshot.gold_bias,
            trade_instruction=snapshot.trade_instruction,
            dashboard_line=dashboard_line,
            reason=snapshot.reason,
        )

    def run_dict(
        self,
        economic_events: Iterable[Mapping[str, object]] | None = None,
        market_factors: Mapping[str, object] | None = None,
        now: datetime | None = None,
    ) -> dict[str, object]:
        return asdict(self.run(economic_events, market_factors, now))
