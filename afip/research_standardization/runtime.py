"""Milestone T Pack 7: research-derived initial standards and context selection.

Validated research evidence can be declared an owner-approved initial standard and
selected deterministically for a matching market context. The module keeps full
lineage, versioning, rollback metadata, and evidence thresholds. It does not send
orders or call MT5. Runtime adapters may consume only ACTIVE standard manifests.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Iterator, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset


def _label(value: Any, fallback: str = "UNCLASSIFIED") -> str:
    text = str(value).strip().upper().replace(" ", "_")
    return text or fallback


def _checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class StandardContext:
    symbol_family: str
    market_regime: str
    market_structure: str
    liquidity_state: str
    trend_state: str
    volatility_state: str
    trading_session: str
    direction: str
    pattern_family: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not str(value).strip():
                raise ValueError(f"{name} is required")

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "StandardContext":
        return cls(**{field: _label(value.get(field, "ANY"), "ANY") for field in cls.__dataclass_fields__})

    @property
    def segment_id(self) -> str:
        return "|".join(_label(value, "ANY") for value in asdict(self).values())

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def match_score(self, actual: "StandardContext") -> float:
        expected = asdict(self)
        observed = asdict(actual)
        matched = 0.0
        possible = 0.0
        weights = {
            "symbol_family": 2.0, "market_regime": 2.0, "market_structure": 1.5,
            "liquidity_state": 1.0, "trend_state": 1.5, "volatility_state": 1.0,
            "trading_session": 0.5, "direction": 1.5, "pattern_family": 2.0,
        }
        for field, weight in weights.items():
            target = _label(expected[field], "ANY")
            value = _label(observed[field], "ANY")
            if target == "ANY":
                continue
            possible += weight
            if target == value:
                matched += weight
            else:
                return 0.0
        return 100.0 if possible == 0 else round(matched / possible * 100.0, 2)


@dataclass(frozen=True)
class ResearchLineage:
    policy_id: str
    policy_version: str
    evidence_record_checksum: str
    source_dataset_checksums: tuple[str, ...]
    walk_forward_run_count: int
    robustness_scenario_count: int
    total_forward_sample_size: int
    historical_start: str
    historical_end: str
    source_instruments: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.policy_id.strip() or not self.policy_version.strip():
            raise ValueError("policy id and version are required")
        if not self.evidence_record_checksum.strip() or not self.source_dataset_checksums:
            raise ValueError("complete evidence lineage is required")
        if min(self.walk_forward_run_count, self.robustness_scenario_count, self.total_forward_sample_size) <= 0:
            raise ValueError("lineage evidence counts must be positive")
        if not self.historical_start or not self.historical_end or self.historical_start > self.historical_end:
            raise ValueError("valid historical coverage is required")
        if not self.source_instruments:
            raise ValueError("at least one source instrument is required")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InitialStandardPolicy:
    standard_id: str
    standard_version: str
    context: StandardContext
    policy_id: str
    policy_parameters: Mapping[str, Any]
    lineage: ResearchLineage
    evidence_score: float
    temporal_stability_score: float
    resilience_score: float
    owner_approved: bool
    approval_reference: str
    status: str = "ACTIVE"
    standard_class: str = "RESEARCH_DERIVED_INITIAL_STANDARD"
    production_usable: bool = True
    automatic_order_execution_allowed: bool = False
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.standard_id.strip() or not self.standard_version.strip():
            raise ValueError("standard id and version are required")
        if self.status not in {"DRAFT", "ACTIVE", "SUPERSEDED", "REVOKED"}:
            raise ValueError("invalid standard status")
        for score in (self.evidence_score, self.temporal_stability_score, self.resilience_score):
            if not 0 <= score <= 100:
                raise ValueError("standard scores must be between 0 and 100")
        if self.status == "ACTIVE" and (not self.owner_approved or not self.approval_reference.strip()):
            raise ValueError("active initial standards require explicit owner approval")
        if self.automatic_order_execution_allowed:
            raise ValueError("this registry cannot authorize automatic order execution")
        if not self.policy_parameters:
            raise ValueError("policy parameters are required")

    @property
    def standard_checksum(self) -> str:
        payload = self.as_dict(include_checksum=False)
        return _checksum(payload)

    def as_dict(self, *, include_checksum: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        payload["context"] = self.context.as_dict()
        payload["lineage"] = self.lineage.as_dict()
        payload["created_at"] = self.created_at or _utc_now()
        if include_checksum:
            payload["standard_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class StandardSelection:
    selection_id: str
    actual_context: StandardContext
    selected_standard_id: str | None
    selected_standard_version: str | None
    selected_policy_id: str | None
    selected_parameters: Mapping[str, Any]
    context_match_score: float
    selection_status: str
    reason: str
    evidence_checksum: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalCoverageRequest:
    request_id: str
    instrument: str
    symbol_family: str
    timeframes: tuple[str, ...]
    earliest_available_required: bool = True
    end_at_latest_closed_bar: bool = True
    include_related_market_context: bool = True
    priority: int = 100

    def __post_init__(self) -> None:
        if not self.request_id.strip() or not self.instrument.strip() or not self.symbol_family.strip():
            raise ValueError("coverage request identifiers are required")
        if not self.timeframes or self.priority <= 0:
            raise ValueError("timeframes and positive priority are required")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalCoveragePlan:
    plan_id: str
    requests: tuple[HistoricalCoverageRequest, ...]
    no_future_leakage_required: bool = True
    append_only_required: bool = True
    deduplication_required: bool = True
    provenance_required: bool = True

    def __post_init__(self) -> None:
        if not self.plan_id.strip() or not self.requests:
            raise ValueError("coverage plan and requests are required")
        identifiers = [item.request_id for item in self.requests]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("coverage request identifiers must be unique")

    @property
    def plan_checksum(self) -> str:
        return _checksum(self.as_dict(include_checksum=False))

    def as_dict(self, *, include_checksum: bool = True) -> dict[str, Any]:
        payload = asdict(self)
        payload["requests"] = [item.as_dict() for item in self.requests]
        if include_checksum:
            payload["plan_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class StandardizationPolicy:
    minimum_evidence_score: float = 70.0
    minimum_temporal_stability_score: float = 65.0
    minimum_resilience_score: float = 65.0
    minimum_context_match_score: float = 100.0
    require_owner_approval: bool = True
    allow_research_derived_initial_standard: bool = True
    require_complete_lineage: bool = True


@dataclass(frozen=True)
class ATRBufferCandidate:
    """One auditable ATR/buffer formula candidate.

    Operators are explicit so `ATR - buffer` is never confused with a negative
    buffer.  Resolved distances are positive point values suitable for the
    existing blind-forward research engine.
    """

    sl_atr_multiplier: float
    sl_buffer_points: int
    sl_operator: str
    tp_atr_multiplier: float
    tp_buffer_points: int
    tp_operator: str

    def __post_init__(self) -> None:
        if self.sl_atr_multiplier <= 0 or self.tp_atr_multiplier <= 0:
            raise ValueError("ATR multipliers must be positive")
        if self.sl_buffer_points < 0 or self.tp_buffer_points < 0:
            raise ValueError("buffer points cannot be negative")
        if self.sl_operator not in {"PLUS", "MINUS"} or self.tp_operator not in {"PLUS", "MINUS"}:
            raise ValueError("ATR buffer operators must be PLUS or MINUS")

    @property
    def candidate_id(self) -> str:
        return "ATRBUF-" + _checksum(asdict(self))[:20].upper()

    @staticmethod
    def _distance(atr_points: float, multiplier: float, buffer_points: int, operator: str) -> float:
        base = float(atr_points) * float(multiplier)
        value = base + buffer_points if operator == "PLUS" else base - buffer_points
        return round(value, 8)

    def resolve(self, atr_points: float) -> tuple[float, float]:
        if not math.isfinite(float(atr_points)) or float(atr_points) <= 0:
            raise ValueError("ATR points must be finite and positive")
        stop = self._distance(atr_points, self.sl_atr_multiplier, self.sl_buffer_points, self.sl_operator)
        target = self._distance(atr_points, self.tp_atr_multiplier, self.tp_buffer_points, self.tp_operator)
        if stop <= 0 or target <= 0:
            raise ValueError("resolved ATR/buffer distances must be positive")
        return stop, target

    def as_dict(self) -> dict[str, Any]:
        return {"candidate_id": self.candidate_id, **asdict(self)}


@dataclass(frozen=True)
class ATRBufferCandidateGrid:
    """Lazily enumerate every configured point unit without materializing it."""

    minimum_buffer_points: int
    maximum_buffer_points: int
    unit_step_points: int = 1
    sl_atr_multipliers: tuple[float, ...] = (1.0,)
    tp_atr_multipliers: tuple[float, ...] = (1.0,)
    sl_operators: tuple[str, ...] = ("PLUS",)
    tp_operators: tuple[str, ...] = ("PLUS", "MINUS")

    def __post_init__(self) -> None:
        if self.minimum_buffer_points < 0 or self.maximum_buffer_points < self.minimum_buffer_points:
            raise ValueError("invalid ATR buffer range")
        if self.unit_step_points <= 0:
            raise ValueError("unit step must be positive")
        if not self.sl_atr_multipliers or not self.tp_atr_multipliers:
            raise ValueError("ATR multiplier grids cannot be empty")
        if not self.sl_operators or not self.tp_operators:
            raise ValueError("ATR operator grids cannot be empty")

    @property
    def buffer_values(self) -> range:
        return range(self.minimum_buffer_points, self.maximum_buffer_points + 1, self.unit_step_points)

    @property
    def candidate_count(self) -> int:
        values = len(self.buffer_values)
        return (
            values * len(self.sl_atr_multipliers) * len(self.sl_operators)
            * values * len(self.tp_atr_multipliers) * len(self.tp_operators)
        )

    def iter_candidates(self) -> Iterator[ATRBufferCandidate]:
        for sl_multiplier in self.sl_atr_multipliers:
            for sl_operator in self.sl_operators:
                for sl_buffer in self.buffer_values:
                    for tp_multiplier in self.tp_atr_multipliers:
                        for tp_operator in self.tp_operators:
                            for tp_buffer in self.buffer_values:
                                yield ATRBufferCandidate(
                                    sl_multiplier, sl_buffer, sl_operator,
                                    tp_multiplier, tp_buffer, tp_operator,
                                )

    def iter_candidate_chunks(self, maximum_chunk_size: int = 5000) -> Iterator[tuple[ATRBufferCandidate, ...]]:
        if maximum_chunk_size <= 0:
            raise ValueError("maximum chunk size must be positive")
        chunk: list[ATRBufferCandidate] = []
        for candidate in self.iter_candidates():
            chunk.append(candidate)
            if len(chunk) >= maximum_chunk_size:
                yield tuple(chunk)
                chunk = []
        if chunk:
            yield tuple(chunk)


@dataclass(frozen=True)
class PatternResearchIdentity:
    """Exact chart-pattern and market-context partition used by research.

    ``pattern_id`` identifies one observed occurrence.  This identity groups
    occurrences only when their chart taxonomy and decision context are the
    same.  Cross-market evidence remains a separate ranking component so it
    cannot silently merge unlike chart patterns.
    """

    symbol: str
    timeframe: str
    pattern_family: str
    pattern_name: str
    pattern_variant: str
    direction: str
    market_regime: str
    trend_state: str
    momentum_state: str
    volatility_state: str
    trading_session: str
    liquidity_state: str
    multi_timeframe_context: str
    entry_plan: str
    management_plan: str
    exit_plan: str

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not str(value).strip():
                raise ValueError(f"{name} is required for exact pattern research")

    def as_dict(self) -> dict[str, str]:
        return {name: _label(value) for name, value in asdict(self).items()}

    @property
    def graph_key(self) -> str:
        values = self.as_dict()
        fields = (
            "symbol", "timeframe", "pattern_family", "pattern_name",
            "pattern_variant", "direction",
        )
        return "|".join(values[field] for field in fields)

    @property
    def research_key(self) -> str:
        values = self.as_dict()
        return "|".join(values[field] for field in self.__dataclass_fields__)

    def context_match_score(self, other: "PatternResearchIdentity") -> float:
        if self.graph_key != other.graph_key:
            return 0.0
        first = self.as_dict()
        second = other.as_dict()
        fields = (
            "market_regime", "trend_state", "momentum_state",
            "volatility_state", "trading_session", "liquidity_state",
            "multi_timeframe_context", "entry_plan", "management_plan",
            "exit_plan",
        )
        return round(sum(first[field] == second[field] for field in fields) / len(fields) * 100.0, 8)


@dataclass(frozen=True)
class PatternShapeSignature:
    """Normalized geometry for distinguishing variants of one named chart pattern."""

    candle_count: int
    duration_seconds: int
    average_body_ratio: float
    upper_wick_ratio: float
    lower_wick_ratio: float
    pullback_depth_atr: float
    total_range_atr: float
    slope_strength: float
    feature_schema_version: str = "PATTERN_SHAPE_V1"

    def __post_init__(self) -> None:
        if self.candle_count <= 0 or self.duration_seconds <= 0:
            raise ValueError("pattern duration and candle count must be positive")
        for name in ("average_body_ratio", "upper_wick_ratio", "lower_wick_ratio"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between zero and one")
        for name in ("pullback_depth_atr", "total_range_atr", "slope_strength"):
            value = float(getattr(self, name))
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if not self.feature_schema_version.strip():
            raise ValueError("shape feature schema version is required")

    @staticmethod
    def _bucket(value: float, first: float, second: float, labels: tuple[str, str, str]) -> str:
        return labels[0] if value < first else labels[1] if value < second else labels[2]

    @property
    def bucket_key(self) -> str:
        duration = "SHORT" if self.candle_count <= 3 else "MEDIUM" if self.candle_count <= 8 else "LONG"
        body = self._bucket(self.average_body_ratio, 0.33, 0.67, ("SMALL_BODY", "MEDIUM_BODY", "LARGE_BODY"))
        upper = self._bucket(self.upper_wick_ratio, 0.20, 0.50, ("SHORT_UW", "MEDIUM_UW", "LONG_UW"))
        lower = self._bucket(self.lower_wick_ratio, 0.20, 0.50, ("SHORT_LW", "MEDIUM_LW", "LONG_LW"))
        pullback = self._bucket(self.pullback_depth_atr, 0.50, 1.00, ("SHALLOW_PULLBACK", "NORMAL_PULLBACK", "DEEP_PULLBACK"))
        range_class = self._bucket(self.total_range_atr, 0.75, 1.50, ("NARROW_RANGE", "NORMAL_RANGE", "WIDE_RANGE"))
        slope = self._bucket(self.slope_strength, 0.33, 0.67, ("LOW_SLOPE", "MEDIUM_SLOPE", "HIGH_SLOPE"))
        return "|".join((self.feature_schema_version.upper(), duration, body, upper, lower, pullback, range_class, slope))

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "shape_bucket_key": self.bucket_key}

    def similarity_score(self, other: "PatternShapeSignature") -> float:
        if self.feature_schema_version.upper() != other.feature_schema_version.upper():
            return 0.0
        pairs = (
            (float(self.candle_count), float(other.candle_count)),
            (float(self.duration_seconds), float(other.duration_seconds)),
            (self.average_body_ratio, other.average_body_ratio),
            (self.upper_wick_ratio, other.upper_wick_ratio),
            (self.lower_wick_ratio, other.lower_wick_ratio),
            (self.pullback_depth_atr, other.pullback_depth_atr),
            (self.total_range_atr, other.total_range_atr),
            (self.slope_strength, other.slope_strength),
        )
        components = [max(0.0, 1.0 - abs(first - second) / max(abs(first), abs(second), 1.0)) for first, second in pairs]
        return round(sum(components) / len(components) * 100.0, 8)


@dataclass(frozen=True)
class ATRBufferPatternObservation:
    pattern_id: str
    pattern_sequence: int
    context_segment_id: str
    candidate: ATRBufferCandidate
    result_points: float
    outcome: str
    data_quality_status: str = "PASS"
    future_data_used: bool = False
    research_identity: PatternResearchIdentity | None = None
    shape_signature: PatternShapeSignature | None = None
    cross_market_context_id: str = ""

    def __post_init__(self) -> None:
        if not self.pattern_id.strip() or self.pattern_sequence <= 0 or not self.context_segment_id.strip():
            raise ValueError("pattern identity, sequence, and context are required")
        if self.outcome not in {"WIN", "LOSS", "FLAT"}:
            raise ValueError("outcome must be WIN, LOSS, or FLAT")
        if not math.isfinite(float(self.result_points)):
            raise ValueError("result points must be finite")
        if self.data_quality_status != "PASS" or self.future_data_used:
            raise ValueError("only leakage-free PASS research evidence is eligible")

    @property
    def research_key(self) -> str:
        if self.research_identity is None or self.shape_signature is None:
            return ""
        return f"{self.research_identity.research_key}|{self.shape_signature.bucket_key}"


@dataclass(frozen=True)
class ATRBufferResearchStandard:
    standard_id: str
    standard_version: str
    context_segment_id: str
    batch_number: int
    pattern_count: int
    selected_candidate: ATRBufferCandidate
    win_rate: float
    win_rate_confidence_95_low: float
    expectancy_points: float
    net_points: float
    research_key: str = ""
    pattern_identity: PatternResearchIdentity | None = None
    shape_signature: PatternShapeSignature | None = None
    shape_bucket_key: str = ""
    cross_market_context_ids: tuple[str, ...] = ()
    research_status: str = "RESEARCH_ACTIVE"
    production_usable: bool = False
    automatic_recalibration_enabled: bool = True
    automatic_production_promotion_allowed: bool = False
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_candidate"] = self.selected_candidate.as_dict()
        payload["pattern_identity"] = self.pattern_identity.as_dict() if self.pattern_identity else None
        payload["shape_signature"] = self.shape_signature.as_dict() if self.shape_signature else None
        payload["standard_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class ATRBufferBatchEvaluation:
    context_segment_id: str
    batch_number: int
    pattern_count: int
    candidate_count: int
    status: str
    reason: str
    standard: ATRBufferResearchStandard | None
    research_key: str = ""
    graph_key: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["standard"] = self.standard.as_dict() if self.standard else None
        payload["evaluation_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class ATRBufferRecalibrationPolicy:
    pattern_batch_size: int = 1000
    minimum_candidate_samples: int = 1000
    require_exact_pattern_research_identity: bool = True
    require_pattern_shape_signature: bool = True
    require_cross_market_context: bool = True
    cumulative_history_recalibration: bool = True
    incremental_cumulative_merge: bool = True

    def __post_init__(self) -> None:
        if self.pattern_batch_size <= 0:
            raise ValueError("pattern batch size must be positive")
        if self.minimum_candidate_samples <= 0 or self.minimum_candidate_samples > self.pattern_batch_size:
            raise ValueError("candidate sample minimum must be within the pattern batch")
        if not self.cumulative_history_recalibration:
            raise ValueError("ATR/buffer recalibration must use full cumulative pattern history")
        if not self.incremental_cumulative_merge:
            raise ValueError("prior pattern outcomes must be merged, not researched again")


class ATRBufferStandardRecalibrator:
    """Recompute a research-only standard from all history at each 1,000-pattern milestone."""

    def __init__(
        self,
        dataset_root: str | None = None,
        policy: ATRBufferRecalibrationPolicy | None = None,
    ) -> None:
        self.policy = policy or ATRBufferRecalibrationPolicy()
        self._dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root else None
        self._cumulative_states = self._load_cumulative_states()

    def _load_cumulative_states(self) -> dict[str, dict[str, Any]]:
        states: dict[str, dict[str, Any]] = {}
        if self._dataset is None:
            return states
        path = self._dataset.path_for("atr_buffer_cumulative_aggregates")
        if not path.exists():
            return states
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                envelope = json.loads(line)
                record = dict(envelope.get("record", {}))
                research_key = str(record.get("research_key", ""))
                if research_key:
                    states[research_key] = record
        return states

    @staticmethod
    def _candidate_from_mapping(value: Mapping[str, Any]) -> ATRBufferCandidate:
        return ATRBufferCandidate(**{
            name: value[name] for name in ATRBufferCandidate.__dataclass_fields__
        })

    @staticmethod
    def _wilson_low(wins: int, samples: int) -> float:
        if samples <= 0:
            return 0.0
        z = 1.959963984540054
        ratio = wins / samples
        denominator = 1.0 + z * z / samples
        centre = ratio + z * z / (2.0 * samples)
        margin = z * math.sqrt((ratio * (1.0 - ratio) + z * z / (4.0 * samples)) / samples)
        return max(0.0, (centre - margin) / denominator)

    def evaluate(
        self,
        observations: Sequence[ATRBufferPatternObservation],
        *,
        expected_candidate_ids: Iterable[str] | None = None,
    ) -> tuple[ATRBufferBatchEvaluation, ...]:
        expected_ids = frozenset(str(value) for value in expected_candidate_ids) if expected_candidate_ids is not None else None
        by_context: dict[str, list[ATRBufferPatternObservation]] = {}
        unique: dict[tuple[str, str, str], ATRBufferPatternObservation] = {}
        for item in observations:
            item.__post_init__()
            partition = item.research_key or f"LEGACY|{item.context_segment_id}"
            identity = (partition, item.pattern_id, item.candidate.candidate_id)
            prior = unique.get(identity)
            if prior is not None and prior != item:
                raise ValueError("conflicting duplicate ATR/buffer observation")
            unique[identity] = item
        for item in unique.values():
            partition = item.research_key or f"LEGACY|{item.context_segment_id}"
            by_context.setdefault(partition, []).append(item)

        evaluations: list[ATRBufferBatchEvaluation] = []
        size = self.policy.pattern_batch_size
        for context in sorted(by_context):
            rows = by_context[context]
            exact_identity = rows[0].research_identity
            shape_signature = rows[0].shape_signature
            graph_key = exact_identity.graph_key if exact_identity else ""
            prior_state = self._cumulative_states.get(context, {})
            prior_pattern_count = int(prior_state.get("processed_pattern_count", 0))
            prior_last_sequence = int(prior_state.get("last_pattern_sequence", 0))
            rows = [item for item in rows if item.pattern_sequence > prior_last_sequence]
            pattern_order = sorted({(item.pattern_sequence, item.pattern_id) for item in rows})
            cumulative_stats: dict[str, dict[str, Any]] = {
                candidate_id: {
                    "candidate": self._candidate_from_mapping(stats["candidate"]),
                    "samples": int(stats["samples"]),
                    "wins": int(stats["wins"]),
                    "net_points": float(stats["net_points"]),
                }
                for candidate_id, stats in dict(prior_state.get("candidate_stats", {})).items()
            }
            cumulative_cross_market_context_ids = set(
                str(value) for value in prior_state.get("cross_market_context_ids", [])
            )
            completed_pattern_counts = range(size, len(pattern_order) + 1, size)
            for new_pattern_count in completed_pattern_counts:
                cumulative_count = prior_pattern_count + new_pattern_count
                batch_number = cumulative_count // size
                # Only the newly completed 1,000-pattern slice is evaluated here.
                # Its sufficient statistics are merged into the cumulative state;
                # prior pattern outcomes are never replayed or researched again.
                pattern_slice = pattern_order[new_pattern_count - size:new_pattern_count]
                new_pattern_ids = {pattern_id for _, pattern_id in pattern_slice}
                batch_rows = [item for item in rows if item.pattern_id in new_pattern_ids]
                if self.policy.require_exact_pattern_research_identity and exact_identity is None:
                    evaluations.append(ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, 0,
                        "QUARANTINED", "exact_pattern_research_identity_required", None,
                        context, graph_key,
                    ))
                    continue
                if self.policy.require_pattern_shape_signature and shape_signature is None:
                    evaluations.append(ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, 0,
                        "QUARANTINED", "pattern_shape_signature_required", None,
                        context, graph_key,
                    ))
                    continue
                if any(item.research_key != context for item in batch_rows):
                    evaluations.append(ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, 0,
                        "QUARANTINED", "mixed_pattern_research_identity", None,
                        context, graph_key,
                    ))
                    continue
                if self.policy.require_cross_market_context and any(not item.cross_market_context_id.strip() for item in batch_rows):
                    evaluations.append(ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, 0,
                        "QUARANTINED", "cross_market_context_required", None,
                        context, graph_key,
                    ))
                    continue
                candidate_ids = {item.candidate.candidate_id for item in batch_rows}
                if expected_ids is not None and candidate_ids != expected_ids:
                    evaluation = ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, len(candidate_ids),
                        "QUARANTINED", "candidate_grid_coverage_incomplete", None,
                        context, graph_key,
                    )
                    evaluations.append(evaluation)
                    continue
                grouped: dict[str, list[ATRBufferPatternObservation]] = {}
                for item in batch_rows:
                    grouped.setdefault(item.candidate.candidate_id, []).append(item)
                if (
                    not grouped
                    or any(len(items) < self.policy.minimum_candidate_samples for items in grouped.values())
                    or any(len(items) != len(new_pattern_ids) for items in grouped.values())
                ):
                    evaluation = ATRBufferBatchEvaluation(
                        context, batch_number, cumulative_count, len(grouped),
                        "QUARANTINED", "candidate_sample_coverage_incomplete", None,
                        context, graph_key,
                    )
                    evaluations.append(evaluation)
                    continue
                for candidate_id, items in grouped.items():
                    stats = cumulative_stats.setdefault(candidate_id, {
                        "candidate": items[0].candidate,
                        "samples": 0,
                        "wins": 0,
                        "net_points": 0.0,
                    })
                    stats["samples"] += len(items)
                    stats["wins"] += sum(item.outcome == "WIN" for item in items)
                    stats["net_points"] += sum(item.result_points for item in items)
                cumulative_cross_market_context_ids.update(
                    item.cross_market_context_id for item in batch_rows
                    if item.cross_market_context_id.strip()
                )

                ranked: list[tuple[float, float, float, str, dict[str, Any]]] = []
                for candidate_id, stats in cumulative_stats.items():
                    samples = int(stats["samples"])
                    wins = int(stats["wins"])
                    net = float(stats["net_points"])
                    expectancy = net / samples
                    ranked.append((self._wilson_low(wins, samples), expectancy, net, candidate_id, stats))
                ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))
                lower, expectancy, net, _, selected_stats = ranked[0]
                selected = selected_stats["candidate"]
                wins = int(selected_stats["wins"])
                samples = int(selected_stats["samples"])
                standard_id = "ATR-BUFFER-" + _checksum({"context": context})[:16].upper()
                version = f"B{batch_number:06d}-P{max(sequence for sequence, _ in pattern_slice):012d}"
                standard = ATRBufferResearchStandard(
                    standard_id=standard_id,
                    standard_version=version,
                    context_segment_id=context,
                    batch_number=batch_number,
                    pattern_count=cumulative_count,
                    selected_candidate=selected,
                    win_rate=round(wins / samples * 100.0, 8),
                    win_rate_confidence_95_low=round(lower * 100.0, 8),
                    expectancy_points=round(expectancy, 8),
                    net_points=round(net, 8),
                    research_key=context,
                    pattern_identity=exact_identity,
                    shape_signature=shape_signature,
                    shape_bucket_key=shape_signature.bucket_key if shape_signature else "",
                    cross_market_context_ids=tuple(sorted(cumulative_cross_market_context_ids)),
                )
                evaluation = ATRBufferBatchEvaluation(
                    context, batch_number, cumulative_count, len(cumulative_stats),
                    "RESEARCH_STANDARD_UPDATED", "incremental_1000_merged_into_cumulative_standard", standard,
                    context, graph_key,
                )
                evaluations.append(evaluation)
                if self._dataset:
                    self._dataset.append("atr_buffer_research_standards", standard.as_dict())
                    aggregate_record = {
                        "schema_version": "atr-buffer-cumulative-aggregate.v1",
                        "research_key": context,
                        "graph_key": graph_key,
                        "processed_pattern_count": cumulative_count,
                        "last_pattern_sequence": max(sequence for sequence, _ in pattern_slice),
                        "candidate_stats": {
                            candidate_id: {
                                "candidate": stats["candidate"].as_dict(),
                                "samples": stats["samples"],
                                "wins": stats["wins"],
                                "net_points": round(float(stats["net_points"]), 8),
                            }
                            for candidate_id, stats in sorted(cumulative_stats.items())
                        },
                        "cross_market_context_ids": sorted(cumulative_cross_market_context_ids),
                        "standard_version": standard.standard_version,
                    }
                    self._dataset.append("atr_buffer_cumulative_aggregates", aggregate_record)
                    self._cumulative_states[context] = aggregate_record
            remainder = len(pattern_order) % size
            if remainder or not pattern_order or len(pattern_order) < size:
                evaluations.append(ATRBufferBatchEvaluation(
                    context,
                    (prior_pattern_count + len(pattern_order)) // size + 1,
                    prior_pattern_count + len(pattern_order),
                    0,
                    "WAITING",
                    "next_cumulative_history_milestone_incomplete",
                    None,
                    context,
                    graph_key,
                ))
            if self._dataset:
                for evaluation in evaluations:
                    if evaluation.context_segment_id == context:
                        self._dataset.append("atr_buffer_batch_evaluations", evaluation.as_dict())
        return tuple(evaluations)


@dataclass(frozen=True)
class StaggeredEntryObservation:
    """Blind-forward result for one plan-specific entry mode and exact shape."""

    pattern_id: str
    pattern_sequence: int
    research_identity: PatternResearchIdentity
    shape_signature: PatternShapeSignature
    entry_mode: str
    outcome: str
    net_points: float
    maximum_drawdown_points: float
    entry_improvement_points: float
    filled_leg_count: int
    first_leg_only: bool
    post_add_failure: bool
    spread_slippage_points: float
    cross_market_context_id: str

    @property
    def research_key(self) -> str:
        return f"{self.research_identity.research_key}|{self.shape_signature.bucket_key}"

    def __post_init__(self) -> None:
        if not self.pattern_id.strip() or self.pattern_sequence <= 0:
            raise ValueError("staggered entry observation identity required")
        if self.entry_mode not in {
            "SINGLE_ENTRY", "STAGGERED_TREND_PULLBACK_1_1_1",
            "BREAKOUT_RETEST_1_1_1", "RANGE_LAYERED_ENTRY",
            "NO_ADDITIONAL_ENTRY",
        }:
            raise ValueError("unsupported staggered entry research mode")
        if self.outcome not in {"WIN", "LOSS", "FLAT"}:
            raise ValueError("invalid staggered entry outcome")
        if not 1 <= self.filled_leg_count <= 3 or not self.cross_market_context_id.strip():
            raise ValueError("leg count and cross-market context required")


@dataclass(frozen=True)
class StaggeredEntryResearchStandard:
    standard_id: str
    standard_version: str
    research_key: str
    entry_mode: str
    pattern_count: int
    family_samples: int
    exact_shape_samples: int
    win_rate: float
    win_rate_confidence_95_low: float
    expectancy_points: float
    maximum_drawdown_points: float
    average_entry_improvement_points: float
    leg_two_fill_rate: float
    leg_three_fill_rate: float
    first_leg_only_rate: float
    post_add_failure_rate: float
    average_spread_slippage_points: float
    minimum_add_spacing_points: float
    oqs: float
    certified: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class StaggeredEntryStandardRecalibrator:
    """Merge only each new 1,000-pattern slice into persistent cumulative stats."""

    MODES = (
        "SINGLE_ENTRY", "STAGGERED_TREND_PULLBACK_1_1_1",
        "BREAKOUT_RETEST_1_1_1", "RANGE_LAYERED_ENTRY", "NO_ADDITIONAL_ENTRY",
    )

    def __init__(self, dataset_root: str | None = None, pattern_batch_size: int = 1000) -> None:
        if pattern_batch_size != 1000:
            raise ValueError("staggered entry standards update only at each new 1000 patterns")
        self.size = pattern_batch_size
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root else None
        self.states: dict[str, dict[str, Any]] = {}
        if self.dataset:
            for envelope in self.dataset.records("staggered_entry_cumulative_aggregates"):
                record = dict(envelope.get("record", {}))
                if record.get("research_key"):
                    self.states[str(record["research_key"])] = record

    @staticmethod
    def _wilson_low(wins: int, samples: int) -> float:
        return ATRBufferStandardRecalibrator._wilson_low(wins, samples)

    def evaluate(self, observations: Sequence[StaggeredEntryObservation]) -> tuple[dict[str, Any], ...]:
        partitions: dict[str, list[StaggeredEntryObservation]] = {}
        unique: dict[tuple[str, str, str], StaggeredEntryObservation] = {}
        for row in observations:
            row.__post_init__()
            key = (row.research_key, row.pattern_id, row.entry_mode)
            if key in unique and unique[key] != row:
                raise ValueError("conflicting duplicate staggered entry observation")
            unique[key] = row
        for row in unique.values():
            partitions.setdefault(row.research_key, []).append(row)
        results: list[dict[str, Any]] = []
        for key in sorted(partitions):
            state = self.states.get(key, {})
            prior_count = int(state.get("processed_pattern_count", 0))
            last_sequence = int(state.get("last_pattern_sequence", 0))
            rows = [row for row in partitions[key] if row.pattern_sequence > last_sequence]
            order = sorted({(row.pattern_sequence, row.pattern_id) for row in rows})
            stats = {mode: dict(values) for mode, values in dict(state.get("mode_stats", {})).items()}
            for complete in range(self.size, len(order) + 1, self.size):
                slice_ids = {pattern_id for _, pattern_id in order[complete-self.size:complete]}
                batch = [row for row in rows if row.pattern_id in slice_ids]
                grouped = {mode: [row for row in batch if row.entry_mode == mode] for mode in self.MODES}
                if any(len(grouped[mode]) != self.size for mode in self.MODES):
                    results.append({"status": "QUARANTINED", "reason": "entry_mode_candidate_coverage_incomplete", "research_key": key})
                    continue
                for mode, items in grouped.items():
                    values = stats.setdefault(mode, {name: 0.0 for name in (
                        "samples", "wins", "net", "max_drawdown", "improvement", "leg2", "leg3",
                        "first_only", "post_add_failure", "cost",
                    )})
                    values["samples"] += len(items)
                    values["wins"] += sum(row.outcome == "WIN" for row in items)
                    values["net"] += sum(row.net_points for row in items)
                    values["max_drawdown"] = max(values["max_drawdown"], max(row.maximum_drawdown_points for row in items))
                    values["improvement"] += sum(row.entry_improvement_points for row in items)
                    values["leg2"] += sum(row.filled_leg_count >= 2 for row in items)
                    values["leg3"] += sum(row.filled_leg_count >= 3 for row in items)
                    values["first_only"] += sum(row.first_leg_only for row in items)
                    values["post_add_failure"] += sum(row.post_add_failure for row in items)
                    values["cost"] += sum(row.spread_slippage_points for row in items)
                cumulative = prior_count + complete
                ranked = []
                for mode, values in stats.items():
                    samples = int(values["samples"])
                    wins = int(values["wins"])
                    expectancy = float(values["net"]) / samples
                    ranked.append((self._wilson_low(wins, samples), expectancy, -float(values["max_drawdown"]), mode, values))
                ranked.sort(reverse=True)
                low, expectancy, _, mode, values = ranked[0]
                samples = int(values["samples"])
                wins = int(values["wins"])
                oqs = min(100.0, max(0.0, low * 100.0 + max(-20.0, min(20.0, expectancy))))
                standard = StaggeredEntryResearchStandard(
                    standard_id="STAGGERED-" + _checksum({"research_key": key})[:16].upper(),
                    standard_version=f"B{cumulative//self.size:06d}-P{max(seq for seq, _ in order[complete-self.size:complete]):012d}",
                    research_key=key, entry_mode=mode, pattern_count=cumulative,
                    family_samples=samples, exact_shape_samples=samples,
                    win_rate=round(wins/samples*100, 8), win_rate_confidence_95_low=round(low*100, 8),
                    expectancy_points=round(expectancy, 8), maximum_drawdown_points=round(float(values["max_drawdown"]), 8),
                    average_entry_improvement_points=round(float(values["improvement"])/samples, 8),
                    leg_two_fill_rate=round(float(values["leg2"])/samples*100, 8),
                    leg_three_fill_rate=round(float(values["leg3"])/samples*100, 8),
                    first_leg_only_rate=round(float(values["first_only"])/samples*100, 8),
                    post_add_failure_rate=round(float(values["post_add_failure"])/samples*100, 8),
                    average_spread_slippage_points=round(float(values["cost"])/samples, 8),
                    minimum_add_spacing_points=max(1.0, round(float(values["improvement"])/samples, 8)),
                    oqs=round(oqs, 8), certified=samples >= 80 and low*100 >= 80.0 and oqs >= 97.0,
                )
                result = {"status": "RESEARCH_STANDARD_UPDATED", "reason": "incremental_1000_merged_into_cumulative_standard", "standard": standard.as_dict(), "research_key": key}
                results.append(result)
                aggregate = {"schema_version": "staggered-entry-cumulative-aggregate.v1", "research_key": key, "processed_pattern_count": cumulative, "last_pattern_sequence": max(seq for seq, _ in order[complete-self.size:complete]), "mode_stats": stats, "standard_version": standard.standard_version}
                if self.dataset:
                    self.dataset.append("staggered_entry_research_standards", standard.as_dict())
                    self.dataset.append("staggered_entry_cumulative_aggregates", aggregate)
                    self.dataset.append("staggered_entry_batch_evaluations", result)
                self.states[key] = aggregate
            if len(order) % self.size or len(order) < self.size:
                result = {"status": "WAITING", "reason": "next_cumulative_history_milestone_incomplete", "research_key": key, "covered_patterns": prior_count + len(order)}
                results.append(result)
                if self.dataset:
                    self.dataset.append("staggered_entry_batch_evaluations", result)
        return tuple(results)


class ResearchStandardizationCoordinator:
    """Single append-only bridge from research observations to recalibrators.

    The coordinator has no execution authority.  Re-reading the observation
    ledgers is safe because each recalibrator advances only beyond its persisted
    last pattern sequence and updates only at a complete 1,000-pattern boundary.
    """

    def __init__(self, dataset_root: str) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)
        self.state_path = self.dataset.root / "research_standardization_coordinator_state.json"

    def _state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return {}
        return dict(json.loads(self.state_path.read_text(encoding="utf-8")))

    def _write_state(self, value: Mapping[str, Any]) -> None:
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        temporary.write_text(json.dumps(dict(value), indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.state_path)

    @staticmethod
    def _identity(value: Mapping[str, Any]) -> PatternResearchIdentity:
        return PatternResearchIdentity(**{
            name: value[name] for name in PatternResearchIdentity.__dataclass_fields__
        })

    @staticmethod
    def _shape(value: Mapping[str, Any]) -> PatternShapeSignature:
        return PatternShapeSignature(**{
            name: value[name] for name in PatternShapeSignature.__dataclass_fields__
        })

    def append_atr_observation(self, observation: ATRBufferPatternObservation) -> dict[str, Any]:
        observation.__post_init__()
        payload = asdict(observation)
        payload["candidate"] = observation.candidate.as_dict()
        payload["research_identity"] = observation.research_identity.as_dict() if observation.research_identity else None
        payload["shape_signature"] = observation.shape_signature.as_dict() if observation.shape_signature else None
        return self.dataset.append("atr_buffer_pattern_observations", payload)

    def append_staggered_observation(self, observation: StaggeredEntryObservation) -> dict[str, Any]:
        observation.__post_init__()
        payload = asdict(observation)
        payload["research_identity"] = observation.research_identity.as_dict()
        payload["shape_signature"] = observation.shape_signature.as_dict()
        return self.dataset.append("staggered_entry_pattern_observations", payload)

    def append_single_unit_profit_observation(self, observation: Any) -> dict[str, Any]:
        from .capital_profit import SingleUnitProfitObservation
        if not isinstance(observation, SingleUnitProfitObservation):
            raise TypeError("SingleUnitProfitObservation is required")
        observation.__post_init__()
        return self.dataset.append("single_unit_profit_pattern_observations", observation.as_dict())

    def append_initial_capital_observation(self, observation: Any) -> dict[str, Any]:
        from .capital_profit import InitialCapitalObservation
        if not isinstance(observation, InitialCapitalObservation):
            raise TypeError("InitialCapitalObservation is required")
        observation.__post_init__()
        return self.dataset.append("initial_capital_pattern_observations", observation.as_dict())

    def _atr_observations(self) -> tuple[ATRBufferPatternObservation, ...]:
        rows: list[ATRBufferPatternObservation] = []
        for envelope in self.dataset.records("atr_buffer_pattern_observations"):
            value = dict(envelope.get("record", {}))
            candidate_value = dict(value.pop("candidate"))
            candidate_value.pop("candidate_id", None)
            identity_value = value.pop("research_identity", None)
            shape_value = value.pop("shape_signature", None)
            if isinstance(shape_value, Mapping):
                shape_value = dict(shape_value)
                shape_value.pop("shape_bucket_key", None)
            rows.append(ATRBufferPatternObservation(
                **value,
                candidate=ATRBufferCandidate(**candidate_value),
                research_identity=self._identity(identity_value) if isinstance(identity_value, Mapping) else None,
                shape_signature=self._shape(shape_value) if isinstance(shape_value, Mapping) else None,
            ))
        return tuple(rows)

    def _staggered_observations(self) -> tuple[StaggeredEntryObservation, ...]:
        rows: list[StaggeredEntryObservation] = []
        for envelope in self.dataset.records("staggered_entry_pattern_observations"):
            value = dict(envelope.get("record", {}))
            identity_value = value.pop("research_identity")
            shape_value = dict(value.pop("shape_signature"))
            shape_value.pop("shape_bucket_key", None)
            rows.append(StaggeredEntryObservation(
                **value,
                research_identity=self._identity(identity_value),
                shape_signature=self._shape(shape_value),
            ))
        return tuple(rows)

    def run(self) -> dict[str, Any]:
        from .capital_profit import (
            InitialCapitalStandardizer, SingleUnitProfitStandardizer,
            capital_observation_from_mapping, profit_observation_from_mapping,
        )
        atr_rows = self._atr_observations()
        staggered_rows = self._staggered_observations()
        profit_rows = tuple(profit_observation_from_mapping(envelope["record"]) for envelope in self.dataset.records("single_unit_profit_pattern_observations"))
        capital_rows = tuple(capital_observation_from_mapping(envelope["record"]) for envelope in self.dataset.records("initial_capital_pattern_observations"))
        counts = {
            "atr_observation_count": len(atr_rows),
            "staggered_observation_count": len(staggered_rows),
            "single_unit_profit_observation_count": len(profit_rows),
            "initial_capital_observation_count": len(capital_rows),
        }
        prior = self._state()
        if all(int(prior.get(name, -1)) == value for name, value in counts.items()):
            return {
                "status": "WAITING",
                "reason": "no_new_pattern_observations_since_last_evaluation",
                **counts,
                "atr_evaluation_count": 0,
                "staggered_evaluation_count": 0,
                "standards_updated": 0,
                "execution_authority": "NONE",
                "automatic_production_promotion_allowed": False,
            }
        atr_results = ATRBufferStandardRecalibrator(str(self.dataset.root)).evaluate(atr_rows)
        staggered_results = StaggeredEntryStandardRecalibrator(str(self.dataset.root)).evaluate(staggered_rows)
        profit_results = SingleUnitProfitStandardizer(self.dataset).evaluate(profit_rows)
        capital_results = InitialCapitalStandardizer(self.dataset).evaluate(capital_rows)
        updated = sum(item.status == "RESEARCH_STANDARD_UPDATED" for item in atr_results)
        updated += sum(item.get("status") == "RESEARCH_STANDARD_UPDATED" for item in staggered_results)
        updated += sum(item.get("status") == "RESEARCH_STANDARD_UPDATED" for item in profit_results)
        updated += sum(item.get("status") == "RESEARCH_STANDARD_UPDATED" for item in capital_results)
        result = {
            "status": "UPDATED" if updated else "WAITING",
            "reason": "cumulative_1000_pattern_standard_updated" if updated else "next_cumulative_1000_pattern_milestone_incomplete",
            **counts,
            "atr_evaluation_count": len(atr_results),
            "staggered_evaluation_count": len(staggered_results),
            "single_unit_profit_evaluation_count": len(profit_results),
            "initial_capital_evaluation_count": len(capital_results),
            "standards_updated": updated,
            "execution_authority": "NONE",
            "automatic_production_promotion_allowed": False,
        }
        self._write_state({**counts, "last_status": result["status"], "last_reason": result["reason"]})
        return result


@dataclass(frozen=True)
class ATRBufferResearchMatch:
    rank: int
    standard_id: str
    standard_version: str
    graph_key: str
    research_key: str
    context_match_score: float
    shape_similarity_score: float
    cross_market_similarity_score: float
    win_rate_confidence_95_low: float
    expectancy_points: float
    selected_candidate: ATRBufferCandidate
    current_cross_market_context_id: str
    historical_cross_market_context_ids: tuple[str, ...]
    research_only: bool = True
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["selected_candidate"] = self.selected_candidate.as_dict()
        return payload


class ATRBufferResearchRanker:
    """Rank same-chart standards beside current cross-market evidence.

    Unlike chart patterns are excluded before ranking.  Cross-market scores
    are supplied by the existing cross-market/context engines and remain a
    separate ranking dimension; this class never creates a trade decision.
    """

    def rank(
        self,
        current_identity: PatternResearchIdentity,
        standards: Iterable[ATRBufferResearchStandard],
        *,
        current_shape_signature: PatternShapeSignature,
        current_cross_market_context_id: str,
        cross_market_similarity_by_standard: Mapping[str, float],
        limit: int = 100,
    ) -> tuple[ATRBufferResearchMatch, ...]:
        if not current_cross_market_context_id.strip():
            raise ValueError("current cross-market context is required")
        if limit <= 0:
            raise ValueError("ranking limit must be positive")
        eligible: list[tuple[float, float, float, float, float, str, ATRBufferResearchStandard]] = []
        for standard in standards:
            identity = standard.pattern_identity
            shape = standard.shape_signature
            if identity is None or shape is None or identity.graph_key != current_identity.graph_key:
                continue
            if standard.standard_id not in cross_market_similarity_by_standard:
                continue
            cross_score = float(cross_market_similarity_by_standard[standard.standard_id])
            if not math.isfinite(cross_score) or not 0.0 <= cross_score <= 100.0:
                raise ValueError("cross-market similarity must be between 0 and 100")
            context_score = current_identity.context_match_score(identity)
            shape_score = current_shape_signature.similarity_score(shape)
            eligible.append((
                context_score, shape_score, cross_score, standard.win_rate_confidence_95_low,
                standard.expectancy_points, standard.standard_version, standard,
            ))
        eligible.sort(key=lambda item: (-item[0], -item[1], -item[2], -item[3], -item[4], item[5]))
        result: list[ATRBufferResearchMatch] = []
        for rank, (context_score, shape_score, cross_score, lower, expectancy, _, standard) in enumerate(eligible[:limit], 1):
            result.append(ATRBufferResearchMatch(
                rank=rank,
                standard_id=standard.standard_id,
                standard_version=standard.standard_version,
                graph_key=current_identity.graph_key,
                research_key=standard.research_key,
                context_match_score=context_score,
                shape_similarity_score=shape_score,
                cross_market_similarity_score=cross_score,
                win_rate_confidence_95_low=lower,
                expectancy_points=expectancy,
                selected_candidate=standard.selected_candidate,
                current_cross_market_context_id=current_cross_market_context_id,
                historical_cross_market_context_ids=standard.cross_market_context_ids,
            ))
        return tuple(result)

    def hierarchical_evidence(
        self,
        current_identity: PatternResearchIdentity,
        current_shape_signature: PatternShapeSignature,
        standards: Iterable[ATRBufferResearchStandard],
        *,
        current_cross_market_context_id: str,
        cross_market_similarity_by_standard: Mapping[str, float],
    ) -> dict[str, Any]:
        rows = tuple(standards)
        family = tuple(
            standard for standard in rows
            if standard.pattern_identity is not None
            and _label(standard.pattern_identity.symbol) == _label(current_identity.symbol)
            and _label(standard.pattern_identity.timeframe) == _label(current_identity.timeframe)
            and _label(standard.pattern_identity.pattern_family) == _label(current_identity.pattern_family)
            and _label(standard.pattern_identity.direction) == _label(current_identity.direction)
        )
        exact = self.rank(
            current_identity, rows,
            current_shape_signature=current_shape_signature,
            current_cross_market_context_id=current_cross_market_context_id,
            cross_market_similarity_by_standard=cross_market_similarity_by_standard,
        )
        family_score = max((item.win_rate_confidence_95_low for item in family), default=0.0)
        exact_score = exact[0].win_rate_confidence_95_low if exact else 0.0
        shape_score = exact[0].shape_similarity_score if exact else 0.0
        return {
            "research_scope": "HIERARCHICAL_FAMILY_AND_EXACT_SHAPE",
            "family_standard_count": len(family),
            "exact_shape_match_count": len(exact),
            "family_research_score": round(family_score, 8),
            "exact_shape_research_score": round(exact_score, 8),
            "shape_similarity_score": round(shape_score, 8),
            "hierarchical_research_ready": bool(family and exact),
            "current_graph_key": current_identity.graph_key,
            "current_shape_bucket_key": current_shape_signature.bucket_key,
            "current_cross_market_context_id": current_cross_market_context_id,
            "execution_authority": False,
            "order_send_allowed": False,
        }


class ResearchDerivedStandardRegistry:
    """Versioned registry and deterministic context selector."""

    def __init__(self, dataset_root: str | None = None, policy: StandardizationPolicy | None = None) -> None:
        self.policy = policy or StandardizationPolicy()
        self._standards: list[InitialStandardPolicy] = []
        self._dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root else None

    def register(self, standard: InitialStandardPolicy) -> InitialStandardPolicy:
        if not self.policy.allow_research_derived_initial_standard:
            raise ValueError("research-derived initial standards are disabled")
        if standard.evidence_score < self.policy.minimum_evidence_score:
            raise ValueError("evidence score below initial-standard threshold")
        if standard.temporal_stability_score < self.policy.minimum_temporal_stability_score:
            raise ValueError("temporal stability below initial-standard threshold")
        if standard.resilience_score < self.policy.minimum_resilience_score:
            raise ValueError("resilience below initial-standard threshold")
        if self.policy.require_owner_approval and not standard.owner_approved:
            raise ValueError("owner approval is required")
        duplicate = any(
            item.standard_id == standard.standard_id and item.standard_version == standard.standard_version
            for item in self._standards
        )
        if duplicate:
            raise ValueError("standard version already exists")
        self._standards.append(standard)
        self._standards.sort(key=lambda item: (item.standard_id, item.standard_version))
        if self._dataset:
            self._dataset.append("research_standard_versions", standard.as_dict())
        return standard

    def supersede(self, standard_id: str, standard_version: str, replacement: InitialStandardPolicy) -> InitialStandardPolicy:
        found = False
        updated: list[InitialStandardPolicy] = []
        for item in self._standards:
            if item.standard_id == standard_id and item.standard_version == standard_version:
                found = True
                payload = item.as_dict(include_checksum=False)
                payload.pop("created_at", None)
                payload["status"] = "SUPERSEDED"
                updated.append(InitialStandardPolicy(**payload))
            else:
                updated.append(item)
        if not found:
            raise KeyError("standard version not found")
        self._standards = updated
        return self.register(replacement)

    def select(self, actual_context: StandardContext, selection_id: str) -> StandardSelection:
        candidates: list[tuple[float, InitialStandardPolicy]] = []
        for standard in self._standards:
            if standard.status != "ACTIVE" or not standard.production_usable:
                continue
            score = standard.context.match_score(actual_context)
            if score >= self.policy.minimum_context_match_score:
                candidates.append((score, standard))
        if not candidates:
            selection = StandardSelection(
                selection_id=selection_id, actual_context=actual_context,
                selected_standard_id=None, selected_standard_version=None,
                selected_policy_id=None, selected_parameters={}, context_match_score=0.0,
                selection_status="NO_MATCH", reason="no_active_standard_matches_context",
                evidence_checksum=None,
            )
        else:
            candidates.sort(key=lambda pair: (
                pair[0], pair[1].evidence_score, pair[1].temporal_stability_score,
                pair[1].resilience_score, pair[1].standard_version,
            ), reverse=True)
            score, standard = candidates[0]
            selection = StandardSelection(
                selection_id=selection_id, actual_context=actual_context,
                selected_standard_id=standard.standard_id,
                selected_standard_version=standard.standard_version,
                selected_policy_id=standard.policy_id,
                selected_parameters=dict(standard.policy_parameters),
                context_match_score=score, selection_status="SELECTED_INITIAL_STANDARD",
                reason="highest_evidence_active_context_match",
                evidence_checksum=standard.lineage.evidence_record_checksum,
            )
        if self._dataset:
            self._dataset.append("research_standard_selections", selection.as_dict())
        return selection

    def active_standards(self) -> tuple[InitialStandardPolicy, ...]:
        return tuple(item for item in self._standards if item.status == "ACTIVE")


class HistoricalCoveragePlanner:
    """Build a deterministic earliest-available research backfill plan."""

    DEFAULT_MARKETS = (
        ("GOLD#", "PRECIOUS_METAL"),
        ("DXY", "USD_INDEX"),
        ("EURUSD", "FOREX_MAJOR"),
        ("GBPUSD", "FOREX_MAJOR"),
        ("USDJPY", "FOREX_MAJOR"),
        ("USOIL", "ENERGY"),
        ("UKOIL", "ENERGY"),
        ("US500", "EQUITY_INDEX"),
        ("US30", "EQUITY_INDEX"),
    )
    DEFAULT_TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")

    def build_default(self, plan_id: str = "AFIP_MAXIMUM_HISTORY_V1") -> HistoricalCoveragePlan:
        requests = tuple(
            HistoricalCoverageRequest(
                request_id=f"{plan_id}_{instrument}", instrument=instrument,
                symbol_family=family, timeframes=self.DEFAULT_TIMEFRAMES,
                priority=100 if instrument == "GOLD#" else 80,
            )
            for instrument, family in self.DEFAULT_MARKETS
        )
        return HistoricalCoveragePlan(plan_id=plan_id, requests=requests)

    def persist(self, plan: HistoricalCoveragePlan, dataset_root: str) -> dict[str, Any]:
        dataset = AppendOnlyResearchDataset(dataset_root)
        return dataset.append("historical_coverage_plans", plan.as_dict())
