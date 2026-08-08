"""Append-only research for observable adverse market behaviour.

This module measures what happened *after* a completed-bar label.  It is not an
order-flow feed, does not infer participant intent, and can never approve an
entry.  Its only purpose is to build cumulative evidence for later review.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from afip.market_regime_v2 import AdversarialMarketBehaviourAnalyzer


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True)
class AdversarialOutcomeObservation:
    observation_id: str
    timeframe: str
    timestamp_utc: str
    threat_state: str
    pattern_name: str
    sweep_side: str
    entry_policy: str
    range_contraction_ratio: float | None
    candle_overlap_ratio: float | None
    forward_horizon_bars: int
    upward_excursion_atr: float
    downward_excursion_atr: float
    whipsaw_observed: bool
    follow_through_direction: str
    source: str = "CLOSED_BAR_OHLC"
    execution_authority: str = "NONE"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AdversarialOutcomeLedger:
    """JSONL append-only ledger with deterministic observation identity."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root) / "adversarial_market_behaviour"
        self.path = self.root / "outcomes.jsonl"

    def existing_ids(self) -> set[str]:
        if not self.path.exists():
            return set()
        values: set[str] = set()
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, Mapping) and item.get("observation_id"):
                values.add(str(item["observation_id"]))
        return values

    def append_new(self, observations: Sequence[AdversarialOutcomeObservation]) -> int:
        existing = self.existing_ids()
        rows = [item for item in observations if item.observation_id not in existing]
        if not rows:
            return 0
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            for item in rows:
                stream.write(json.dumps(item.as_dict(), ensure_ascii=False, sort_keys=True) + "\n")
        return len(rows)

    def all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, Mapping):
                records.append(dict(item))
        return records


