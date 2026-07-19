"""Milestone T Pack 8: runtime standard adapter and historical backfill orchestration.

Consumes owner-approved ACTIVE research-derived standards, converts selected policy
parameters into bounded runtime guidance, and orchestrates earliest-available
historical collection through injected providers. This module never sends orders,
never calls MT5 order_send, and never bypasses existing risk/execution gates.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Callable, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.research_standardization import ResearchDerivedStandardRegistry, StandardContext


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class RuntimeSafetyEnvelope:
    maximum_units: int = 3
    minimum_lot: float = 0.01
    maximum_lot_per_unit: float = 0.01
    minimum_stop_points: float = 1.0
    maximum_stop_points: float = 100000.0
    minimum_target_points: float = 1.0
    maximum_target_points: float = 100000.0
    require_risk_approval: bool = True
    require_trading_cost_approval: bool = True
    require_profile_capacity: bool = True
    require_execution_permission: bool = True


@dataclass(frozen=True)
class RuntimeStandardGuidance:
    guidance_id: str
    selection_status: str
    selected_standard_id: str | None
    selected_standard_version: str | None
    selected_policy_id: str | None
    context_match_score: float
    entry_confidence_adjustment: float
    requested_units: int
    lot_per_unit: float
    stop_points: float | None
    target_points: float | None
    break_even_trigger_points: float | None
    trailing_stop_points: float | None
    hold_policy: str
    close_policy: str
    safety_gate_requirements: tuple[str, ...]
    runtime_usable: bool
    reason: str
    evidence_checksum: str | None
    generated_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["guidance_checksum"] = _checksum(payload)
        return payload


class RuntimeStandardAdapter:
    """Select and normalize an ACTIVE standard without authorizing execution."""

    def __init__(self, registry: ResearchDerivedStandardRegistry, dataset_root: str | None = None,
                 envelope: RuntimeSafetyEnvelope | None = None) -> None:
        self.registry = registry
        self.envelope = envelope or RuntimeSafetyEnvelope()
        self.dataset = AppendOnlyResearchDataset(dataset_root) if dataset_root else None

    def build_guidance(self, context: StandardContext, guidance_id: str) -> RuntimeStandardGuidance:
        selection = self.registry.select(context, f"{guidance_id}-selection")
        requirements = tuple(name for name, enabled in (
            ("risk_approval", self.envelope.require_risk_approval),
            ("trading_cost_approval", self.envelope.require_trading_cost_approval),
            ("profile_unit_capacity", self.envelope.require_profile_capacity),
            ("execution_permission", self.envelope.require_execution_permission),
        ) if enabled)
        if selection.selection_status != "SELECTED_INITIAL_STANDARD":
            guidance = RuntimeStandardGuidance(
                guidance_id, selection.selection_status, None, None, None,
                selection.context_match_score, 0.0, 0, self.envelope.minimum_lot,
                None, None, None, None, "DEFAULT", "DEFAULT", requirements,
                False, "no_context_appropriate_active_standard", None, _utc_now())
        else:
            p = dict(selection.selected_parameters)
            units = max(0, min(int(p.get("units", p.get("max_units", 1))), self.envelope.maximum_units))
            lot = max(self.envelope.minimum_lot, min(float(p.get("lot_per_unit", 0.01)), self.envelope.maximum_lot_per_unit))
            def bounded(key: str, low: float, high: float) -> float | None:
                if key not in p or p[key] is None:
                    return None
                return max(low, min(float(p[key]), high))
            guidance = RuntimeStandardGuidance(
                guidance_id, selection.selection_status, selection.selected_standard_id,
                selection.selected_standard_version, selection.selected_policy_id,
                selection.context_match_score,
                max(-100.0, min(float(p.get("entry_confidence_adjustment", 0.0)), 100.0)),
                units, lot,
                bounded("stop_points", self.envelope.minimum_stop_points, self.envelope.maximum_stop_points),
                bounded("target_points", self.envelope.minimum_target_points, self.envelope.maximum_target_points),
                bounded("break_even_trigger_points", 0.0, self.envelope.maximum_target_points),
                bounded("trailing_stop_points", 0.0, self.envelope.maximum_stop_points),
                str(p.get("hold_policy", "STANDARD")).upper(),
                str(p.get("close_policy", "STANDARD")).upper(), requirements,
                True, "active_research_derived_standard_selected_with_safety_gates_preserved",
                selection.evidence_checksum, _utc_now())
        if self.dataset:
            self.dataset.append("runtime_standard_guidance", guidance.as_dict())
        return guidance


@dataclass(frozen=True)
class BackfillRequest:
    request_id: str
    instrument: str
    timeframe: str
    start_utc: str | None = None
    end_utc: str | None = None
    maximum_bars_per_batch: int = 50000


@dataclass(frozen=True)
class BackfillResult:
    request_id: str
    instrument: str
    timeframe: str
    status: str
    earliest_available_utc: str | None
    latest_closed_bar_utc: str | None
    bars_received: int
    bars_persisted: int
    duplicates_skipped: int
    batches: int
    provenance: Mapping[str, Any]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["result_checksum"] = _checksum(payload)
        return payload


class HistoricalBackfillOrchestrator:
    """Provider-neutral, append-only, deterministic historical collector."""

    def __init__(self, dataset_root: str) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)

    def run(self, request: BackfillRequest,
            provider: Callable[[BackfillRequest], Iterable[Mapping[str, Any]]],
            provenance: Mapping[str, Any]) -> BackfillResult:
        rows = list(provider(request))
        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        duplicates = 0
        for row in rows:
            timestamp = str(row.get("timestamp_utc", "")).strip()
            if not timestamp:
                continue
            key = f"{request.instrument}|{request.timeframe}|{timestamp}"
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            normalized.append({
                "request_id": request.request_id, "instrument": request.instrument,
                "timeframe": request.timeframe, "timestamp_utc": timestamp,
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": float(row.get("volume", 0.0)), "provenance": dict(provenance),
            })
        normalized.sort(key=lambda item: item["timestamp_utc"])
        for row in normalized:
            self.dataset.append("historical_market_bars", row)
        result = BackfillResult(
            request.request_id, request.instrument, request.timeframe,
            "COMPLETED" if normalized else "NO_DATA",
            normalized[0]["timestamp_utc"] if normalized else None,
            normalized[-1]["timestamp_utc"] if normalized else None,
            len(rows), len(normalized), duplicates, 1, dict(provenance),
            "earliest_available_to_latest_closed_bar_collected" if normalized else "provider_returned_no_valid_bars")
        self.dataset.append("historical_backfill_results", result.as_dict())
        return result
