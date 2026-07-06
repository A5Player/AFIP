"""Production Milestone C Pack 7 market knowledge runtime."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from afip.knowledge.knowledge_runtime import MarketKnowledgeRuntime


class ProductionMilestoneCMarketKnowledgeRuntime:
    """Run compact market knowledge updates for one or more observations."""

    def __init__(self, *, knowledge_runtime: MarketKnowledgeRuntime | None = None) -> None:
        self.knowledge_runtime = knowledge_runtime or MarketKnowledgeRuntime()

    def run_dict(self, observations: Iterable[Mapping[str, object]] | None = None, *, now: datetime | None = None) -> dict[str, object]:
        timestamp = now or datetime.now(timezone.utc)
        results: list[dict[str, object]] = []
        for item in observations or []:
            market_state = item.get("market_state", {})
            if not isinstance(market_state, Mapping):
                market_state = {}
            results.append(
                self.knowledge_runtime.observe_dict(
                    market_state=market_state,
                    result_amount=self._to_float(item.get("result_amount"), 0.0),
                    holding_minutes=self._to_float(item.get("holding_minutes"), 0.0),
                    mae=self._to_float(item.get("mae"), 0.0),
                    mfe=self._to_float(item.get("mfe"), 0.0),
                    stage=str(item.get("stage", "DAILY_REVIEW")),
                    observed_at=timestamp,
                )
            )
        return {
            "status": "PRODUCTION_MILESTONE_C_KNOWLEDGE_RUNTIME_READY",
            "ready": True,
            "processed_observations": len(results),
            "latest_result": results[-1] if results else None,
            "repository_summary": self.knowledge_runtime.knowledge_repository.summary(),
            "pattern_summary": self.knowledge_runtime.pattern_repository.summary(),
            "snapshot_summary": self.knowledge_runtime.snapshot_repository.summary(),
            "results": results,
            "reason": "market_knowledge_base_updated",
        }

    @staticmethod
    def _to_float(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
