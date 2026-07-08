"""Production Freeze P5 runtime wrapper for walk-forward historical paper simulation."""

from __future__ import annotations

from typing import Any, Mapping

from afip.walk_forward_simulation import WalkForwardRuntime


def run_production_freeze_p5_walk_forward(record: Mapping[str, Any]) -> dict[str, object]:
    """Return a deterministic report for a single walk-forward simulation record."""
    return WalkForwardRuntime().explain_one(record).as_dict()
