"""Runtime entry point for Production Milestone G Pack 3 feature flag framework."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.feature_flags import FeatureFlagProfile, FeatureFlagReport, FeatureFlagRuntime


def evaluate_feature_flag_record(record: Mapping[str, Any]) -> FeatureFlagProfile:
    """Evaluate one feature flag record using deterministic production control rules."""

    return FeatureFlagRuntime().evaluate_one(record)


def evaluate_feature_flag_records(records: Iterable[Mapping[str, Any]]) -> list[FeatureFlagProfile]:
    """Evaluate feature flag records while preserving input order."""

    return FeatureFlagRuntime().evaluate_many(records)


def explain_feature_flag_record(record: Mapping[str, Any]) -> FeatureFlagReport:
    """Build a human-readable feature flag report for review workflows."""

    return FeatureFlagRuntime().explain_one(record)
