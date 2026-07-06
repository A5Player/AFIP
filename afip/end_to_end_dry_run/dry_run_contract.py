"""Production Milestone D Pack 5 end-to-end dry run contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Tuple

from .dry_run_evidence import EndToEndDryRunEvidence

REQUIRED_DRY_RUN_SEQUENCE: Tuple[str, ...] = (
    "RUNTIME_WIRING",
    "DATA_PIPELINE",
    "DECISION_EXECUTION",
    "SAFETY_AUDIT",
)


@dataclass(frozen=True)
class EndToEndDryRunContract:
    """Contract proving the runtime path can be replayed as a deterministic dry run."""

    evidence: Tuple[EndToEndDryRunEvidence, ...]
    capability_keys: Tuple[str, ...]
    missing_capabilities: Tuple[str, ...]
    active_market_regime: str
    average_runtime_readiness: float
    average_data_quality: float
    average_decision_confidence: float
    average_execution_score: float
    average_audit_score: float
    dry_run_score: float
    trace_ids: Tuple[str, ...]
    sequence_is_valid: bool
    all_evidence_usable: bool

    @classmethod
    def from_evidence(cls, values: Iterable[Mapping[str, Any] | EndToEndDryRunEvidence]) -> "EndToEndDryRunContract":
        evidence = tuple(
            value if isinstance(value, EndToEndDryRunEvidence) else EndToEndDryRunEvidence.from_mapping(value)
            for value in values
        )
        by_capability = {item.capability_key: item for item in evidence}
        ordered_keys = tuple(key for key in REQUIRED_DRY_RUN_SEQUENCE if key in by_capability)
        missing = tuple(key for key in REQUIRED_DRY_RUN_SEQUENCE if key not in by_capability)
        ordered_evidence = tuple(by_capability[key] for key in ordered_keys)

        regimes = tuple(item.market_regime for item in ordered_evidence if item.has_market_regime)
        active_regime = regimes[0] if regimes and all(regime == regimes[0] for regime in regimes) else "UNKNOWN"

        runtime_values = tuple(item.readiness_score for item in ordered_evidence)
        data_values = tuple(item.data_quality_score for item in ordered_evidence)
        decision_values = tuple(item.decision_confidence for item in ordered_evidence)
        execution_values = tuple(item.execution_score for item in ordered_evidence)
        audit_values = tuple(item.audit_score for item in ordered_evidence)

        average_runtime = round(sum(runtime_values) / len(runtime_values), 4) if runtime_values else 0.0
        average_data = round(sum(data_values) / len(data_values), 4) if data_values else 0.0
        average_decision = round(sum(decision_values) / len(decision_values), 4) if decision_values else 0.0
        average_execution = round(sum(execution_values) / len(execution_values), 4) if execution_values else 0.0
        average_audit = round(sum(audit_values) / len(audit_values), 4) if audit_values else 0.0

        trace_ids = tuple(item.trace_id for item in ordered_evidence if item.trace_id)
        all_usable = bool(ordered_evidence) and all(item.is_usable for item in ordered_evidence)
        sequence_valid = ordered_keys == REQUIRED_DRY_RUN_SEQUENCE and active_regime != "UNKNOWN"
        trace_bonus = 5.0 if len(trace_ids) == len(REQUIRED_DRY_RUN_SEQUENCE) else 0.0
        dry_run_score = round(
            (average_runtime * 0.18)
            + (average_data * 0.2)
            + (average_decision * 0.22)
            + (average_execution * 0.2)
            + (average_audit * 0.15)
            + trace_bonus,
            4,
        )

        return cls(
            evidence=ordered_evidence,
            capability_keys=ordered_keys,
            missing_capabilities=missing,
            active_market_regime=active_regime,
            average_runtime_readiness=average_runtime,
            average_data_quality=average_data,
            average_decision_confidence=average_decision,
            average_execution_score=average_execution,
            average_audit_score=average_audit,
            dry_run_score=dry_run_score,
            trace_ids=trace_ids,
            sequence_is_valid=sequence_valid,
            all_evidence_usable=all_usable,
        )

    @property
    def is_ready(self) -> bool:
        return (
            not self.missing_capabilities
            and self.sequence_is_valid
            and self.all_evidence_usable
            and len(self.trace_ids) == len(REQUIRED_DRY_RUN_SEQUENCE)
            and self.dry_run_score >= 70.0
        )
