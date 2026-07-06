"""Data quality checks for integrated runtime pipeline readiness."""

from __future__ import annotations

from dataclasses import dataclass

from .pipeline_contract import DataPipelineContract


@dataclass(frozen=True)
class DataQualityDecision:
    status: str
    action: str
    reason: str
    readiness_score: float

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "action": self.action,
            "reason": self.reason,
            "readiness_score": self.readiness_score,
        }


class DataPipelineQualityPolicy:
    """Confirm that runtime data can safely move into integrated flow."""

    def __init__(self, minimum_readiness: float = 70.0) -> None:
        self.minimum_readiness = float(minimum_readiness)

    def decide(self, contract: DataPipelineContract) -> DataQualityDecision:
        if contract.missing_sources:
            return DataQualityDecision("DATA_PIPELINE_WAIT", "WAIT", "missing_required_financial_data_source", contract.readiness_score)
        if not contract.sequence_is_valid:
            return DataQualityDecision("DATA_PIPELINE_BLOCKED", "WAIT", "data_sequence_not_regime_first", contract.readiness_score)
        if len(contract.usable_records) != len(contract.records):
            return DataQualityDecision("DATA_PIPELINE_BLOCKED", "WAIT", "financial_data_record_not_usable", contract.readiness_score)
        if contract.readiness_score < self.minimum_readiness:
            return DataQualityDecision("DATA_PIPELINE_BLOCKED", "WAIT", "data_readiness_below_learned_requirement", contract.readiness_score)
        return DataQualityDecision("DATA_PIPELINE_READY", "INTEGRATE_DATA", "financial_data_pipeline_ready", contract.readiness_score)
