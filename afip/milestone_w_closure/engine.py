from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

MILESTONE_W_COMPLETE = "MILESTONE_W_COMPLETE"
MILESTONE_W_REVIEW_REQUIRED = "MILESTONE_W_REVIEW_REQUIRED"
MILESTONE_W_BLOCKED = "MILESTONE_W_BLOCKED"

EXPECTED_CERTIFICATION_STATUS = "CERTIFIED"


@dataclass(frozen=True)
class MilestoneWClosureCheck:
    name: str
    status: str
    reason: str


@dataclass(frozen=True)
class MilestoneWClosureRecord:
    status: str
    reason: str
    closure_id: str
    closed_at_utc: str
    certification_id: str
    certification_digest: str
    completed_packs: Sequence[str]
    checks: Sequence[MilestoneWClosureCheck]
    execution_authority: bool = False
    order_send_called: bool = False
    order_modify_called: bool = False
    order_close_called: bool = False


class MilestoneWClosureRuntime:
    """Creates a deterministic, read-only Milestone W closure record."""

    COMPLETED_PACKS = tuple(f"W{number}" for number in range(2, 18))

    def __init__(self, project_root: str | Path) -> None:
        self.root = Path(project_root)

    @staticmethod
    def _utc_text(value: datetime | None = None) -> str:
        current = (value or datetime.now(timezone.utc)).astimezone(timezone.utc)
        return current.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _digest_payload(payload: Mapping[str, Any]) -> str:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    def _required_files(self) -> tuple[str, ...]:
        return (
            "afip/advisory_orchestration/engine.py",
            "afip/advisory_certification/engine.py",
            "afip/advisory_snapshot/engine.py",
            "afip/advisory_dashboard_read_model/engine.py",
            "afip/advisory_dashboard_presentation/engine.py",
            "afip/advisory_dashboard_adapter/engine.py",
            "afip/advisory_dashboard_runtime/engine.py",
            "afip/advisory_integration_certification/engine.py",
            "config/advisory_integration_certification_contract.json",
        )

    def _file_checks(self) -> list[MilestoneWClosureCheck]:
        checks: list[MilestoneWClosureCheck] = []
        for relative in self._required_files():
            path = self.root / relative
            if path.is_file():
                checks.append(MilestoneWClosureCheck(relative, "PASS", "required_file_present"))
            else:
                checks.append(MilestoneWClosureCheck(relative, "FAIL", "required_file_missing"))
        return checks

    def close(
        self,
        certification: Mapping[str, Any],
        closed_at_utc: datetime | None = None,
    ) -> MilestoneWClosureRecord:
        checks = self._file_checks()

        certification_status = str(certification.get("status", ""))
        certification_id = str(certification.get("certification_id", ""))
        certification_digest = str(certification.get("source_digest", ""))

        if certification_status == EXPECTED_CERTIFICATION_STATUS:
            checks.append(
                MilestoneWClosureCheck(
                    "integration_certification",
                    "PASS",
                    "certification_status_certified",
                )
            )
        else:
            checks.append(
                MilestoneWClosureCheck(
                    "integration_certification",
                    "FAIL",
                    "certification_status_not_certified",
                )
            )

        digest_valid = (
            len(certification_digest) == 64
            and all(ch in "0123456789abcdef" for ch in certification_digest.lower())
        )
        checks.append(
            MilestoneWClosureCheck(
                "certification_digest",
                "PASS" if digest_valid else "FAIL",
                "certification_digest_valid" if digest_valid else "certification_digest_invalid",
            )
        )

        id_valid = certification_id.startswith("AFIP-W16-")
        checks.append(
            MilestoneWClosureCheck(
                "certification_id",
                "PASS" if id_valid else "FAIL",
                "certification_id_valid" if id_valid else "certification_id_invalid",
            )
        )

        statuses = {check.status for check in checks}
        if "FAIL" in statuses:
            status = MILESTONE_W_BLOCKED
            reason = "milestone_w_closure_blocked"
        elif "REVIEW" in statuses:
            status = MILESTONE_W_REVIEW_REQUIRED
            reason = "milestone_w_closure_review_required"
        else:
            status = MILESTONE_W_COMPLETE
            reason = "milestone_w_closed_successfully"

        closed_at = self._utc_text(closed_at_utc)
        closure_material = {
            "status": status,
            "certification_id": certification_id,
            "certification_digest": certification_digest,
            "completed_packs": self.COMPLETED_PACKS,
            "checks": [asdict(check) for check in checks],
        }
        closure_digest = self._digest_payload(closure_material)

        return MilestoneWClosureRecord(
            status=status,
            reason=reason,
            closure_id=f"AFIP-W17-{closure_digest[:16].upper()}",
            closed_at_utc=closed_at,
            certification_id=certification_id,
            certification_digest=certification_digest,
            completed_packs=self.COMPLETED_PACKS,
            checks=tuple(checks),
        )

    @staticmethod
    def to_dict(record: MilestoneWClosureRecord) -> dict[str, Any]:
        return asdict(record)

    @staticmethod
    def write_atomic(record: MilestoneWClosureRecord, output_path: str | Path) -> Path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(record), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
        return target
