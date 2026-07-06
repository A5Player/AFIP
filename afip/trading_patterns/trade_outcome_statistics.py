"""Compact outcome statistics for trading pattern research."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass
class TradeOutcomeStatistics:
    """Track trading results without storing every repeated observation."""

    observations: int = 0
    profitable_results: int = 0
    losing_results: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    total_holding_minutes: float = 0.0
    total_mae_points: float = 0.0
    total_mfe_points: float = 0.0
    total_execution_cost_points: float = 0.0
    _mean_result: float = 0.0
    _m2_result: float = 0.0

    def observe(
        self,
        *,
        result_amount: float,
        holding_minutes: float = 0.0,
        mae_points: float = 0.0,
        mfe_points: float = 0.0,
        execution_cost_points: float = 0.0,
    ) -> "TradeOutcomeStatistics":
        """Add one outcome and update compact running statistics."""

        result_amount = float(result_amount)
        self.observations += 1
        if result_amount > 0:
            self.profitable_results += 1
            self.total_profit += result_amount
        elif result_amount < 0:
            self.losing_results += 1
            self.total_loss += abs(result_amount)
        self.total_holding_minutes += max(0.0, float(holding_minutes))
        self.total_mae_points += abs(float(mae_points))
        self.total_mfe_points += abs(float(mfe_points))
        self.total_execution_cost_points += max(0.0, float(execution_cost_points))

        delta = result_amount - self._mean_result
        self._mean_result += delta / self.observations
        delta_two = result_amount - self._mean_result
        self._m2_result += delta * delta_two
        return self

    @property
    def win_rate(self) -> float:
        if self.observations == 0:
            return 0.0
        return round((self.profitable_results / self.observations) * 100.0, 2)

    @property
    def expectancy(self) -> float:
        if self.observations == 0:
            return 0.0
        return round((self.total_profit - self.total_loss) / self.observations, 4)

    @property
    def profit_factor(self) -> float:
        if self.total_loss == 0:
            return round(self.total_profit, 4) if self.total_profit else 0.0
        return round(self.total_profit / self.total_loss, 4)

    @property
    def average_holding_minutes(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_holding_minutes / self.observations, 2)

    @property
    def average_mae_points(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_mae_points / self.observations, 4)

    @property
    def average_mfe_points(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_mfe_points / self.observations, 4)

    @property
    def average_execution_cost_points(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_execution_cost_points / self.observations, 4)

    @property
    def result_std(self) -> float:
        if self.observations < 2:
            return 0.0
        return round(sqrt(self._m2_result / (self.observations - 1)), 4)

    def as_dict(self) -> dict[str, object]:
        return {
            "observations": self.observations,
            "profitable_results": self.profitable_results,
            "losing_results": self.losing_results,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "profit_factor": self.profit_factor,
            "average_holding_minutes": self.average_holding_minutes,
            "average_mae_points": self.average_mae_points,
            "average_mfe_points": self.average_mfe_points,
            "average_execution_cost_points": self.average_execution_cost_points,
            "result_std": self.result_std,
        }
