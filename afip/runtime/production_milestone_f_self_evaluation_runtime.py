"""Production Milestone F Pack 2 self evaluation runtime adapter."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.self_evaluation import SelfEvaluationRuntime


def run_production_milestone_f_self_evaluation(
    closed_decision_observations: Iterable[Mapping[str, Any]],
) -> dict[str, object]:
    """Run deterministic self evaluation and return a serializable report."""

    runtime = SelfEvaluationRuntime()
    return runtime.run(closed_decision_observations).as_dict()
