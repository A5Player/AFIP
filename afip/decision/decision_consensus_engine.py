"""Decision consensus calculation for financial intelligence inputs."""

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

VALID_ACTIONS = {"BUY", "SELL", "WAIT", "NO_ACTION", "REDUCE"}

@dataclass(frozen=True)
class DecisionConsensusResult:
    status: str
    action: str
    consensus_score: float
    agreement_ratio: float
    reason: str

class DecisionConsensusEngine:
    """Aggregates decision candidates into a single consensus action."""

    def evaluate(self, candidates: Iterable[Mapping[str, Any]]) -> DecisionConsensusResult:
        entries = [dict(item) for item in candidates]
        if not entries:
            return DecisionConsensusResult("DECISION_CONSENSUS_EMPTY", "NO_ACTION", 0.0, 0.0, "no_decision_candidates")

        scores: dict[str, float] = {}
        total = 0.0
        for item in entries:
            action = str(item.get("action", "NO_ACTION")).upper()
            if action not in VALID_ACTIONS:
                action = "NO_ACTION"
            confidence = max(0.0, min(100.0, float(item.get("confidence", 0.0))))
            weight = max(0.0, float(item.get("weight", 1.0)))
            contribution = confidence * weight
            scores[action] = scores.get(action, 0.0) + contribution
            total += contribution

        if total <= 0:
            return DecisionConsensusResult("DECISION_CONSENSUS_REVIEW", "NO_ACTION", 0.0, 0.0, "zero_weighted_contribution")

        action, score = max(scores.items(), key=lambda pair: pair[1])
        consensus_score = round(score / total * 100.0, 2)
        agreement_ratio = round(sum(1 for item in entries if str(item.get("action", "NO_ACTION")).upper() == action) / len(entries), 4)
        status = "DECISION_CONSENSUS_READY" if consensus_score >= 55.0 and action != "NO_ACTION" else "DECISION_CONSENSUS_REVIEW"
        return DecisionConsensusResult(status, action, consensus_score, agreement_ratio, f"consensus_{action.lower()}")
