"""Production Milestone F Pack 3 adaptive confidence runtime entrypoint."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.adaptive_confidence import AdaptiveConfidenceRuntime


def run_production_milestone_f_adaptive_confidence(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, object]:
    """Run deterministic adaptive confidence evaluation for Pack 3."""

    runtime = AdaptiveConfidenceRuntime()
    return runtime.run(observations).as_dict()
