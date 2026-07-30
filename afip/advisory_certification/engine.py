from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

CERTIFIED = "CERTIFIED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
BLOCKED = "BLOCKED"

REQUIRED_COMPONENTS = (
    ("W2_CONTEXT_MATCHING", "afip/context_matching/engine.py", "config/context_matching_contract.json"),
    ("W3_STRATEGY_INTELLIGENCE", "afip/strategy_intelligence/engine.py", "config/strategy_intelligence_contract.json"),
    ("W4_TRADING_PLAN_SELECTION", "afip/trading_plan_selection/engine.py", "config/trading_plan_selection_contract.json"),
    ("W5_OPPORTUNITY_QUALITY", "afip/opportunity_quality/engine.py", "config/opportunity_quality_runtime_contract.json"),
    ("W6_ADAPTIVE_SL", "afip/adaptive_sl/engine.py", "config/adaptive_sl_runtime_contract.json"),
    ("W7_HOLDING_INTELLIGENCE", "afip/holding_intelligence/engine.py", "config/holding_intelligence_runtime_contract.json"),
    ("W8_EXIT_INTELLIGENCE", "afip/exit_intelligence/engine.py", "config/exit_intelligence_runtime_contract.json"),
    ("W9_ADVISORY_ORCHESTRATION", "afip/advisory_orchestration/engine.py", "config/advisory_orchestration_contract.json"),
)

FORBIDDEN_AUTHORITY_KEYS = {
    "execution_authority",
    "order_send_allowed",
    "order_modify_allowed",
    "order_close_allowed",
    "mt5_authority",
    "lot_authority",
    "final_sl_tp_authority",
}

@dataclass(frozen=True)
class ComponentCertification:
    component: str
    module_present: bool
    contract_present: bool
    contract_parseable: bool
    authority_boundary_passed: bool
    reason: str

@dataclass(frozen=True)
class AdvisoryCertificationSnapshot:
    snapshot_id: str
    status: str
    reason: str
    created_at_utc: str
    source_root: str
    components: Sequence[ComponentCertification]
    required_count: int
    passed_count: int
    authority_boundary_passed: bool
    trace_contract_present: bool
    snapshot_digest: str
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False

class AdvisoryCertificationRuntime:
    """Read-only Milestone W advisory certification."""

    def __init__(self, required_components=REQUIRED_COMPONENTS) -> None:
        self.required_components = tuple(required_components)

    @staticmethod
    def _contract_boundary(contract: Mapping[str, Any]) -> bool:
        authority = str(contract.get("authority", "")).upper()
        if authority not in {"ADVISORY_ONLY", "TRACE_AND_VALIDATION_ONLY", "READ_ONLY_CERTIFICATION"}:
            return False

        for key in FORBIDDEN_AUTHORITY_KEYS:
            if contract.get(key) is True:
                return False

        forbidden = {str(v).upper() for v in contract.get("forbidden_authorities", [])}
        if authority == "ADVISORY_ONLY" and not forbidden:
            return False
        return True

    @staticmethod
    def _digest(records: Sequence[ComponentCertification]) -> str:
        body = [
            {
                "component": r.component,
                "module_present": r.module_present,
                "contract_present": r.contract_present,
                "contract_parseable": r.contract_parseable,
                "authority_boundary_passed": r.authority_boundary_passed,
                "reason": r.reason,
            }
            for r in records
        ]
        raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def certify(self, project_root: str | Path) -> AdvisoryCertificationSnapshot:
        root = Path(project_root)
        records: list[ComponentCertification] = []

        for component, module_rel, contract_rel in self.required_components:
            module_path = root / module_rel
            contract_path = root / contract_rel
            module_present = module_path.is_file()
            contract_present = contract_path.is_file()
            parseable = False
            boundary = False
            reason = "component_ready"

            if not module_present:
                reason = "module_missing"
            elif not contract_present:
                reason = "contract_missing"
            else:
                try:
                    contract = json.loads(contract_path.read_text(encoding="utf-8"))
                    parseable = isinstance(contract, dict)
                    boundary = parseable and self._contract_boundary(contract)
                    if not parseable:
                        reason = "contract_not_object"
                    elif not boundary:
                        reason = "authority_boundary_failed"
                except (OSError, UnicodeError, json.JSONDecodeError):
                    reason = "contract_unreadable"

            records.append(ComponentCertification(
                component=component,
                module_present=module_present,
                contract_present=contract_present,
                contract_parseable=parseable,
                authority_boundary_passed=boundary,
                reason=reason,
            ))

        digest = self._digest(records)
        passed = sum(
            1 for r in records
            if r.module_present and r.contract_present
            and r.contract_parseable and r.authority_boundary_passed
        )
        boundary_passed = all(r.authority_boundary_passed for r in records)
        trace_present = (root / "config/advisory_orchestration_contract.json").is_file()

        if passed == len(records) and boundary_passed and trace_present:
            status, reason = CERTIFIED, "milestone_w_advisory_foundation_certified"
        elif any(r.reason in {"contract_unreadable", "authority_boundary_failed"} for r in records):
            status, reason = BLOCKED, "certification_blocker_detected"
        else:
            status, reason = REVIEW_REQUIRED, "required_component_incomplete"

        created = datetime.now(timezone.utc).isoformat()
        return AdvisoryCertificationSnapshot(
            snapshot_id=f"AFIP-W10-{digest[:16].upper()}",
            status=status,
            reason=reason,
            created_at_utc=created,
            source_root=str(root),
            components=tuple(records),
            required_count=len(records),
            passed_count=passed,
            authority_boundary_passed=boundary_passed,
            trace_contract_present=trace_present,
            snapshot_digest=digest,
        )
