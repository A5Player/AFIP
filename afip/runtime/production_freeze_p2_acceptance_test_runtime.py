"""Runtime entry point for Production Freeze P2 production acceptance test."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.production_acceptance_test import ProductionAcceptanceTestProfile, ProductionAcceptanceTestRuntime


def run_production_acceptance_test(records: Iterable[Mapping[str, Any]]) -> list[ProductionAcceptanceTestProfile]:
    """Evaluate production acceptance scenarios without enabling live execution."""

    return ProductionAcceptanceTestRuntime().evaluate_many(records)
