"""Production Milestone F Pack 5 strategy evolution runtime entrypoint."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from afip.strategy_evolution import StrategyEvolutionRuntime


def run_production_milestone_f_strategy_evolution(records: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Run deterministic strategy evolution and return a serializable report."""

    return StrategyEvolutionRuntime().run(records).as_dict()
