"""Production Milestone E Pack 8 macro context runtime adapter."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.macro_context import MacroReport, MacroRuntime


class ProductionMilestoneEMacroContextRuntime:
    """Adapter that exposes deterministic macro context runtime for production tests."""

    def __init__(self, runtime: MacroRuntime | None = None) -> None:
        self.runtime = runtime or MacroRuntime()

    def run(self, observations: Iterable[Mapping[str, Any]]) -> MacroReport:
        return self.runtime.run(observations)
