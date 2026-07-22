from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CertifiedPolicyPromotion:
    """Promote only certified research metadata; never mutates execution code/config."""
    REQUIRED_TRUE = ("walk_forward_passed", "out_of_sample_passed", "drawdown_limit_passed", "stability_passed", "no_data_leakage")

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.candidate_path = self.root / "runtime/research/candidates/latest.json"
        self.active_path = self.root / "runtime/research/policies/active_certified_policy.json"
        self.ledger_path = self.root / "runtime/research/policies/promotion_ledger.jsonl"

    def evaluate(self, candidate: Mapping[str, Any]) -> tuple[bool, tuple[str, ...]]:
        blockers: list[str] = []
        for field in self.REQUIRED_TRUE:
            if candidate.get(field) is not True:
                blockers.append(f"{field}_required")
        if int(candidate.get("sample_size", 0) or 0) < int(candidate.get("minimum_sample_size", 1000) or 1000):
            blockers.append("minimum_sample_size_not_met")
        if not str(candidate.get("policy_version", "")).strip():
            blockers.append("policy_version_required")
        return not blockers, tuple(blockers)

    def promote_latest(self) -> dict[str, Any]:
        if not self.candidate_path.exists():
            return {"status": "WAITING", "reason": "certified_candidate_not_available", "promoted": False}
        candidate = json.loads(self.candidate_path.read_text(encoding="utf-8"))
        allowed, blockers = self.evaluate(candidate)
        result = {"status": "READY" if allowed else "WAITING", "reason": "certified_policy_promoted" if allowed else "candidate_not_certified", "promoted": allowed, "blockers": list(blockers), "evaluated_at_utc": _utc(), "candidate_policy_version": candidate.get("policy_version")}
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
        if allowed:
            payload = {"schema_version": "AFIP-CERTIFIED-RESEARCH-POLICY-V1", "promoted_at_utc": _utc(), "execution_authority": False, "candidate": candidate}
            temporary = self.active_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(self.active_path)
        return result
