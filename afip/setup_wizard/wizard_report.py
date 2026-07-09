"""Setup Wizard report objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SetupWizardStep:
    step_id: str
    name_en: str
    name_th: str
    status: str
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SetupWizardReport:
    status: str
    reason: str
    wizard_gate: str
    steps: tuple[SetupWizardStep, ...]
    next_step: str
    profile_name: str
    broker: str
    symbol: str
    can_save: bool
    can_run_afip: bool
    trading_logic_changed: bool = False
    live_execution_enabled: bool = False

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["steps"] = [step.as_dict() for step in self.steps]
        return data

    def as_text(self) -> str:
        return (
            "AFIP Setup Wizard\n"
            f"Status: {self.status}\n"
            f"Gate: {self.wizard_gate}\n"
            f"Reason: {self.reason}\n"
            f"Next Step: {self.next_step}\n"
            f"Profile: {self.profile_name}\n"
            f"Can Save: {self.can_save}\n"
            f"Can Run AFIP: {self.can_run_afip}"
        )
