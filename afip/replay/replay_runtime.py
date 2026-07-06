"""Production-ready historical replay runtime facade."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from afip.replay.historical_replay_provider import HistoricalReplayProvider, StaticHistoricalReplayProvider
from afip.replay.replay_report import ReplayReportBuilder
from afip.replay.replay_session import ReplaySessionEngine
from afip.replay.replay_timeline import ReplayTimeline
from afip.replay.replay_validation import ReplayValidationEngine


@dataclass(frozen=True)
class ReplayRuntimeState:
    """State returned by the replay runtime."""

    status: str
    validation: dict[str, object]
    session: dict[str, object]
    report: dict[str, object]
    reason: str = "historical_replay_runtime_ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "validation": self.validation,
            "session": self.session,
            "report": self.report,
            "reason": self.reason,
        }


class ReplayRuntime:
    """Coordinate historical replay provider, validation, session processing, and reporting."""

    def __init__(
        self,
        provider: HistoricalReplayProvider | None = None,
        validator: ReplayValidationEngine | None = None,
        session_engine: ReplaySessionEngine | None = None,
        report_builder: ReplayReportBuilder | None = None,
    ) -> None:
        self.provider = provider or StaticHistoricalReplayProvider()
        self.validator = validator or ReplayValidationEngine()
        self.session_engine = session_engine or ReplaySessionEngine()
        self.report_builder = report_builder or ReplayReportBuilder()

    def run(self, start_at: datetime, end_at: datetime, symbol: str = "GOLD#") -> ReplayRuntimeState:
        snapshots = self.provider.load(start_at=start_at, end_at=end_at, symbol=symbol)
        timeline = ReplayTimeline(snapshots)
        validation = self.validator.validate(timeline)
        session_result = self.session_engine.run(timeline)
        report = self.report_builder.build(session_result, validation)
        if validation.status == "REPLAY_VALIDATION_BLOCKED":
            status = "REPLAY_RUNTIME_REVIEW"
            reason = "historical_replay_validation_blocked"
        elif session_result.status == "REPLAY_SESSION_EMPTY":
            status = "REPLAY_RUNTIME_REVIEW"
            reason = "historical_replay_empty"
        else:
            status = "REPLAY_RUNTIME_READY"
            reason = "historical_replay_runtime_ready"
        return ReplayRuntimeState(
            status=status,
            validation=validation.as_dict(),
            session=session_result.as_dict(),
            report=report.as_dict(),
            reason=reason,
        )
