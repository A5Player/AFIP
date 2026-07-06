"""Trading pattern research package for AFIP."""

from afip.trading_patterns.trade_outcome_statistics import TradeOutcomeStatistics
from afip.trading_patterns.trade_pattern_quality import TradePatternQuality, TradePatternQualityResult
from afip.trading_patterns.trade_pattern_record import TradePatternRecord
from afip.trading_patterns.trade_pattern_repository import TradePatternRepository, TradingSetupRepository
from afip.trading_patterns.trading_pattern_runtime import TradingPatternRuntime, TradingPatternRuntimeState

__all__ = [
    "TradeOutcomeStatistics",
    "TradePatternQuality",
    "TradePatternQualityResult",
    "TradePatternRecord",
    "TradePatternRepository",
    "TradingSetupRepository",
    "TradingPatternRuntime",
    "TradingPatternRuntimeState",
]
