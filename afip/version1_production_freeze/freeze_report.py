"""Version 1 production freeze report for Production Freeze Pack P6."""

from __future__ import annotations

from dataclasses import asdict

from .freeze_profile import Version1FreezeProfile


class Version1FreezeReport:
    """Human-readable final release readiness report."""

    def __init__(self, profile: Version1FreezeProfile) -> None:
        self.profile = profile

    def as_dict(self) -> dict[str, object]:
        data = asdict(self.profile)
        data["freeze_gate"] = self.profile.freeze_gate
        data["version1_frozen"] = self.profile.status == "READY"
        data["trading_logic_changed"] = False
        return data

    def as_text(self) -> str:
        return (
            "AFIP Version 1 Production Freeze Report\n"
            f"Status: {self.profile.status}\n"
            f"Gate: {self.profile.freeze_gate}\n"
            f"Release version: {self.profile.release_version}\n"
            f"Market regime: {self.profile.market_regime}\n"
            f"Signal context: {self.profile.signal_context}\n"
            f"Release score: {self.profile.release_score:.4f}\n"
            f"Walk-forward standard score: {self.profile.walk_forward_standard_score:.4f}\n"
            f"Decision reason: {self.profile.reason}"
        )
