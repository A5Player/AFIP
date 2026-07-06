"""Runtime integration for compact market knowledge storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from afip.knowledge.knowledge_quality import KnowledgeQualityEngine
from afip.knowledge.market_knowledge_repository import MarketKnowledgeRepository
from afip.knowledge.market_pattern_repository import MarketPatternRepository
from afip.knowledge.market_snapshot_repository import MarketSnapshotRepository
from afip.research.market_signature import MarketSignatureEngine


class MarketKnowledgeRuntime:
    """Build market signatures, aggregate observations, and expose knowledge summaries."""

    def __init__(
        self,
        *,
        signature_engine: MarketSignatureEngine | None = None,
        knowledge_repository: MarketKnowledgeRepository | None = None,
        pattern_repository: MarketPatternRepository | None = None,
        snapshot_repository: MarketSnapshotRepository | None = None,
        quality_engine: KnowledgeQualityEngine | None = None,
    ) -> None:
        self.signature_engine = signature_engine or MarketSignatureEngine()
        self.knowledge_repository = knowledge_repository or MarketKnowledgeRepository()
        self.pattern_repository = pattern_repository or MarketPatternRepository()
        self.snapshot_repository = snapshot_repository or MarketSnapshotRepository()
        self.quality_engine = quality_engine or KnowledgeQualityEngine()

    def observe_dict(
        self,
        *,
        market_state: Mapping[str, object],
        result_amount: float = 0.0,
        holding_minutes: float = 0.0,
        mae: float = 0.0,
        mfe: float = 0.0,
        stage: str = "DAILY_REVIEW",
        observed_at: datetime | None = None,
    ) -> dict[str, object]:
        timestamp = observed_at or datetime.now(timezone.utc)
        signature = self.signature_engine.build(market_state).as_dict()
        knowledge_record = self.knowledge_repository.observe(
            signature=signature,
            result_amount=result_amount,
            holding_minutes=holding_minutes,
            mae=mae,
            mfe=mfe,
            observed_at=timestamp,
        )
        pattern_record = self.pattern_repository.observe(
            self._pattern_attributes(market_state),
            result_amount=result_amount,
            holding_minutes=holding_minutes,
            mae=mae,
            mfe=mfe,
        )
        snapshot = self.snapshot_repository.store(stage=stage, signature_id=str(signature["signature_id"]), data=market_state, observed_at=timestamp, important=True)
        quality = self.quality_engine.assess_dict(knowledge_record.as_dict(), now=timestamp)
        return {
            "status": "MARKET_KNOWLEDGE_RUNTIME_READY",
            "ready": True,
            "signature": signature,
            "knowledge_record": knowledge_record.as_dict(),
            "pattern_record": pattern_record.as_dict(),
            "snapshot": snapshot.as_dict() if snapshot else None,
            "quality": quality,
            "repository_summary": self.knowledge_repository.summary(),
            "pattern_summary": self.pattern_repository.summary(),
            "snapshot_summary": self.snapshot_repository.summary(),
        }

    def _pattern_attributes(self, market_state: Mapping[str, object]) -> dict[str, object]:
        return {
            "session": market_state.get("session", "UNKNOWN"),
            "market_regime": market_state.get("market_regime", "UNKNOWN"),
            "gold_market_bias": market_state.get("gold_market_bias", "NEUTRAL"),
            "event_risk_state": market_state.get("event_risk_state", "CLEAR"),
            "volatility_group": market_state.get("volatility_group", "NORMAL"),
        }
