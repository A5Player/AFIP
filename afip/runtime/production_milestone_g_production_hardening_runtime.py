"""Runtime entry point for Production Milestone G Pack 5."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.production_hardening import ProductionHardeningProfile, ProductionHardeningReport, ProductionHardeningRuntime


def evaluate_production_hardening_record(record: Mapping[str, Any]) -> ProductionHardeningProfile:
    """Evaluate one production hardening record without changing execution behavior."""

    return ProductionHardeningRuntime().evaluate_one(record)


def evaluate_production_hardening_records(records: Iterable[Mapping[str, Any]]) -> list[ProductionHardeningProfile]:
    """Evaluate production hardening records in deterministic input order."""

    return ProductionHardeningRuntime().evaluate_many(records)


def explain_production_hardening_record(record: Mapping[str, Any]) -> ProductionHardeningReport:
    """Build a deterministic production hardening report for one record."""

    return ProductionHardeningRuntime().explain_one(record)
