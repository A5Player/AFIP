"""Production Milestone F Pack 6 runtime adapter."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from afip.runtime_adaptation import RuntimeAdaptationRuntime


def run_production_milestone_f_runtime_adaptation(records: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Run deterministic runtime adaptation planning from strategy evolution records."""

    return RuntimeAdaptationRuntime().run(records).as_dict()
