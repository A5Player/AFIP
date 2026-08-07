from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

KNOWLEDGE_CONTRACT_VERSION = "AFIP-W1-KNOWLEDGE-1.0"
OQS_MINIMUM_ENTRY = 97.0
OQS_HIGH_QUALITY = 98.0
OQS_ELITE = 99.0
OQS_MAXIMUM = 100.0


class RepositoryValidationError(ValueError):
    """Raised when evidence violates the W1 knowledge contract."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), sort_keys=True, separators=(",", ":"), default=str)


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def classify_oqs(score: float) -> "OpportunityAssessment":
    value = float(score)
    if value < 0.0 or value > OQS_MAXIMUM:
        raise RepositoryValidationError("oqs_out_of_range")
    if value < OQS_MINIMUM_ENTRY:
        return OpportunityAssessment(value, "WAIT_OR_SKIP", False, False, "oqs_below_97")
    if value < OQS_HIGH_QUALITY:
        return OpportunityAssessment(value, "GATE_ELIGIBLE", True, False, "all_authority_gates_required")
    if value < OQS_ELITE:
        return OpportunityAssessment(value, "HIGH_QUALITY", True, False, "all_authority_gates_required")
    return OpportunityAssessment(value, "ELITE", True, True, "extended_sl_review_eligible")


@dataclass(frozen=True)
class OpportunityAssessment:
    oqs: float
    classification: str
    entry_review_eligible: bool
    extended_sl_review_eligible: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptiveSLAssessment:
    requested_sl_points: int
    allowed: bool
    policy_class: str
    reason: str
    requires_all_gates: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_adaptive_sl(
    requested_sl_points: int,
    *,
    oqs: float,
    final_confidence: float,
    evidence_quality: str,
    all_gates_passed: bool,
    reward_risk_approved: bool,
) -> AdaptiveSLAssessment:
    points = int(requested_sl_points)
    opportunity = classify_oqs(oqs)
    allowed = points > 0 and opportunity.entry_review_eligible and all_gates_passed and reward_risk_approved
    return AdaptiveSLAssessment(
        points,
        allowed,
        "STRUCTURE_ATR_RESEARCH_BUFFER",
        "structural_sl_review_approved" if allowed else "structural_sl_gate_blocked",
    )


@dataclass(frozen=True)
class KnowledgeRecord:
    opportunity_id: str
    symbol: str
    observed_at_utc: str
    pattern_family: str
    pattern_variant: str
    market_regime: str
    volatility_class: str
    session: str
    trend_state: str
    sample_size: int
    evidence_quality: str
    historical_win_rate: float
    historical_expectancy: float
    historical_mae_points: float
    historical_mfe_points: float
    research_optimal_sl_points: int
    research_optimal_tp_points: int
    opportunity_quality_score: float
    source_ids: tuple[str, ...]
    contract_version: str = KNOWLEDGE_CONTRACT_VERSION
    execution_authority: bool = False
    order_send_called: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.opportunity_id.strip(): raise RepositoryValidationError("opportunity_id_required")
        if not self.symbol.strip(): raise RepositoryValidationError("symbol_required")
        if self.sample_size < 0: raise RepositoryValidationError("sample_size_negative")
        if not 0.0 <= float(self.historical_win_rate) <= 100.0: raise RepositoryValidationError("win_rate_out_of_range")
        classify_oqs(self.opportunity_quality_score)
        if self.execution_authority: raise RepositoryValidationError("research_execution_authority_forbidden")
        if self.order_send_called: raise RepositoryValidationError("research_order_send_forbidden")
        if not self.source_ids: raise RepositoryValidationError("source_ids_required")

    def as_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


class ResearchKnowledgeRepository:
    """Append-only, profile-independent research evidence repository.

    It does not import MT5, calculate lots, approve risk, or send orders.
    """
    def __init__(self, root: Path | str = Path("runtime/research_knowledge")) -> None:
        self.root = Path(root)
        self.records_path = self.root / "knowledge_records.jsonl"
        self.index_path = self.root / "knowledge_index.json"

    @staticmethod
    def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(dict(payload), indent=2, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(path)

    def _known_ids(self) -> set[str]:
        if not self.records_path.exists(): return set()
        ids=set()
        for line in self.records_path.read_text(encoding="utf-8-sig").splitlines():
            try: ids.add(str(json.loads(line).get("opportunity_id", "")))
            except (ValueError, TypeError): continue
        return ids

    def append(self, record: KnowledgeRecord) -> dict[str, Any]:
        payload = record.as_dict()
        self.root.mkdir(parents=True, exist_ok=True)
        known = self._known_ids()
        if record.opportunity_id in known:
            return {"status":"DUPLICATE","opportunity_id":record.opportunity_id,"written":False}
        with self.records_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(payload, sort_keys=True, default=str) + "\n")
        digest = _sha(_canonical(payload))
        count = len(known) + 1
        self._atomic_json(self.index_path, {
            "status":"READY", "contract_version":KNOWLEDGE_CONTRACT_VERSION,
            "record_count":count, "last_opportunity_id":record.opportunity_id,
            "last_record_sha256":digest, "updated_at_utc":_utc_now(),
            "execution_authority":False, "order_send_called":False,
        })
        return {"status":"WRITTEN","opportunity_id":record.opportunity_id,"written":True,"sha256":digest}

    def read_all(self) -> tuple[dict[str, Any], ...]:
        if not self.records_path.exists(): return ()
        result=[]
        for line in self.records_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip(): result.append(json.loads(line))
        return tuple(result)
