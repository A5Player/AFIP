"""Deterministic registry for Production Milestone E completion evidence."""

from __future__ import annotations

from dataclasses import dataclass

from .completion_evidence import MilestoneECapabilityEvidence


@dataclass(frozen=True)
class MilestoneECompletionRegistry:
    evidence: tuple[MilestoneECapabilityEvidence, ...]

    required_pack_ids: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8, 9)

    @classmethod
    def build(cls, values: list[MilestoneECapabilityEvidence]) -> "MilestoneECompletionRegistry":
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
    def intelligence_sequence_ready(self) -> bool:
        by_pack = {item.pack_id: item for item in self.evidence}
        checks = (
            (2, "SESSION_INTELLIGENCE"),
            (3, "VOLATILITY_INTELLIGENCE"),
            (4, "MARKET_MEMORY"),
            (5, "CONFIDENCE_CALIBRATION"),
            (6, "DYNAMIC_WEIGHT_ENGINE"),
            (7, "PERFORMANCE_ATTRIBUTION"),
            (8, "PORTFOLIO_INTELLIGENCE"),
            (9, "MACRO_CONTEXT"),
        )
        return all(by_pack.get(pack_id) is not None and by_pack[pack_id].dependency == dependency for pack_id, dependency in checks)

    @property
    def knowledge_first_ready(self) -> bool:
        required = {"MARKET_MEMORY", "CONFIDENCE_CALIBRATION", "ADAPTIVE_LEARNING"}
        observed = {item.capability_name.strip().upper().replace(" ", "_") for item in self.evidence if item.is_complete}
        return required.issubset(observed)

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
            "intelligence_sequence_ready": self.intelligence_sequence_ready,
            "knowledge_first_ready": self.knowledge_first_ready,
            "completion_ratio": self.completion_ratio,
            "evidence": [item.as_dict() for item in self.evidence],
        }
