"""Production quality checkpoint governance for AFIP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class QualityCheckpointResult:
    status: str
    score: float
    passed_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    reason: str


class QualityCheckpoint:
    """Evaluate production readiness checks without mutating runtime state."""

    REQUIRED_CHECKS = (
        "financial_naming_validation",
        "pytest",
        "simulation",
        "mt5_check",
        "github_ci",
    )

    def evaluate(self, checks: dict[str, bool] | None = None) -> QualityCheckpointResult:
        checks = checks or {}
        passed: list[str] = []
        failed: list[str] = []

        for name in self.REQUIRED_CHECKS:
            if bool(checks.get(name, False)):
                passed.append(name)
            else:
                failed.append(name)

        score = round((len(passed) / len(self.REQUIRED_CHECKS)) * 100, 2)
        status = "PASS" if not failed else "BLOCKED"
        reason = "all_required_checks_passed" if status == "PASS" else "required_checks_failed"

        return QualityCheckpointResult(
            status=status,
            score=score,
            passed_checks=tuple(passed),
            failed_checks=tuple(failed),
            reason=reason,
        )

    def from_completed_names(self, completed_checks: Iterable[str]) -> QualityCheckpointResult:
        completed = set(completed_checks)
        return self.evaluate({name: name in completed for name in self.REQUIRED_CHECKS})
