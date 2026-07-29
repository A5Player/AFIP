"""Milestone T Pack 9: MT5 historical provider and dashboard data contracts.

This module is dependency-injected so Linux validation never imports MetaTrader5.
It resolves broker symbols, performs resumable historical backfill, writes append-only
checkpoints/results, and records research-standard influence in decision traces.
It never calls order_send and never grants execution permission.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset
from afip.runtime_standard_adapter import BackfillRequest, RuntimeStandardGuidance


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _checksum(value: Mapping[str, Any]) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@dataclass(frozen=True)
class SymbolResolution:
    requested_symbol: str
    resolved_symbol: str | None
    status: str
    reason: str
    candidates_checked: tuple[str, ...]


class BrokerSymbolResolver:
    """Resolve canonical research symbols to symbols exposed by one MT5 terminal."""

    DEFAULT_ALIASES: Mapping[str, tuple[str, ...]] = {
        "GOLD": ("GOLD#", "GOLD", "XAUUSD", "XAUUSD#", "XAUUSD.", "XAUUSDm"),
        "GOLD#": ("GOLD#", "GOLD", "XAUUSD", "XAUUSD#", "XAUUSD.", "XAUUSDm"),
        "XAUUSD": ("XAUUSD", "GOLD#", "GOLD", "XAUUSD#", "XAUUSD.", "XAUUSDm"),
        "USOIL": ("USOIL", "USOIL#", "WTI", "WTI#", "XTIUSD"),
        "UKOIL": ("UKOIL", "UKOIL#", "BRENT", "BRENT#", "XBRUSD"),
    }

    def __init__(self, aliases: Mapping[str, Sequence[str]] | None = None) -> None:
        merged = dict(self.DEFAULT_ALIASES)
        if aliases:
            merged.update({str(k).upper(): tuple(str(v) for v in values) for k, values in aliases.items()})
        self.aliases = merged

    def resolve(self, requested_symbol: str, available_symbols: Iterable[str]) -> SymbolResolution:
        requested = str(requested_symbol).strip()
        available = tuple(str(item).strip() for item in available_symbols if str(item).strip())
        exact = {item.upper(): item for item in available}
        candidates = self.aliases.get(requested.upper(), (requested,))
        for candidate in candidates:
            if candidate.upper() in exact:
                return SymbolResolution(requested, exact[candidate.upper()], "RESOLVED", "broker_symbol_resolved", tuple(candidates))
        return SymbolResolution(requested, None, "NOT_FOUND", "broker_symbol_unavailable", tuple(candidates))


@dataclass(frozen=True)
class HistoricalCheckpoint:
    request_id: str
    resolved_symbol: str
    timeframe: str
    next_start_utc: str | None
    batches_completed: int
    bars_persisted: int
    status: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checkpoint_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class ProviderBackfillSummary:
    request_id: str
    requested_symbol: str
    resolved_symbol: str | None
    timeframe: str
    status: str
    batches_completed: int
    bars_received: int
    bars_persisted: int
    duplicates_skipped: int
    resumed_from_checkpoint: bool
    earliest_available_utc: str | None
    latest_closed_bar_utc: str | None
    reason: str
    bars_rejected: int = 0
    missing_interval_count: int = 0
    quality_status: str = "UNKNOWN"
    bytes_written: int = 0

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["summary_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class HistoricalDataQuality:
    accepted: int
    rejected: int
    duplicate_count: int
    missing_interval_count: int
    impossible_ohlc_count: int
    invalid_timestamp_count: int
    status: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _valid_ohlc(row: Mapping[str, Any]) -> bool:
    try:
        o, h, l, c = (float(row[name]) for name in ("open", "high", "low", "close"))
    except (KeyError, TypeError, ValueError):
        return False
    return h >= max(o, c, l) and l <= min(o, c, h)


def _parse_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _timeframe_seconds(timeframe: str) -> int | None:
    value = str(timeframe).upper().strip()
    units = {"M": 60, "H": 3600, "D": 86400}
    if len(value) < 2 or value[0] not in units:
        return None
    try:
        return int(value[1:]) * units[value[0]]
    except ValueError:
        return None


class ResumableMT5HistoricalProvider:
    """Run chunked historical collection through an injected MT5-compatible gateway.

    Gateway contract:
      available_symbols() -> Iterable[str]
      earliest_available(symbol, timeframe) -> str | None
      latest_closed_bar(symbol, timeframe) -> str | None
      fetch(symbol, timeframe, start_utc, end_utc, maximum_bars) -> Iterable[OHLC rows]
    """

    def __init__(self, dataset_root: str | Path, resolver: BrokerSymbolResolver | None = None) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)
        self.resolver = resolver or BrokerSymbolResolver()

    def _latest_checkpoint(self, request_id: str) -> Mapping[str, Any] | None:
        values = self.dataset.records("historical_backfill_checkpoints")
        for envelope in reversed(values):
            record = envelope.get("record", {})
            if record.get("request_id") == request_id:
                return record
        return None

    def run(self, request: BackfillRequest, gateway: Any, maximum_batches: int | None = None) -> ProviderBackfillSummary:
        resolution = self.resolver.resolve(request.instrument, gateway.available_symbols())
        if resolution.status != "RESOLVED" or not resolution.resolved_symbol:
            summary = ProviderBackfillSummary(request.request_id, request.instrument, None, request.timeframe,
                "BLOCKED", 0, 0, 0, 0, False, None, None, resolution.reason)
            self.dataset.append("mt5_historical_provider_runs", summary.as_dict())
            return summary

        symbol = resolution.resolved_symbol
        earliest = request.start_utc or gateway.earliest_available(symbol, request.timeframe)
        latest = request.end_utc or gateway.latest_closed_bar(symbol, request.timeframe)
        if not earliest or not latest or earliest > latest:
            summary = ProviderBackfillSummary(request.request_id, request.instrument, symbol, request.timeframe,
                "NO_DATA", 0, 0, 0, 0, False, earliest, latest, "historical_range_unavailable")
            self.dataset.append("mt5_historical_provider_runs", summary.as_dict())
            return summary

        prior = self._latest_checkpoint(request.request_id)
        cursor = str(prior.get("next_start_utc")) if prior and prior.get("next_start_utc") else earliest
        resumed = bool(prior and prior.get("status") != "COMPLETED")
        known = {
            f"{env['record'].get('instrument')}|{env['record'].get('timeframe')}|{env['record'].get('timestamp_utc')}"
            for env in self.dataset.records("historical_market_bars")
        }
        received = persisted = duplicates = batches = 0
        rejected = impossible_ohlc = invalid_timestamp = missing_intervals = bytes_written = 0
        prior_timestamp: datetime | None = None
        expected_seconds = _timeframe_seconds(request.timeframe)
        final_status = "COMPLETED"
        empty_fetch = False
        while cursor <= latest:
            if maximum_batches is not None and batches >= maximum_batches:
                final_status = "PAUSED"
                break
            rows = list(gateway.fetch(symbol, request.timeframe, cursor, latest, request.maximum_bars_per_batch))
            if not rows:
                empty_fetch = True
                final_status = "NO_DATA"
                break
            rows.sort(key=lambda row: str(row["timestamp_utc"]))
            newest = cursor
            for row in rows:
                received += 1
                timestamp = str(row.get("timestamp_utc", ""))
                parsed_timestamp = _parse_utc(timestamp)
                if parsed_timestamp is None:
                    rejected += 1
                    invalid_timestamp += 1
                    continue
                if not _valid_ohlc(row):
                    rejected += 1
                    impossible_ohlc += 1
                    continue
                newest = max(newest, timestamp)
                if prior_timestamp is not None and expected_seconds:
                    delta = int((parsed_timestamp - prior_timestamp).total_seconds())
                    if delta > expected_seconds:
                        missing_intervals += max(0, delta // expected_seconds - 1)
                prior_timestamp = parsed_timestamp
                key = f"{request.instrument}|{request.timeframe}|{timestamp}"
                if key in known:
                    duplicates += 1
                    continue
                known.add(key)
                envelope = self.dataset.append("historical_market_bars", {
                    "request_id": request.request_id, "instrument": request.instrument,
                    "resolved_symbol": symbol, "timeframe": request.timeframe,
                    "timestamp_utc": timestamp, "open": float(row["open"]),
                    "high": float(row["high"]), "low": float(row["low"]),
                    "close": float(row["close"]), "volume": float(row.get("volume", 0.0)),
                    "provenance": {"provider": "MT5", "resolved_symbol": symbol},
                })
                bytes_written += len(json.dumps(envelope, sort_keys=True, ensure_ascii=False).encode("utf-8")) + 1
                persisted += 1
            batches += 1
            next_cursor = str(rows[-1].get("next_start_utc") or newest)
            if next_cursor <= cursor:
                final_status = "BLOCKED"
                break
            cursor = next_cursor
            checkpoint = HistoricalCheckpoint(request.request_id, symbol, request.timeframe, cursor,
                (int(prior.get("batches_completed", 0)) if prior else 0) + batches,
                (int(prior.get("bars_persisted", 0)) if prior else 0) + persisted,
                "IN_PROGRESS", _utc_now())
            self.dataset.append("historical_backfill_checkpoints", checkpoint.as_dict())

        checkpoint = HistoricalCheckpoint(request.request_id, symbol, request.timeframe, cursor,
            (int(prior.get("batches_completed", 0)) if prior else 0) + batches,
            (int(prior.get("bars_persisted", 0)) if prior else 0) + persisted,
            final_status, _utc_now())
        self.dataset.append("historical_backfill_checkpoints", checkpoint.as_dict())
        reason = {
            "COMPLETED": "earliest_available_to_latest_closed_bar_collection_completed",
            "PAUSED": "maximum_batches_reached_resume_available",
            "BLOCKED": "provider_cursor_did_not_advance",
            "NO_DATA": "provider_returned_no_rows_for_discovered_range",
        }[final_status]
        quality_status = "UNKNOWN" if empty_fetch else "PASS"
        if rejected:
            quality_status = "FAIL"
        elif missing_intervals:
            quality_status = "PASS_WITH_GAPS"
        quality = HistoricalDataQuality(
            accepted=persisted, rejected=rejected, duplicate_count=duplicates,
            missing_interval_count=missing_intervals, impossible_ohlc_count=impossible_ohlc,
            invalid_timestamp_count=invalid_timestamp, status=quality_status,
        )
        self.dataset.append("historical_data_quality", {
            "request_id": request.request_id, "instrument": request.instrument,
            "timeframe": request.timeframe, "generated_at": _utc_now(), **quality.as_dict(),
        })
        summary = ProviderBackfillSummary(request.request_id, request.instrument, symbol, request.timeframe,
            final_status, batches, received, persisted, duplicates, resumed, earliest, latest, reason,
            rejected, missing_intervals, quality_status, bytes_written)
        self.dataset.append("mt5_historical_provider_runs", summary.as_dict())
        return summary


class HistoricalDataDashboard:
    """Build a truthful dashboard read model from persisted loader evidence."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)
        self.root = Path(dataset_root)

    def snapshot(self, request_id: str | None = None) -> dict[str, Any]:
        runs = [item.get("record", {}) for item in self.dataset.records("mt5_historical_provider_runs")]
        checkpoints = [item.get("record", {}) for item in self.dataset.records("historical_backfill_checkpoints")]
        quality = [item.get("record", {}) for item in self.dataset.records("historical_data_quality")]
        if request_id is not None:
            runs = [item for item in runs if item.get("request_id") == request_id]
            checkpoints = [item for item in checkpoints if item.get("request_id") == request_id]
            quality = [item for item in quality if item.get("request_id") == request_id]
        latest_run = runs[-1] if runs else {}
        latest_checkpoint = checkpoints[-1] if checkpoints else {}
        latest_quality = quality[-1] if quality else {}
        total_bytes = sum(path.stat().st_size for path in self.root.glob("*.jsonl") if path.is_file())
        status = str(latest_run.get("status") or latest_checkpoint.get("status") or "NOT_STARTED")
        payload = {
            "schema_version": "historical-data-dashboard.v1",
            "generated_at": _utc_now(),
            "request_id": request_id or latest_run.get("request_id"),
            "status": status,
            "reason": latest_run.get("reason", "loader_has_not_been_started"),
            "instrument": latest_run.get("requested_symbol"),
            "resolved_symbol": latest_run.get("resolved_symbol"),
            "timeframe": latest_run.get("timeframe"),
            "coverage_start_utc": latest_run.get("earliest_available_utc"),
            "coverage_end_utc": latest_run.get("latest_closed_bar_utc"),
            "batches_completed": latest_checkpoint.get("batches_completed", latest_run.get("batches_completed", 0)),
            "bars_received": latest_run.get("bars_received", 0),
            "bars_accepted": latest_run.get("bars_persisted", 0),
            "bars_rejected": latest_run.get("bars_rejected", 0),
            "exact_duplicates": latest_run.get("duplicates_skipped", 0),
            "missing_intervals": latest_run.get("missing_interval_count", 0),
            "quality_status": latest_run.get("quality_status", latest_quality.get("status", "UNKNOWN")),
            "bytes_added_this_run": latest_run.get("bytes_written", 0),
            "total_dataset_bytes": total_bytes,
            "resumed_from_checkpoint": bool(latest_run.get("resumed_from_checkpoint", False)),
            "next_start_utc": latest_checkpoint.get("next_start_utc"),
            "updated_at": latest_checkpoint.get("updated_at"),
        }
        payload["dashboard_checksum"] = _checksum(payload)
        return payload


