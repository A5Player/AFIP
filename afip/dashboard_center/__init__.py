"""AFIP Dashboard Center foundation exports."""

from .dashboard_report import DashboardFoundationReport
from .dashboard_runtime import DashboardFoundationRuntime
from .engine_catalog import EngineCard, default_engine_catalog
from .intelligence_catalog import IntelligenceCard, default_intelligence_catalog
from .status_icon import DashboardStatusIcon, normalize_status, status_icon
from .top10_summary import TopRankItem, build_top_rankings

__all__ = [
    "DashboardFoundationReport",
    "DashboardFoundationRuntime",
    "DashboardStatusIcon",
    "EngineCard",
    "IntelligenceCard",
    "TopRankItem",
    "build_top_rankings",
    "default_engine_catalog",
    "default_intelligence_catalog",
    "normalize_status",
    "status_icon",
    "DashboardRuntimeStatus",
    "DashboardRuntimeStatusReport",
    "RuntimeServiceManager",
    "HistoricalDataDownloadPipeline",
    "ResearchCenterRuntime",
]


from afip.runtime_service_manager import RuntimeServiceManager

from .dashboard_runtime_status import DashboardRuntimeStatus, DashboardRuntimeStatusReport

from afip.historical_data_manager import HistoricalDataDownloadPipeline

from afip.research_center import ResearchCenterRuntime
