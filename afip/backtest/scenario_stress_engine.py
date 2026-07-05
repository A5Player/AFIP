"""Scenario stress testing engine for market condition resilience."""
from __future__ import annotations


class ScenarioStressEngine:
    """Score performance across adverse market scenarios."""

    name = "ScenarioStressEngine"

    def evaluate(self, scenarios: list[dict]) -> dict:
        if not scenarios:
            return {"name": self.name, "status": "NO_DATA", "score": 0.0, "reason": "no_scenarios", "scenarios": []}
        reviewed = []
        total = 0.0
        blockers = 0
        for scenario in scenarios:
            name = str(scenario.get("name", "UNKNOWN")).upper()
            net_profit = float(scenario.get("net_profit", 0.0) or 0.0)
            drawdown_percent = float(scenario.get("drawdown_percent", 0.0) or 0.0)
            recovery_factor = float(scenario.get("recovery_factor", 0.0) or 0.0)
            score = max(0.0, min(100.0, 50.0 + net_profit * 0.1 + recovery_factor * 10.0 - drawdown_percent * 1.5))
            blocked = drawdown_percent >= 35.0
            blockers += 1 if blocked else 0
            total += score
            reviewed.append({"name": name, "score": round(score, 2), "blocked": blocked, "drawdown_percent": round(drawdown_percent, 2)})
        average = round(total / len(reviewed), 2)
        status = "READY" if blockers == 0 else "CAUTION"
        return {"name": self.name, "status": status, "score": average, "reason": "scenario_stress_ready", "scenarios": reviewed, "blockers": blockers}
