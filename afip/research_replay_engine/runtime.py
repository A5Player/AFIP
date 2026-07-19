"""Blind historical replay that exposes one market event at a time."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

@dataclass(frozen=True)
class ReplayPolicy:
    starting_equity: float = 10000.0
    maximum_drawdown_percentage: float = 20.0
    stop_on_drawdown_limit: bool = True

class ReplayEngine:
    def __init__(self, policy: ReplayPolicy | None = None) -> None:
        self.policy = policy or ReplayPolicy()

    def run(
        self,
        events: Iterable[Mapping[str, Any]],
        decision_function: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        equity = self.policy.starting_equity
        peak = equity
        maximum_drawdown_percentage = 0.0
        timeline = []
        status = "COMPLETED"

        for index, source_event in enumerate(events):
            event = dict(source_event)
            visible_event = dict(event)
            visible_event.pop("future_profit", None)
            decision = dict(decision_function(visible_event))
            realized = float(event.get("future_profit", 0.0)) if decision.get("action") in {"BUY", "SELL"} else 0.0
            equity += realized
            peak = max(peak, equity)
            drawdown_percentage = ((peak - equity) / peak * 100.0) if peak else 0.0
            maximum_drawdown_percentage = max(maximum_drawdown_percentage, drawdown_percentage)
            timeline.append({
                "index": index,
                "timestamp_utc": event.get("timestamp_utc"),
                "decision": decision,
                "realized_profit": realized,
                "equity": round(equity, 8),
                "drawdown_percentage": round(drawdown_percentage, 8),
            })
            if (
                self.policy.stop_on_drawdown_limit
                and maximum_drawdown_percentage > self.policy.maximum_drawdown_percentage
            ):
                status = "STOPPED_DRAWDOWN_LIMIT"
                break

        return {
            "schema_version": "1.0",
            "status": status,
            "starting_equity": self.policy.starting_equity,
            "ending_equity": round(equity, 8),
            "maximum_drawdown_percentage": round(maximum_drawdown_percentage, 8),
            "processed_event_count": len(timeline),
            "execution_permission": False,
            "timeline": timeline,
        }
