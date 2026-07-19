"""Canonical AFIP timeframe registry.

This module is the single ordered source for historical collection, research
replay, data-quality coverage and timeframe conversion.  It contains no order
execution or live trading authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from types import MappingProxyType
from typing import Any, Iterator, Mapping


@dataclass(frozen=True)
class TimeframeDefinition:
    name: str
    minutes: int
    mt5_constant_name: str
    historical_collection_enabled: bool = True
    chronological_replay_enabled: bool = True
    research_enabled: bool = True
    gap_detection_enabled: bool = True
    dashboard_enabled: bool = True

    @property
    def seconds(self) -> int:
        return self.minutes * 60

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["seconds"] = self.seconds
        return payload


_DEFINITIONS = (
    TimeframeDefinition("M1", 1, "TIMEFRAME_M1"),
    TimeframeDefinition("M5", 5, "TIMEFRAME_M5"),
    TimeframeDefinition("M15", 15, "TIMEFRAME_M15"),
    TimeframeDefinition("M30", 30, "TIMEFRAME_M30"),
    TimeframeDefinition("H1", 60, "TIMEFRAME_H1"),
    TimeframeDefinition("H4", 240, "TIMEFRAME_H4"),
    TimeframeDefinition("D1", 1440, "TIMEFRAME_D1"),
)

TIMEFRAME_REGISTRY: Mapping[str, TimeframeDefinition] = MappingProxyType(
    {definition.name: definition for definition in _DEFINITIONS}
)
SUPPORTED_TIMEFRAMES = tuple(TIMEFRAME_REGISTRY)


def normalize_timeframe(timeframe: str) -> str:
    key = str(timeframe).strip().upper()
    if key not in TIMEFRAME_REGISTRY:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return key


def is_supported(timeframe: str) -> bool:
    return str(timeframe).strip().upper() in TIMEFRAME_REGISTRY


def get_timeframe_definition(timeframe: str) -> TimeframeDefinition:
    return TIMEFRAME_REGISTRY[normalize_timeframe(timeframe)]


def get_timeframe_metadata(timeframe: str) -> dict[str, Any]:
    return get_timeframe_definition(timeframe).as_dict()


def get_supported_timeframes(*, capability: str | None = None) -> tuple[str, ...]:
    if capability is None:
        return SUPPORTED_TIMEFRAMES
    attribute = {
        "historical_collection": "historical_collection_enabled",
        "chronological_replay": "chronological_replay_enabled",
        "research": "research_enabled",
        "gap_detection": "gap_detection_enabled",
        "dashboard": "dashboard_enabled",
    }.get(str(capability).strip().lower())
    if attribute is None:
        raise ValueError(f"Unsupported timeframe capability: {capability}")
    return tuple(
        definition.name for definition in _DEFINITIONS if bool(getattr(definition, attribute))
    )


def get_minutes(timeframe: str) -> int:
    return get_timeframe_definition(timeframe).minutes


def get_seconds(timeframe: str) -> int:
    return get_timeframe_definition(timeframe).seconds


def get_mt5_constant_name(timeframe: str) -> str:
    return get_timeframe_definition(timeframe).mt5_constant_name


def get_mt5_timeframe_code(mt5_module: Any, timeframe: str) -> Any:
    constant_name = get_mt5_constant_name(timeframe)
    try:
        return getattr(mt5_module, constant_name)
    except AttributeError as exc:
        raise RuntimeError(f"MT5 module does not provide {constant_name}") from exc


def iter_timeframes(*, capability: str | None = None) -> Iterator[TimeframeDefinition]:
    names = get_supported_timeframes(capability=capability)
    return (TIMEFRAME_REGISTRY[name] for name in names)
