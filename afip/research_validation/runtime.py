"""Milestone T Pack 6: robustness, walk-forward validation, and evidence gate.

The module is research-only. It validates quarantined exit-policy evidence across
chronological windows and deterministic stress scenarios. It never promotes a
policy automatically, never marks evidence production-usable, and never calls
MT5 or production execution services.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from statistics import mean, pstdev
from typing import Any, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _bounded(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _label(value: Any, fallback: str = "UNCLASSIFIED") -> str:
    normalized = str(value).strip().upper().replace(" ", "_")
    return normalized or fallback


@dataclass(frozen=True, order=True)
class WalkForwardWindow:
    window_id: str
    sequence: int
    train_start_index: int
    train_end_index: int
    validation_start_index: int
    validation_end_index: int
    forward_start_index: int
    forward_end_index: int

    def __post_init__(self) -> None:
        if not self.window_id.strip() or self.sequence <= 0:
            raise ValueError("window identifier and positive sequence are required")
        values = (
            self.train_start_index, self.train_end_index,
            self.validation_start_index, self.validation_end_index,
            self.forward_start_index, self.forward_end_index,
        )
        if any(value < 0 for value in values):
            raise ValueError("walk-forward indexes cannot be negative")
        if not (
            self.train_start_index <= self.train_end_index
            < self.validation_start_index <= self.validation_end_index
            < self.forward_start_index <= self.forward_end_index
        ):
            raise ValueError("walk-forward windows must be chronological and non-overlapping")

    @property
    def train_size(self) -> int:
        return self.train_end_index - self.train_start_index + 1

    @property
    def validation_size(self) -> int:
        return self.validation_end_index - self.validation_start_index + 1

    @property
    def forward_size(self) -> int:
        return self.forward_end_index - self.forward_start_index + 1

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationObservation:
    observation_id: str
    policy_id: str
    segment_id: str
    chronological_index: int
    realized_r: float
    exit_quality_score: float
    capital_preservation_score: float
    research_state: str = "EXPERIMENTAL"
    production_usable: bool = False

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.policy_id.strip() or not self.segment_id.strip():
            raise ValueError("observation, policy, and segment identifiers are required")
        if self.chronological_index < 0:
            raise ValueError("chronological_index cannot be negative")
        if not 0 <= self.exit_quality_score <= 100:
            raise ValueError("exit_quality_score must be between 0 and 100")
        if not 0 <= self.capital_preservation_score <= 100:
            raise ValueError("capital_preservation_score must be between 0 and 100")
        if self.research_state != "EXPERIMENTAL" or self.production_usable:
            raise ValueError("validation observations must remain experimental and quarantined")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ValidationObservation":
        return cls(
            observation_id=str(value["observation_id"]),
            policy_id=str(value["policy_id"]),
            segment_id=str(value["segment_id"]),
            chronological_index=int(value["chronological_index"]),
            realized_r=float(value["realized_r"]),
            exit_quality_score=float(value["exit_quality_score"]),
            capital_preservation_score=float(value["capital_preservation_score"]),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, order=True)
class RobustnessScenario:
    scenario_id: str
    spread_multiplier: float = 1.0
    slippage_r: float = 0.0
    volatility_multiplier: float = 1.0
    liquidity_penalty_r: float = 0.0
    session_penalty_r: float = 0.0
    gap_penalty_r: float = 0.0

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id is required")
        if self.spread_multiplier < 1.0 or self.volatility_multiplier <= 0:
            raise ValueError("scenario multipliers are invalid")
        if any(value < 0 for value in (
            self.slippage_r, self.liquidity_penalty_r,
            self.session_penalty_r, self.gap_penalty_r,
        )):
            raise ValueError("scenario penalties cannot be negative")

    @property
    def total_penalty_r(self) -> float:
        spread_penalty = (self.spread_multiplier - 1.0) * 0.10
        volatility_penalty = abs(self.volatility_multiplier - 1.0) * 0.08
        return (
            spread_penalty + volatility_penalty + self.slippage_r
            + self.liquidity_penalty_r + self.session_penalty_r + self.gap_penalty_r
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["total_penalty_r"] = self.total_penalty_r
        return payload


@dataclass(frozen=True)
class WalkForwardResult:
    run_id: str
    window_id: str
    policy_id: str
    segment_id: str
    train_sample_size: int
    validation_sample_size: int
    forward_sample_size: int
    train_average_realized_r: float
    validation_average_realized_r: float
    forward_average_realized_r: float
    forward_win_rate: float
    forward_exit_quality_score: float
    forward_capital_preservation_score: float
    validation_degradation_ratio: float
    forward_degradation_ratio: float
    temporal_stability_score: float
    no_future_leakage: bool
    validation_status: str
    research_state: str
    production_usable: bool
    result_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RobustnessResult:
    run_id: str
    policy_id: str
    segment_id: str
    scenario_id: str
    sample_size: int
    baseline_average_realized_r: float
    stressed_average_realized_r: float
    stressed_win_rate: float
    degradation_r: float
    resilience_score: float
    robustness_status: str
    research_state: str
    production_usable: bool
    result_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromotionEvidenceRecord:
    policy_id: str
    segment_id: str
    walk_forward_run_count: int
    robustness_scenario_count: int
    minimum_forward_sample_size: int
    total_forward_sample_size: int
    average_temporal_stability_score: float
    average_resilience_score: float
    positive_forward_ratio: float
    promotion_evidence_score: float
    evidence_stage: str
    promotion_evidence_eligible: bool
    eligibility_reasons: tuple[str, ...]
    human_approval_required: bool
    automatic_promotion_allowed: bool
    quarantine_status: str
    research_state: str
    production_usable: bool
    record_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchValidationPolicy:
    minimum_walk_forward_runs: int = 3
    minimum_robustness_scenarios: int = 4
    minimum_forward_sample_size: int = 30
    minimum_temporal_stability_score: float = 65.0
    minimum_resilience_score: float = 65.0
    minimum_positive_forward_ratio: float = 0.67
    minimum_promotion_evidence_score: float = 70.0

    def __post_init__(self) -> None:
        if min(
            self.minimum_walk_forward_runs,
            self.minimum_robustness_scenarios,
            self.minimum_forward_sample_size,
        ) <= 0:
            raise ValueError("research validation minimums must be positive")
        for value in (
            self.minimum_temporal_stability_score,
            self.minimum_resilience_score,
            self.minimum_promotion_evidence_score,
        ):
            if not 0 <= value <= 100:
                raise ValueError("research validation scores must be between 0 and 100")
        if not 0 <= self.minimum_positive_forward_ratio <= 1:
            raise ValueError("minimum_positive_forward_ratio must be between 0 and 1")


class ResearchValidationEngine:
    """Run chronological validation and deterministic stress evidence checks."""

    def __init__(
        self,
        dataset: AppendOnlyResearchDataset,
        *,
        policy: ResearchValidationPolicy | None = None,
    ) -> None:
        self.dataset = dataset
        self.policy = policy or ResearchValidationPolicy()

    @staticmethod
    def _select(
        observations: Sequence[ValidationObservation],
        *,
        policy_id: str,
        segment_id: str,
        start: int,
        end: int,
    ) -> list[ValidationObservation]:
        return [
            value for value in observations
            if value.policy_id == policy_id
            and value.segment_id == segment_id
            and start <= value.chronological_index <= end
        ]

    @staticmethod
    def _average(values: Sequence[ValidationObservation]) -> float:
        return mean(item.realized_r for item in values) if values else 0.0

    @staticmethod
    def _degradation(reference: float, candidate: float) -> float:
        denominator = max(abs(reference), 0.01)
        return max(0.0, (reference - candidate) / denominator)

    def run_walk_forward(
        self,
        *,
        run_id: str,
        window: WalkForwardWindow,
        observations: Iterable[ValidationObservation],
        policy_id: str,
        segment_id: str,
    ) -> WalkForwardResult:
        values = tuple(sorted(observations, key=lambda item: (item.chronological_index, item.observation_id)))
        if not run_id.strip():
            raise ValueError("run_id is required")
        identifiers = [item.observation_id for item in values]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("observation identifiers must be unique")
        train = self._select(values, policy_id=policy_id, segment_id=segment_id,
                             start=window.train_start_index, end=window.train_end_index)
        validation = self._select(values, policy_id=policy_id, segment_id=segment_id,
                                  start=window.validation_start_index, end=window.validation_end_index)
        forward = self._select(values, policy_id=policy_id, segment_id=segment_id,
                               start=window.forward_start_index, end=window.forward_end_index)
        if not train or not validation or not forward:
            raise ValueError("walk-forward train, validation, and forward phases require observations")
        train_average = self._average(train)
        validation_average = self._average(validation)
        forward_average = self._average(forward)
        validation_degradation = self._degradation(train_average, validation_average)
        forward_degradation = self._degradation(validation_average, forward_average)
        phase_dispersion = pstdev((train_average, validation_average, forward_average))
        temporal_stability = _bounded(
            100.0 - phase_dispersion * 30.0
            - validation_degradation * 20.0
            - forward_degradation * 25.0
        )
        status = "WALK_FORWARD_STABLE" if forward_average > 0 and temporal_stability >= 65 else "WALK_FORWARD_UNSTABLE"
        base = {
            "run_id": run_id,
            "window_id": window.window_id,
            "policy_id": policy_id,
            "segment_id": segment_id,
            "train_sample_size": len(train),
            "validation_sample_size": len(validation),
            "forward_sample_size": len(forward),
            "train_average_realized_r": train_average,
            "validation_average_realized_r": validation_average,
            "forward_average_realized_r": forward_average,
            "forward_win_rate": sum(item.realized_r > 0 for item in forward) / len(forward),
            "forward_exit_quality_score": mean(item.exit_quality_score for item in forward),
            "forward_capital_preservation_score": mean(item.capital_preservation_score for item in forward),
            "validation_degradation_ratio": validation_degradation,
            "forward_degradation_ratio": forward_degradation,
            "temporal_stability_score": temporal_stability,
            "no_future_leakage": True,
            "validation_status": status,
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        }
        result = WalkForwardResult(result_checksum=_checksum(base), **base)
        self.dataset.append("walk_forward_windows", {
            **window.as_dict(), "run_id": run_id,
            "research_state": "EXPERIMENTAL", "production_usable": False,
        })
        for phase, phase_values in (("TRAIN", train), ("VALIDATION", validation), ("FORWARD", forward)):
            for item in phase_values:
                self.dataset.append("walk_forward_observations", {
                    **item.as_dict(), "run_id": run_id, "window_id": window.window_id,
                    "validation_phase": phase,
                })
        self.dataset.append("walk_forward_results", result.as_dict())
        return result

    def run_robustness(
        self,
        *,
        run_id: str,
        observations: Iterable[ValidationObservation],
        policy_id: str,
        segment_id: str,
        scenarios: Iterable[RobustnessScenario],
    ) -> tuple[RobustnessResult, ...]:
        values = tuple(
            item for item in observations
            if item.policy_id == policy_id and item.segment_id == segment_id
        )
        scenario_values = tuple(sorted(scenarios, key=lambda item: item.scenario_id))
        if not values:
            raise ValueError("robustness evaluation requires observations")
        if not scenario_values:
            raise ValueError("robustness evaluation requires scenarios")
        if len({item.scenario_id for item in scenario_values}) != len(scenario_values):
            raise ValueError("scenario identifiers must be unique")
        baseline = mean(item.realized_r for item in values)
        results: list[RobustnessResult] = []
        for scenario in scenario_values:
            stressed = [item.realized_r - scenario.total_penalty_r for item in values]
            stressed_average = mean(stressed)
            degradation = max(0.0, baseline - stressed_average)
            resilience = _bounded(
                100.0 - scenario.total_penalty_r * 45.0
                - max(0.0, -stressed_average) * 30.0
            )
            status = "ROBUSTNESS_RETAINED" if stressed_average > 0 and resilience >= 65 else "ROBUSTNESS_DEGRADED"
            base = {
                "run_id": run_id,
                "policy_id": policy_id,
                "segment_id": segment_id,
                "scenario_id": scenario.scenario_id,
                "sample_size": len(values),
                "baseline_average_realized_r": baseline,
                "stressed_average_realized_r": stressed_average,
                "stressed_win_rate": sum(value > 0 for value in stressed) / len(stressed),
                "degradation_r": degradation,
                "resilience_score": resilience,
                "robustness_status": status,
                "research_state": "EXPERIMENTAL",
                "production_usable": False,
            }
            result = RobustnessResult(result_checksum=_checksum(base), **base)
            self.dataset.append("robustness_scenarios", {
                **scenario.as_dict(), "run_id": run_id,
                "research_state": "EXPERIMENTAL", "production_usable": False,
            })
            self.dataset.append("robustness_results", result.as_dict())
            results.append(result)
        return tuple(results)

    def evaluate_promotion_evidence(
        self,
        *,
        policy_id: str,
        segment_id: str,
        walk_forward_results: Iterable[WalkForwardResult],
        robustness_results: Iterable[RobustnessResult],
    ) -> PromotionEvidenceRecord:
        walk_values = tuple(
            item for item in walk_forward_results
            if item.policy_id == policy_id and item.segment_id == segment_id
        )
        robustness_values = tuple(
            item for item in robustness_results
            if item.policy_id == policy_id and item.segment_id == segment_id
        )
        total_forward = sum(item.forward_sample_size for item in walk_values)
        average_stability = mean(item.temporal_stability_score for item in walk_values) if walk_values else 0.0
        average_resilience = mean(item.resilience_score for item in robustness_values) if robustness_values else 0.0
        positive_forward_ratio = (
            sum(item.forward_average_realized_r > 0 for item in walk_values) / len(walk_values)
            if walk_values else 0.0
        )
        sample_component = _bounded(total_forward / self.policy.minimum_forward_sample_size * 100.0)
        run_component = _bounded(len(walk_values) / self.policy.minimum_walk_forward_runs * 100.0)
        scenario_component = _bounded(len(robustness_values) / self.policy.minimum_robustness_scenarios * 100.0)
        evidence_score = _bounded(
            average_stability * 0.25
            + average_resilience * 0.25
            + positive_forward_ratio * 100.0 * 0.20
            + sample_component * 0.15
            + run_component * 0.075
            + scenario_component * 0.075
        )
        reasons: list[str] = []
        if len(walk_values) < self.policy.minimum_walk_forward_runs:
            reasons.append("minimum_walk_forward_runs_not_met")
        if len(robustness_values) < self.policy.minimum_robustness_scenarios:
            reasons.append("minimum_robustness_scenarios_not_met")
        if total_forward < self.policy.minimum_forward_sample_size:
            reasons.append("minimum_forward_sample_size_not_met")
        if average_stability < self.policy.minimum_temporal_stability_score:
            reasons.append("temporal_stability_below_threshold")
        if average_resilience < self.policy.minimum_resilience_score:
            reasons.append("resilience_below_threshold")
        if positive_forward_ratio < self.policy.minimum_positive_forward_ratio:
            reasons.append("positive_forward_ratio_below_threshold")
        if evidence_score < self.policy.minimum_promotion_evidence_score:
            reasons.append("promotion_evidence_score_below_threshold")
        eligible = not reasons
        stage = "PROMOTION_CANDIDATE_RESEARCH_ONLY" if eligible else "RESEARCH_VALIDATION_REQUIRED"
        base = {
            "policy_id": policy_id,
            "segment_id": segment_id,
            "walk_forward_run_count": len(walk_values),
            "robustness_scenario_count": len(robustness_values),
            "minimum_forward_sample_size": self.policy.minimum_forward_sample_size,
            "total_forward_sample_size": total_forward,
            "average_temporal_stability_score": average_stability,
            "average_resilience_score": average_resilience,
            "positive_forward_ratio": positive_forward_ratio,
            "promotion_evidence_score": evidence_score,
            "evidence_stage": stage,
            "promotion_evidence_eligible": eligible,
            "eligibility_reasons": tuple(reasons or ("research_promotion_evidence_thresholds_met",)),
            "human_approval_required": True,
            "automatic_promotion_allowed": False,
            "quarantine_status": "RESEARCH_QUARANTINE",
            "research_state": "EXPERIMENTAL",
            "production_usable": False,
        }
        record = PromotionEvidenceRecord(record_checksum=_checksum(base), **base)
        self.dataset.append("promotion_evidence_records", record.as_dict())
        return record

    def dashboard_metadata(self) -> dict[str, Any]:
        names = (
            "walk_forward_windows", "walk_forward_observations", "walk_forward_results",
            "robustness_scenarios", "robustness_results", "promotion_evidence_records",
        )
        records = self.dataset.records("promotion_evidence_records")
        latest = records[-1]["record"] if records else None
        return {
            "research_validation_state": "EXPERIMENTAL",
            "quarantine_status": "RESEARCH_QUARANTINE",
            "production_usable": False,
            "automatic_promotion_allowed": False,
            "dataset_counts": {name: self.dataset.count(name) for name in names},
            "latest_promotion_evidence": latest,
        }
