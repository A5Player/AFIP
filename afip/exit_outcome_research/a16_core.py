"""A16 research-only exit policy catalogue.

This is a policy compiler for the existing chronological ExitOutcomeResearchEngine;
it deliberately has no broker, MT5, or execution imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .runtime import ExitPolicyExperimentRunner, ExitResearchPolicy, PositionOutcome, PositionResearchCase


@dataclass(frozen=True)
class A16PolicySet:
    """Candidate parameters only; none is a production selection."""
    initial_risk_distance: float
    fixed_target_r: float = 2.0
    r_step_distance_r: float = 1.0
    mfe_distance_r: float = 0.5
    atr_distance_r: float = 1.0
    structure_distance_r: float = 1.0

    def __post_init__(self) -> None:
        if self.initial_risk_distance <= 0 or self.fixed_target_r <= 0:
            raise ValueError("risk distance and target R must be positive")
        if min(self.r_step_distance_r, self.mfe_distance_r, self.atr_distance_r, self.structure_distance_r) <= 0:
            raise ValueError("trailing distances must be positive")

    def policies(self) -> tuple[ExitResearchPolicy, ...]:
        r = self.initial_risk_distance
        return (
            ExitResearchPolicy("FIXED_TP", r, profit_target_distance=r * self.fixed_target_r),
            ExitResearchPolicy("BREAK_EVEN_FIXED_TP", r, profit_target_distance=r * self.fixed_target_r, break_even_trigger_r=1.0),
            ExitResearchPolicy("R_STEP", r, trailing_trigger_r=1.5, trailing_distance_r=self.r_step_distance_r),
            ExitResearchPolicy("MFE_PERCENT", r, trailing_trigger_r=1.0, trailing_distance_r=self.mfe_distance_r),
            ExitResearchPolicy("ATR", r, trailing_trigger_r=1.0, trailing_distance_r=self.atr_distance_r),
            ExitResearchPolicy("STRUCTURE", r, trailing_trigger_r=1.0, trailing_distance_r=self.structure_distance_r),
            ExitResearchPolicy("HYBRID_R_STRUCTURE", r, trailing_trigger_r=1.5, trailing_distance_r=min(self.r_step_distance_r, self.structure_distance_r)),
            ExitResearchPolicy("PARTIAL_RUNNER", r, trailing_trigger_r=2.0, trailing_distance_r=self.r_step_distance_r),
        )


class A16ExitResearchRunner:
    """Run all candidates through the existing append-only research engine."""

    def __init__(self, runner: ExitPolicyExperimentRunner) -> None:
        self.runner = runner

    def run(self, *, case: PositionResearchCase, policy_set: A16PolicySet, candles: Iterable[object]) -> tuple[PositionOutcome, ...]:
        if case.position_units < 2:
            policies = tuple(p for p in policy_set.policies() if p.policy_id != "PARTIAL_RUNNER")
        else:
            policies = policy_set.policies()
        return self.runner.run(case=case, policies=policies, candles=tuple(candles))
