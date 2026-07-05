"""Execution readiness engine for final pre-order validation."""
from __future__ import annotations

from afip.engine._common import EngineResult, clamp


class ExecutionReadinessEngine:
    """Validate decision, risk, cost, and position readiness before execution."""

    name = "ExecutionReadinessEngine"

    required_allow_actions = {"ALLOW", "BUY", "SELL"}

    def evaluate(self, snapshot: dict) -> dict:
        checks = list(snapshot.get("checks", []))
        if not checks:
            return EngineResult(self.name, "LEARNING", "WAIT", 30.0, "execution_checks_not_available", {}).as_dict()
        failed = [check for check in checks if check.get("action") not in self.required_allow_actions]
        cautions = [check for check in checks if check.get("status") == "CAUTION"]
        average_confidence = sum(float(check.get("confidence", 0.0) or 0.0) for check in checks) / len(checks)
        confidence = clamp(average_confidence - len(cautions) * 5.0 - len(failed) * 20.0)
        allowed = not failed and confidence >= 55.0
        return EngineResult(
            self.name,
            "READY" if allowed else "BLOCKED",
            "ALLOW" if allowed else "WAIT",
            confidence,
            "execution_ready" if allowed else "execution_not_ready",
            {"check_count": len(checks), "failed_checks": [check.get("name", "unknown") for check in failed], "caution_count": len(cautions)},
        ).as_dict()
