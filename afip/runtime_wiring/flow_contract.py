"""Runtime flow contract for Production Milestone D Pack 1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .component_state import RuntimeComponentState

REQUIRED_COMPONENT_ORDER = (
    "MARKET_REGIME",
    "DECISION_INTELLIGENCE",
    "EXECUTION_READINESS",
    "PRODUCTION_INTEGRATION",
    "MILESTONE_COMPLETION",
)


@dataclass(frozen=True)
class RuntimeFlowContract:
    """Deterministic contract that proves the runtime can be wired in order."""

    components: tuple[RuntimeComponentState, ...]

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.components, key=lambda item: (item.sequence_index, item.component_key)))
        object.__setattr__(self, "components", ordered)

    @property
    def component_keys(self) -> tuple[str, ...]:
        return tuple(component.component_key for component in self.components)

    @property
    def missing_components(self) -> tuple[str, ...]:
        present = set(self.component_keys)
        return tuple(key for key in REQUIRED_COMPONENT_ORDER if key not in present)

    @property
    def failed_components(self) -> tuple[str, ...]:
        return tuple(component.component_key for component in self.components if not component.is_ready)

    @property
    def sequence_is_valid(self) -> bool:
        observed = [key for key in self.component_keys if key in REQUIRED_COMPONENT_ORDER]
        expected = [key for key in REQUIRED_COMPONENT_ORDER if key in observed]
        return observed == expected

    @property
    def aggregate_readiness(self) -> float:
        if not self.components:
            return 0.0
        return round(sum(component.readiness_score for component in self.components) / len(self.components), 4)

    @property
    def is_wirable(self) -> bool:
        return not self.missing_components and not self.failed_components and self.sequence_is_valid

    @classmethod
    def from_runtime_states(cls, states: Mapping[str, Mapping[str, Any]]) -> "RuntimeFlowContract":
        components: list[RuntimeComponentState] = []
        for index, key in enumerate(REQUIRED_COMPONENT_ORDER, start=1):
            payload = states.get(key, {})
            if payload:
                components.append(RuntimeComponentState.from_mapping(key, payload, index))
        extras = sorted(key for key in states if key not in REQUIRED_COMPONENT_ORDER)
        for offset, key in enumerate(extras, start=len(REQUIRED_COMPONENT_ORDER) + 1):
            components.append(RuntimeComponentState.from_mapping(key, states[key], offset))
        return cls(tuple(components))

    def as_dict(self) -> dict[str, object]:
        return {
            "components": [component.as_dict() for component in self.components],
            "component_keys": list(self.component_keys),
            "missing_components": list(self.missing_components),
            "failed_components": list(self.failed_components),
            "sequence_is_valid": self.sequence_is_valid,
            "aggregate_readiness": self.aggregate_readiness,
            "is_wirable": self.is_wirable,
        }
