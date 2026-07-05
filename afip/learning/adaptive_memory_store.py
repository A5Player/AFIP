"""Production Milestone A Pack 2: lightweight adaptive learning memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping


@dataclass
class AdaptiveMemoryStore:
    """In-memory learning record store with deterministic export/import."""

    maximum_records: int = 500
    records: list[Dict[str, Any]] = field(default_factory=list)

    def add_record(self, record: Mapping[str, Any]) -> None:
        clean = {
            "group": str(record.get("group", "general")),
            "outcome": str(record.get("outcome", "UNKNOWN")).upper(),
            "entry_score": float(record.get("entry_score", 0.0) or 0.0),
            "position_confidence": float(record.get("position_confidence", 0.0) or 0.0),
            "net_points": float(record.get("net_points", 0.0) or 0.0),
        }
        self.records.append(clean)
        if len(self.records) > self.maximum_records:
            self.records = self.records[-self.maximum_records :]

    def extend(self, records: Iterable[Mapping[str, Any]]) -> None:
        for record in records:
            self.add_record(record)

    def export_state(self) -> Dict[str, Any]:
        return {"maximum_records": self.maximum_records, "records": [dict(r) for r in self.records]}

    @classmethod
    def from_state(cls, state: Mapping[str, Any]) -> "AdaptiveMemoryStore":
        store = cls(maximum_records=int(state.get("maximum_records", 500) or 500))
        store.extend(state.get("records", []) or [])
        return store

    def by_group(self, group: str) -> list[Dict[str, Any]]:
        return [dict(record) for record in self.records if record.get("group") == group]
