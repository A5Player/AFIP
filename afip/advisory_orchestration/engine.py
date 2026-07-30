from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping, Sequence

TRACE_COMPLETE = "TRACE_COMPLETE"
TRACE_WAIT = "TRACE_WAIT"
TRACE_BLOCKED = "TRACE_BLOCKED"

STAGE_ORDER = (
    "CONTEXT",
    "STRATEGY",
    "PLAN",
    "OQS",
    "ADAPTIVE_SL",
    "HOLDING",
    "EXIT",
)

@dataclass(frozen=True)
class AdvisoryStage:
    stage: str
    status: str
    reason: str
    authority_passed: bool
    data_integrity_passed: bool
    payload: Mapping[str, Any] = field(default_factory=dict)
    timestamp_utc: str | None = None

@dataclass(frozen=True)
class AdvisoryTrace:
    trace_id: str
    case_id: str
    status: str
    reason: str
    stages: Sequence[AdvisoryStage]
    input_digest: str
    created_at_utc: str
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False

class AdvisoryOrchestrator:
    """Validates and records the W2-W8 advisory chain.

    It does not execute any stage and cannot place, modify, or close orders.
    """

    def __init__(self, required_stage_order: Sequence[str] = STAGE_ORDER) -> None:
        self.required_stage_order = tuple(required_stage_order)

    @staticmethod
    def _canonical_digest(case_id: str, stages: Sequence[AdvisoryStage]) -> str:
        body = {
            "case_id": case_id,
            "stages": [
                {
                    "stage": s.stage,
                    "status": s.status,
                    "reason": s.reason,
                    "authority_passed": s.authority_passed,
                    "data_integrity_passed": s.data_integrity_passed,
                    "payload": dict(s.payload),
                }
                for s in stages
            ],
        }
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def build_trace(self, case_id: str, stages: Sequence[AdvisoryStage]) -> AdvisoryTrace:
        now = datetime.now(timezone.utc).isoformat()
        ordered = tuple(stages)
        digest = self._canonical_digest(case_id, ordered)
        trace_id = f"AFIP-W9-{digest[:16].upper()}"

        def result(status: str, reason: str) -> AdvisoryTrace:
            return AdvisoryTrace(
                trace_id=trace_id,
                case_id=case_id,
                status=status,
                reason=reason,
                stages=ordered,
                input_digest=digest,
                created_at_utc=now,
            )

        actual = tuple(s.stage for s in ordered)
        expected_prefix = self.required_stage_order[:len(actual)]
        if actual != expected_prefix:
            return result(TRACE_BLOCKED, "invalid_stage_order")
        if len(actual) > len(self.required_stage_order):
            return result(TRACE_BLOCKED, "unexpected_stage_count")
        if not ordered:
            return result(TRACE_WAIT, "no_advisory_stages")
        if any(not s.data_integrity_passed for s in ordered):
            return result(TRACE_BLOCKED, "data_integrity_failure")
        if any(not s.authority_passed for s in ordered):
            return result(TRACE_BLOCKED, "authority_failure")
        if any(not str(s.status).strip() for s in ordered):
            return result(TRACE_BLOCKED, "stage_status_missing")
        if len(ordered) < len(self.required_stage_order):
            return result(TRACE_WAIT, "advisory_chain_incomplete")
        return result(TRACE_COMPLETE, "advisory_chain_validated")

    @staticmethod
    def to_record(trace: AdvisoryTrace) -> dict[str, Any]:
        return asdict(trace)
