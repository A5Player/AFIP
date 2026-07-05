"""Shared analytics helpers for AFIP production reporting."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return round(max(minimum, min(maximum, float(value))), 2)


def values(items: Iterable[object], key: str) -> list[float]:
    output: list[float] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        try:
            output.append(float(item.get(key, 0.0) or 0.0))
        except (TypeError, ValueError):
            continue
    return output


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    denominator = float(denominator or 0.0)
    if denominator == 0.0:
        return round(float(default), 4)
    return round(float(numerator) / denominator, 4)


@dataclass(frozen=True)
class AnalyticsResult:
    name: str
    status: str
    score: float
    reason: str
    details: dict

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "score": clamp(self.score),
            "reason": self.reason,
            **self.details,
        }
