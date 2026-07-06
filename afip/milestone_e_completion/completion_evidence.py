"""Completion evidence models for AFIP Production Milestone E."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _status(value: object) -> str:
    normalized = str(value or "UNKNOWN").strip().upper()
    if normalized in {"PASS", "COMPLETE", "READY"}:
        return "COMPLETE"
    if normalized in {"WAIT", "PENDING", "REVIEW"}:
        return "WAIT"
    if normalized in {"FAIL", "FAILED", "BLOCK", "BLOCKED"}:
        return "BLOCK"
    return normalized or "UNKNOWN"


def _quality(value: object) -> str:
    normalized = str(value or "UNKNOWN").strip().upper()
    if normalized in {"PASS", "READY", "COMPLETE"}:
        return "PASS"
    if normalized in {"FAIL", "FAILED", "BLOCK", "BLOCKED"}:
        return "FAIL"
    return normalized or "UNKNOWN"


@dataclass(frozen=True)
class MilestoneECapabilityEvidence:
    pack_id: int
    capability_name: str
    status: str
    quality_status: str
    sequence_order: int
    dependency: str
    runtime_entrypoint: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "pack_id", int(self.pack_id))
        object.__setattr__(self, "capability_name", str(self.capability_name or "unknown_capability").strip())
        object.__setattr__(self, "status", _status(self.status))
        object.__setattr__(self, "quality_status", _quality(self.quality_status))
        object.__setattr__(self, "sequence_order", int(self.sequence_order))
        object.__setattr__(self, "dependency", str(self.dependency or "ROOT").strip().upper())
        object.__setattr__(self, "runtime_entrypoint", str(self.runtime_entrypoint or "unknown_runtime").strip())

    @property
    def completion_key(self) -> str:
        return f"PACK_E{self.pack_id}|{self.sequence_order}|{self.capability_name.upper()}"

    @property
    def is_complete(self) -> bool:
        return self.status == "COMPLETE" and self.quality_status == "PASS"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "MilestoneECapabilityEvidence":
        return cls(
            pack_id=int(value.get("pack_id", 0)),
            capability_name=str(value.get("capability_name", value.get("name", "unknown_capability"))),
            status=str(value.get("status", "UNKNOWN")),
            quality_status=str(value.get("quality_status", value.get("quality", "UNKNOWN"))),
            sequence_order=int(value.get("sequence_order", value.get("order", 0))),
            dependency=str(value.get("dependency", "ROOT")),
            runtime_entrypoint=str(value.get("runtime_entrypoint", value.get("runtime", "unknown_runtime"))),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "pack_id": self.pack_id,
            "capability_name": self.capability_name,
            "status": self.status,
            "quality_status": self.quality_status,
            "sequence_order": self.sequence_order,
            "dependency": self.dependency,
            "runtime_entrypoint": self.runtime_entrypoint,
            "completion_key": self.completion_key,
            "is_complete": self.is_complete,
        }
