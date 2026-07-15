from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

RESEARCH_CONTRACT_VERSION = "AFIP-RESEARCH-DATA-1.0"
POST_TRADE_CHECKPOINTS = ("M30", "H1", "H4", "D1")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ResearchEvent:
    event_id: str
    event_type: str
    observed_at_utc: str
    profile_id: str
    symbol: str
    contract_version: str = RESEARCH_CONTRACT_VERSION
    source_type: str = "DEMO_EXECUTION_LEDGER"
    source_path: str = ""
    source_line_number: int = 0
    source_sha256: str = ""
    lineage_parent_ids: tuple[str, ...] = ()
    payload: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TradeCase:
    trade_case_id: str
    profile_id: str
    symbol: str
    created_at_utc: str
    updated_at_utc: str
    lifecycle_state: str
    decision_action: str
    decision_confidence: float
    order_status: str
    tickets: tuple[int, ...]
    event_ids: tuple[str, ...]
    contract_version: str = RESEARCH_CONTRACT_VERSION
    market_context: Mapping[str, Any] = field(default_factory=dict)
    decision_trace: Mapping[str, Any] = field(default_factory=dict)
    execution_result: Mapping[str, Any] = field(default_factory=dict)
    holding_timeline: tuple[Mapping[str, Any], ...] = ()
    exit_context: Mapping[str, Any] = field(default_factory=dict)
    post_trade_checkpoints: Mapping[str, Any] = field(default_factory=dict)
    counterfactual_plans: tuple[Mapping[str, Any], ...] = ()
    data_lineage: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
