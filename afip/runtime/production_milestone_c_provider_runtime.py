"""Production Milestone C Pack 9 provider management runtime."""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Sequence

from afip.provider_management.provider_health import ProviderHealthRecord
from afip.provider_management.provider_management_runtime import ProviderManagementRuntime


def build_production_milestone_c_provider_state(
    provider_records: Sequence[ProviderHealthRecord] | None = None,
    values: Mapping[str, object] | None = None,
    observed_at: datetime | None = None,
    now: datetime | None = None,
    preferred_provider: str | None = None,
    required_fields: tuple[str, ...] = (),
) -> dict[str, object]:
    """Build Pack 9 provider management state for runtime, replay, and tests."""
    return ProviderManagementRuntime(
        records=provider_records or (),
        required_fields=required_fields,
    ).run_dict(
        values=values,
        observed_at=observed_at,
        now=now,
        preferred_provider=preferred_provider,
    )
