"""Read-only A16 research report payload for dashboard consumers."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Iterable

from .a16_evidence import A16PolicyRanking

@dataclass(frozen=True)
class A16ResearchReport:
    status: str
    reason: str
    policy_count: int
    rankings: tuple[dict[str, object], ...]
    read_only: bool = True
    execution_authority: str = "NONE"
    automatic_promotion_allowed: bool = False

    def as_dict(self) -> dict[str, object]: return asdict(self)

def build_a16_research_report(rankings: Iterable[A16PolicyRanking]) -> A16ResearchReport:
    values = tuple(rankings)
    if not values:
        return A16ResearchReport("WAIT", "minimum_research_sample_not_met", 0, ())
    ordered = tuple(asdict(item) for item in sorted(values, key=lambda item: item.research_rank))
    return A16ResearchReport("READY", "research_ranking_available", len(ordered), ordered)