@dataclass(frozen=True)
class RuntimeDecisionTrace:
    trace_id: str
    profile_id: str
    symbol: str
    timestamp_utc: str
    action: str
    selected_standard_id: str | None
    selected_standard_version: str | None
    selected_policy_id: str | None
    context_match_score: float
    requested_units: int
    lot_per_unit: float
    stop_points: float | None
    target_points: float | None
    hold_policy: str
    close_policy: str
    safety_gate_requirements: tuple[str, ...]
    gate_states: Mapping[str, bool]
    execution_allowed: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["trace_checksum"] = _checksum(payload)
        return payload


class RuntimeDecisionTraceWriter:
    """Persist how a selected standard influenced one profile decision."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)

    def write(self, *, trace_id: str, profile_id: str, symbol: str, action: str,
              guidance: RuntimeStandardGuidance, gate_states: Mapping[str, bool]) -> RuntimeDecisionTrace:
        required = tuple(guidance.safety_gate_requirements)
        allowed = bool(guidance.runtime_usable and all(bool(gate_states.get(name, False)) for name in required))
        trace = RuntimeDecisionTrace(trace_id, profile_id.upper(), symbol, _utc_now(), action.upper(),
            guidance.selected_standard_id, guidance.selected_standard_version, guidance.selected_policy_id,
            guidance.context_match_score, guidance.requested_units, guidance.lot_per_unit,
            guidance.stop_points, guidance.target_points, guidance.hold_policy, guidance.close_policy,
            required, dict(gate_states), allowed,
            "all_existing_safety_gates_passed" if allowed else "standard_guidance_recorded_execution_gate_not_complete")
        self.dataset.append("runtime_decision_traces", trace.as_dict())
        return trace


@dataclass(frozen=True)
class DashboardDataContract:
    operations_page_refresh_seconds: int = 5
    operations_profiles: tuple[str, ...] = ("P1", "P2", "P3", "P4")
    intelligence_page_refresh_mode: str = "MANUAL"
    top_visible_limit: int = 10
    top_expandable_limit: int = 100
    preserve_scroll_on_manual_refresh: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DashboardResearchRanking:
    """Create deterministic Top-10 / expandable Top-100 records for dashboard use."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.dataset = AppendOnlyResearchDataset(dataset_root)

    def rank(self, rows: Sequence[Mapping[str, Any]], *, ranking_id: str, category: str,
             name_field: str = "name") -> dict[str, Any]:
        normalized = []
        for row in rows:
            normalized.append({
                "name": str(row.get(name_field, "UNNAMED")),
                "sample_size": int(row.get("sample_size", 0)),
                "win_rate": float(row.get("win_rate", 0.0)),
                "drawdown": float(row.get("drawdown", 0.0)),
                "net_profit": float(row.get("net_profit", 0.0)),
                "evidence_score": float(row.get("evidence_score", 0.0)),
                "details": dict(row.get("details", {})),
            })
        normalized.sort(key=lambda item: (-item["evidence_score"], -item["net_profit"], item["drawdown"], item["name"]))
        payload = {
            "ranking_id": ranking_id, "category": category.upper(), "generated_at": _utc_now(),
            "top_10": normalized[:10], "top_100": normalized[:100],
            "total_ranked": len(normalized), "hidden_record_count": max(0, len(normalized) - 100),
        }
        payload["ranking_checksum"] = _checksum(payload)
        self.dataset.append("dashboard_research_rankings", payload)
        return payload
