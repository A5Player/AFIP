"""Production Milestone F Pack 8 validation runtime entry point."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from afip.validation import ValidationRuntime


def run_production_milestone_f_validation(records: Sequence[Mapping[str, Any]]) -> dict[str, object]:
    """Run deterministic validation before production readiness review."""

    return ValidationRuntime().run(records).as_dict()
