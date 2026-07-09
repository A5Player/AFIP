"""AFIP Historical Data Manager public API."""

from .history_runtime import HistoricalDataManagerRuntime
from .history_report import HistoricalDataManagerReport

__all__ = ["HistoricalDataManagerReport", "HistoricalDataManagerRuntime"]
