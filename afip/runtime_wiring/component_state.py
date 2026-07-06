"""Normalized component state for deterministic runtime wiring."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _text(value: object, default: str = "UNKNOWN") -> str:
    text = str(value or default).strip().upper()
    return text or default


def _float(value: object) -> float:
    try:
        number = float(value or 0.0)
    except (TypeError, ValueError):
        number = 0.0
    return round(max(0.0, min(100.0, number)), 4)


@dataclass(frozen=True)
class RuntimeComponentState:
    """A compact runtime state record used before cross-module wiring."""

    component_key: str
    status: str
    readiness_score: float
    sequence_index: int
    evidence_count: int
    reason: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_key", _text(self.component_key))
        object.__setattr__(self, "status", _text(self.status))
        object.__setattr__(self, "readiness_score", _float(self.readiness_score))
        object.__setattr__(self, "sequence_index", max(0, int(self.sequence_index)))
        object.__setattr__(self, "evidence_count", max(0, int(self.evidence_count)))
        object.__setattr__(self, "reason", str(self.reason or "runtime_component_observed"))

    @property
    def is_ready(self) -> bool:
        return (self.status.endswith("READY") or self.status.endswith("COMPLETE")) and self.readiness_score >= 50.0 and self.evidence_count > 0

    @classmethod
    def from_mapping(cls, component_key: str, payload: Mapping[str, Any], sequence_index: int) -> "RuntimeComponentState":
        evidence = payload.get("evidence_count", payload.get("sample_count", payload.get("capability_count", 0)))
        score = payload.get("readiness_score", payload.get("confidence", payload.get("completion_score", 0.0)))
        return cls(
            component_key=component_key,
            status=str(payload.get("status", "UNKNOWN")),
            readiness_score=score,
            sequence_index=sequence_index,
            evidence_count=int(evidence or 0),
            reason=str(payload.get("reason", f"{component_key}_observed")),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "component_key": self.component_key,
            "status": self.status,
            "readiness_score": self.readiness_score,
            "sequence_index": self.sequence_index,
            "evidence_count": self.evidence_count,
            "reason": self.reason,
            "is_ready": self.is_ready,
        }
