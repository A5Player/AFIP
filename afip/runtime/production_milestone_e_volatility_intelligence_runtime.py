"""Production Milestone E Pack 2 volatility intelligence runtime entrypoint."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.volatility_intelligence import VolatilityIntelligenceReport, VolatilityIntelligenceRuntime


def run_production_milestone_e_volatility_intelligence(
    observations: Iterable[Mapping[str, Any]],
) -> VolatilityIntelligenceReport:
    """Run deterministic volatility intelligence for Production Milestone E Pack 2."""

    return VolatilityIntelligenceRuntime().run(observations)
