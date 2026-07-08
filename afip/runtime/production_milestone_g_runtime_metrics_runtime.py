"""Runtime entry point for Production Milestone G Pack 4."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.runtime_metrics_integration import RuntimeMetricsIntegrationRuntime, RuntimeMetricsProfile, RuntimeMetricsReport


def evaluate_runtime_metrics_record(record: Mapping[str, Any]) -> RuntimeMetricsProfile:
    """Evaluate one runtime metrics record without changing execution behavior."""

    return RuntimeMetricsIntegrationRuntime().evaluate_one(record)


def evaluate_runtime_metrics_records(records: Iterable[Mapping[str, Any]]) -> list[RuntimeMetricsProfile]:
    """Evaluate runtime metrics records in deterministic input order."""

    return RuntimeMetricsIntegrationRuntime().evaluate_many(records)


def explain_runtime_metrics_record(record: Mapping[str, Any]) -> RuntimeMetricsReport:
    """Build a deterministic runtime metrics report for one record."""

    return RuntimeMetricsIntegrationRuntime().explain_one(record)
