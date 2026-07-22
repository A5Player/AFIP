"""Single runtime progress authority for AFIP historical loading, replay and research."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Mapping

SCHEMA_VERSION = "AFIP-RUNTIME-OBSERVATORY-V1"
VALID_STATES = {"RUNNING", "WAITING", "STALLED", "COMPLETED", "FAILED"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


class RuntimeProgressAuthority:
    """Own the canonical read-only runtime progress snapshot and append-only timeline."""

    def __init__(self, root: str | Path = ".", *, stalled_after_seconds: int = 120) -> None:
        self.root = Path(root).resolve()
        self.status_path = self.root / "runtime/research/runtime_observatory_status.json"
        self.timeline_path = self.root / "runtime/research/runtime_observatory_timeline.jsonl"
        self.stalled_after_seconds = max(10, int(stalled_after_seconds))
        self._started_monotonic = time.monotonic()
        self._processed_at_start = 0

    def read(self) -> dict[str, Any]:
        try:
            value = json.loads(self.status_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError, UnicodeError):
            return {}

    def update(self, *, state: str, stage: str, activity: str, **values: Any) -> dict[str, Any]:
        normalized = str(state).upper()
        if normalized not in VALID_STATES:
            raise ValueError(f"invalid runtime observatory state: {state}")
        previous = self.read()
        now = _utc_now()
        payload = {
            **previous,
            **values,
            "schema_version": SCHEMA_VERSION,
            "status": normalized,
            "stage": str(stage),
            "current_activity": str(activity),
            "heartbeat_utc": now,
            "updated_at_utc": now,
            "process_id": os.getpid(),
            "execution_authority": False,
            "order_send_called": False,
        }
        _atomic_json(self.status_path, payload)
        event = {
            "timestamp_utc": now,
            "status": normalized,
            "stage": str(stage),
            "activity": str(activity),
            "current_timeframe": payload.get("current_timeframe"),
            "replay_processed": payload.get("replay_processed", 0),
            "replay_total": payload.get("replay_total", 0),
            "current_replay_timestamp_utc": payload.get("current_replay_timestamp_utc"),
        }
        self.timeline_path.parent.mkdir(parents=True, exist_ok=True)
        with self.timeline_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
        return payload

    def replay_update(self, *, timeframe: str, replay_index: int, processed: int, total: int,
                      candle_timestamp_utc: str, candidates: int = 0, resumed_from_index: int = 0) -> dict[str, Any]:
        elapsed = max(0.001, time.monotonic() - self._started_monotonic)
        effective_processed = max(0, int(processed) - self._processed_at_start)
        speed = effective_processed / elapsed
        remaining = max(0, int(total) - int(processed))
        eta = remaining / speed if speed > 0 else None
        percent = min(100.0, max(0.0, (int(processed) * 100.0 / int(total)))) if int(total) > 0 else 0.0
        return self.update(
            state="RUNNING", stage="HISTORICAL_REPLAY",
            activity=f"Replay {timeframe} {processed}/{total}",
            current_timeframe=str(timeframe).upper(), current_replay_index=int(replay_index),
            replay_processed=int(processed), replay_total=int(total), replay_percent=round(percent, 4),
            replay_speed_bars_per_second=round(speed, 3), eta_seconds=None if eta is None else round(eta, 1),
            current_replay_timestamp_utc=str(candle_timestamp_utc), last_processed_candle_utc=str(candle_timestamp_utc),
            replay_candidates=int(candidates), resumed_from_index=int(resumed_from_index),
        )

    def classified(self, now: datetime | None = None) -> dict[str, Any]:
        payload = self.read()
        if not payload:
            return {"status": "WAITING", "reason": "runtime_progress_not_recorded"}
        if payload.get("status") != "RUNNING":
            return payload
        heartbeat = _parse_utc(payload.get("heartbeat_utc"))
        current = now or datetime.now(timezone.utc)
        if heartbeat is not None and (current - heartbeat).total_seconds() > self.stalled_after_seconds:
            return {**payload, "status": "STALLED", "reason": "heartbeat_timeout"}
        return payload
