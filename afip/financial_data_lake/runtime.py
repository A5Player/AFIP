"""Append-only, traceable financial research data lake for AFIP.

This module is deliberately execution-neutral. It stores observations and
research context; it never sends trading orders and never changes execution
locks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping

_ALLOWED_LAYERS = {"raw", "normalized", "derived", "decision_context", "outcome"}
_SAFE = re.compile(r"[^A-Za-z0-9_.=-]+")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def classify_layer(layer: str) -> str:
    value = str(layer).strip().lower()
    if value not in _ALLOWED_LAYERS:
        raise ValueError(f"unsupported data-lake layer: {layer!r}")
    return value


def _safe(value: str) -> str:
    cleaned = _SAFE.sub("_", str(value).strip())
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError("partition value must not be empty")
    return cleaned


def _utc(value: datetime | str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("observed_at_utc must include timezone")
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class DataLakeRecord:
    schema_version: str
    record_id: str
    layer: str
    domain: str
    instrument: str
    source_id: str
    observed_at_utc: str
    ingested_at_utc: str
    payload: Mapping[str, Any]
    provenance: Mapping[str, Any]
    quality: Mapping[str, Any]
    research_eligibility: str
    formula_version: str | None = None
    decision_trace_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LakeWriteResult:
    status: str
    record_id: str
    relative_path: str
    checksum_sha256: str
    bytes_written: int
    duplicate: bool


class FinancialDataLake:
    """Append-only JSONL writer with deterministic IDs and daily manifests."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def build_record(
        self,
        *,
        layer: str,
        domain: str,
        instrument: str,
        source_id: str,
        observed_at_utc: datetime | str,
        payload: Mapping[str, Any],
        provenance: Mapping[str, Any],
        quality: Mapping[str, Any],
        research_eligibility: str,
        formula_version: str | None = None,
        decision_trace_id: str | None = None,
    ) -> DataLakeRecord:
        layer = classify_layer(layer)
        observed = _utc(observed_at_utc)
        stable = {
            "schema_version": "financial-data-lake.v1",
            "layer": layer,
            "domain": str(domain),
            "instrument": str(instrument),
            "source_id": str(source_id),
            "observed_at_utc": observed.isoformat(),
            "payload": dict(payload),
            "provenance": dict(provenance),
            "formula_version": formula_version,
            "decision_trace_id": decision_trace_id,
        }
        record_id = sha256(canonical_json(stable).encode("utf-8")).hexdigest()
        return DataLakeRecord(
            **stable,
            record_id=record_id,
            ingested_at_utc=datetime.now(timezone.utc).isoformat(),
            quality=dict(quality),
            research_eligibility=str(research_eligibility),
        )

    def _relative_path(self, record: DataLakeRecord) -> Path:
        dt = _utc(record.observed_at_utc)
        return Path(
            f"layer={_safe(record.layer)}",
            f"domain={_safe(record.domain)}",
            f"instrument={_safe(record.instrument)}",
            f"year={dt:%Y}", f"month={dt:%m}", f"day={dt:%d}",
            "records.jsonl",
        )

    def append(self, record: DataLakeRecord) -> LakeWriteResult:
        relative = self._relative_path(record)
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        index_path = path.with_name("record_ids.txt")
        existing = set(index_path.read_text(encoding="utf-8").splitlines()) if index_path.exists() else set()
        if record.record_id in existing:
            return LakeWriteResult("DUPLICATE_SKIPPED", record.record_id, relative.as_posix(), "", 0, True)

        line = canonical_json(record.to_dict()) + "\n"
        encoded = line.encode("utf-8")
        with path.open("ab") as stream:
            stream.write(encoded)
            stream.flush()
        with index_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(record.record_id + "\n")

        checksum = sha256(encoded).hexdigest()
        manifest = {
            "record_id": record.record_id,
            "record_checksum_sha256": checksum,
            "relative_path": relative.as_posix(),
            "bytes_written": len(encoded),
            "written_at_utc": datetime.now(timezone.utc).isoformat(),
            "schema_version": record.schema_version,
            "layer": record.layer,
            "domain": record.domain,
            "instrument": record.instrument,
            "source_id": record.source_id,
            "research_eligibility": record.research_eligibility,
        }
        with path.with_name("manifest.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(canonical_json(manifest) + "\n")
        return LakeWriteResult("APPENDED", record.record_id, relative.as_posix(), checksum, len(encoded), False)
