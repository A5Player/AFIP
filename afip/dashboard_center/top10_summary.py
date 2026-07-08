"""Top ranking summaries for AFIP Dashboard Center."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TopRankItem:
    category: str
    label_en: str
    label_th: str
    metric_name: str
    metric_value: float
    sample_size: int

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TopRankItem":
        return cls(
            category=str(value.get("category", "Top 10")).strip() or "Top 10",
            label_en=str(value.get("label_en", value.get("name", "Unknown"))).strip(),
            label_th=str(value.get("label_th", value.get("label_en", "ไม่ระบุ"))).strip(),
            metric_name=str(value.get("metric_name", "score")).strip(),
            metric_value=_ratio(value.get("metric_value", value.get("score", 0.0))),
            sample_size=max(int(value.get("sample_size", value.get("count", 0))), 0),
        )

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def build_top_rankings(records: Iterable[Mapping[str, Any]], limit: int = 10) -> list[TopRankItem]:
    items = [TopRankItem.from_mapping(item) for item in records]
    items.sort(key=lambda item: (item.metric_value, item.sample_size, item.label_en), reverse=True)
    return items[: max(int(limit), 0)]


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return round(min(max(number, 0.0), 1.0), 6)
