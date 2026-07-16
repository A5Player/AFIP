from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ReplayJob:
    replay_id: str
    symbol: str
    timeframe: str
    start_utc: str
    end_utc: str
    status: str = "QUEUED"
    cursor_utc: str | None = None
    processed_candles: int = 0
    total_candles: int = 0
    decisions_recorded: int = 0
    exits_recorded: int = 0
    leakage_policy: str = "CANDLE_CLOSE_ONLY_NO_FUTURE_DATA"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class HistoricalReplayRecorder:
    """Deterministic candle-by-candle replay architecture; no optimization."""

    def __init__(self, root: Path | str = Path("runtime/research/replay")) -> None:
        self.root = Path(root)
        self.queue_path = self.root / "replay_queue.json"
        self.events_path = self.root / "replay_events.jsonl"
        self.statistics_path = self.root / "replay_statistics.json"

    @staticmethod
    def create_job(symbol: str, timeframe: str, start_utc: str, end_utc: str, total_candles: int = 0) -> ReplayJob:
        key = f"{symbol}|{timeframe}|{start_utc}|{end_utc}"
        replay_id = "REPLAY-" + hashlib.sha256(key.encode()).hexdigest()[:20].upper()
        return ReplayJob(replay_id, symbol, timeframe, start_utc, end_utc, total_candles=max(0, int(total_candles)))

    def _read_queue(self) -> list[dict[str, Any]]:
        if not self.queue_path.exists():
            return []
        value = json.loads(self.queue_path.read_text(encoding="utf-8"))
        return list(value.get("jobs", ()))

    def _write(self, path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(payload), indent=2, sort_keys=True), encoding="utf-8")

    def enqueue(self, job: ReplayJob) -> dict[str, Any]:
        jobs = self._read_queue()
        if not any(item.get("replay_id") == job.replay_id for item in jobs):
            jobs.append(job.as_dict())
        self._write(self.queue_path, {"updated_at_utc": _now(), "jobs": jobs})
        self._refresh_statistics(jobs)
        return job.as_dict()

    def record_candle(self, replay_id: str, candle: Mapping[str, Any], *, visible_history_end_utc: str,
                      decision: Mapping[str, Any] | None = None, exit_record: Mapping[str, Any] | None = None) -> dict[str, Any]:
        candle_utc = str(candle.get("close_time_utc", candle.get("time_utc", "")))
        if not candle_utc or candle_utc > str(visible_history_end_utc):
            raise ValueError("future_data_leakage_blocked:candle_beyond_visible_history")
        jobs = self._read_queue()
        target = next((item for item in jobs if item.get("replay_id") == replay_id), None)
        if target is None:
            raise KeyError(f"replay_job_not_found:{replay_id}")
        if target.get("cursor_utc") and candle_utc <= str(target["cursor_utc"]):
            raise ValueError("non_monotonic_replay_candle")
        target["status"] = "RUNNING"
        target["cursor_utc"] = candle_utc
        target["processed_candles"] = int(target.get("processed_candles", 0)) + 1
        target["decisions_recorded"] = int(target.get("decisions_recorded", 0)) + int(decision is not None)
        target["exits_recorded"] = int(target.get("exits_recorded", 0)) + int(exit_record is not None)
        event = {"replay_id": replay_id, "recorded_at_utc": _now(), "visible_history_end_utc": visible_history_end_utc,
                 "candle": dict(candle), "decision": dict(decision or {}), "exit": dict(exit_record or {}),
                 "future_data_used": False}
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, sort_keys=True, default=str) + "\n")
        self._write(self.queue_path, {"updated_at_utc": _now(), "jobs": jobs})
        self._refresh_statistics(jobs)
        return event

    def complete(self, replay_id: str) -> None:
        jobs = self._read_queue()
        target = next((item for item in jobs if item.get("replay_id") == replay_id), None)
        if target is None:
            raise KeyError(f"replay_job_not_found:{replay_id}")
        target["status"] = "COMPLETED"
        self._write(self.queue_path, {"updated_at_utc": _now(), "jobs": jobs})
        self._refresh_statistics(jobs)

    def _refresh_statistics(self, jobs: Iterable[Mapping[str, Any]]) -> None:
        values = list(jobs)
        total = sum(int(item.get("total_candles", 0)) for item in values)
        processed = sum(int(item.get("processed_candles", 0)) for item in values)
        self._write(self.statistics_path, {"updated_at_utc": _now(), "queued": sum(item.get("status") == "QUEUED" for item in values),
            "active": sum(item.get("status") == "RUNNING" for item in values), "completed": sum(item.get("status") == "COMPLETED" for item in values),
            "processed_candles": processed, "total_candles": total, "completed_percent": round(processed / total * 100, 2) if total else 0.0,
            "remaining_candles": max(0, total - processed), "decisions_recorded": sum(int(item.get("decisions_recorded", 0)) for item in values),
            "exits_recorded": sum(int(item.get("exits_recorded", 0)) for item in values), "optimization_enabled": False})
