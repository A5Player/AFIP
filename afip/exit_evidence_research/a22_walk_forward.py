"""A22 chronological walk-forward validation for holding/exit evidence."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from hashlib import sha256
import json
from math import isfinite, sqrt
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping

from afip.historical_replay_research import AppendOnlyResearchDataset

_PHASES = ("TRAIN", "VALIDATION", "BLIND_FORWARD")
_PARTITION_FIELDS = ("policy_id", "holding_bucket_id", "timeframe", "market_regime",
                     "session_name", "event_window", "calendar_context")


def _time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _identity(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class A22WalkForwardWindow:
    window_id: str
    phase: str
    start_timestamp_utc: str
    end_timestamp_utc: str

    def __post_init__(self) -> None:
        if not self.window_id.strip() or self.phase not in _PHASES:
            raise ValueError("walk-forward window identity or phase is invalid")
        if _time(self.start_timestamp_utc) >= _time(self.end_timestamp_utc):
            raise ValueError("walk-forward window start must precede end")

    def contains(self, timestamp: str) -> bool:
        value = _time(timestamp)
        return _time(self.start_timestamp_utc) <= value < _time(self.end_timestamp_utc)


@dataclass(frozen=True)
class A22RobustnessPolicy:
    minimum_sample_size_per_phase: int
    maximum_expectancy_degradation_r: float
    baseline_expectancy_r: float = 0.0
    confidence_z: float = 1.96

    def __post_init__(self) -> None:
        if self.minimum_sample_size_per_phase <= 0 or self.maximum_expectancy_degradation_r < 0:
            raise ValueError("robustness sample and degradation limits are invalid")
        if self.confidence_z <= 0 or not all(isfinite(value) for value in (
                self.maximum_expectancy_degradation_r, self.baseline_expectancy_r, self.confidence_z)):
            raise ValueError("robustness policy values must be finite")


@dataclass(frozen=True)
class A22ValidationResult:
    result_id: str
    partition: Mapping[str, str]
    status: str
    reason: str
    train_samples: int
    validation_samples: int
    blind_forward_samples: int
    train_expectancy_r: float | None
    validation_expectancy_r: float | None
    blind_forward_expectancy_r: float | None
    blind_forward_confidence_low_r: float | None
    blind_forward_confidence_high_r: float | None
    blind_forward_net_profit_r: float | None
    blind_forward_average_win_r: float | None
    blind_forward_average_loss_r: float | None
    blind_forward_profit_factor: float | None
    blind_forward_max_drawdown_r: float | None
    blind_forward_tail_loss_r: float | None
    blind_forward_max_consecutive_losses: int | None
    blind_forward_average_mfe_r: float | None
    blind_forward_average_mae_r: float | None
    blind_forward_average_holding_seconds: float | None
    out_of_sample_degradation_r: float | None
    baseline_expectancy_r: float
    sensitivity_pass: bool
    overfitting_detected: bool
    drift_detected: bool
    automatic_promotion_allowed: bool = False
    research_only: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class A22WalkForwardValidator:
    """Validate exact context partitions across one chronological three-phase fold."""

    def __init__(self, dataset: AppendOnlyResearchDataset, *, windows: Iterable[A22WalkForwardWindow],
                 policy: A22RobustnessPolicy) -> None:
        values = tuple(windows)
        if tuple(item.phase for item in values) != _PHASES:
            raise ValueError("windows must be ordered TRAIN, VALIDATION, BLIND_FORWARD")
        if any(_time(left.end_timestamp_utc) > _time(right.start_timestamp_utc)
               for left, right in zip(values, values[1:])):
            raise ValueError("walk-forward windows must not overlap")
        self.dataset = dataset
        self.windows = values
        self.policy = policy

    def validate_recorded(self) -> tuple[A22ValidationResult, ...]:
        grouped: dict[tuple[str, ...], dict[str, list[dict[str, Any]]]] = {}
        for envelope in self.dataset.records("a22_holding_exit_validation_observations"):
            record = dict(envelope["record"])
            timestamp = str(record.get("decision_timestamp_utc", ""))
            phase = next((window.phase for window in self.windows if window.contains(timestamp)), None)
            if phase is None:
                continue
            key = tuple(str(record.get(field, "")) for field in _PARTITION_FIELDS)
            if not all(key):
                continue
            grouped.setdefault(key, {name: [] for name in _PHASES})[phase].append(record)
        results = tuple(self._evaluate(key, phases) for key, phases in sorted(grouped.items()))
        existing = {str(envelope["record"].get("result_id"))
                    for envelope in self.dataset.records("a22_holding_exit_validation_results")}
        if any(item.result_id in existing for item in results):
            raise ValueError("walk-forward validation result already exists")
        for item in results:
            self.dataset.append("a22_holding_exit_validation_results", item.as_dict())
        return results

    def _evaluate(self, key: tuple[str, ...], phases: dict[str, list[dict[str, Any]]]) -> A22ValidationResult:
        partition = dict(zip(_PARTITION_FIELDS, key))
        counts = {phase: len(phases[phase]) for phase in _PHASES}
        source = [{"timestamp": item.get("decision_timestamp_utc"), "net": item.get("net_realized_r")}
                  for phase in _PHASES for item in phases[phase]]
        base = {"partition": partition, "windows": [asdict(item) for item in self.windows],
                "policy": asdict(self.policy), "counts": counts, "source": source}
        result_id = f"A22-{_identity(base)[:20].upper()}"
        if min(counts.values()) < self.policy.minimum_sample_size_per_phase:
            return A22ValidationResult(
                result_id=result_id, partition=partition, status="WAIT", reason="minimum_sample_not_met",
                train_samples=counts["TRAIN"], validation_samples=counts["VALIDATION"],
                blind_forward_samples=counts["BLIND_FORWARD"], train_expectancy_r=None,
                validation_expectancy_r=None, blind_forward_expectancy_r=None,
                blind_forward_confidence_low_r=None, blind_forward_confidence_high_r=None,
                blind_forward_net_profit_r=None, blind_forward_average_win_r=None,
                blind_forward_average_loss_r=None, blind_forward_profit_factor=None,
                blind_forward_max_drawdown_r=None, blind_forward_tail_loss_r=None,
                blind_forward_max_consecutive_losses=None, blind_forward_average_mfe_r=None,
                blind_forward_average_mae_r=None, blind_forward_average_holding_seconds=None,
                out_of_sample_degradation_r=None, baseline_expectancy_r=self.policy.baseline_expectancy_r,
                sensitivity_pass=False, overfitting_detected=False, drift_detected=False)
        train = self._metrics(phases["TRAIN"])
        validation = self._metrics(phases["VALIDATION"])
        blind = self._metrics(phases["BLIND_FORWARD"])
        degradation = train["expectancy"] - blind["expectancy"]
        drift = degradation > self.policy.maximum_expectancy_degradation_r
        overfit = train["expectancy"] > self.policy.baseline_expectancy_r and (
            validation["expectancy"] <= self.policy.baseline_expectancy_r
            or blind["expectancy"] <= self.policy.baseline_expectancy_r
        )
        sensitivity = validation["expectancy"] > self.policy.baseline_expectancy_r and blind["expectancy"] > self.policy.baseline_expectancy_r and abs(validation["expectancy"] - blind["expectancy"]) <= self.policy.maximum_expectancy_degradation_r
        robust = not drift and not overfit and sensitivity and blind["confidence_low"] > self.policy.baseline_expectancy_r
        reason = "walk_forward_robust" if robust else "out_of_sample_robustness_failed"
        return A22ValidationResult(
            result_id=result_id, partition=partition, status="ROBUST" if robust else "REJECTED", reason=reason,
            train_samples=counts["TRAIN"], validation_samples=counts["VALIDATION"],
            blind_forward_samples=counts["BLIND_FORWARD"], train_expectancy_r=train["expectancy"],
            validation_expectancy_r=validation["expectancy"], blind_forward_expectancy_r=blind["expectancy"],
            blind_forward_confidence_low_r=blind["confidence_low"],
            blind_forward_confidence_high_r=blind["confidence_high"],
            blind_forward_net_profit_r=blind["net_profit"],
            blind_forward_average_win_r=blind["average_win"],
            blind_forward_average_loss_r=blind["average_loss"],
            blind_forward_profit_factor=blind["profit_factor"],
            blind_forward_max_drawdown_r=blind["max_drawdown"], blind_forward_tail_loss_r=blind["tail_loss"],
            blind_forward_max_consecutive_losses=blind["max_consecutive_losses"],
            blind_forward_average_mfe_r=blind["average_mfe"], blind_forward_average_mae_r=blind["average_mae"],
            blind_forward_average_holding_seconds=blind["average_holding_seconds"],
            out_of_sample_degradation_r=degradation, baseline_expectancy_r=self.policy.baseline_expectancy_r,
            sensitivity_pass=sensitivity, overfitting_detected=overfit, drift_detected=drift)

    def _metrics(self, values: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(values, key=lambda item: _time(str(item["decision_timestamp_utc"])))
        returns = [float(item["net_realized_r"]) for item in ordered]
        expectancy = mean(returns)
        standard_error = pstdev(returns) / sqrt(len(returns))
        wins = sum(value for value in returns if value > 0)
        losses = abs(sum(value for value in returns if value < 0))
        win_values = [value for value in returns if value > 0]
        loss_values = [value for value in returns if value < 0]
        equity = peak = max_drawdown = 0.0
        consecutive = maximum_consecutive = 0
        for value in returns:
            equity += value; peak = max(peak, equity); max_drawdown = max(max_drawdown, peak - equity)
            consecutive = consecutive + 1 if value < 0 else 0
            maximum_consecutive = max(maximum_consecutive, consecutive)
        return {"expectancy": expectancy,
            "confidence_low": expectancy - self.policy.confidence_z * standard_error,
            "confidence_high": expectancy + self.policy.confidence_z * standard_error,
            "net_profit": sum(returns),
            "average_win": mean(win_values) if win_values else 0.0,
            "average_loss": mean(loss_values) if loss_values else 0.0,
            "profit_factor": None if losses == 0 else wins / losses,
            "max_drawdown": max_drawdown, "tail_loss": min(returns),
            "max_consecutive_losses": maximum_consecutive,
            "average_mfe": mean(float(item["mfe_r"]) for item in ordered),
            "average_mae": mean(float(item["mae_r"]) for item in ordered),
            "average_holding_seconds": mean(float(item["holding_seconds"]) for item in ordered)}
