from __future__ import annotations

import json
from pathlib import Path

from afip.four_profile_operations.runtime import (
    LOCKED_EXECUTION,
    FourProfileOperationalRuntime,
)


CONFIG_PATH = Path("config/four_profile_demo.json")
EXPECTED_PROFILE_IDS = {"P1", "P2", "P3", "P4"}


def test_repository_configuration_enables_all_four_demo_profiles() -> None:
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    enabled_by_profile = {
        str(profile["profile_id"]).strip().upper(): bool(profile.get("enabled", False))
        for profile in payload["profiles"]
    }

    assert set(enabled_by_profile) == EXPECTED_PROFILE_IDS
    assert enabled_by_profile == {profile_id: True for profile_id in sorted(EXPECTED_PROFILE_IDS)}


def test_four_profile_loader_preserves_enabled_source_of_truth() -> None:
    profiles = FourProfileOperationalRuntime(CONFIG_PATH).load()
    loaded = {profile.profile_id: profile.enabled for profile in profiles}

    assert loaded == {profile_id: True for profile_id in sorted(EXPECTED_PROFILE_IDS)}


def test_profile_restore_does_not_unlock_execution_safety() -> None:
    profiles = FourProfileOperationalRuntime(CONFIG_PATH).load()

    assert all(profile.execution in {LOCKED_EXECUTION, 'DEMO_EXECUTION_ONLY'} for profile in profiles)
    assert all(profile.direct_execution is False for profile in profiles)
    assert all(profile.live_execution is False for profile in profiles)
    assert FourProfileOperationalRuntime(CONFIG_PATH).validate(profiles) == ()
