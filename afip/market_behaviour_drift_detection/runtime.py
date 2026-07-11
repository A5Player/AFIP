"""Milestone P Pack 6: deterministic market behaviour drift detection.

Compares accepted Pack 5 stability reports across certified baseline and recent
research segments. This runtime is research-only and has no adaptive,
production, position, broker, or order-transmission authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class MarketBehaviourDriftDetectionReport:
    report_id: str
    status: str
    reason: str
    milestone: str
    pack: str
    detection_timestamp: int
    baseline_window_count: int
    recent_window_count: int
    baseline_transition_count: int
    recent_transition_count: int
    baseline_mean_persistence_ratio: float
    recent_mean_persistence_ratio: float
    persistence_drift: float
    baseline_mean_regime_change_rate: float
    recent_mean_regime_change_rate: float
    regime_change_rate_drift: float
    baseline_mean_behaviour_change_rate: float
    recent_mean_behaviour_change_rate: float
    behaviour_change_rate_drift: float
    baseline_stable_window_rate: float
    recent_stable_window_rate: float
    stable_window_rate_drift: float
    source_report_ids: tuple[str, ...]
    schema_version: str
    pack_5_stability_accepted: bool
    unique_source_reports: bool
    baseline_coverage_met: bool
    recent_coverage_met: bool
    chronology_valid: bool
    data_quality_certified: bool
    future_safe: bool
    market_regime_before_behaviour: bool
    drift_detected: bool
    immutable_record: bool
    research_only: bool
    automatic_parameter_update_allowed: bool
    trading_logic_change_allowed: bool
    production_knowledge_allowed: bool
    production_certification_granted: bool
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    base_lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    position_modification_attempted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketBehaviourDriftDetectionRuntime:
    """Detect Pack 5 behaviour drift without adaptive or execution authority."""

    def evaluate_many(
        self,
        reports: Iterable[Mapping[str, Any]],
        *,
        detection_timestamp: int,
        baseline_window_count: int = 3,
        recent_window_count: int = 3,
        minimum_transitions_per_segment: int = 27,
        maximum_absolute_persistence_drift: float = 0.20,
        maximum_absolute_change_rate_drift: float = 0.25,
        maximum_absolute_stable_window_rate_drift: float = 0.35,
    ) -> MarketBehaviourDriftDetectionReport:
        rows = [dict(item) for item in reports]
        ids = tuple(str(row.get("report_id", "")).strip().upper() for row in rows)
        timestamps = tuple(self._integer(row.get("validation_timestamp", 0)) for row in rows)
        detection_ts = self._integer(detection_timestamp)
        base_n = max(1, self._integer(baseline_window_count))
        recent_n = max(1, self._integer(recent_window_count))
        baseline = rows[:base_n]
        recent = rows[-recent_n:] if len(rows) >= recent_n else []

        source_ready = bool(rows) and all(
            str(row.get("status", "")).strip().upper() == "READY"
            and str(row.get("schema_version", "")).strip().upper() == "AFIP_MARKET_BEHAVIOUR_STABILITY_VALIDATION_V1"
            and report_id.startswith("PBST-")
            for row, report_id in zip(rows, ids)
        )
        unique = bool(ids) and len(ids) == len(set(ids))
        chronology = (
            bool(rows)
            and all(ts > 0 for ts in timestamps)
            and tuple(sorted(timestamps)) == timestamps
            and detection_ts >= max(timestamps)
        )
        quality = bool(rows) and all(bool(row.get("data_quality_certified", False)) for row in rows)
        future_safe = bool(rows) and all(bool(row.get("future_safe", False)) for row in rows)
        regime_first = bool(rows) and all(bool(row.get("market_regime_before_behaviour", False)) for row in rows)
        policy_valid = bool(rows) and all(self._policy_valid(row) for row in rows)

        baseline_transitions = sum(max(0, self._integer(row.get("total_transition_count", 0))) for row in baseline)
        recent_transitions = sum(max(0, self._integer(row.get("total_transition_count", 0))) for row in recent)
        baseline_coverage = len(baseline) == base_n and baseline_transitions >= max(1, self._integer(minimum_transitions_per_segment))
        recent_coverage = len(recent) == recent_n and recent_transitions >= max(1, self._integer(minimum_transitions_per_segment))

        metric_keys = (
            "mean_persistence_ratio", "mean_regime_change_rate",
            "mean_behaviour_change_rate", "stable_window_rate",
        )
        metrics_valid = bool(rows) and all(
            all(self._unit_interval(self._number(row.get(key, float("nan")))) for key in metric_keys)
            for row in rows
        )

        base_p = self._mean(baseline, "mean_persistence_ratio") if metrics_valid else 0.0
        recent_p = self._mean(recent, "mean_persistence_ratio") if metrics_valid else 0.0
        p_drift = round(recent_p - base_p, 8)
        base_r = self._mean(baseline, "mean_regime_change_rate") if metrics_valid else 0.0
        recent_r = self._mean(recent, "mean_regime_change_rate") if metrics_valid else 0.0
        r_drift = round(recent_r - base_r, 8)
        base_b = self._mean(baseline, "mean_behaviour_change_rate") if metrics_valid else 0.0
        recent_b = self._mean(recent, "mean_behaviour_change_rate") if metrics_valid else 0.0
        b_drift = round(recent_b - base_b, 8)
        base_s = self._mean(baseline, "stable_window_rate") if metrics_valid else 0.0
        recent_s = self._mean(recent, "stable_window_rate") if metrics_valid else 0.0
        s_drift = round(recent_s - base_s, 8)

        p_ok = abs(p_drift) <= self._number(maximum_absolute_persistence_drift)
        r_ok = abs(r_drift) <= self._number(maximum_absolute_change_rate_drift)
        b_ok = abs(b_drift) <= self._number(maximum_absolute_change_rate_drift)
        s_ok = abs(s_drift) <= self._number(maximum_absolute_stable_window_rate_drift)

        checks = (
            (not source_ready, "pack_5_stability_lineage_invalid"),
            (not unique, "duplicate_stability_report_id_detected"),
            (len(rows) < base_n + recent_n, "insufficient_drift_window_count"),
            (not baseline_coverage, "baseline_transition_coverage_not_met"),
            (not recent_coverage, "recent_transition_coverage_not_met"),
            (not chronology, "market_behaviour_drift_chronology_invalid"),
            (not quality, "data_quality_not_certified"),
            (not future_safe, "future_leakage_detected"),
            (not regime_first, "market_regime_not_evaluated_before_behaviour"),
            (not metrics_valid, "market_behaviour_drift_metrics_invalid"),
            (metrics_valid and not p_ok, "persistence_drift_limit_exceeded"),
            (metrics_valid and (not r_ok or not b_ok), "change_rate_drift_limit_exceeded"),
            (metrics_valid and not s_ok, "stable_window_rate_drift_limit_exceeded"),
            (not policy_valid, "feature_freeze_or_execution_policy_violation"),
        )
        blocked = tuple(sorted({reason for condition, reason in checks if condition}))
        drift_detected = any(reason.endswith("drift_limit_exceeded") for reason in blocked)
        ready = not blocked

        identity = {
            "ids": ids,
            "timestamps": timestamps,
            "detection_timestamp": detection_ts,
            "thresholds": [base_n, recent_n, minimum_transitions_per_segment, maximum_absolute_persistence_drift, maximum_absolute_change_rate_drift, maximum_absolute_stable_window_rate_drift],
            "blocked": blocked,
        }
        report_id = "PBDR-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        if ready:
            reason = "MARKET_BEHAVIOUR_DRIFT_NOT_DETECTED_RESEARCH_ONLY"
            en = "Accepted Pack 5 stability reports remained within certified behaviour-drift limits across baseline and recent research segments."
            th = "รายงานเสถียรภาพจาก Pack 5 อยู่ภายในเพดาน Drift ของพฤติกรรมตลาดที่รับรองระหว่างช่วง Baseline และ Recent"
        else:
            reason = "MARKET_BEHAVIOUR_DRIFT_DETECTION_BLOCKED"
            en = "Behaviour drift validation was blocked by lineage, coverage, chronology, data, drift-limit, or frozen-policy validation."
            th = "การตรวจ Drift ของพฤติกรรมตลาดถูกระงับจาก Lineage, Coverage, ลำดับเวลา, ข้อมูล, เพดาน Drift หรือนโยบายล็อก"

        return MarketBehaviourDriftDetectionReport(
            report_id=report_id, status="READY" if ready else "BLOCKED", reason=reason,
            milestone="P", pack="6", detection_timestamp=detection_ts,
            baseline_window_count=len(baseline), recent_window_count=len(recent),
            baseline_transition_count=baseline_transitions, recent_transition_count=recent_transitions,
            baseline_mean_persistence_ratio=base_p, recent_mean_persistence_ratio=recent_p, persistence_drift=p_drift,
            baseline_mean_regime_change_rate=base_r, recent_mean_regime_change_rate=recent_r, regime_change_rate_drift=r_drift,
            baseline_mean_behaviour_change_rate=base_b, recent_mean_behaviour_change_rate=recent_b, behaviour_change_rate_drift=b_drift,
            baseline_stable_window_rate=base_s, recent_stable_window_rate=recent_s, stable_window_rate_drift=s_drift,
            source_report_ids=ids, schema_version="AFIP_MARKET_BEHAVIOUR_DRIFT_DETECTION_V1",
            pack_5_stability_accepted=source_ready, unique_source_reports=unique,
            baseline_coverage_met=baseline_coverage, recent_coverage_met=recent_coverage,
            chronology_valid=chronology, data_quality_certified=quality, future_safe=future_safe,
            market_regime_before_behaviour=regime_first, drift_detected=drift_detected,
            immutable_record=True, research_only=True, automatic_parameter_update_allowed=False,
            trading_logic_change_allowed=False, production_knowledge_allowed=False,
            production_certification_granted=False, block_reasons=blocked,
            explanation_reason_en=en, explanation_reason_th=th,
        )

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float("nan")

    @staticmethod
    def _integer(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _unit_interval(value: float) -> bool:
        return math.isfinite(value) and 0.0 <= value <= 1.0

    def _mean(self, rows: list[dict[str, Any]], key: str) -> float:
        if not rows:
            return 0.0
        values = [self._number(row.get(key, 0.0)) for row in rows]
        return round(sum(values) / len(values), 8)

    def _policy_valid(self, row: Mapping[str, Any]) -> bool:
        return (
            str(row.get("broker", "XM")).strip().upper() == "XM"
            and str(row.get("symbol", "GOLD#")).strip().upper() == "GOLD#"
            and abs(self._number(row.get("base_lot_per_unit", 0.01)) - 0.01) <= 1e-12
            and str(row.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper() == "LOCKED_SIMULATION_ONLY"
            and str(row.get("order_status", "NO_ORDER_SENT")).strip().upper() == "NO_ORDER_SENT"
            and not bool(row.get("direct_execution", False))
            and not bool(row.get("live_execution_enabled", False))
            and not bool(row.get("automatic_parameter_update_allowed", False))
            and not bool(row.get("trading_logic_change_allowed", False))
            and not bool(row.get("production_knowledge_allowed", False))
        )
