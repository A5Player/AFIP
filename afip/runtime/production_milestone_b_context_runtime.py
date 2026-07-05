"""Production Milestone B Pack 6 market context runtime."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from afip.context.market_context_engine import MarketContextEngine


class ProductionMilestoneBContextRuntime:
    """Runtime adapter for market context assessment."""

    def __init__(self) -> None:
        self.market_context_engine = MarketContextEngine()

    def run(
        self,
        metrics: Mapping[str, Any] | None = None,
        previous_state: str | None = None,
    ) -> dict[str, Any]:
        """Return a serializable market context payload."""

        result = self.market_context_engine.assess(metrics=metrics, previous_state=previous_state)
        payload = asdict(result)
        payload["runtime_status"] = "PRODUCTION_MILESTONE_B_CONTEXT_READY"
        payload["milestone"] = "PRODUCTION_MILESTONE_B_PACK_6"
        return payload


def run_production_milestone_b_context_runtime(
    metrics: Mapping[str, Any] | None = None,
    previous_state: str | None = None,
) -> dict[str, Any]:
    """Functional entry point for CI and documentation examples."""

    return ProductionMilestoneBContextRuntime().run(
        metrics=metrics,
        previous_state=previous_state,
    )
