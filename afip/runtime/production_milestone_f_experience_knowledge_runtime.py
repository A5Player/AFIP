"""Production Milestone F Pack 4 experience knowledge runtime entrypoint."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.experience_knowledge import ExperienceKnowledgeRuntime


def run_production_milestone_f_experience_knowledge(
    observations: Iterable[Mapping[str, Any]],
) -> dict[str, object]:
    """Run deterministic experience knowledge evaluation for Pack 4."""

    runtime = ExperienceKnowledgeRuntime()
    return runtime.run(observations).as_dict()
