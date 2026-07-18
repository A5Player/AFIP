from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import json


@dataclass(frozen=True)
class RetentionDecision:
    decision_id: str
    dataset_id: str
    action: str
    reason: str
    target_tier: str
    automatic_action_taken: bool
    evaluated_at: str
    execution_authority: str = "NONE"

    def to_dict(self) -> dict:
        return asdict(self)


class ArchiveRetentionPlanner:
    """Creates retention recommendations only; never deletes or moves data."""

    ALLOWED_ACTIONS = {"KEEP_ACTIVE", "ARCHIVE", "REVIEW", "LEGAL_HOLD", "QUARANTINE_REVIEW"}

    def __init__(self, policy: Mapping[str, object] | None = None) -> None:
        self.policy = dict(policy or {})
        if self.policy.get("execution_authority","NONE") != "NONE":
            raise ValueError("execution_authority_must_be_none")
        if self.policy.get("automatic_deletion","PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_deletion_must_be_prohibited")

    def evaluate(self, dataset_id: str, age_days: int, lifecycle_status: str,
                 legal_hold: bool=False, integrity_status: str="HEALTHY") -> RetentionDecision:
        if age_days < 0:
            raise ValueError("age_days_must_be_non_negative")
        if legal_hold:
            action, reason, tier = "LEGAL_HOLD", "legal_hold_active", "IMMUTABLE_HOLD"
        elif integrity_status in {"CORRUPTED","QUARANTINED"}:
            action, reason, tier = "QUARANTINE_REVIEW", "integrity_review_required", "QUARANTINE"
        elif lifecycle_status == "ARCHIVED":
            action, reason, tier = "KEEP_ACTIVE", "already_archived", "COLD_ARCHIVE"
        elif age_days >= int(self.policy.get("archive_after_days", 365)):
            action, reason, tier = "ARCHIVE", "retention_threshold_reached", "COLD_ARCHIVE"
        else:
            action, reason, tier = "KEEP_ACTIVE", "within_active_retention_window", "ACTIVE"
        canonical = f"{dataset_id}|{age_days}|{lifecycle_status}|{legal_hold}|{integrity_status}|{action}|{tier}"
        did = "ret_" + sha256(canonical.encode()).hexdigest()[:24]
        return RetentionDecision(did,dataset_id,action,reason,tier,False,datetime.now(timezone.utc).isoformat())

    @staticmethod
    def append_ledger(decision: RetentionDecision, path: str|Path) -> None:
        p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("a",encoding="utf-8",newline="\n") as h:
            h.write(json.dumps(decision.to_dict(),sort_keys=True,separators=(",",":"))+"\n")
