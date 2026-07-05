"""Shared helpers for AFIP production financial engines."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class EngineResult:
    """Standard engine result payload."""

    name: str
    status: str
    action: str
    confidence: float
    reason: str
    details: dict

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "action": self.action,
            "confidence": round(float(self.confidence), 2),
            "reason": self.reason,
            **self.details,
        }


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return round(max(minimum, min(maximum, float(value))), 2)


def numbers(values: object) -> list[float]:
    if values is None:
        return []
    if isinstance(values, (int, float)):
        return [float(values)]
    if not isinstance(values, Iterable) or isinstance(values, (str, bytes, dict)):
        return []
    out: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            out.append(float(value))
        except (TypeError, ValueError):
            continue
    return out


def weighted_average(items: list[tuple[float, float]], default: float = 0.0) -> float:
    total_weight = sum(max(0.0, weight) for _, weight in items)
    if total_weight <= 0:
        return round(float(default), 2)
    return round(sum(float(value) * max(0.0, weight) for value, weight in items) / total_weight, 2)


def direction_scores(intelligence: list[dict]) -> tuple[float, float, float]:
    buy_items: list[tuple[float, float]] = []
    sell_items: list[tuple[float, float]] = []
    flat_items: list[tuple[float, float]] = []
    for item in intelligence:
        confidence = clamp(item.get("confidence", 0.0))
        weight = float(item.get("weight", 1.0) or 1.0)
        direction = str(item.get("direction", "FLAT")).upper()
        if direction == "BUY":
            buy_items.append((confidence, weight))
        elif direction == "SELL":
            sell_items.append((confidence, weight))
        else:
            flat_items.append((confidence, weight))
    return (
        weighted_average(buy_items, 0.0),
        weighted_average(sell_items, 0.0),
        weighted_average(flat_items, 0.0),
    )
