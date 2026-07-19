"""AFIP Historical Data Manager public API."""

from .history_runtime import HistoricalDataManagerRuntime
from .history_report import HistoricalDataManagerReport
from .live_runtime import HistoricalDataLiveReport, HistoricalDataLiveRuntime
from .timeframe_quality import BackfillResult, GapRange, TimeframeDataQuality, TimeframeQualityEvidence
from .download_pipeline import (
    HistoricalDataDownloadPipeline,
    HistoricalDataDownloadStep,
    HistoricalDataQualityReport,
    default_download_steps,
)

__all__ = [
    "HistoricalDataDownloadPipeline",
    "HistoricalDataDownloadStep",
    "HistoricalDataManagerReport",
    "HistoricalDataManagerRuntime",
    "HistoricalDataQualityReport",
    "HistoricalDataLiveReport",
    "HistoricalDataLiveRuntime",
    "BackfillResult",
    "GapRange",
    "TimeframeDataQuality",
    "TimeframeQualityEvidence",
    "default_download_steps",
]
