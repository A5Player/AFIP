"""Production Milestone D Pack 2 data pipeline integration runtime."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from .data_pipeline_report import DataPipelineReport, DataPipelineReporter
from .data_quality import DataPipelineQualityPolicy
from .pipeline_contract import DataPipelineContract


class DataPipelineRuntime:
    """Normalize, validate, and report integrated financial data readiness."""

    def __init__(self) -> None:
        self.policy = DataPipelineQualityPolicy()
        self.reporter = DataPipelineReporter()

    def run(self, records: Iterable[Mapping[str, Any]]) -> DataPipelineReport:
        contract = DataPipelineContract.from_records(records)
        decision = self.policy.decide(contract)
        return self.reporter.build(contract, decision)
