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
from typing import Any, Iterable, Mapping, Sequence

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
