"""AFIP Dashboard Foundation report model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .engine_catalog import EngineCard
from .intelligence_catalog import IntelligenceCard
from .top10_summary import TopRankItem


@dataclass(frozen=True)
class DashboardFoundationReport:
    status: str
    reason: str
    dashboard_gate: str
    market_regime: str
    signal_context: str
    intelligence_cards: tuple[IntelligenceCard, ...]
    engine_cards: tuple[EngineCard, ...]
    top_rankings: tuple[TopRankItem, ...]
    bilingual_ready: bool
    trading_logic_changed: bool = False

    @property
    def total_cards(self) -> int:
        return len(self.intelligence_cards) + len(self.engine_cards)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason,
            "dashboard_gate": self.dashboard_gate,
            "market_regime": self.market_regime,
            "signal_context": self.signal_context,
            "intelligence_cards": [item.as_dict() for item in self.intelligence_cards],
            "engine_cards": [item.as_dict() for item in self.engine_cards],
            "top_rankings": [item.as_dict() for item in self.top_rankings],
            "bilingual_ready": self.bilingual_ready,
            "total_cards": self.total_cards,
            "trading_logic_changed": self.trading_logic_changed,
        }

    def as_text(self) -> str:
        return "\n".join(
            [
                "AFIP Dashboard Foundation",
                f"Status: {self.status}",
                f"Dashboard gate: {self.dashboard_gate}",
                f"Market regime: {self.market_regime}",
                f"Signal context: {self.signal_context}",
                f"Intelligence cards: {len(self.intelligence_cards)}",
                f"Engine cards: {len(self.engine_cards)}",
                f"Top rankings: {len(self.top_rankings)}",
                f"Decision reason: {self.reason}",
                "Trading logic changed: False",
            ]
        )
