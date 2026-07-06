"""Replay session engine for deterministic historical market playback."""

from __future__ import annotations

from dataclasses import dataclass, field

from afip.market_history.historical_market_runtime import HistoricalMarketRuntime
from afip.replay.replay_timeline import ReplayTimeline


@dataclass
class ReplaySessionResult:
    """Result produced after a historical replay session."""

    status: str
    processed_snapshots: int
    timeline_summary: dict[str, object]
    history_summary: dict[str, object]
    reason: str = "replay_session_ready"

    def as_dict(self) -> dict[str, object]:
        history_summary = dict(self.history_summary)
        database_summary = dict(history_summary.get("database_summary", {}))
        database_summary.pop("timestamp", None)
        if database_summary:
            history_summary["database_summary"] = database_summary
        return {
            "status": self.status,
            "processed_snapshots": self.processed_snapshots,
            "timeline_summary": self.timeline_summary,
            "history_summary": history_summary,
            "reason": self.reason,
        }


@dataclass
class ReplaySessionEngine:
    """Process a replay timeline into the historical market runtime."""

    history_runtime: HistoricalMarketRuntime = field(default_factory=HistoricalMarketRuntime)

    def run(self, timeline: ReplayTimeline) -> ReplaySessionResult:
        if timeline.is_empty():
            return ReplaySessionResult(
                status="REPLAY_SESSION_EMPTY",
                processed_snapshots=0,
                timeline_summary=timeline.as_dict(),
                history_summary=self.history_runtime.state().as_dict(),
                reason="no_replay_snapshots_available",
            )
        observations = [snapshot.to_observation(stage="REPLAY_STEP") for snapshot in timeline.snapshots]
        history_state = self.history_runtime.observe_many(observations)
        return ReplaySessionResult(
            status="REPLAY_SESSION_READY",
            processed_snapshots=len(observations),
            timeline_summary=timeline.as_dict(),
            history_summary=history_state.as_dict(),
        )
