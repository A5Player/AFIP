"""Decision traceability utilities for audit-ready financial decision records."""

from dataclasses import dataclass
from typing import Mapping, Any

@dataclass(frozen=True)
class DecisionTraceRecord:
    status: str
    trace_id: str
    action: str
    confidence: float
    reason: str

class DecisionTraceability:
    """Creates compact deterministic trace records for decision review."""

    def create(self, decision: Mapping[str, Any], sequence: int = 1) -> DecisionTraceRecord:
        action = str(decision.get("action", "NO_ACTION")).upper()
        confidence = round(max(0.0, min(100.0, float(decision.get("confidence", 0.0)))), 2)
        reason = str(decision.get("reason", "decision_trace_recorded"))
        trace_id = f"AFIP-DECISION-{int(sequence):06d}-{action}"
        return DecisionTraceRecord("DECISION_TRACE_READY", trace_id, action, confidence, reason)
