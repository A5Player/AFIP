"""Production Milestone G Pack 1 runtime observability entry point."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.runtime_observability import RuntimeObservabilityRuntime


def run_production_milestone_g_runtime_observability(values: Iterable[Mapping[str, Any]]):
    """Evaluate runtime observability records with deterministic metrics and explanations."""

    return RuntimeObservabilityRuntime().explain_many(values)
