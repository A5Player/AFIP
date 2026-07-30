from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

CERTIFIED = "CERTIFIED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
BLOCKED = "BLOCKED"

REQUIRED_MODULES = (
    "afip.advisory_orchestration",
    "afip.advisory_certification",
    "afip.advisory_snapshot",
    "afip.advisory_dashboard_read_model",
    "afip.advisory_dashboard_presentation",
    "afip.advisory_dashboard_adapter",
    "afip.advisory_dashboard_runtime",
)

REQUIRED_CONTRACTS = (
    "config/advisory_orchestration_contract.json",
    "config/advisory_certification_contract.json",
    "config/advisory_snapshot_contract.json",
    "config/advisory_dashboard_read_model_contract.json",
    "config/advisory_dashboard_presentation_contract.json",
    "config/advisory_dashboard_adapter_contract.json",
    "config/advisory_dashboard_runtime_contract.json",
)

FORBIDDEN_AUTHORITY_TOKENS = (
    "ORDER_SEND",
    "ORDER_MODIFY",
    "ORDER_CLOSE",
    "PARTIAL_CLOSE",
    "LOT_SIZING",
    "FINAL_SL_TP",
    "MT5_SESSION",
)


@dataclass(frozen=True)
class CertificationCheck:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class AdvisoryIntegrationCertification:
    status: str
    reason: str
    certification_id: str
    checks: Sequence[CertificationCheck]
    source_digest: str
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class AdvisoryIntegrationCertificationRuntime:
    """Read-only certification for the complete Milestone W advisory chain."""

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root)

    def _module_checks(self) -> list[CertificationCheck]:
        checks: list[CertificationCheck] = []
        for module_name in REQUIRED_MODULES:
            try:
                importlib.import_module(module_name)
                checks.append(CertificationCheck(module_name, "PASS", "module_importable"))
            except Exception as exc:
                checks.append(
                    CertificationCheck(
                        module_name,
                        "FAIL",
                        f"module_import_failed:{type(exc).__name__}",
                    )
                )
        return checks

    def _contract_checks(self) -> tuple[list[CertificationCheck], list[Mapping[str, Any]]]:
        checks: list[CertificationCheck] = []
        contracts: list[Mapping[str, Any]] = []

        for relative in REQUIRED_CONTRACTS:
            path = self.root / relative
            if not path.is_file():
                checks.append(CertificationCheck(relative, "FAIL", "contract_missing"))
                continue

            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                checks.append(CertificationCheck(relative, "FAIL", "contract_unreadable"))
                continue

            contracts.append(data)
            if data.get("fail_closed") is not True:
                checks.append(CertificationCheck(relative, "FAIL", "fail_closed_missing"))
                continue

            forbidden = tuple(data.get("forbidden_authorities", ()) or ())
            missing = [token for token in FORBIDDEN_AUTHORITY_TOKENS if token not in forbidden]
            if missing:
                checks.append(
                    CertificationCheck(
                        relative,
                        "REVIEW",
                        "authority_boundary_incomplete:" + ",".join(missing),
                    )
                )
            else:
                checks.append(CertificationCheck(relative, "PASS", "contract_valid"))

        return checks, contracts

    @staticmethod
    def _digest(checks: Sequence[CertificationCheck], contracts: Sequence[Mapping[str, Any]]) -> str:
        canonical = {
            "checks": [asdict(check) for check in checks],
            "contracts": contracts,
        }
        return hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()
        ).hexdigest()

    def certify(self) -> AdvisoryIntegrationCertification:
        module_checks = self._module_checks()
        contract_checks, contracts = self._contract_checks()
        checks = tuple(module_checks + contract_checks)

        statuses = {check.status for check in checks}
        if "FAIL" in statuses:
            status = BLOCKED
            reason = "integration_certification_failed"
        elif "REVIEW" in statuses:
            status = REVIEW_REQUIRED
            reason = "integration_certification_review_required"
        else:
            status = CERTIFIED
            reason = "integration_certification_passed"

        digest = self._digest(checks, contracts)
        return AdvisoryIntegrationCertification(
            status=status,
            reason=reason,
            certification_id=f"AFIP-W16-{digest[:16].upper()}",
            checks=checks,
            source_digest=digest,
        )
