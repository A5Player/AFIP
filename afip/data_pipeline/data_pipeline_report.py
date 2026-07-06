"""Audit report for Production Milestone D Pack 2 data pipeline integration."""

from __future__ import annotations

from dataclasses import dataclass

from .data_quality import DataQualityDecision
from .pipeline_contract import DataPipelineContract


@dataclass(frozen=True)
class DataPipelineReport:
    status: str
    action: str
    reason: str
    readiness_score: float
    source_count: int
    record_count: int
    usable_record_count: int
    active_market_regime: str
    missing_sources: tuple[str, ...]
    sequence_is_valid: bool
    maximum_spread: float

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "readiness_score": self.readiness_score,
            "source_count": self.source_count,
            "record_count": self.record_count,
            "usable_record_count": self.usable_record_count,
            "active_market_regime": self.active_market_regime,
            "missing_sources": list(self.missing_sources),
            "sequence_is_valid": self.sequence_is_valid,
            "maximum_spread": self.maximum_spread,
        }


class DataPipelineReporter:
    def build(self, contract: DataPipelineContract, decision: DataQualityDecision) -> DataPipelineReport:
        return DataPipelineReport(
            status=decision.status,
            action=decision.action,
            reason=decision.reason,
            readiness_score=decision.readiness_score,
            source_count=len(contract.source_keys),
            record_count=len(contract.records),
            usable_record_count=len(contract.usable_records),
            active_market_regime=contract.active_market_regime,
            missing_sources=contract.missing_sources,
            sequence_is_valid=contract.sequence_is_valid,
            maximum_spread=contract.maximum_spread,
        )
