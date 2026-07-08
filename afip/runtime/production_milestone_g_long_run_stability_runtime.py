"""Runtime entry point for Production Milestone G Pack 7."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.long_run_stability import LongRunStabilityProfile, LongRunStabilityReport, LongRunStabilityRuntime


def evaluate_long_run_stability_record(record: Mapping[str, Any]) -> LongRunStabilityProfile:
    """Evaluate one long-run stability record without changing trading logic."""

    return LongRunStabilityRuntime().evaluate_one(record)


def evaluate_long_run_stability_records(records: Iterable[Mapping[str, Any]]) -> list[LongRunStabilityProfile]:
    """Evaluate long-run stability records in deterministic input order."""

    return LongRunStabilityRuntime().evaluate_many(records)


def explain_long_run_stability_record(record: Mapping[str, Any]) -> LongRunStabilityReport:
    """Build a deterministic long-run stability report for one record."""

    return LongRunStabilityRuntime().explain_one(record)
