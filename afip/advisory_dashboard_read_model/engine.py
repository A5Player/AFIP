from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

READ_MODEL_READY = "READ_MODEL_READY"
READ_MODEL_STALE = "READ_MODEL_STALE"
READ_MODEL_BLOCKED = "READ_MODEL_BLOCKED"
READ_MODEL_WAIT = "READ_MODEL_WAIT"

EXPECTED_SCHEMA = "AFIP_ADVISORY_SNAPSHOT_V1"


@dataclass(frozen=True)
class AdvisoryDashboardReadModel:
    status: str
    reason: str
    schema_version: str
    snapshot_id: str
    certification_status: str
    trace_status: str
    case_id: str
    generated_at_utc: str
    age_seconds: int
    stage_count: int
    stage_summary: Sequence[Mapping[str, Any]]
    source_digest: str
    display_ready: bool
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class AdvisoryDashboardReadModelRuntime:
    """Read-only dashboard consumer for the W11 advisory snapshot."""

    def __init__(self, max_age_seconds: int = 300) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        self.max_age_seconds = int(max_age_seconds)

    @staticmethod
    def _parse_utc(value: str) -> datetime:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _required_fields_present(snapshot: Mapping[str, Any]) -> bool:
        required = (
            "schema_version",
            "snapshot_id",
            "status",
            "generated_at_utc",
            "certification_status",
            "trace_status",
            "case_id",
            "stage_summary",
            "source_digest",
        )
        return all(key in snapshot for key in required)

    @staticmethod
    def _digest_shape_valid(value: Any) -> bool:
        text = str(value)
        return len(text) == 64 and all(ch in "0123456789abcdef" for ch in text.lower())

    def build(
        self,
        snapshot: Mapping[str, Any],
        now_utc: datetime | None = None,
    ) -> AdvisoryDashboardReadModel:
        now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)

        def result(status: str, reason: str, age_seconds: int = 0) -> AdvisoryDashboardReadModel:
            stages = tuple(snapshot.get("stage_summary", ()) or ())
            return AdvisoryDashboardReadModel(
                status=status,
                reason=reason,
                schema_version=str(snapshot.get("schema_version", "")),
                snapshot_id=str(snapshot.get("snapshot_id", "")),
                certification_status=str(snapshot.get("certification_status", "")),
                trace_status=str(snapshot.get("trace_status", "")),
                case_id=str(snapshot.get("case_id", "")),
                generated_at_utc=str(snapshot.get("generated_at_utc", "")),
                age_seconds=max(0, int(age_seconds)),
                stage_count=len(stages),
                stage_summary=stages,
                source_digest=str(snapshot.get("source_digest", "")),
                display_ready=status == READ_MODEL_READY,
            )

        if not self._required_fields_present(snapshot):
            return result(READ_MODEL_WAIT, "snapshot_required_fields_missing")

        if str(snapshot.get("schema_version")) != EXPECTED_SCHEMA:
            return result(READ_MODEL_BLOCKED, "snapshot_schema_unsupported")

        if not self._digest_shape_valid(snapshot.get("source_digest")):
            return result(READ_MODEL_BLOCKED, "snapshot_digest_invalid")

        try:
            generated = self._parse_utc(str(snapshot.get("generated_at_utc")))
        except (TypeError, ValueError):
            return result(READ_MODEL_BLOCKED, "snapshot_timestamp_invalid")

        age = int((now - generated).total_seconds())
        if age < 0:
            return result(READ_MODEL_BLOCKED, "snapshot_timestamp_in_future", age_seconds=0)

        if str(snapshot.get("status")) == "SNAPSHOT_BLOCKED":
            return result(READ_MODEL_BLOCKED, "upstream_snapshot_blocked", age_seconds=age)

        if str(snapshot.get("status")) != "SNAPSHOT_READY":
            return result(READ_MODEL_WAIT, "upstream_snapshot_not_ready", age_seconds=age)

        if age > self.max_age_seconds:
            return result(READ_MODEL_STALE, "snapshot_freshness_expired", age_seconds=age)

        if snapshot.get("certification_status") != "CERTIFIED":
            return result(READ_MODEL_BLOCKED, "certification_not_certified", age_seconds=age)

        if snapshot.get("trace_status") != "TRACE_COMPLETE":
            return result(READ_MODEL_BLOCKED, "trace_not_complete", age_seconds=age)

        return result(READ_MODEL_READY, "dashboard_read_model_ready", age_seconds=age)

    def load(self, path: str | Path, now_utc: datetime | None = None) -> AdvisoryDashboardReadModel:
        source = Path(path)
        if not source.is_file():
            return self.build({}, now_utc=now_utc)
        try:
            snapshot = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            snapshot = {
                "schema_version": EXPECTED_SCHEMA,
                "snapshot_id": "",
                "status": "SNAPSHOT_BLOCKED",
                "generated_at_utc": "",
                "certification_status": "",
                "trace_status": "",
                "case_id": "",
                "stage_summary": (),
                "source_digest": "",
            }
        return self.build(snapshot, now_utc=now_utc)
