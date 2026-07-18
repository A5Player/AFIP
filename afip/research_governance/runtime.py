"""Milestone T Pack 1: research quarantine and knowledge promotion controls.

This module is deliberately isolated from order execution.  It decides only
whether research evidence is safe enough to be visible to production readers.
It does not select, size, open, manage, or close positions.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


class KnowledgeState(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    REJECTED = "REJECTED"
    APPROVED_CANDIDATE = "APPROVED_CANDIDATE"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class PromotionPolicy:
    """Fail-closed minimum evidence required before production visibility."""

    minimum_sample_size: int = 300
    minimum_out_of_sample_size: int = 100
    minimum_walk_forward_windows: int = 3
    minimum_profit_factor: float = 1.20
    minimum_expectancy: float = 0.0
    maximum_drawdown: float = 0.20
    require_out_of_sample: bool = True
    require_walk_forward: bool = True
    require_data_quality_certification: bool = True
    require_manual_approval: bool = True

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "PromotionPolicy":
        allowed = {field_name for field_name in cls.__dataclass_fields__}
        payload = {key: value[key] for key in allowed if key in value}
        return cls(**payload)

    @classmethod
    def from_json_file(cls, path: str | Path) -> "PromotionPolicy":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("research promotion policy must be a JSON object")
        return cls.from_mapping(payload)


@dataclass(frozen=True)
class PromotionDecision:
    status: str
    reason: str
    source_state: str
    target_state: str
    production_usable: bool
    block_reasons: tuple[str, ...]
    evidence_checksum: str
    evaluated_at_utc: str
    objective_evidence: dict[str, float | int | None]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchZoneLayout:
    """Physical storage boundary between unapproved research and knowledge."""

    root: Path

    @property
    def experimental(self) -> Path:
        return self.root / "research" / "experimental"

    @property
    def pending(self) -> Path:
        return self.root / "research" / "validation_pending"

    @property
    def candidates(self) -> Path:
        return self.root / "research" / "approved_candidates"

    @property
    def rejected(self) -> Path:
        return self.root / "research" / "rejected"

    @property
    def approved(self) -> Path:
        return self.root / "knowledge" / "production_approved"

    @property
    def revoked(self) -> Path:
        return self.root / "knowledge" / "revoked"

    def ensure(self) -> None:
        for path in (
            self.experimental,
            self.pending,
            self.candidates,
            self.rejected,
            self.approved,
            self.revoked,
        ):
            path.mkdir(parents=True, exist_ok=True)


class ResearchPromotionGate:
    """Decide when isolated research evidence may become production knowledge.

    TOP10/TOP100 ranking is intentionally absent.  Promotion is based on
    evidence quality.  Later selection may compare approved candidates by
    lower drawdown, higher profit and higher win probability in matching
    market context, but unapproved evidence is never eligible for selection.
    """

    def __init__(self, policy: PromotionPolicy | None = None) -> None:
        self.policy = policy or PromotionPolicy()

    def evaluate(self, record: Mapping[str, Any], *, now: datetime | None = None) -> PromotionDecision:
        state = self._state(record.get("state", KnowledgeState.EXPERIMENTAL.value))
        blocked: list[str] = []

        if state in {KnowledgeState.REJECTED, KnowledgeState.REVOKED}:
            blocked.append("knowledge_state_not_promotable")
        if state == KnowledgeState.PRODUCTION_APPROVED:
            blocked.append("knowledge_already_production_approved")

        sample_size = self._integer(record.get("sample_size"))
        out_of_sample_size = self._integer(record.get("out_of_sample_size"))
        walk_forward_windows = self._integer(record.get("walk_forward_windows"))
        win_rate = self._number(record.get("win_rate"))
        net_profit = self._number(record.get("net_profit"))
        profit_factor = self._number(record.get("profit_factor"))
        expectancy = self._number(record.get("expectancy"))
        maximum_drawdown = self._number(record.get("maximum_drawdown"))

        if sample_size is None or sample_size < self.policy.minimum_sample_size:
            blocked.append("minimum_sample_size_not_met")
        if win_rate is None or win_rate < 0.0 or win_rate > 1.0:
            blocked.append("valid_win_rate_required")
        if net_profit is None:
            blocked.append("net_profit_required")
        if profit_factor is None or profit_factor < self.policy.minimum_profit_factor:
            blocked.append("minimum_profit_factor_not_met")
        if expectancy is None or expectancy <= self.policy.minimum_expectancy:
            blocked.append("positive_expectancy_required")
        if maximum_drawdown is None or maximum_drawdown < 0.0:
            blocked.append("valid_maximum_drawdown_required")
        elif maximum_drawdown > self.policy.maximum_drawdown:
            blocked.append("maximum_drawdown_exceeded")

        if self.policy.require_out_of_sample:
            if not bool(record.get("out_of_sample_passed", False)):
                blocked.append("out_of_sample_not_passed")
            if out_of_sample_size is None or out_of_sample_size < self.policy.minimum_out_of_sample_size:
                blocked.append("minimum_out_of_sample_size_not_met")
        if self.policy.require_walk_forward:
            if not bool(record.get("walk_forward_passed", False)):
                blocked.append("walk_forward_not_passed")
            if walk_forward_windows is None or walk_forward_windows < self.policy.minimum_walk_forward_windows:
                blocked.append("minimum_walk_forward_windows_not_met")
        if self.policy.require_data_quality_certification and not bool(record.get("data_quality_certified", False)):
            blocked.append("data_quality_not_certified")
        if bool(record.get("future_leakage_detected", False)):
            blocked.append("future_leakage_detected")
        if not bool(record.get("chronological_replay_verified", False)):
            blocked.append("chronological_replay_not_verified")
        if not str(record.get("dataset_version", "")).strip():
            blocked.append("dataset_version_required")
        if not str(record.get("research_run_id", "")).strip():
            blocked.append("research_run_id_required")
        if not str(record.get("validation_report_id", "")).strip():
            blocked.append("validation_report_required")
        if not str(record.get("market_context_signature", "")).strip():
            blocked.append("market_context_signature_required")
        if self.policy.require_manual_approval and not bool(record.get("manual_approval_granted", False)):
            blocked.append("manual_approval_required")
        if bool(record.get("manual_approval_granted", False)) and not str(record.get("approved_by", "")).strip():
            blocked.append("approver_identity_required")

        checksum = self._checksum(record)
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        objectives: dict[str, float | int | None] = {
            "sample_size": sample_size,
            "win_rate": win_rate,
            "net_profit": net_profit,
            "maximum_drawdown": maximum_drawdown,
            "profit_factor": profit_factor,
            "expectancy": expectancy,
        }
        if blocked:
            target = KnowledgeState.VALIDATION_PENDING.value
            if state in {KnowledgeState.REJECTED, KnowledgeState.REVOKED}:
                target = state.value
            return PromotionDecision(
                status="BLOCK",
                reason="research_evidence_not_production_eligible",
                source_state=state.value,
                target_state=target,
                production_usable=False,
                block_reasons=tuple(sorted(set(blocked))),
                evidence_checksum=checksum,
                evaluated_at_utc=timestamp,
                objective_evidence=objectives,
            )

        return PromotionDecision(
            status="APPROVED",
            reason="research_evidence_production_eligible",
            source_state=state.value,
            target_state=KnowledgeState.PRODUCTION_APPROVED.value,
            production_usable=True,
            block_reasons=(),
            evidence_checksum=checksum,
            evaluated_at_utc=timestamp,
            objective_evidence=objectives,
        )

    @staticmethod
    def production_read_allowed(record: Mapping[str, Any]) -> bool:
        """Production readers fail closed unless every promotion marker is valid."""
        return (
            str(record.get("state", "")).strip().upper() == KnowledgeState.PRODUCTION_APPROVED.value
            and bool(record.get("production_usable", False))
            and bool(record.get("promotion_checksum_verified", False))
            and not bool(record.get("revoked", False))
        )

    @staticmethod
    def dashboard_snapshot(records: list[Mapping[str, Any]]) -> dict[str, Any]:
        counts = {state.value: 0 for state in KnowledgeState}
        usable = 0
        for record in records:
            raw_state = str(record.get("state", KnowledgeState.EXPERIMENTAL.value)).strip().upper()
            if raw_state in counts:
                counts[raw_state] += 1
            if ResearchPromotionGate.production_read_allowed(record):
                usable += 1
        return {
            "status": "READY",
            "research_quarantine_enabled": True,
            "production_fail_closed": True,
            "selection_method": "CONTEXT_OBJECTIVES",
            "selection_objectives": [
                "LOWER_DRAWDOWN",
                "HIGHER_NET_PROFIT",
                "HIGHER_WIN_PROBABILITY",
            ],
            "top_ranking_enabled": False,
            "state_counts": counts,
            "production_usable_count": usable,
            "experimental_data_used_by_production": False,
        }

    @staticmethod
    def _state(value: Any) -> KnowledgeState:
        try:
            return KnowledgeState(str(value).strip().upper())
        except ValueError:
            return KnowledgeState.EXPERIMENTAL

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if result == result and abs(result) != float("inf") else None

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            result = int(value)
        except (TypeError, ValueError):
            return None
        return result if result >= 0 else None

    @staticmethod
    def _checksum(record: Mapping[str, Any]) -> str:
        payload = {
            str(key): value
            for key, value in record.items()
            if key not in {"promotion_checksum", "promotion_checksum_verified"}
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return sha256(encoded).hexdigest().upper()
