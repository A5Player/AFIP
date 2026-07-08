"""Runtime adapter for Production Freeze Pack P1 architecture audit."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.production_architecture_audit import ProductionArchitectureAuditRuntime


def evaluate_production_architecture_audit_record(record: Mapping[str, Any]):
    return ProductionArchitectureAuditRuntime().evaluate_one(record)


def evaluate_production_architecture_audit_records(records: Iterable[Mapping[str, Any]]):
    return ProductionArchitectureAuditRuntime().evaluate_many(records)


def explain_production_architecture_audit_record(record: Mapping[str, Any]):
    return ProductionArchitectureAuditRuntime().explain_one(record)
