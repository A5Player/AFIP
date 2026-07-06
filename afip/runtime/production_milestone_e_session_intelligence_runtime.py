"""Production Milestone E Pack 1 runtime entry point."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.session_intelligence import SessionIntelligenceReport, SessionIntelligenceRuntime


def run_production_milestone_e_session_intelligence(
    observations: Iterable[Mapping[str, Any]],
) -> SessionIntelligenceReport:
    """Run deterministic session intelligence for Production Milestone E Pack 1."""

    return SessionIntelligenceRuntime().run(observations)
