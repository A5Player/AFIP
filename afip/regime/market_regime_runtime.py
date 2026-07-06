"""Production Milestone C Pack 16 market regime intelligence runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from .regime_classifier import RegimeClassifier
from .regime_evidence import RegimeEvidence
from .regime_profile import RegimeProfileRepository
from .regime_thresholds import RegimeThresholdLearner


@dataclass(frozen=True)
class MarketRegimeState:
    status: str
    reason: str
    repository: dict[str, object]
    thresholds: dict[str, object] | None
    classification: dict[str, object]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "reason": self.reason,
            "repository": self.repository,
            "thresholds": self.thresholds,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class MarketRegimeRuntime:
    threshold_learner: RegimeThresholdLearner = RegimeThresholdLearner()
    classifier: RegimeClassifier = RegimeClassifier()

    def run(
        self,
        evidence: Iterable[RegimeEvidence | Mapping[str, Any]],
        current_snapshot: Mapping[str, Any] | None = None,
    ) -> MarketRegimeState:
        records = [item if isinstance(item, RegimeEvidence) else RegimeEvidence.from_mapping(item) for item in evidence]
        repository = RegimeProfileRepository(records)
        repository_dict = repository.as_dict()
        thresholds = self.threshold_learner.learn(records)
        classification = self.classifier.classify(current_snapshot or {}, thresholds)
        if thresholds is None:
            return MarketRegimeState(
                status="MARKET_REGIME_DATA_REQUIRED",
                reason="insufficient_regime_evidence",
                repository=repository_dict,
                thresholds=None,
                classification=classification.as_dict(),
            )
        return MarketRegimeState(
            status="MARKET_REGIME_INTELLIGENCE_READY",
            reason="learned_regime_thresholds_applied_before_signal",
            repository=repository_dict,
            thresholds=thresholds.as_dict(),
            classification=classification.as_dict(),
        )
