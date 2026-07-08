"""Runtime entry point for Production Milestone G Pack 8."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.production_release_candidate import (
    ProductionReleaseCandidateProfile,
    ProductionReleaseCandidateReport,
    ProductionReleaseCandidateRuntime,
)


def evaluate_production_release_candidate_record(record: Mapping[str, Any]) -> ProductionReleaseCandidateProfile:
    """Evaluate one Release Candidate record without changing trading logic."""

    return ProductionReleaseCandidateRuntime().evaluate_one(record)


def evaluate_production_release_candidate_records(records: Iterable[Mapping[str, Any]]) -> list[ProductionReleaseCandidateProfile]:
    """Evaluate RC records in deterministic input order."""

    return ProductionReleaseCandidateRuntime().evaluate_many(records)


def explain_production_release_candidate_record(record: Mapping[str, Any]) -> ProductionReleaseCandidateReport:
    """Build a deterministic RC report for one record."""

    return ProductionReleaseCandidateRuntime().explain_one(record)
