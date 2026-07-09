"""Production readiness models for Production Milestone H Pack 10."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DeploymentStep:
    step_id: str
    english_name: str
    thai_name: str
    status: str
    reason: str
    required_before_demo: bool
    blocks_live_execution: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DemoTradingReadiness:
    status: str
    broker: str
    symbol: str
    profile_name: str
    execution_mode: str
    demo_order_enabled: bool
    live_execution_enabled: bool
    reason: str
    validation_items: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductionReadinessReport:
    status: str
    reason: str
    release_stage: str
    broker: str
    symbol: str
    profile_name: str
    vps_ready: bool
    historical_data_ready: bool
    walk_forward_ready: bool
    research_ready: bool
    paper_trading_ready: bool
    dashboard_ready: bool
    demo_trading_ready: bool
    live_execution_enabled: bool
    trading_logic_changed: bool
    deployment_steps: tuple[DeploymentStep, ...]
    demo_readiness: DemoTradingReadiness
    dashboard_sections: tuple[str, ...]
    handoff_items: tuple[str, ...]
    validation_items: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_text(self) -> str:
        return (
            "AFIP Production Readiness\n"
            f"Status: {self.status}\n"
            f"Reason: {self.reason}\n"
            f"Release Stage: {self.release_stage}\n"
            f"Broker: {self.broker}\n"
            f"Symbol: {self.symbol}\n"
            f"Profile: {self.profile_name}\n"
            f"Live Execution Enabled: {self.live_execution_enabled}"
        )
