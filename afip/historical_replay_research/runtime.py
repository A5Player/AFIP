"""Milestone T Pack 3: historical replay runner and research dataset builder.

The implementation is research-only. It walks candles in strict chronological
order, exposes only the current and previous candles to decision functions,
and writes append-only EXPERIMENTAL records. It never sends or modifies MT5
orders and it does not alter production trading logic.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from afip.research_replay import ChronologicalReplay, ReplayCandle


SnapshotProvider = Callable[[tuple[ReplayCandle, ...], "ReplayClock"], Mapping[str, Any]]
CandidateProvider = Callable[["ReplaySnapshot"], Iterable[Mapping[str, Any]]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_checksum(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReplayClock:
    replay_index: int
    replay_timestamp_utc: str
    visible_candle_count: int
    total_candle_count: int

    @property
    def progress_ratio(self) -> float:
        return self.visible_candle_count / self.total_candle_count

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["progress_ratio"] = self.progress_ratio
        return payload


@dataclass(frozen=True)
class ReplaySnapshot:
    replay_id: str
    research_run_id: str
    dataset_version: str
    scenario_id: str
    replay_clock: dict[str, Any]
    market_snapshot: dict[str, Any]
    decision_context: dict[str, Any]
    future_data_exposed: bool
    snapshot_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayCandidate:
    candidate_id: str
    replay_id: str
    research_run_id: str
    dataset_version: str
    scenario_id: str
    replay_index: int
    replay_timestamp_utc: str
    direction: str
    pattern_family: str
    setup_id: str
    confidence: float
    rationale_codes: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    research_state: str
    candidate_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayTimelineEvent:
    event_sequence: int
    event_type: str
    replay_id: str
    research_run_id: str
    replay_index: int
    replay_timestamp_utc: str
    payload_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReplayRunSummary:
    replay_id: str
    research_run_id: str
    dataset_version: str
    scenario_id: str
    bars_processed: int
    total_bars: int
    candidates_generated: int
    resumed_from_index: int
    completed: bool
    future_leakage_detected: bool
    research_state: str
    dataset_records_written: dict[str, int]
    summary_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class HistoricalSnapshotBuilder:
    """Build a deterministic snapshot from visible candles only."""

    @staticmethod
    def build_default(visible: tuple[ReplayCandle, ...], clock: ReplayClock) -> dict[str, Any]:
        latest = visible[-1]
        closes = [candle.close for candle in visible]
        direction = "FLAT"
        if len(closes) >= 2:
            if closes[-1] > closes[0]:
                direction = "BUY"
            elif closes[-1] < closes[0]:
                direction = "SELL"
        true_ranges = [candle.high - candle.low for candle in visible]
        return {
            "latest_open": latest.open,
            "latest_high": latest.high,
            "latest_low": latest.low,
            "latest_close": latest.close,
            "latest_volume": latest.volume,
            "visible_open": visible[0].open,
            "visible_high": max(candle.high for candle in visible),
            "visible_low": min(candle.low for candle in visible),
            "visible_direction": direction,
            "average_visible_range": sum(true_ranges) / len(true_ranges),
            "replay_bar_count": clock.visible_candle_count,
        }


class ResearchCandidateFactory:
    """Normalize candidate-provider output into auditable research candidates."""

    @staticmethod
    def build(
        *,
        sequence: int,
        snapshot: ReplaySnapshot,
        value: Mapping[str, Any],
    ) -> ReplayCandidate:
        direction = str(value.get("direction", "FLAT")).strip().upper()
        if direction not in {"BUY", "SELL", "FLAT", "WAIT"}:
            raise ValueError("candidate direction must be BUY, SELL, FLAT, or WAIT")
        confidence = float(value.get("confidence", 0.0))
        if confidence < 0.0 or confidence > 100.0:
            raise ValueError("candidate confidence must be between 0 and 100")
        replay_clock = snapshot.replay_clock
        base = {
            "candidate_id": f"{snapshot.replay_id}-C{sequence:08d}",
            "replay_id": snapshot.replay_id,
            "research_run_id": snapshot.research_run_id,
            "dataset_version": snapshot.dataset_version,
            "scenario_id": snapshot.scenario_id,
            "replay_index": int(replay_clock["replay_index"]),
            "replay_timestamp_utc": str(replay_clock["replay_timestamp_utc"]),
            "direction": direction,
            "pattern_family": str(value.get("pattern_family", "UNCLASSIFIED")).strip().upper(),
            "setup_id": str(value.get("setup_id", "UNSPECIFIED")).strip(),
            "confidence": confidence,
            "rationale_codes": tuple(str(item) for item in value.get("rationale_codes", ())),
            "missing_evidence": tuple(str(item) for item in value.get("missing_evidence", ())),
            "research_state": "EXPERIMENTAL",
        }
        return ReplayCandidate(candidate_checksum=_canonical_checksum(base), **base)


class AppendOnlyResearchDataset:
    """Write chain-verified JSONL datasets without mutation or replacement."""

    DATASET_NAMES = (
        "snapshots", "candidates", "decisions", "timeline", "run_summaries",
        "position_lifecycles", "exit_alternatives", "position_outcomes", "exit_quality",
        "exit_evidence_observations", "exit_context_segments", "exit_evidence_summaries",
        "exit_evidence_evaluations", "exit_policy_comparisons",
        "walk_forward_windows", "walk_forward_observations", "walk_forward_results",
        "robustness_scenarios", "robustness_results", "promotion_evidence_records",
        "research_standard_versions", "research_standard_selections", "historical_coverage_plans",
        "runtime_standard_guidance", "historical_market_bars", "historical_backfill_results",
        "historical_backfill_checkpoints", "mt5_historical_provider_runs",
        "runtime_decision_traces", "dashboard_research_rankings", "adaptive_plan_rankings",
        "complete_trade_plans", "trade_plan_certifications", "trade_plan_lifecycle_events",
        "capital_capacity_snapshots", "recovery_reconciliations",
        "certified_plan_runtime_decisions", "profile_operations_read_models",
        "position_care_snapshots", "position_care_decisions", "position_care_dashboard_records",
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, dataset_name: str) -> Path:
        if dataset_name not in self.DATASET_NAMES:
            raise ValueError(f"unknown research dataset: {dataset_name}")
        return self.root / f"{dataset_name}.jsonl"

    def append(self, dataset_name: str, record: Mapping[str, Any]) -> dict[str, Any]:
        path = self.path_for(dataset_name)
        previous_checksum = self.last_chain_checksum(dataset_name)
        envelope = {
            "dataset_name": dataset_name,
            "record_sequence": self.count(dataset_name) + 1,
            "previous_chain_checksum": previous_checksum,
            "record": dict(record),
        }
        envelope["chain_checksum"] = _canonical_checksum(envelope)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n")
        return envelope

    def records(self, dataset_name: str) -> tuple[dict[str, Any], ...]:
        path = self.path_for(dataset_name)
        if not path.exists():
            return ()
        values: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                values.append(json.loads(line))
        return tuple(values)

    def count(self, dataset_name: str) -> int:
        return len(self.records(dataset_name))

    def last_chain_checksum(self, dataset_name: str) -> str:
        records = self.records(dataset_name)
        return str(records[-1]["chain_checksum"]) if records else "GENESIS"

    def verify(self, dataset_name: str) -> bool:
        previous = "GENESIS"
        for expected_sequence, envelope in enumerate(self.records(dataset_name), start=1):
            checksum = envelope.get("chain_checksum")
            unsigned = dict(envelope)
            unsigned.pop("chain_checksum", None)
            if envelope.get("record_sequence") != expected_sequence:
                return False
            if envelope.get("previous_chain_checksum") != previous:
                return False
            if checksum != _canonical_checksum(unsigned):
                return False
            previous = str(checksum)
        return True

    def dashboard_metadata(self) -> dict[str, Any]:
        counts = {name: self.count(name) for name in self.DATASET_NAMES}
        return {
            "research_state": "EXPERIMENTAL",
            "dataset_counts": counts,
            "research_dataset_size": sum(counts.values()),
            "quarantine_size": sum(counts.values()),
            "production_usable": False,
            "append_only_verified": all(self.verify(name) for name in self.DATASET_NAMES),
        }


class ReplayResumeRegistry:
    """Read the latest completed bar for a replay without rewriting history."""

    @staticmethod
    def next_index(dataset: AppendOnlyResearchDataset, replay_id: str) -> int:
        latest = -1
        for envelope in dataset.records("timeline"):
            record = envelope["record"]
            if record.get("replay_id") == replay_id and record.get("event_type") == "BAR_PROCESSED":
                latest = max(latest, int(record["replay_index"]))
        return latest + 1


class HistoricalReplayRunner:
    """Run deterministic historical research one candle at a time."""

    def __init__(
        self,
        *,
        dataset: AppendOnlyResearchDataset,
        snapshot_provider: SnapshotProvider | None = None,
        candidate_provider: CandidateProvider | None = None,
    ) -> None:
        self.dataset = dataset
        self.snapshot_provider = snapshot_provider or HistoricalSnapshotBuilder.build_default
        self.candidate_provider = candidate_provider or (lambda snapshot: ())

    def run(
        self,
        *,
        replay_id: str,
        research_run_id: str,
        dataset_version: str,
        scenario_id: str,
        candles: Sequence[ReplayCandle | Mapping[str, Any]],
        resume: bool = False,
        maximum_bars: int | None = None,
    ) -> ReplayRunSummary:
        required = {
            "replay_id": replay_id,
            "research_run_id": research_run_id,
            "dataset_version": dataset_version,
            "scenario_id": scenario_id,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"required historical replay identifiers missing: {', '.join(sorted(missing))}")
        replay = ChronologicalReplay(candles)
        start_index = ReplayResumeRegistry.next_index(self.dataset, replay_id) if resume else 0
        if start_index > replay.candle_count:
            raise ValueError("replay resume index exceeds available candle count")
        stop_index = replay.candle_count
        if maximum_bars is not None:
            if maximum_bars <= 0:
                raise ValueError("maximum_bars must be positive")
            stop_index = min(stop_index, start_index + maximum_bars)

        candidate_sequence = self.dataset.count("candidates")
        timeline_sequence = self.dataset.count("timeline")
        bars_processed = 0
        candidates_generated = 0
        future_leakage_detected = False
        written = {name: 0 for name in AppendOnlyResearchDataset.DATASET_NAMES}

        for replay_index in range(start_index, stop_index):
            decision_context = replay.context_at(replay_index)
            visible = replay.visible_candles(replay_index)
            clock = ReplayClock(
                replay_index=replay_index,
                replay_timestamp_utc=decision_context.replay_timestamp_utc,
                visible_candle_count=decision_context.visible_candle_count,
                total_candle_count=replay.candle_count,
            )
            market_snapshot = dict(self.snapshot_provider(visible, clock))
            base = {
                "replay_id": replay_id,
                "research_run_id": research_run_id,
                "dataset_version": dataset_version,
                "scenario_id": scenario_id,
                "replay_clock": clock.as_dict(),
                "market_snapshot": market_snapshot,
                "decision_context": decision_context.as_dict(),
                "future_data_exposed": bool(decision_context.future_data_exposed),
            }
            snapshot = ReplaySnapshot(snapshot_checksum=_canonical_checksum(base), **base)
            self.dataset.append("snapshots", snapshot.as_dict())
            written["snapshots"] += 1
            future_leakage_detected = future_leakage_detected or snapshot.future_data_exposed

            generated = tuple(self.candidate_provider(snapshot))
            for candidate_value in generated:
                candidate_sequence += 1
                candidate = ResearchCandidateFactory.build(
                    sequence=candidate_sequence,
                    snapshot=snapshot,
                    value=candidate_value,
                )
                self.dataset.append("candidates", candidate.as_dict())
                written["candidates"] += 1
                candidates_generated += 1

            decision_record = {
                "replay_id": replay_id,
                "research_run_id": research_run_id,
                "dataset_version": dataset_version,
                "scenario_id": scenario_id,
                "replay_index": replay_index,
                "replay_timestamp_utc": clock.replay_timestamp_utc,
                "candidate_count": len(generated),
                "decision_status": "CANDIDATES_GENERATED" if generated else "NO_CANDIDATE",
                "future_data_exposed": snapshot.future_data_exposed,
                "research_state": "EXPERIMENTAL",
                "production_usable": False,
            }
            decision_record["decision_checksum"] = _canonical_checksum(decision_record)
            self.dataset.append("decisions", decision_record)
            written["decisions"] += 1

            timeline_sequence += 1
            event_base = {
                "event_sequence": timeline_sequence,
                "event_type": "BAR_PROCESSED",
                "replay_id": replay_id,
                "research_run_id": research_run_id,
                "replay_index": replay_index,
                "replay_timestamp_utc": clock.replay_timestamp_utc,
            }
            event = ReplayTimelineEvent(payload_checksum=_canonical_checksum(event_base), **event_base)
            self.dataset.append("timeline", event.as_dict())
            written["timeline"] += 1
            bars_processed += 1

        completed = stop_index >= replay.candle_count
        written["run_summaries"] = 1
        summary_base = {
            "replay_id": replay_id,
            "research_run_id": research_run_id,
            "dataset_version": dataset_version,
            "scenario_id": scenario_id,
            "bars_processed": bars_processed,
            "total_bars": replay.candle_count,
            "candidates_generated": candidates_generated,
            "resumed_from_index": start_index,
            "completed": completed,
            "future_leakage_detected": future_leakage_detected,
            "research_state": "EXPERIMENTAL",
            "dataset_records_written": written,
        }
        summary = ReplayRunSummary(summary_checksum=_canonical_checksum(summary_base), **summary_base)
        self.dataset.append("run_summaries", summary.as_dict())
        return summary


__all__ = [
    "AppendOnlyResearchDataset",
    "HistoricalReplayRunner",
    "HistoricalSnapshotBuilder",
    "ReplayCandidate",
    "ReplayClock",
    "ReplayResumeRegistry",
    "ReplayRunSummary",
    "ReplaySnapshot",
    "ReplayTimelineEvent",
    "ResearchCandidateFactory",
]
