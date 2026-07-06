"""Dashboard-friendly replay reporting."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.replay.replay_session import ReplaySessionResult
from afip.replay.replay_validation import ReplayValidationResult


@dataclass(frozen=True)
class ReplayReport:
    """Compact replay report for research dashboard surfaces."""

    summary: str
    rows: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {"summary": self.summary, "rows": list(self.rows)}


class ReplayReportBuilder:
    """Build compact replay report lines."""

    def build(self, session_result: ReplaySessionResult, validation: ReplayValidationResult) -> ReplayReport:
        timeline = session_result.timeline_summary
        direction_counts = timeline.get("direction_counts", {})
        regime_counts = timeline.get("market_regime_counts", {})
        summary = (
            f"Replay {session_result.processed_snapshots} snapshots | "
            f"Validation {validation.status} {round(validation.quality_score, 2)}"
        )
        rows = (
            f"Period {timeline.get('start_at')} -> {timeline.get('end_at')}",
            f"Direction {direction_counts}",
            f"Market Regime {regime_counts}",
            f"Spread Avg {timeline.get('average_spread_points')} | Volatility Avg {timeline.get('average_volatility_points')}",
            f"Reason {session_result.reason}",
        )
        return ReplayReport(summary=summary, rows=rows)
