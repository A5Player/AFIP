"""Data-derived execution readiness checks."""

from __future__ import annotations

from dataclasses import dataclass

from .readiness_input import ExecutionReadinessInput


@dataclass(frozen=True)
class ReadinessCheckResult:
    name: str
    status: str
    score: float
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "score": self.score,
            "reasons": list(self.reasons),
        }


class CostReadinessCheck:
    name = "cost_readiness"

    def evaluate(self, value: ExecutionReadinessInput) -> ReadinessCheckResult:
        if value.maximum_spread_points <= 0.0:
            return ReadinessCheckResult(self.name, "BLOCK", 0.0, ("maximum_spread_required",))
        utilization = value.spread_points / value.maximum_spread_points
        score = round(max(0.0, 100.0 - utilization * 100.0), 4)
        status = "PASS" if value.spread_points <= value.maximum_spread_points else "BLOCK"
        reason = "spread_within_learned_limit" if status == "PASS" else "spread_above_learned_limit"
        return ReadinessCheckResult(self.name, status, score, (reason,))


class LiquidityReadinessCheck:
    name = "liquidity_readiness"
    minimum_liquidity_score = 50.0

    def evaluate(self, value: ExecutionReadinessInput) -> ReadinessCheckResult:
        status = "PASS" if value.liquidity_score >= self.minimum_liquidity_score else "BLOCK"
        reason = "liquidity_sufficient" if status == "PASS" else "liquidity_below_readiness_floor"
        return ReadinessCheckResult(self.name, status, value.liquidity_score, (reason,))


class RiskReadinessCheck:
    name = "risk_readiness"
    minimum_risk_score = 55.0
    minimum_margin_ratio = 1.5

    def evaluate(self, value: ExecutionReadinessInput) -> ReadinessCheckResult:
        if value.risk_score < self.minimum_risk_score:
            return ReadinessCheckResult(self.name, "BLOCK", value.risk_score, ("risk_score_below_readiness_floor",))
        if value.available_margin_ratio < self.minimum_margin_ratio:
            return ReadinessCheckResult(self.name, "BLOCK", value.risk_score, ("available_margin_ratio_below_floor",))
        return ReadinessCheckResult(self.name, "PASS", value.risk_score, ("risk_capacity_sufficient",))


class CapacityReadinessCheck:
    name = "capacity_readiness"

    def evaluate(self, value: ExecutionReadinessInput) -> ReadinessCheckResult:
        if value.maximum_position_count <= 0:
            return ReadinessCheckResult(self.name, "BLOCK", 0.0, ("maximum_position_count_required",))
        remaining = max(0, value.maximum_position_count - value.open_position_count)
        score = round((remaining / value.maximum_position_count) * 100.0, 4)
        status = "PASS" if remaining > 0 else "BLOCK"
        reason = "position_capacity_available" if status == "PASS" else "position_capacity_full"
        return ReadinessCheckResult(self.name, status, score, (reason,))
