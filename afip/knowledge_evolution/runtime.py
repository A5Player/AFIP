"""Deterministic, execution-neutral knowledge evolution for AFIP research.

The engine converts research leaderboard evidence into candidate knowledge.
It never edits trading policy, profile configuration, risk limits, or execution.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable, Mapping, Sequence


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def deterministic_hash(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EvidenceSnapshot:
    snapshot_id: str
    observed_at_utc: str
    group_key: str
    dimensions: Mapping[str, Any]
    sample_count: int
    expectancy_points: float
    confidence_interval_95_low: float
    confidence_interval_95_high: float
    win_rate: float
    stability_score: float
    ranking_score: float
    eligible_for_ranking: bool
    source_report_id: str

    def validate(self) -> None:
        if not self.snapshot_id or not self.group_key or not self.source_report_id:
            raise ValueError("snapshot identity is required")
        if self.sample_count < 0:
            raise ValueError("sample_count cannot be negative")
        if self.confidence_interval_95_low > self.confidence_interval_95_high:
            raise ValueError("confidence interval is invalid")
        if not 0 <= self.win_rate <= 100 or not 0 <= self.stability_score <= 100:
            raise ValueError("percentage metric is invalid")


@dataclass(frozen=True)
class KnowledgeCandidate:
    schema_version: str
    candidate_id: str
    hypothesis_key: str
    dimensions: Mapping[str, Any]
    evidence_snapshot_count: int
    total_samples: int
    latest_expectancy_points: float
    weighted_expectancy_points: float
    latest_confidence_interval_low: float
    latest_stability_score: float
    evidence_consistency_score: float
    recency_drift_score: float
    knowledge_confidence_score: float
    lifecycle_status: str
    status_reasons: tuple[str, ...]
    source_snapshot_ids: tuple[str, ...]
    execution_authority: str
    promotion_to_execution: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeEvolutionReport:
    schema_version: str
    report_id: str
    generated_from_snapshots: int
    candidates: tuple[KnowledgeCandidate, ...]
    execution_authority: str
    promotion_to_execution: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KnowledgeEvolutionEngine:
    """Build conservative candidate knowledge from time-ordered evidence."""

    def __init__(self, minimum_snapshots: int = 3, minimum_total_samples: int = 100,
                 minimum_confidence_score: float = 70.0, drift_warning_threshold: float = 35.0):
        if minimum_snapshots <= 0 or minimum_total_samples <= 0:
            raise ValueError("minimum evidence requirements must be positive")
        if not 0 <= minimum_confidence_score <= 100 or not 0 <= drift_warning_threshold <= 100:
            raise ValueError("score thresholds must be between 0 and 100")
        self.minimum_snapshots = minimum_snapshots
        self.minimum_total_samples = minimum_total_samples
        self.minimum_confidence_score = minimum_confidence_score
        self.drift_warning_threshold = drift_warning_threshold

    def evolve(self, snapshots: Sequence[EvidenceSnapshot]) -> KnowledgeEvolutionReport:
        unique: dict[str, EvidenceSnapshot] = {}
        for item in snapshots:
            item.validate()
            unique.setdefault(deterministic_hash(asdict(item)), item)
        groups: dict[str, list[EvidenceSnapshot]] = {}
        for item in unique.values():
            groups.setdefault(item.group_key, []).append(item)
        candidates = []
        for group_key, members in groups.items():
            ordered = sorted(members, key=lambda x: (x.observed_at_utc, x.snapshot_id))
            candidates.append(self._candidate(group_key, ordered))
        candidates.sort(key=lambda x: (-x.knowledge_confidence_score, x.hypothesis_key, x.candidate_id))
        stable = {
            "snapshots": [asdict(x) for x in sorted(unique.values(), key=lambda x: (x.group_key, x.observed_at_utc, x.snapshot_id))],
            "candidates": [x.to_dict() for x in candidates],
            "execution_authority": "NONE",
            "promotion_to_execution": "PROHIBITED",
        }
        return KnowledgeEvolutionReport("knowledge-evolution-report.v1", deterministic_hash(stable), len(unique), tuple(candidates), "NONE", "PROHIBITED")

    def _candidate(self, group_key: str, ordered: Sequence[EvidenceSnapshot]) -> KnowledgeCandidate:
        latest = ordered[-1]
        total_samples = sum(x.sample_count for x in ordered)
        weights = [max(1, x.sample_count) for x in ordered]
        weighted_expectancy = sum(x.expectancy_points*w for x,w in zip(ordered,weights))/sum(weights)
        signs = [1 if x.expectancy_points > 0 else -1 if x.expectancy_points < 0 else 0 for x in ordered]
        majority = max(signs.count(-1), signs.count(0), signs.count(1)) / len(signs)
        ci_positive_ratio = sum(x.confidence_interval_95_low > 0 for x in ordered) / len(ordered)
        eligible_ratio = sum(x.eligible_for_ranking for x in ordered) / len(ordered)
        consistency = max(0.0, min(100.0, 100.0*(0.45*majority + 0.35*ci_positive_ratio + 0.20*eligible_ratio)))
        first = ordered[0].expectancy_points
        scale = max(abs(first), abs(latest.expectancy_points), 1.0)
        drift = min(100.0, abs(latest.expectancy_points-first)/scale*100.0)
        sample_score = min(100.0, total_samples/self.minimum_total_samples*100.0)
        history_score = min(100.0, len(ordered)/self.minimum_snapshots*100.0)
        confidence = max(0.0, min(100.0,
            0.25*sample_score + 0.15*history_score + 0.25*consistency +
            0.20*latest.stability_score + 0.15*max(0.0, 100.0-drift)))
        reasons=[]
        if len(ordered) < self.minimum_snapshots: reasons.append("MINIMUM_SNAPSHOTS_NOT_MET")
        if total_samples < self.minimum_total_samples: reasons.append("MINIMUM_TOTAL_SAMPLES_NOT_MET")
        if latest.confidence_interval_95_low <= 0: reasons.append("LATEST_CONFIDENCE_INTERVAL_NOT_POSITIVE")
        if not latest.eligible_for_ranking: reasons.append("LATEST_EVIDENCE_NOT_RANKING_ELIGIBLE")
        if drift >= self.drift_warning_threshold: reasons.append("RECENCY_DRIFT_WARNING")
        if confidence < self.minimum_confidence_score: reasons.append("KNOWLEDGE_CONFIDENCE_BELOW_THRESHOLD")
        if "LATEST_CONFIDENCE_INTERVAL_NOT_POSITIVE" in reasons or "LATEST_EVIDENCE_NOT_RANKING_ELIGIBLE" in reasons:
            status="REJECTED"
        elif reasons:
            status="CANDIDATE"
        else:
            status="RESEARCH_CERTIFIED"
        stable={"group_key":group_key,"dimensions":dict(latest.dimensions),"source_snapshot_ids":[x.snapshot_id for x in ordered]}
        return KnowledgeCandidate(
            "knowledge-candidate.v1", deterministic_hash(stable), group_key, dict(latest.dimensions), len(ordered), total_samples,
            round(latest.expectancy_points,8), round(weighted_expectancy,8), round(latest.confidence_interval_95_low,8),
            round(latest.stability_score,8), round(consistency,8), round(drift,8), round(confidence,8), status,
            tuple(reasons), tuple(x.snapshot_id for x in ordered), "NONE", "PROHIBITED")


def snapshots_from_leaderboard_report(report: Mapping[str, Any], observed_at_utc: str) -> tuple[EvidenceSnapshot, ...]:
    if str(report.get("execution_authority")) != "NONE":
        raise ValueError("leaderboard report must have execution_authority NONE")
    if str(report.get("promotion_to_execution")) != "PROHIBITED":
        raise ValueError("leaderboard report must prohibit execution promotion")
    report_id=str(report["report_id"])
    output=[]
    for row in report.get("ranked_rows", ()):
        metrics=row["metrics"]
        dimensions=dict(row.get("group_values", {}))
        group_key=canonical_json(dimensions)
        stable={"source_report_id":report_id,"observed_at_utc":observed_at_utc,"group_key":group_key,"metrics":metrics}
        output.append(EvidenceSnapshot(
            deterministic_hash(stable), observed_at_utc, group_key, dimensions, int(metrics["sample_count"]),
            float(metrics["expectancy_points"]), float(metrics["confidence_interval_95_low"]),
            float(metrics["confidence_interval_95_high"]), float(metrics["win_rate"]),
            float(metrics["stability_score"]), float(row["ranking_score"]), bool(row["eligible_for_ranking"]), report_id))
    return tuple(output)


def load_snapshots_from_json(paths: Iterable[str | Path]) -> tuple[EvidenceSnapshot, ...]:
    output=[]
    for path in sorted(Path(x) for x in paths):
        value=json.loads(path.read_text(encoding="utf-8"))
        output.extend(snapshots_from_leaderboard_report(value, str(value.get("generated_at_utc", path.stem))))
    return tuple(output)


def write_report(report: KnowledgeEvolutionReport, path: str | Path) -> str:
    target=Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    payload=canonical_json(report.to_dict())+"\n"
    target.write_text(payload, encoding="utf-8", newline="\n")
    return sha256(payload.encode("utf-8")).hexdigest()
