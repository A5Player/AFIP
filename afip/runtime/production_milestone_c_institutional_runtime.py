"""Production Milestone C Pack 8 institutional positioning runtime."""

from __future__ import annotations

from datetime import datetime

from afip.institutional.institutional_positioning_runtime import InstitutionalPositioningRuntime
from afip.institutional.provider import InstitutionalDataProvider, StaticInstitutionalDataProvider


def build_production_milestone_c_institutional_state(
    values: dict[str, object] | None = None,
    observed_at: datetime | None = None,
    provider: InstitutionalDataProvider | None = None,
) -> dict[str, object]:
    """Build a Pack 8 institutional positioning state for runtime, tests, and replay."""

    selected_provider = provider or StaticInstitutionalDataProvider(values or {})
    return InstitutionalPositioningRuntime(provider=selected_provider).run_dict(observed_at=observed_at)
