"""Unified market context engine for AFIP Production Milestone B Pack 6."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .context_transition_model import ContextTransitionModel
from .liquidity_context import LiquidityContext
from .market_state_classifier import MarketStateClassifier
from .volatility_context import VolatilityContext


@dataclass(frozen=True)
class MarketContextResult:
    """Unified market context result consumed by decision runtime."""

    status: str
    market_state: str
    volatility_state: str
    liquidity_state: str
    transition_state: str
    confidence: float
    context_score: float
    execution_quality_factor: float
    reason: str


class MarketContextEngine:
    """Combines state, volatility, liquidity, and transition context."""

    def __init__(self) -> None:
        self.market_state_classifier = MarketStateClassifier()
        self.volatility_context = VolatilityContext()
        self.liquidity_context = LiquidityContext()
        self.context_transition_model = ContextTransitionModel()

    def assess(
        self,
        metrics: Mapping[str, Any] | None = None,
        previous_state: str | None = None,
    ) -> MarketContextResult:
        """Assess market context without mutating existing runtime state."""

        data = dict(metrics or {})
        state_result = self.market_state_classifier.classify(data)
        volatility_result = self.volatility_context.assess(data)
        liquidity_result = self.liquidity_context.assess(data)
        transition_result = self.context_transition_model.evaluate(
            previous_state=previous_state,
            current_state=state_result.market_state,
        )

        context_score = round(
            (state_result.context_score * 0.40)
            + (volatility_result.confidence * 0.20)
            + (liquidity_result.confidence * 0.25)
            + (transition_result.stability_score * 0.15),
            2,
        )
        execution_quality_factor = round(
            volatility_result.adjustment_factor * liquidity_result.execution_quality_factor,
            4,
        )
        confidence = round(min(100.0, max(0.0, context_score)), 2)

        review_required = (
            volatility_result.status.endswith("REVIEW")
            or liquidity_result.status.endswith("REVIEW")
            or transition_result.status.endswith("REVIEW")
        )
        status = "MARKET_CONTEXT_REVIEW" if review_required else "MARKET_CONTEXT_READY"
        if confidence >= 70.0 and not review_required:
            status = "MARKET_CONTEXT_READY"
        elif confidence < 55.0:
            status = "MARKET_CONTEXT_REVIEW"

        reason = "|".join(
            [
                state_result.reason,
                volatility_result.reason,
                liquidity_result.reason,
                transition_result.reason,
            ]
        )
        return MarketContextResult(
            status=status,
            market_state=state_result.market_state,
            volatility_state=volatility_result.volatility_state,
            liquidity_state=liquidity_result.liquidity_state,
            transition_state=transition_result.transition_state,
            confidence=confidence,
            context_score=context_score,
            execution_quality_factor=execution_quality_factor,
            reason=reason,
        )
