"""Deterministic walk-forward research with explicit drawdown measurement."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class WalkForwardPolicy:
    training_size: int = 100
    validation_size: int = 30
    out_of_sample_size: int = 30
    step_size: int = 30
    minimum_trades: int = 20
    maximum_drawdown_percentage: float = 20.0
    minimum_profit_factor: float = 1.05

    def __post_init__(self) -> None:
        values = (
            self.training_size,
            self.validation_size,
            self.out_of_sample_size,
            self.step_size,
            self.minimum_trades,
        )
        if any(value <= 0 for value in values):
            raise ValueError("window sizes and minimum trades must be positive")
        if self.maximum_drawdown_percentage <= 0:
            raise ValueError("maximum drawdown percentage must be positive")


def _trade_return(row: Mapping[str, Any]) -> float:
    for key in ("return_value", "profit", "net_profit", "pnl"):
        if key in row:
            return float(row[key])
    raise ValueError("trade row requires return_value, profit, net_profit, or pnl")


def calculate_metrics(rows: Sequence[Mapping[str, Any]], starting_equity: float = 10000.0) -> dict[str, float]:
    if starting_equity <= 0:
        raise ValueError("starting_equity must be positive")
    returns = [_trade_return(row) for row in rows]
    equity = starting_equity
    peak = starting_equity
    maximum_drawdown = 0.0
    maximum_drawdown_percentage = 0.0
    current_drawdown_duration = 0
    maximum_drawdown_duration = 0
    gross_profit = 0.0
    gross_loss = 0.0
    wins = 0
    losses = 0
    consecutive_losses = 0
    maximum_consecutive_losses = 0
    sum_negative_squared = 0.0

    for value in returns:
        equity += value
        if value > 0:
            wins += 1
            gross_profit += value
            consecutive_losses = 0
        elif value < 0:
            losses += 1
            gross_loss += abs(value)
            consecutive_losses += 1
            maximum_consecutive_losses = max(maximum_consecutive_losses, consecutive_losses)
            sum_negative_squared += value * value

        if equity >= peak:
            peak = equity
            current_drawdown_duration = 0
        else:
            current_drawdown_duration += 1
            maximum_drawdown_duration = max(maximum_drawdown_duration, current_drawdown_duration)
            drawdown = peak - equity
            drawdown_percentage = (drawdown / peak) * 100.0 if peak else 0.0
            maximum_drawdown = max(maximum_drawdown, drawdown)
            maximum_drawdown_percentage = max(maximum_drawdown_percentage, drawdown_percentage)

    count = len(returns)
    net_profit = sum(returns)
    expectancy = net_profit / count if count else 0.0
    win_rate = (wins / count) * 100.0 if count else 0.0
    profit_factor = gross_profit / gross_loss if gross_loss else (999.0 if gross_profit else 0.0)
    recovery_factor = net_profit / maximum_drawdown if maximum_drawdown else (999.0 if net_profit > 0 else 0.0)
    downside_deviation = sqrt(sum_negative_squared / count) if count else 0.0
    sortino = expectancy / downside_deviation if downside_deviation else (999.0 if expectancy > 0 else 0.0)
    calmar = (net_profit / starting_equity * 100.0) / maximum_drawdown_percentage if maximum_drawdown_percentage else (999.0 if net_profit > 0 else 0.0)

    return {
        "trade_count": float(count),
        "wins": float(wins),
        "losses": float(losses),
        "win_rate_percentage": round(win_rate, 8),
        "net_profit": round(net_profit, 8),
        "expectancy": round(expectancy, 8),
        "profit_factor": round(profit_factor, 8),
        "maximum_drawdown": round(maximum_drawdown, 8),
        "maximum_drawdown_percentage": round(maximum_drawdown_percentage, 8),
        "maximum_drawdown_duration_trades": float(maximum_drawdown_duration),
        "maximum_consecutive_losses": float(maximum_consecutive_losses),
        "recovery_factor": round(recovery_factor, 8),
        "sortino_ratio": round(sortino, 8),
        "calmar_ratio": round(calmar, 8),
        "ending_equity": round(equity, 8),
    }


class WalkForwardResearchEngine:
    def __init__(self, policy: WalkForwardPolicy | None = None) -> None:
        self.policy = policy or WalkForwardPolicy()

    def run(self, rows: Iterable[Mapping[str, Any]], starting_equity: float = 10000.0) -> dict[str, Any]:
        ordered = list(rows)
        total_window = (
            self.policy.training_size
            + self.policy.validation_size
            + self.policy.out_of_sample_size
        )
        windows: list[dict[str, Any]] = []
        start = 0
        while start + total_window <= len(ordered):
            train_end = start + self.policy.training_size
            validation_end = train_end + self.policy.validation_size
            out_end = validation_end + self.policy.out_of_sample_size
            training = ordered[start:train_end]
            validation = ordered[train_end:validation_end]
            out_of_sample = ordered[validation_end:out_end]
            out_metrics = calculate_metrics(out_of_sample, starting_equity)
            eligible = (
                out_metrics["trade_count"] >= self.policy.minimum_trades
                and out_metrics["maximum_drawdown_percentage"] <= self.policy.maximum_drawdown_percentage
                and out_metrics["profit_factor"] >= self.policy.minimum_profit_factor
                and out_metrics["expectancy"] > 0
            )
            windows.append({
                "window_index": len(windows),
                "training_range": [start, train_end],
                "validation_range": [train_end, validation_end],
                "out_of_sample_range": [validation_end, out_end],
                "training_metrics": calculate_metrics(training, starting_equity),
                "validation_metrics": calculate_metrics(validation, starting_equity),
                "out_of_sample_metrics": out_metrics,
                "research_eligible": eligible,
            })
            start += self.policy.step_size

        eligible_count = sum(1 for window in windows if window["research_eligible"])
        status = "READY" if windows and eligible_count == len(windows) else ("CAUTION" if eligible_count else "QUARANTINED")
        return {
            "schema_version": "1.0",
            "status": status,
            "window_count": len(windows),
            "eligible_window_count": eligible_count,
            "policy": self.policy.__dict__,
            "windows": windows,
        }
