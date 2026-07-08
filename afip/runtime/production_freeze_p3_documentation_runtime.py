"""Runtime entry point for Production Freeze Pack P3 documentation readiness."""

from __future__ import annotations

from typing import Any, Mapping

from afip.production_documentation import ProductionDocumentationReport, ProductionDocumentationRuntime


def run_production_freeze_p3_documentation(record: Mapping[str, Any]) -> ProductionDocumentationReport:
    """Return a deterministic production documentation readiness report."""

    return ProductionDocumentationRuntime().explain_one(record)