class AdversarialMarketBehaviourResearch:
    """Cumulative, exact-label outcome research; always research-only."""

    POLICY_ID = "AFIP-ADVERSARIAL-MARKET-BEHAVIOUR-V1"
    RECALIBRATION_INTERVAL = 1000
    MINIMUM_REVIEW_SAMPLE_SIZE = 30
    FORWARD_HORIZON_BARS = 8
    OBSERVABLE_STATES = {
        "SIDEWAY_COMPRESSION_NO_TRADE",
        "BREAKOUT_UNCONFIRMED",
        "POST_SWEEP_WAITING_CONFIRMATION",
    }

    def __init__(self, dataset_root: str | Path) -> None:
        self.ledger = AdversarialOutcomeLedger(dataset_root)
        self.summary_path = self.ledger.root / "summary.json"
        self.analyzer = AdversarialMarketBehaviourAnalyzer()

    @staticmethod
    def _identity(timeframe: str, timestamp: str, threat_state: str, pattern_name: str) -> str:
        raw = "|".join((timeframe, timestamp, threat_state, pattern_name, "V1"))
        return sha256(raw.encode("utf-8")).hexdigest()

    def _observe_timeframe(self, timeframe: str, bars: Sequence[Mapping[str, Any]]) -> list[AdversarialOutcomeObservation]:
        output: list[AdversarialOutcomeObservation] = []
        horizon = self.FORWARD_HORIZON_BARS
        for index in range(self.analyzer.minimum_bars - 1, len(bars) - horizon):
            visible = bars[: index + 1]
            behaviour = self.analyzer.analyze(visible, timeframe=timeframe)
            if behaviour.threat_state not in self.OBSERVABLE_STATES:
                continue
            close = _number(bars[index].get("close"))
            timestamp = str(bars[index].get("timestamp_utc", ""))
            recent = visible[-8:]
            ranges = [(_number(row.get("high")) or 0.0) - (_number(row.get("low")) or 0.0) for row in recent]
            reference_atr = sum(max(0.0, value) for value in ranges) / max(1, len(ranges))
            future = bars[index + 1 : index + 1 + horizon]
            highs = [_number(row.get("high")) for row in future]
            lows = [_number(row.get("low")) for row in future]
            if close is None or not timestamp or reference_atr <= 0 or any(value is None for value in highs + lows):
                continue
            up = (max(highs) - close) / reference_atr
            down = (close - min(lows)) / reference_atr
            whipsaw = up >= 0.75 and down >= 0.75
            if behaviour.sweep_side == "LOWER":
                direction = "UP" if up > down else "DOWN_OR_FAILED_RECLAIM"
            elif behaviour.sweep_side == "UPPER":
                direction = "DOWN" if down > up else "UP_OR_FAILED_RECLAIM"
            else:
                direction = "BOTH" if whipsaw else "UP" if up > down else "DOWN" if down > up else "FLAT"
            output.append(AdversarialOutcomeObservation(
                observation_id=self._identity(str(timeframe).upper(), timestamp, behaviour.threat_state, behaviour.pattern_name),
                timeframe=str(timeframe).upper(), timestamp_utc=timestamp,
                threat_state=behaviour.threat_state, pattern_name=behaviour.pattern_name,
                sweep_side=behaviour.sweep_side, entry_policy=behaviour.entry_policy,
                range_contraction_ratio=behaviour.range_contraction_ratio,
                candle_overlap_ratio=behaviour.candle_overlap_ratio,
                forward_horizon_bars=horizon, upward_excursion_atr=round(up, 6),
                downward_excursion_atr=round(down, 6), whipsaw_observed=whipsaw,
                follow_through_direction=direction,
            ))
        return output

    def _summary(self, records: Sequence[Mapping[str, Any]], appended: int) -> dict[str, Any]:
        groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
        for row in records:
            groups[(str(row.get("timeframe", "UNKNOWN")), str(row.get("threat_state", "UNKNOWN")), str(row.get("pattern_name", "UNKNOWN")))].append(row)
        rankings = []
        for (timeframe, state, name), rows in groups.items():
            sample = len(rows)
            whipsaw_rate = sum(bool(row.get("whipsaw_observed")) for row in rows) / sample * 100.0
            up = sum(float(row.get("upward_excursion_atr", 0.0) or 0.0) for row in rows) / sample
            down = sum(float(row.get("downward_excursion_atr", 0.0) or 0.0) for row in rows) / sample
            rankings.append({
                "timeframe": timeframe, "threat_state": state, "pattern_name": name,
                "sample_size": sample, "whipsaw_rate_percent": round(whipsaw_rate, 4),
                "average_upward_excursion_atr": round(up, 6), "average_downward_excursion_atr": round(down, 6),
                "research_status": "REVIEWABLE" if sample >= self.MINIMUM_REVIEW_SAMPLE_SIZE else "RESEARCH_ONLY_INSUFFICIENT_SAMPLE",
                "execution_authority": "NONE",
            })
        rankings.sort(key=lambda row: (row["research_status"] == "REVIEWABLE", row["whipsaw_rate_percent"], row["sample_size"]), reverse=True)
        previous = {}
        if self.summary_path.exists():
            try:
                previous = json.loads(self.summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeError):
                previous = {}
        total = len(records)
        milestone = total // self.RECALIBRATION_INTERVAL
        prior_milestone = int(previous.get("recalibration_milestone", 0) or 0)
        return {
            "policy_id": self.POLICY_ID, "status": "READY" if total else "WAITING",
            "reason": "cumulative_adversarial_outcome_research_ready" if total else "no_completed_forward_outcomes_available",
            "recorded_at_utc": _utc_now(), "new_observations_accepted": appended,
            "cumulative_observations": total, "recalibration_interval_patterns": self.RECALIBRATION_INTERVAL,
            "recalibration_milestone": milestone,
            "recalibration_due": milestone > prior_milestone,
            "rankings": rankings,
            "research_only": True, "execution_authority": "NONE",
        }

    def run(self, bars_by_timeframe: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, Any]:
        observations: list[AdversarialOutcomeObservation] = []
        for timeframe, bars in bars_by_timeframe.items():
            observations.extend(self._observe_timeframe(str(timeframe).upper(), tuple(bars)))
        appended = self.ledger.append_new(observations)
        summary = self._summary(self.ledger.all(), appended)
        self.ledger.root.mkdir(parents=True, exist_ok=True)
        temporary = self.summary_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        temporary.replace(self.summary_path)
        return summary
