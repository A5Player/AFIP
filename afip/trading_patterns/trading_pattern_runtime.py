"""Runtime facade for trading pattern repository integration."""

from __future__ import annotations

from dataclasses import dataclass

from afip.trading_patterns.trade_pattern_quality import TradePatternQuality
from afip.trading_patterns.trade_pattern_record import TradePatternRecord
from afip.trading_patterns.trade_pattern_repository import TradePatternRepository, TradingSetupRepository


@dataclass(frozen=True)
class TradingPatternRuntimeState:
    """State returned by the trading pattern runtime."""

    status: str
    observed_records: int
    pattern_repository: dict[str, object]
    setup_repository: dict[str, object]
    best_pattern_quality: dict[str, object]
    reason: str = "trading_pattern_runtime_ready"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "observed_records": self.observed_records,
            "pattern_repository": self.pattern_repository,
            "setup_repository": self.setup_repository,
            "best_pattern_quality": self.best_pattern_quality,
            "reason": self.reason,
        }


class TradingPatternRuntime:
    """Build compact pattern repositories from trading outcomes."""

    def __init__(
        self,
        pattern_repository: TradePatternRepository | None = None,
        setup_repository: TradingSetupRepository | None = None,
        quality: TradePatternQuality | None = None,
    ) -> None:
        self.pattern_repository = pattern_repository or TradePatternRepository()
        self.setup_repository = setup_repository or TradingSetupRepository()
        self.quality = quality or TradePatternQuality()

    def run(self, records: list[TradePatternRecord]) -> TradingPatternRuntimeState:
        for record in records:
            self.pattern_repository.observe(record)
            self.setup_repository.observe(record)
        ranked = self.pattern_repository.ranked(limit=1)
        if not records:
            return TradingPatternRuntimeState(
                status="TRADING_PATTERN_REVIEW",
                observed_records=0,
                pattern_repository=self.pattern_repository.as_dict(),
                setup_repository=self.setup_repository.as_dict(),
                best_pattern_quality={"status": "PATTERN_OBSERVE_ONLY", "quality_score": 0.0, "reasons": ["no_pattern_records"]},
                reason="no_trading_pattern_records",
            )
        best_quality = self.quality.assess(ranked[0]).as_dict() if ranked else {}
        status = "TRADING_PATTERN_READY" if best_quality.get("status") == "PATTERN_RESEARCH_READY" else "TRADING_PATTERN_REVIEW"
        reason = "trading_pattern_runtime_ready" if status == "TRADING_PATTERN_READY" else "trading_pattern_observe_only"
        return TradingPatternRuntimeState(
            status=status,
            observed_records=len(records),
            pattern_repository=self.pattern_repository.as_dict(),
            setup_repository=self.setup_repository.as_dict(),
            best_pattern_quality=best_quality,
            reason=reason,
        )
