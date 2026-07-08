"""Runtime entry point for Production Milestone G Pack 6."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afip.paper_trading import PaperTradingProfile, PaperTradingReport, PaperTradingRuntime


def evaluate_paper_trading_record(record: Mapping[str, Any]) -> PaperTradingProfile:
    """Evaluate one paper trading record without creating live orders."""

    return PaperTradingRuntime().evaluate_one(record)


def evaluate_paper_trading_records(records: Iterable[Mapping[str, Any]]) -> list[PaperTradingProfile]:
    """Evaluate paper trading records in deterministic input order."""

    return PaperTradingRuntime().evaluate_many(records)


def explain_paper_trading_record(record: Mapping[str, Any]) -> PaperTradingReport:
    """Build a deterministic paper trading report for one record."""

    return PaperTradingRuntime().explain_one(record)
