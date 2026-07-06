"""Deterministic registry for Production Milestone C completion evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_evidence import MilestoneCapabilityEvidence


@dataclass(frozen=True)
class MilestoneCompletionRegistry:
    evidence: tuple[MilestoneCapabilityEvidence, ...]

    required_pack_ids: tuple[int, ...] = (13, 14, 15, 16, 17, 18, 19)

    @classmethod
    def build(cls, values: list[MilestoneCapabilityEvidence]) -> "MilestoneCompletionRegistry":
        ordered = tuple(sorted(values, key=lambda item: (item.sequence_order, item.pack_id, item.capability_name)))
        return cls(ordered)

    @property
    def ordered_pack_ids(self) -> tuple[int, ...]:
        return tuple(item.pack_id for item in self.evidence)

    @property
    def missing_pack_ids(self) -> tuple[int, ...]:
        observed = {item.pack_id for item in self.evidence}
        return tuple(pack_id for pack_id in self.required_pack_ids if pack_id not in observed)

    @property
    def failed_capability_keys(self) -> tuple[str, ...]:
        return tuple(item.completion_key for item in self.evidence if not item.is_complete)

    @property
    def dependency_sequence_ready(self) -> bool:
        by_pack = {item.pack_id: item for item in self.evidence}
        checks = (
            (16, "LEARNING_FOUNDATION"),
            (17, "MARKET_REGIME_INTELLIGENCE"),
            (18, "DECISION_INTELLIGENCE"),
            (19, "EXECUTION_READINESS"),
        )
        return all(by_pack.get(pack_id) is not None and by_pack[pack_id].dependency == dependency for pack_id, dependency in checks)

    @property
    def completion_ratio(self) -> float:
        if not self.required_pack_ids:
            return 0.0
        complete_count = len([item for item in self.evidence if item.pack_id in self.required_pack_ids and item.is_complete])
        return round(complete_count / len(self.required_pack_ids), 4)

    def as_dict(self) -> dict[str, object]:
        return {
            "required_pack_ids": list(self.required_pack_ids),
            "ordered_pack_ids": list(self.ordered_pack_ids),
            "missing_pack_ids": list(self.missing_pack_ids),
            "failed_capability_keys": list(self.failed_capability_keys),
            "dependency_sequence_ready": self.dependency_sequence_ready,
            "completion_ratio": self.completion_ratio,
            "evidence": [item.as_dict() for item in self.evidence],
        }
