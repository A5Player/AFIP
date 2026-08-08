from __future__ import annotations

from afip.research_standardization.adversarial_market_behaviour import AdversarialMarketBehaviourResearch


def _bars() -> list[dict[str, object]]:
    rows = []
    for index in range(44):
        compressed = index >= 12
        centre = 2000.0 + ((index % 3) - 1) * (0.07 if compressed else 1.5)
        width = 0.10 if compressed else 2.0
        rows.append({
            "timestamp_utc": f"2026-01-{index + 1:02d}T00:00:00Z",
            "open": centre, "high": centre + width, "low": centre - width, "close": centre + width * 0.1,
        })
    return rows


def test_adversarial_outcome_research_is_append_only_and_cumulative(tmp_path) -> None:
    research = AdversarialMarketBehaviourResearch(tmp_path)
    first = research.run({"M15": _bars()})
    assert first["new_observations_accepted"] > 0
    assert first["cumulative_observations"] == first["new_observations_accepted"]
    assert first["research_only"] is True
    assert first["execution_authority"] == "NONE"
    assert first["rankings"]

    second = research.run({"M15": _bars()})
    assert second["new_observations_accepted"] == 0
    assert second["cumulative_observations"] == first["cumulative_observations"]
