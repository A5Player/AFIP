"""Automatic research bootstrap for AFIP.

This runtime is research-only. It discovers usable historical OHLC records,
optionally collects closed bars from the locally connected MT5 terminal, and
runs a strict chronological replay into a new schema-versioned append-only
research dataset. Missing evidence is recorded and excluded from confidence
calculation rather than being treated as zero.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from afip.historical_replay_research import AppendOnlyResearchDataset, HistoricalReplayRunner, ReplayResumeRegistry
from afip.financial_data_lake import FinancialDataLake
from afip.timeframe_registry import get_mt5_timeframe_code, get_supported_timeframes
from afip.historical_data_manager.timeframe_quality import GapRange, TimeframeDataQuality

_TIMEFRAMES = get_supported_timeframes(capability="chronological_replay")
_SCHEMA_VERSION = "AFIP-RESEARCH-SCHEMA-V2"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result


def _timestamp(record: Mapping[str, Any]) -> str | None:
    for key in ("timestamp_utc", "time_utc", "closed_at_utc", "timestamp", "time"):
        value = record.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), timezone.utc).isoformat().replace("+00:00", "Z")
        text = str(value).strip()
        if text:
            return text
    return None


def _ohlc(record: Mapping[str, Any], *, source: str, timeframe: str | None = None) -> dict[str, Any] | None:
    timestamp = _timestamp(record)
    values = {name: _number(record.get(name)) for name in ("open", "high", "low", "close")}
    if not timestamp or any(value is None for value in values.values()):
        return None
    if values["high"] < values["low"]:
        return None
    volume = _number(record.get("volume", record.get("tick_volume")))
    return {
        "timestamp_utc": timestamp,
        "open": values["open"], "high": values["high"], "low": values["low"], "close": values["close"],
        "volume": 0.0 if volume is None else volume,
        "timeframe": str(record.get("timeframe", timeframe or "UNKNOWN")).upper(),
        "source": source,
    }


@dataclass(frozen=True)
class AutomaticResearchSummary:
    status: str
    reason: str
    started_at_utc: str
    completed_at_utc: str
    schema_version: str
    source_files_scanned: int
    source_records_scanned: int
    usable_bars: int
    rejected_records: int
    mt5_collection_attempted: bool
    mt5_bars_collected: int
    replay_bars_processed: int
    replay_candidates_generated: int
    replay_completed: bool
    missing_evidence_policy: str
    score_denominator_policy: str
    dataset_root: str
    historical_lake_root: str = "runtime/research/historical_data_lake"
    historical_lake_appended: int = 0
    historical_lake_duplicates: int = 0
    live_execution_enabled: bool = False
    order_send_called: bool = False
    replay_timeframe_evidence: dict[str, dict[str, Any]] | None = None
    timeframe_data_quality: dict[str, dict[str, Any]] | None = None
    gap_ranges_detected: int = 0
    missing_bars_detected: int = 0
    freshness_review_timeframes: tuple[str, ...] = ()
    backfill_ranges_requested: int = 0
    backfill_bars_returned: int = 0
    backfill_bars_accepted: int = 0

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutomaticResearchRuntime:
    """Best-effort automatic research activation with visible status evidence."""

    def __init__(self, project_root: str | Path = ".", progress: Callable[[str], None] | None = None) -> None:
        self.root = Path(project_root).resolve()
        self.output_root = self.root / "runtime" / "research" / "automatic" / "schema_v2"
        self.status_path = self.root / "runtime" / "research" / "automatic_research_status.json"
        self.historical_lake_root = self.root / "runtime" / "research" / "historical_data_lake"
        self.progress = progress

    def _report(self, message: str) -> None:
        if self.progress is not None:
            self.progress(message)

    def _write_stage(self, stage: str, reason: str) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": "RUNNING",
            "stage": stage,
            "reason": reason,
            "updated_at_utc": _utc_now(),
            "schema_version": _SCHEMA_VERSION,
            "live_execution_enabled": False,
            "order_send_called": False,
        }
        self.status_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _iter_json_records(self, path: Path) -> Iterable[Mapping[str, Any]]:
        try:
            if path.suffix.lower() == ".jsonl":
                for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                    if not line.strip():
                        continue
                    value = json.loads(line)
                    if isinstance(value, Mapping):
                        yield value.get("record", value) if isinstance(value.get("record", value), Mapping) else value
                return
            value = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            if isinstance(value, Mapping):
                candidate = value.get("records", value.get("bars", value.get("data", value)))
                if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes)):
                    for item in candidate:
                        if isinstance(item, Mapping):
                            yield item.get("record", item) if isinstance(item.get("record", item), Mapping) else item
                else:
                    yield value.get("record", value) if isinstance(value.get("record", value), Mapping) else value
            elif isinstance(value, Sequence):
                for item in value:
                    if isinstance(item, Mapping):
                        yield item
        except (OSError, json.JSONDecodeError, UnicodeError):
            return

    def discover_bars(self) -> tuple[list[dict[str, Any]], int, int, int]:
        bars: dict[tuple[str, str], dict[str, Any]] = {}
        files = scanned = rejected = 0
        roots = (
            self.root / "runtime" / "research",
            self.root / "data" / "research",
            self.root / "data" / "knowledge",
            self.root / "data" / "historical",
        )
        for base in roots:
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in {".json", ".jsonl"}:
                    continue
                if path == self.status_path or self.output_root in path.parents:
                    continue
                files += 1
                for record in self._iter_json_records(path):
                    scanned += 1
                    bar = _ohlc(record, source=str(path.relative_to(self.root)))
                    if bar is None:
                        rejected += 1
                        continue
                    key = (bar["timeframe"], bar["timestamp_utc"])
                    bars[key] = bar
        ordered = sorted(bars.values(), key=lambda item: (item["timeframe"], item["timestamp_utc"]))
        return ordered, files, scanned, rejected

    def collect_mt5_bars(self, maximum_per_timeframe: int = 5000) -> list[dict[str, Any]]:
        if os.name != "nt":
            return []
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception:
            return []
        values: list[dict[str, Any]] = []
        mapping = {
            name: get_mt5_timeframe_code(mt5, name)
            for name in get_supported_timeframes(capability="historical_collection")
        }
        initialized_here = False
        try:
            if mt5.terminal_info() is None:
                if not mt5.initialize():
                    return []
                initialized_here = True
            symbols = {str(item.name).upper(): str(item.name) for item in (mt5.symbols_get() or ())}
            symbol = next((symbols[name] for name in ("GOLD#", "GOLD", "XAUUSD", "XAUUSD#") if name in symbols), None)
            if not symbol:
                return []
            mt5.symbol_select(symbol, True)
            for name, code in mapping.items():
                self._report(f"MT5 history: loading {symbol} {name} (up to {maximum_per_timeframe} closed bars)")
                rows = mt5.copy_rates_from_pos(symbol, code, 1, maximum_per_timeframe)
                if rows is None:
                    self._report(f"MT5 history: {name} returned no bars")
                    continue
                self._report(f"MT5 history: {name} received {len(rows)} bars")
                for row in rows:
                    record = {field: row[field].item() if hasattr(row[field], "item") else row[field] for field in row.dtype.names}
                    bar = _ohlc(record, source=f"MT5:{symbol}", timeframe=name)
                    if bar is not None:
                        values.append(bar)
        except Exception:
            return values
        finally:
            if initialized_here:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
        return values

    def persist_historical_bars(self, bars: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
        """Persist normalized closed bars into the append-only financial data lake."""
        lake = FinancialDataLake(self.historical_lake_root)
        records = []
        for bar in bars:
            timeframe = str(bar.get("timeframe", "UNKNOWN")).upper()
            records.append(lake.build_record(
                layer="normalized", domain="market_ohlc", instrument="GOLD#",
                source_id=str(bar.get("source", "MT5:GOLD#")), observed_at_utc=str(bar["timestamp_utc"]),
                payload={"timeframe": timeframe, "open": float(bar["open"]), "high": float(bar["high"]),
                         "low": float(bar["low"]), "close": float(bar["close"]), "volume": float(bar.get("volume", 0.0)),
                         "closed_bar": True},
                provenance={"provider": "MT5", "collection_runtime": "automatic_research_runtime", "timeframe": timeframe},
                quality={"ohlc_valid": True, "timeframe_registered": timeframe in _TIMEFRAMES},
                research_eligibility="ELIGIBLE" if timeframe in _TIMEFRAMES else "QUARANTINED",
            ))
        results = lake.append_many(tuple(records))
        return sum(not item.duplicate for item in results), sum(item.duplicate for item in results)


    def collect_mt5_gap_backfill(self, gaps: Sequence[GapRange], *, maximum_requests: int = 25) -> list[dict[str, Any]]:
        """Best-effort closed-bar backfill for detected ranges; never sends orders."""
        if os.name != "nt" or not gaps or maximum_requests <= 0:
            return []
        try:
            import MetaTrader5 as mt5  # type: ignore
        except Exception:
            return []
        initialized_here = False
        values: list[dict[str, Any]] = []
        try:
            if mt5.terminal_info() is None:
                if not mt5.initialize():
                    return []
                initialized_here = True
            symbols = {str(item.name).upper(): str(item.name) for item in (mt5.symbols_get() or ())}
            symbol = next((symbols[name] for name in ("GOLD#", "GOLD", "XAUUSD", "XAUUSD#") if name in symbols), None)
            if not symbol:
                return []
            mt5.symbol_select(symbol, True)
            for gap in tuple(gaps)[:maximum_requests]:
                code = get_mt5_timeframe_code(mt5, gap.timeframe)
                start = datetime.fromisoformat(gap.after_timestamp_utc.replace("Z", "+00:00"))
                end = datetime.fromisoformat(gap.before_timestamp_utc.replace("Z", "+00:00"))
                rows = mt5.copy_rates_range(symbol, code, start, end)
                if rows is None:
                    continue
                for row in rows:
                    record = {field: row[field].item() if hasattr(row[field], "item") else row[field] for field in row.dtype.names}
                    bar = _ohlc(record, source=f"MT5_BACKFILL:{symbol}", timeframe=gap.timeframe)
                    if bar is not None:
                        values.append(bar)
        except Exception:
            return values
        finally:
            if initialized_here:
                try:
                    mt5.shutdown()
                except Exception:
                    pass
        return values

    @staticmethod
    def _candidate_provider(snapshot: Any) -> tuple[dict[str, Any], ...]:
        market = snapshot.market_snapshot
        available: list[tuple[str, float, float]] = []
        missing: list[str] = []
        latest_close = _number(market.get("latest_close"))
        visible_open = _number(market.get("visible_open"))
        latest_open = _number(market.get("latest_open"))
        average_range = _number(market.get("average_visible_range"))
        latest_volume = _number(market.get("latest_volume"))

        if latest_close is not None and visible_open is not None:
            available.append(("trend", 45.0, 1.0 if latest_close > visible_open else -1.0 if latest_close < visible_open else 0.0))
        else:
            missing.append("trend_price_history")
        if latest_close is not None and latest_open is not None:
            available.append(("momentum", 30.0, 1.0 if latest_close > latest_open else -1.0 if latest_close < latest_open else 0.0))
        else:
            missing.append("momentum_open_close")
        if average_range is not None and average_range > 0:
            available.append(("volatility", 15.0, 0.25))
        else:
            missing.append("volatility_range")
        if latest_volume is not None and latest_volume > 0:
            available.append(("volume", 10.0, 0.25))
        else:
            missing.append("volume")

        denominator = sum(weight for _, weight, _ in available)
        if denominator <= 0:
            return ()
        signed = sum(weight * signal for _, weight, signal in available) / denominator
        direction = "BUY" if signed > 0.08 else "SELL" if signed < -0.08 else "WAIT"
        confidence = round(min(100.0, abs(signed) * 100.0), 2)
        return ({
            "direction": direction,
            "pattern_family": "AUTOMATIC_EVIDENCE_REPLAY",
            "setup_id": "AVAILABLE_EVIDENCE_ONLY",
            "confidence": confidence,
            "rationale_codes": tuple(f"{name}_available" for name, _, _ in available),
            "missing_evidence": tuple(missing),
        },)

    def _write_status(self, summary: AutomaticResearchSummary) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        self.status_path.write_text(json.dumps(summary.as_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def run(self, *, collect_mt5_when_needed: bool = True, maximum_replay_bars: int = 2000) -> AutomaticResearchSummary:
        started = _utc_now()
        self._write_stage("DISCOVER_LOCAL_DATA", "scanning_existing_research_and_historical_files")
        self._report("[1/5] Scanning existing research and historical files...")
        bars, files, scanned, rejected = self.discover_bars()
        self._report(f"      Files: {files} | Records: {scanned} | Usable OHLC: {len(bars)} | Non-OHLC: {rejected}")
        mt5_attempted = False
        mt5_bars: list[dict[str, Any]] = []
        if collect_mt5_when_needed and len(bars) < 100:
            mt5_attempted = True
            self._write_stage("COLLECT_MT5_HISTORY", "local_ohlc_below_minimum_attempting_mt5_history")
            self._report("[2/5] Local OHLC is insufficient; collecting closed bars from MT5...")
            mt5_bars = self.collect_mt5_bars(maximum_per_timeframe=max(500, maximum_replay_bars))
            self._report(f"      MT5 bars collected: {len(mt5_bars)}")
            merged = {(item["timeframe"], item["timestamp_utc"]): item for item in bars}
            for item in mt5_bars:
                merged[(item["timeframe"], item["timestamp_utc"])] = item
            bars = sorted(merged.values(), key=lambda item: (item["timeframe"], item["timestamp_utc"]))

        lake_appended = lake_duplicates = 0
        if mt5_bars:
            self._write_stage("PERSIST_HISTORICAL_DATA_LAKE", "persisting_closed_mt5_bars_append_only")
            self._report("      Persisting MT5 closed bars to append-only historical data lake...")
            lake_appended, lake_duplicates = self.persist_historical_bars(mt5_bars)
            self._report(f"      Historical lake: appended {lake_appended} | duplicates {lake_duplicates}")

        quality_engine = TimeframeDataQuality()
        quality_evidence_objects = quality_engine.evaluate(bars)
        initial_gaps = tuple(
            gap for timeframe in _TIMEFRAMES
            for gap in quality_evidence_objects[timeframe].gaps
        )
        backfill_returned = backfill_accepted = 0
        if collect_mt5_when_needed and initial_gaps:
            self._write_stage("AUTOMATIC_GAP_BACKFILL", "requesting_detected_mt5_historical_gaps")
            self._report(f"      Automatic backfill: requesting up to {min(25, len(initial_gaps))} detected ranges")
            returned = self.collect_mt5_gap_backfill(initial_gaps, maximum_requests=25)
            backfill_returned = len(returned)
            if returned:
                result = quality_engine.backfill(
                    bars, quality_evidence_objects, lambda gap: (
                        item for item in returned
                        if item.get("timeframe") == gap.timeframe
                        and gap.after_timestamp_utc < str(item.get("timestamp_utc", "")) < gap.before_timestamp_utc
                    )
                )
                backfill_accepted = result.accepted_bars
                bars = list(result.merged_bars)
                quality_evidence_objects = quality_engine.evaluate(bars)
                if backfill_accepted:
                    appended, duplicates = self.persist_historical_bars(returned)
                    lake_appended += appended
                    lake_duplicates += duplicates
            self._report(f"      Automatic backfill: returned {backfill_returned} | accepted {backfill_accepted}")
        quality_evidence = {name: item.as_dict() for name, item in quality_evidence_objects.items()}
        gap_ranges_detected = sum(item.gap_count for item in quality_evidence_objects.values())
        missing_bars_detected = sum(item.missing_bars for item in quality_evidence_objects.values())
        freshness_review = tuple(
            name for name, item in quality_evidence_objects.items() if item.fresh is False
        )
        self._report(
            f"      Data quality: gaps {gap_ranges_detected} | missing bars {missing_bars_detected} "
            f"| freshness review {len(freshness_review)}"
        )

        processed = candidates = 0
        completed = False
        replay_evidence: dict[str, dict[str, Any]] = {}
        self._write_stage("REPLAY_RESEARCH", "running_chronological_replay_with_available_evidence")
        self._report("[3/5] Running chronological replay by timeframe...")
        reason = "historical_bars_unavailable"
        status = "WAITING"
        if bars:
            # Run each timeframe independently so chronology never mixes unlike bars.
            dataset = AppendOnlyResearchDataset(self.output_root)
            for timeframe in _TIMEFRAMES:
                candles = [item for item in bars if item["timeframe"] == timeframe]
                if not candles:
                    continue
                base_replay_id = f"AUTO-{_SCHEMA_VERSION}-{timeframe}"
                first_timestamp = str(candles[0].get("timestamp_utc", ""))
                last_timestamp = str(candles[-1].get("timestamp_utc", ""))
                window_identity = hashlib.sha256(
                    f"{timeframe}|{len(candles)}|{first_timestamp}|{last_timestamp}".encode("utf-8")
                ).hexdigest()[:12].upper()
                # A replay checkpoint is valid only for the exact immutable source window.
                # Legacy base IDs do not encode first/last timestamps and therefore cannot
                # prove coverage when a fixed-size MT5 window moves. New work always uses a
                # generation ID derived from timeframe, count, first timestamp, and last timestamp.
                legacy_next = ReplayResumeRegistry.next_index(dataset, base_replay_id)
                replay_id = f"{base_replay_id}-GEN-{window_identity}"
                next_index = ReplayResumeRegistry.next_index(dataset, replay_id)
                selection_reason = "new_window_generation"
                if next_index > len(candles):
                    selection_reason = "stale_generation_checkpoint_recovery"
                    replay_id = f"{replay_id}-RECOVERY-{len(candles)}"
                    next_index = ReplayResumeRegistry.next_index(dataset, replay_id)
                    self._report(
                        f"      Replay {timeframe}: stale generation checkpoint exceeds "
                        f"available bars {len(candles)}; starting recovery generation"
                    )
                elif next_index > 0:
                    selection_reason = "exact_window_checkpoint_continuation"
                elif legacy_next > 0:
                    selection_reason = "legacy_checkpoint_not_coverage_provable"
                    legacy_label = "stale checkpoint" if legacy_next > len(candles) else "legacy checkpoint"
                    self._report(
                        f"      Replay {timeframe}: {legacy_label} {legacy_next} cannot prove "
                        f"coverage for window {window_identity}; replaying exact window from index 0"
                    )
                self._report(f"      Replay {timeframe}: {len(candles)} bars")
                runner = HistoricalReplayRunner(dataset=dataset, candidate_provider=self._candidate_provider)
                summary = runner.run(
                    replay_id=replay_id,
                    research_run_id=f"AUTO-STARTUP-{timeframe}",
                    dataset_version=_SCHEMA_VERSION,
                    scenario_id=f"GOLD-{timeframe}-AVAILABLE-DATA",
                    candles=candles,
                    resume=True,
                    maximum_bars=min(maximum_replay_bars, max(1, len(candles))),
                )
                processed += summary.bars_processed
                candidates += summary.candidates_generated
                completed = completed or summary.completed
                replay_evidence[timeframe] = {
                    "timeframe": timeframe,
                    "available_bars": len(candles),
                    "first_timestamp_utc": first_timestamp,
                    "last_timestamp_utc": last_timestamp,
                    "window_identity": window_identity,
                    "replay_id": replay_id,
                    "legacy_checkpoint_next_index": legacy_next,
                    "resumed_from_index": summary.resumed_from_index,
                    "bars_processed_this_run": summary.bars_processed,
                    "covered_bars_after_run": summary.resumed_from_index + summary.bars_processed,
                    "coverage_complete": summary.completed,
                    "selection_reason": selection_reason,
                    "candidates_generated_this_run": summary.candidates_generated,
                }
                self._report(
                    f"      Replay {timeframe}: processed {summary.bars_processed}, "
                    f"coverage {summary.resumed_from_index + summary.bars_processed}/{len(candles)}, "
                    f"reason {selection_reason}"
                )
            status = "READY" if processed else "REVIEW"
            reason = "automatic_research_replay_updated" if processed else "research_dataset_already_current"

        self._write_stage("WRITE_RESEARCH_STATUS", "writing_research_summary_for_dashboard")
        self._report("[4/5] Writing research status and dataset evidence...")
        result = AutomaticResearchSummary(
            status=status, reason=reason, started_at_utc=started, completed_at_utc=_utc_now(),
            schema_version=_SCHEMA_VERSION, source_files_scanned=files, source_records_scanned=scanned,
            usable_bars=len(bars), rejected_records=rejected, mt5_collection_attempted=mt5_attempted,
            mt5_bars_collected=len(mt5_bars), replay_bars_processed=processed,
            replay_candidates_generated=candidates, replay_completed=completed,
            missing_evidence_policy="RECORD_AS_MISSING_AND_EXCLUDE_FROM_SCORE",
            score_denominator_policy="AVAILABLE_EVIDENCE_WEIGHT_ONLY",
            dataset_root=str(self.output_root.relative_to(self.root)),
            historical_lake_root=str(self.historical_lake_root.relative_to(self.root)),
            historical_lake_appended=lake_appended, historical_lake_duplicates=lake_duplicates,
            replay_timeframe_evidence=replay_evidence,
            timeframe_data_quality=quality_evidence,
            gap_ranges_detected=gap_ranges_detected,
            missing_bars_detected=missing_bars_detected,
            freshness_review_timeframes=freshness_review,
            backfill_ranges_requested=min(25, len(initial_gaps)),
            backfill_bars_returned=backfill_returned,
            backfill_bars_accepted=backfill_accepted,
        )
        self._write_status(result)
        self._report(f"[5/5] Complete: {result.status} | {result.reason} | usable bars {result.usable_bars} | replay {result.replay_bars_processed}")
        return result
