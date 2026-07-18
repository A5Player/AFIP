"""Execution-neutral research metrics and deterministic leaderboards for AFIP.

This module reads blind-forward research outcomes and produces descriptive
statistics only.  It cannot promote a candidate into trading policy and has no
broker, order, profile, or execution authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Iterable, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def deterministic_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResearchObservation:
    result_id: str
    case_id: str
    candidate_set_id: str
    candidate_set_version: str
    take_profit_points: int
    stop_loss_points: int
    time_exit_bars: int | None
    result_points: float
    outcome: str
    exit_reason: str
    holding_bars: int
    holding_seconds: int
    maximum_favorable_excursion_points: float
    maximum_adverse_excursion_points: float
    market_regime: str = "UNKNOWN"
    pattern_family: str = "UNKNOWN"
    confidence_bucket: str = "UNKNOWN"
    direction: str = "UNKNOWN"
    timeframe: str = "UNKNOWN"

    def validate(self) -> None:
        if not self.result_id or not self.case_id:
            raise ValueError("result_id and case_id are required")
        if self.take_profit_points <= 0 or self.stop_loss_points <= 0:
            raise ValueError("TP and SL points must be positive")
        if self.time_exit_bars is not None and self.time_exit_bars <= 0:
            raise ValueError("time_exit_bars must be positive when supplied")
        if self.holding_bars <= 0 or self.holding_seconds < 0:
            raise ValueError("holding values are invalid")
        if self.outcome not in {"WIN", "LOSS", "FLAT"}:
            raise ValueError("outcome must be WIN, LOSS, or FLAT")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ResearchObservation":
        obj = cls(
            result_id=str(value["result_id"]), case_id=str(value["case_id"]),
            candidate_set_id=str(value.get("candidate_set_id", "UNKNOWN")),
            candidate_set_version=str(value.get("candidate_set_version", "UNKNOWN")),
            take_profit_points=int(value["take_profit_points"]),
            stop_loss_points=int(value["stop_loss_points"]),
            time_exit_bars=None if value.get("time_exit_bars") is None else int(value["time_exit_bars"]),
            result_points=float(value["result_points"]), outcome=str(value["outcome"]),
            exit_reason=str(value["exit_reason"]), holding_bars=int(value["holding_bars"]),
            holding_seconds=int(value["holding_seconds"]),
            maximum_favorable_excursion_points=float(value["maximum_favorable_excursion_points"]),
            maximum_adverse_excursion_points=float(value["maximum_adverse_excursion_points"]),
            market_regime=str(value.get("market_regime", "UNKNOWN") or "UNKNOWN"),
            pattern_family=str(value.get("pattern_family", "UNKNOWN") or "UNKNOWN"),
            confidence_bucket=str(value.get("confidence_bucket", "UNKNOWN") or "UNKNOWN"),
            direction=str(value.get("direction", "UNKNOWN") or "UNKNOWN"),
            timeframe=str(value.get("timeframe", "UNKNOWN") or "UNKNOWN"),
        )
        obj.validate()
        return obj


@dataclass(frozen=True)
class MetricSummary:
    sample_count: int
    win_count: int
    loss_count: int
    flat_count: int
    win_rate: float
    net_points: float
    average_points: float
    median_points: float
    standard_deviation_points: float
    downside_deviation_points: float
    gross_profit_points: float
    gross_loss_points: float
    profit_factor: float | None
    expectancy_points: float
    average_holding_bars: float
    average_holding_seconds: float
    average_mfe_points: float
    average_mae_points: float
    reward_to_adverse_ratio: float | None
    confidence_interval_95_low: float
    confidence_interval_95_high: float
    sharpe_like_score: float | None
    stability_score: float
    sample_sufficiency_score: float


@dataclass(frozen=True)
class LeaderboardRow:
    rank: int
    group_key: str
    group_values: Mapping[str, Any]
    metrics: MetricSummary
    ranking_score: float
    eligible_for_ranking: bool
    exclusion_reasons: tuple[str, ...]


@dataclass(frozen=True)
class LeaderboardReport:
    schema_version: str
    report_id: str
    leaderboard_name: str
    dimensions: tuple[str, ...]
    source_observation_count: int
    ranked_rows: tuple[LeaderboardRow, ...]
    execution_authority: str
    promotion_to_execution: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchMetricsEngine:
    """Calculate descriptive metrics without changing execution behaviour."""

    def summarize(self, observations: Sequence[ResearchObservation]) -> MetricSummary:
        if not observations:
            raise ValueError("at least one observation is required")
        for item in observations:
            item.validate()
        points = [x.result_points for x in observations]
        ordered = sorted(points)
        n = len(points)
        median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
        mean = fmean(points)
        std = pstdev(points) if n > 1 else 0.0
        negatives = [min(x, 0.0) for x in points]
        downside = math.sqrt(fmean([x * x for x in negatives]))
        gross_profit = sum(x for x in points if x > 0)
        gross_loss_abs = abs(sum(x for x in points if x < 0))
        profit_factor = None if gross_loss_abs == 0 else gross_profit / gross_loss_abs
        stderr = std / math.sqrt(n) if n else 0.0
        ci = 1.96 * stderr
        avg_mae = fmean(x.maximum_adverse_excursion_points for x in observations)
        avg_mfe = fmean(x.maximum_favorable_excursion_points for x in observations)
        reward_adverse = None if avg_mae == 0 else avg_mfe / avg_mae
        sharpe_like = None if std == 0 else mean / std * math.sqrt(n)
        positive_ratio = sum(1 for x in points if x > 0) / n
        dispersion_penalty = 1.0 / (1.0 + (std / (abs(mean) + 1.0)))
        balance = 1.0 - abs(0.5 - positive_ratio) * 0.25
        stability = max(0.0, min(100.0, 100.0 * dispersion_penalty * balance))
        sufficiency = min(100.0, n / 100.0 * 100.0)
        return MetricSummary(
            sample_count=n, win_count=sum(x.outcome == "WIN" for x in observations),
            loss_count=sum(x.outcome == "LOSS" for x in observations),
            flat_count=sum(x.outcome == "FLAT" for x in observations),
            win_rate=round(sum(x.outcome == "WIN" for x in observations) / n * 100.0, 8),
            net_points=round(sum(points), 8), average_points=round(mean, 8),
            median_points=round(median, 8), standard_deviation_points=round(std, 8),
            downside_deviation_points=round(downside, 8), gross_profit_points=round(gross_profit, 8),
            gross_loss_points=round(gross_loss_abs, 8),
            profit_factor=None if profit_factor is None else round(profit_factor, 8),
            expectancy_points=round(mean, 8),
            average_holding_bars=round(fmean(x.holding_bars for x in observations), 8),
            average_holding_seconds=round(fmean(x.holding_seconds for x in observations), 8),
            average_mfe_points=round(avg_mfe, 8), average_mae_points=round(avg_mae, 8),
            reward_to_adverse_ratio=None if reward_adverse is None else round(reward_adverse, 8),
            confidence_interval_95_low=round(mean-ci, 8), confidence_interval_95_high=round(mean+ci, 8),
            sharpe_like_score=None if sharpe_like is None else round(sharpe_like, 8),
            stability_score=round(stability, 8), sample_sufficiency_score=round(sufficiency, 8),
        )


class ResearchLeaderboardEngine:
    ALLOWED_DIMENSIONS = {
        "take_profit_points", "stop_loss_points", "time_exit_bars", "market_regime",
        "pattern_family", "confidence_bucket", "direction", "timeframe", "exit_reason",
    }

    def __init__(self, minimum_samples: int = 30):
        if minimum_samples <= 0:
            raise ValueError("minimum_samples must be positive")
        self.minimum_samples = minimum_samples
        self.metrics = ResearchMetricsEngine()

    def build(self, leaderboard_name: str, observations: Sequence[ResearchObservation], dimensions: Sequence[str]) -> LeaderboardReport:
        dims = tuple(dimensions)
        if not leaderboard_name or not dims:
            raise ValueError("leaderboard name and dimensions are required")
        invalid = set(dims) - self.ALLOWED_DIMENSIONS
        if invalid:
            raise ValueError(f"unsupported dimensions: {sorted(invalid)}")
        unique: dict[str, ResearchObservation] = {}
        for item in observations:
            item.validate()
            identity = deterministic_hash(asdict(item))
            unique.setdefault(identity, item)
        groups: dict[tuple[Any, ...], list[ResearchObservation]] = {}
        for item in unique.values():
            key = tuple(getattr(item, d) for d in dims)
            groups.setdefault(key, []).append(item)
        rows=[]
        for key, members in groups.items():
            metric = self.metrics.summarize(members)
            reasons=[]
            if metric.sample_count < self.minimum_samples:
                reasons.append("MINIMUM_SAMPLE_NOT_MET")
            if metric.confidence_interval_95_low <= 0:
                reasons.append("CONFIDENCE_INTERVAL_NOT_POSITIVE")
            eligible=not reasons
            risk_adjusted = metric.sharpe_like_score or 0.0
            score = metric.expectancy_points * math.log1p(metric.sample_count) + risk_adjusted + metric.stability_score / 100.0
            group_values={dim:value for dim,value in zip(dims,key)}
            rows.append((eligible, score, canonical_json(group_values), group_values, metric, tuple(reasons)))
        rows.sort(key=lambda x: (-int(x[0]), -x[1], x[2]))
        ranked=tuple(LeaderboardRow(i, key, vals, metric, round(score,8), eligible, reasons)
                     for i,(eligible,score,key,vals,metric,reasons) in enumerate(rows,1))
        stable={"leaderboard_name":leaderboard_name,"dimensions":dims,"minimum_samples":self.minimum_samples,
                "observations":[asdict(x) for x in sorted(unique.values(), key=lambda x: deterministic_hash(asdict(x)))],
                "rows":[asdict(x) for x in ranked],"execution_authority":"NONE","promotion_to_execution":"PROHIBITED"}
        return LeaderboardReport("research-leaderboard.v1", deterministic_hash(stable), leaderboard_name,
                                 dims, len(unique), ranked, "NONE", "PROHIBITED")


def observations_from_blind_forward_result(result: Mapping[str, Any], dimensions: Mapping[str, Any] | None = None) -> tuple[ResearchObservation, ...]:
    if str(result.get("research_eligibility")) != "ELIGIBLE":
        return ()
    if str(result.get("execution_authority")) != "NONE":
        raise ValueError("research result must have execution_authority NONE")
    dimensions = dict(dimensions or {})
    base={"result_id":result["result_id"],"case_id":result["case_id"],
          "candidate_set_id":result.get("candidate_set_id","UNKNOWN"),
          "candidate_set_version":result.get("candidate_set_version","UNKNOWN"), **dimensions}
    return tuple(ResearchObservation.from_mapping({**base, **outcome}) for outcome in result.get("outcomes",()))


def load_observations_from_jsonl(paths: Iterable[str | Path], dimensions_by_case: Mapping[str, Mapping[str, Any]] | None = None) -> tuple[ResearchObservation, ...]:
    dimensions_by_case = dimensions_by_case or {}
    observations=[]
    for raw_path in sorted(Path(x) for x in paths):
        with raw_path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                result=json.loads(line)
                observations.extend(observations_from_blind_forward_result(result, dimensions_by_case.get(str(result.get("case_id")), {})))
    return tuple(observations)


def write_report(report: LeaderboardReport, path: str | Path) -> str:
    target=Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload=canonical_json(report.to_dict())+"\n"
    target.write_text(payload, encoding="utf-8", newline="\n")
    return sha256(payload.encode("utf-8")).hexdigest()
