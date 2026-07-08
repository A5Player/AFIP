"""Runtime entrypoint for Production Freeze P4 operations readiness."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.production_operations import ProductionOperationsProfile, ProductionOperationsRuntime


def evaluate_production_operations(records: Iterable[Mapping[str, Any]]) -> list[ProductionOperationsProfile]:
    """Evaluate deployment and operations readiness records deterministically."""

    return ProductionOperationsRuntime().evaluate_many(records)
