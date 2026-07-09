"""Profile Manager runtime for Milestone H Pack 3."""

from __future__ import annotations

from typing import Any, Mapping

from .profile_policy import build_profile_report
from .profile_report import ProfileManagerReport


class ProfileManagerRuntime:
    """Evaluate reusable profile policy without binding it to an account."""

    def evaluate_one(self, record: Mapping[str, Any]) -> ProfileManagerReport:
        return build_profile_report(record)

    def explain_one(self, record: Mapping[str, Any]) -> ProfileManagerReport:
        return self.evaluate_one(record)

    def preview_save(self, record: Mapping[str, Any]) -> ProfileManagerReport:
        return self.evaluate_one(record)
