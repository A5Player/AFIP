"""Running statistics for compact market knowledge records."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass
class RunningMarketStatistics:
    """Maintain compact outcome statistics without storing repeated observations."""

    observations: int = 0
    wins: int = 0
    losses: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    total_holding_minutes: float = 0.0
    total_mae: float = 0.0
    total_mfe: float = 0.0
    _mean_result: float = 0.0
    _m2_result: float = 0.0

    def update(
        self,
        *,
        result_amount: float = 0.0,
        holding_minutes: float = 0.0,
        mae: float = 0.0,
        mfe: float = 0.0,
    ) -> "RunningMarketStatistics":
        """Add one result using Welford variance and aggregate totals."""

        result_amount = float(result_amount)
        self.observations += 1
        if result_amount > 0:
            self.wins += 1
            self.total_profit += result_amount
        elif result_amount < 0:
            self.losses += 1
            self.total_loss += abs(result_amount)
        self.total_holding_minutes += max(0.0, float(holding_minutes))
        self.total_mae += abs(float(mae))
        self.total_mfe += abs(float(mfe))

        delta = result_amount - self._mean_result
        self._mean_result += delta / self.observations
        delta_two = result_amount - self._mean_result
        self._m2_result += delta * delta_two
        return self

    @property
    def win_rate(self) -> float:
        if self.observations == 0:
            return 0.0
        return round((self.wins / self.observations) * 100.0, 2)

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
    def average_mae(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_mae / self.observations, 4)

    @property
    def average_mfe(self) -> float:
        if self.observations == 0:
            return 0.0
        return round(self.total_mfe / self.observations, 4)

    @property
    def result_std(self) -> float:
        if self.observations < 2:
            return 0.0
        return round(sqrt(self._m2_result / (self.observations - 1)), 4)

    def as_dict(self) -> dict[str, object]:
        return {
            "observations": self.observations,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.win_rate,
            "expectancy": self.expectancy,
            "profit_factor": self.profit_factor,
            "average_holding_minutes": self.average_holding_minutes,
            "average_mae": self.average_mae,
            "average_mfe": self.average_mfe,
            "result_std": self.result_std,
        }
