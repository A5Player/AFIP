from __future__ import annotations

from datetime import datetime, timedelta, timezone

from afip.provider_management import (
    DataQualityAssessment,
    ProviderHealthRecord,
    ProviderQualityEngine,
    ProviderRegistry,
    ProviderRouter,
)
from afip.provider_management.provider_management_runtime import ProviderManagementRuntime
from afip.runtime.production_milestone_c_provider_runtime import build_production_milestone_c_provider_state

NOW = datetime(2026, 7, 6, 12, 0, tzinfo=timezone.utc)


def test_provider_quality_scores_ready_provider_high() -> None:
    record = ProviderHealthRecord(
        provider_name="FRED_FREE",
        latency_ms=120,
        freshness_seconds=45,
        coverage_score=98,
        reliability_score=99,
        observed_at=NOW,
    )

    score = ProviderQualityEngine().score(record)

    assert score.decision == "READY"
    assert score.score >= 90
    assert score.reason == "provider_quality_ready"


def test_provider_quality_routes_offline_provider_unavailable() -> None:
    record = ProviderHealthRecord(provider_name="RSS_FREE", status="OFFLINE", observed_at=NOW)

    score = ProviderQualityEngine().score(record)

    assert score.decision == "UNAVAILABLE"
    assert score.score == 0


def test_provider_registry_ranks_best_provider_first() -> None:
    registry = ProviderRegistry()
    registry.extend(
        [
            ProviderHealthRecord(provider_name="SLOW_FREE", latency_ms=1900, freshness_seconds=500, coverage_score=70),
            ProviderHealthRecord(provider_name="FAST_FREE", latency_ms=80, freshness_seconds=30, coverage_score=98),
        ]
    )

    scores = registry.quality_scores()

    assert scores[0].provider_name == "FAST_FREE"
    assert registry.best_available().provider_name == "FAST_FREE"


def test_provider_router_uses_preferred_when_ready() -> None:
    registry = ProviderRegistry()
    registry.extend(
        [
            ProviderHealthRecord(provider_name="PREFERRED_FREE", latency_ms=100, freshness_seconds=20),
            ProviderHealthRecord(provider_name="BACKUP_FREE", latency_ms=60, freshness_seconds=10),
        ]
    )

    result = ProviderRouter(registry).route(preferred_provider="PREFERRED_FREE")

    assert result.provider_name == "PREFERRED_FREE"
    assert result.fallback_used is False
    assert result.status == "PROVIDER_ROUTE_READY"


def test_provider_router_falls_back_when_preferred_degraded() -> None:
    registry = ProviderRegistry()
    registry.extend(
        [
            ProviderHealthRecord(provider_name="PREFERRED_FREE", latency_ms=9000, freshness_seconds=4000, coverage_score=20),
            ProviderHealthRecord(provider_name="BACKUP_FREE", latency_ms=50, freshness_seconds=10, coverage_score=95),
        ]
    )

    result = ProviderRouter(registry).route(preferred_provider="PREFERRED_FREE")

    assert result.provider_name == "BACKUP_FREE"
    assert result.fallback_used is True


def test_provider_router_returns_unavailable_when_all_sources_fail() -> None:
    registry = ProviderRegistry()
    registry.extend(
        [
            ProviderHealthRecord(provider_name="ONE", status="OFFLINE"),
            ProviderHealthRecord(provider_name="TWO", status="ERROR"),
        ]
    )

    result = ProviderRouter(registry).route(preferred_provider="ONE")

    assert result.status == "PROVIDER_ROUTE_UNAVAILABLE"
    assert result.provider_name is None


def test_data_quality_ready_for_complete_fresh_payload() -> None:
    assessment = DataQualityAssessment(required_fields=("dxy", "us10y"), max_age_seconds=300)

    result = assessment.assess({"dxy": 101.2, "us10y": 4.1}, observed_at=NOW, now=NOW + timedelta(seconds=30))

    assert result.decision == "READY"
    assert result.missing_fields == ()
    assert result.stale is False


def test_data_quality_detects_missing_required_fields() -> None:
    assessment = DataQualityAssessment(required_fields=("dxy", "us10y", "real_yield"), max_age_seconds=300)

    result = assessment.assess({"dxy": 101.2}, observed_at=NOW, now=NOW)

    assert result.decision in {"REVIEW", "BLOCKED"}
    assert "us10y" in result.missing_fields
    assert "real_yield" in result.missing_fields


def test_data_quality_blocks_stale_duplicate_payload() -> None:
    assessment = DataQualityAssessment(required_fields=("dxy", "us10y"), max_age_seconds=60)

    result = assessment.assess({"dxy": 100.0, "us10y": 100.0}, observed_at=NOW, now=NOW + timedelta(minutes=5))

    assert result.decision == "BLOCKED"
    assert result.duplicate_count == 1
    assert result.stale is True


def test_provider_management_runtime_builds_ready_state() -> None:
    runtime = ProviderManagementRuntime(
        records=(ProviderHealthRecord(provider_name="MACRO_FREE", latency_ms=50, freshness_seconds=20),),
        required_fields=("dxy", "us10y"),
    )

    state = runtime.run_dict(values={"dxy": 101.0, "us10y": 4.0}, observed_at=NOW, now=NOW)

    assert state["status"] == "PROVIDER_MANAGEMENT_READY"
    assert state["decision"] == "READY"
    assert state["route"]["provider_name"] == "MACRO_FREE"


def test_production_milestone_c_provider_runtime_routes_review_when_data_quality_fails() -> None:
    state = build_production_milestone_c_provider_state(
        provider_records=(ProviderHealthRecord(provider_name="MACRO_FREE", latency_ms=50, freshness_seconds=20),),
        values={"dxy": 101.0},
        observed_at=NOW,
        now=NOW,
        required_fields=("dxy", "us10y", "real_yield"),
    )

    assert state["status"] == "PROVIDER_MANAGEMENT_REVIEW"
    assert state["decision"] == "REVIEW_ONLY"
    assert state["data_quality"]["decision"] in {"REVIEW", "BLOCKED"}
