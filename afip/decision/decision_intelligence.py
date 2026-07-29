from __future__ import annotations

from afip.decision.intelligence_activation import activation_for


class DecisionIntelligence:
    """Combine modular outputs through explicit, traceable activation policy."""

    READY_STATUSES = {"READY", "PASS", "ACTIVE"}
    BLOCK_STATUSES = {"BLOCKED", "FAIL", "ERROR"}

    def decide(self, intelligence_results: list) -> dict:
        buy_weighted = 0.0
        sell_weighted = 0.0
        buy_weight = 0.0
        sell_weight = 0.0
        penalties = 0.0
        explain = []
        supporting = []
        opposing = []
        neutral = []
        blocking = []

        for item in intelligence_results:
            name = str(item.get("name", "UNKNOWN"))
            activation = activation_for(name)
            direction = str(item.get("direction", "FLAT")).upper()
            status = str(item.get("status", "UNKNOWN")).upper()
            confidence = max(0.0, min(100.0, float(item.get("confidence", 0) or 0)))
            penalty = max(0.0, float(item.get("confidence_penalty", 0) or 0))
            penalties += penalty

            eligible = activation.decision_vote and status in self.READY_STATUSES and direction in {"BUY", "SELL"}
            contribution = confidence * activation.weight if eligible else 0.0
            evidence = {
                "name": name,
                "role": activation.role,
                "direction": direction,
                "confidence": confidence,
                "status": status,
                "reason": item.get("reason"),
                "decision_vote": activation.decision_vote,
                "vote_eligible": eligible,
                "weight": activation.weight,
                "confidence_contribution": round(contribution, 4),
                "activation_reason": activation.reason,
            }
            explain.append(evidence)

            if status in self.BLOCK_STATUSES:
                blocking.append(evidence)
            elif not eligible:
                neutral.append(evidence)
            elif direction == "BUY":
                buy_weighted += contribution
                buy_weight += activation.weight
                supporting.append(evidence)
            elif direction == "SELL":
                sell_weighted += contribution
                sell_weight += activation.weight
                opposing.append(evidence)

        buy_score = buy_weighted / buy_weight if buy_weight else 0.0
        sell_score = sell_weighted / sell_weight if sell_weight else 0.0
        confidence = max(buy_score, sell_score)
        edge = abs(buy_score - sell_score)

        if blocking:
            action = "WAIT"
            decision_reason = "blocking_intelligence_present"
            conflict_reason = "one_or_more_intelligence_modules_reported_blocking_status"
        elif confidence < 60:
            action = "WAIT"
            decision_reason = "confidence_below_threshold"
            conflict_reason = "eligible_directional_consensus_below_threshold"
        elif edge < 5:
            action = "WAIT"
            decision_reason = "no_clear_edge"
            conflict_reason = "buy_sell_weighted_edge_below_minimum"
        elif buy_score > sell_score:
            action = "BUY"
            decision_reason = "decision_intelligence_buy_edge"
            conflict_reason = "weighted_buy_evidence_exceeded_sell_evidence"
        else:
            action = "SELL"
            decision_reason = "decision_intelligence_sell_edge"
            conflict_reason = "weighted_sell_evidence_exceeded_buy_evidence"

        selected = supporting if action == "BUY" else opposing if action == "SELL" else []
        rejected = opposing if action == "BUY" else supporting if action == "SELL" else supporting + opposing

        return {
            "action": action,
            "confidence": round(confidence, 2),
            "buy_score": round(buy_score, 2),
            "sell_score": round(sell_score, 2),
            "edge": round(edge, 2),
            "penalties": round(penalties, 2),
            "reason": decision_reason,
            "conflict_resolution_reason": conflict_reason,
            "supporting_intelligence": supporting if action != "SELL" else opposing,
            "opposing_intelligence": opposing if action != "SELL" else supporting,
            "neutral_intelligence": neutral,
            "blocking_intelligence": blocking,
            "selected_scenario": f"{action}_WEIGHTED_INTELLIGENCE" if action in {"BUY", "SELL"} else "WAIT_FOR_CLEAR_EDGE",
            "rejected_scenarios": ["SELL" if action == "BUY" else "BUY"] if action in {"BUY", "SELL"} else ["BUY", "SELL"],
            "selected_evidence": selected,
            "rejected_evidence": rejected,
            "explain": explain,
        }
