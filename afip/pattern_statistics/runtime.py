"""Milestone M Pack 5: deterministic research pattern statistics."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import sqrt
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternStatistic:
    scope_id: str
    scope_type: str
    market_regime: str
    sample_count: int
    accepted_count: int
    rejected_count: int
    win_count: int
    loss_count: int
    breakeven_count: int
    win_rate: float
    average_r_multiple: float
    expectancy_r: float
    gross_profit_r: float
    gross_loss_r: float
    profit_factor: float
    r_standard_deviation: float
    confidence_tier: str
    source_lineages: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternStatisticsReport:
    status: str
    reason: str
    milestone: str
    pack: str
    statistics_id: str
    knowledge_version: str
    source_pattern_count: int
    source_cluster_count: int
    eligible_outcome_count: int
    statistic_count: int
    sufficient_sample_count: int
    minimum_sample_size: int
    chronology_valid: bool
    pattern_lineage_valid: bool
    cluster_lineage_valid: bool
    outcome_values_valid: bool
    deterministic_statistics_valid: bool
    future_safe: bool
    research_only: bool
    pattern_statistics_enabled: bool
    pattern_validation_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    statistics: tuple[PatternStatistic, ...]
    block_reasons: tuple[str, ...]
    statistics_reason_en: str
    statistics_reason_th: str
    expected_next_action_en: str
    expected_next_action_th: str
    broker: str = "XM"
    symbol: str = "GOLD#"
    lot_per_unit: float = 0.01
    execution_status: str = "LOCKED_SIMULATION_ONLY"
    direct_execution: bool = False
    live_execution_enabled: bool = False
    order_status: str = "NO_ORDER_SENT"
    broker_request_created: bool = False
    order_transmission_attempted: bool = False
    trading_logic_changed: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["statistics"] = [item.as_dict() for item in self.statistics]
        return payload


class PatternStatisticsRuntime:
    """Calculates auditable pattern and cluster outcome statistics without execution authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternStatisticsReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.5.0-RESEARCH")).strip() or "M1.5.0-RESEARCH"
        patterns = self._records(record.get("patterns", ()))
        clusters = self._records(record.get("clusters", ()))
        outcomes = self._records(record.get("outcomes", ()))
        minimum_sample_size = max(1, int(self._number(record.get("minimum_sample_size", 20)) or 20))

        pattern_ids = [str(item.get("pattern_id", "")).strip() for item in patterns]
        pattern_regimes = {str(item.get("pattern_id", "")).strip(): str(item.get("market_regime", "UNKNOWN")).strip().upper() for item in patterns}
        pattern_lineages = {str(item.get("pattern_id", "")).strip(): str(item.get("source_lineage", "")).strip() for item in patterns}
        cluster_members: dict[str, tuple[str, ...]] = {}
        cluster_regimes: dict[str, str] = {}
        cluster_lineages: dict[str, tuple[str, ...]] = {}
        for cluster in clusters:
            cluster_id = str(cluster.get("cluster_id", "")).strip()
            members = tuple(sorted(str(value).strip() for value in cluster.get("member_pattern_ids", ()) if str(value).strip()))
            cluster_members[cluster_id] = members
            cluster_regimes[cluster_id] = str(cluster.get("market_regime", "UNKNOWN")).strip().upper()
            raw_lineages = cluster.get("source_lineages", ())
            cluster_lineages[cluster_id] = tuple(sorted(str(value).strip() for value in raw_lineages if str(value).strip()))

        pattern_lineage_valid = bool(patterns) and len(pattern_ids) == len(set(pattern_ids)) and all(pattern_ids) and all(pattern_lineages.values())
        cluster_lineage_valid = bool(clusters) and all(cluster_members) and all(
            members and all(member in pattern_regimes for member in members) and cluster_lineages.get(cluster_id)
            for cluster_id, members in cluster_members.items()
        )
        timestamps = [str(item.get("closed_at", "")).strip() for item in outcomes]
        chronology_valid = all(timestamps) and timestamps == sorted(timestamps) and len(timestamps) == len(set(timestamps))

        normalized_outcomes: list[dict[str, Any]] = []
        outcome_values_valid = True
        for item in outcomes:
            pattern_id = str(item.get("pattern_id", "")).strip()
            accepted = bool(item.get("accepted", True))
            r_multiple = self._number(item.get("r_multiple"))
            lineage = str(item.get("source_lineage", "")).strip()
            if pattern_id not in pattern_regimes or r_multiple is None or not lineage:
                outcome_values_valid = False
                continue
            normalized_outcomes.append({
                "pattern_id": pattern_id,
                "accepted": accepted,
                "r_multiple": float(r_multiple),
                "source_lineage": lineage,
                "closed_at": str(item.get("closed_at", "")).strip(),
            })

        blocked = []
        if not bool(record.get("pattern_clustering_ready", False)):
            blocked.append("pattern_clustering_not_ready")
        if not bool(record.get("research_knowledge_approved", False)):
            blocked.append("research_knowledge_not_approved")
        if not pattern_lineage_valid:
            blocked.append("pattern_lineage_invalid")
        if not cluster_lineage_valid:
            blocked.append("cluster_lineage_invalid")
        if not chronology_valid:
            blocked.append("outcome_chronology_invalid")
        if not outcome_values_valid or not normalized_outcomes:
            blocked.append("outcome_values_invalid")
        if bool(record.get("future_leakage_detected", False)):
            blocked.append("future_leakage_detected")
        if not bool(record.get("data_quality_certified", False)):
            blocked.append("data_quality_not_certified")
        if broker != "XM":
            blocked.append("broker_policy_violation")
        if symbol != "GOLD#":
            blocked.append("symbol_policy_violation")
        if abs(lot - 0.01) > 1e-12:
            blocked.append("base_unit_policy_violation")
        if execution_status != "LOCKED_SIMULATION_ONLY":
            blocked.append("execution_lock_invalid")
        if order_status != "NO_ORDER_SENT":
            blocked.append("order_status_invalid")
        if bool(record.get("direct_execution", False)) or bool(record.get("live_execution_enabled", False)):
            blocked.append("execution_enablement_forbidden")
        if bool(record.get("broker_request_created", False)) or bool(record.get("order_transmission_attempted", False)):
            blocked.append("order_transmission_forbidden")

        statistics: tuple[PatternStatistic, ...] = ()
        if not blocked:
            built: list[PatternStatistic] = []
            by_pattern = {pattern_id: [item for item in normalized_outcomes if item["pattern_id"] == pattern_id] for pattern_id in sorted(pattern_ids)}
            for pattern_id, items in by_pattern.items():
                if items:
                    built.append(self._build_statistic(
                        pattern_id, "PATTERN", pattern_regimes[pattern_id], items,
                        (pattern_lineages[pattern_id],), minimum_sample_size,
                    ))
            for cluster_id in sorted(cluster_members):
                members = set(cluster_members[cluster_id])
                items = [item for item in normalized_outcomes if item["pattern_id"] in members]
                if items:
                    built.append(self._build_statistic(
                        cluster_id, "CLUSTER", cluster_regimes[cluster_id], items,
                        cluster_lineages[cluster_id], minimum_sample_size,
                    ))
            statistics = tuple(sorted(built, key=lambda item: (item.scope_type, item.market_regime, item.scope_id)))

        identity_payload = {
            "knowledge_version": knowledge_version,
            "minimum_sample_size": minimum_sample_size,
            "statistics": [item.as_dict() for item in statistics],
        }
        statistics_id = "PSTAT-" + sha256(json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocked
        sufficient = sum(item.sample_count >= minimum_sample_size for item in statistics)
        return PatternStatisticsReport(
            status="READY" if ready else "BLOCKED",
            reason="Pattern statistics are deterministic and research-ready." if ready else "Pattern statistics blocked by validation controls.",
            milestone="M", pack="5", statistics_id=statistics_id, knowledge_version=knowledge_version,
            source_pattern_count=len(patterns), source_cluster_count=len(clusters),
            eligible_outcome_count=len(normalized_outcomes), statistic_count=len(statistics),
            sufficient_sample_count=sufficient, minimum_sample_size=minimum_sample_size,
            chronology_valid=chronology_valid, pattern_lineage_valid=pattern_lineage_valid,
            cluster_lineage_valid=cluster_lineage_valid, outcome_values_valid=outcome_values_valid,
            deterministic_statistics_valid=ready, future_safe=not bool(record.get("future_leakage_detected", False)),
            research_only=True, pattern_statistics_enabled=ready, pattern_validation_enabled=False,
            production_knowledge_approved=False,
            research_knowledge_approved=ready and bool(record.get("research_knowledge_approved", False)),
            statistics=statistics, block_reasons=tuple(sorted(set(blocked))),
            statistics_reason_en="Calculates auditable pattern and cluster outcome statistics without changing trading decisions." if ready else "Statistics remain blocked until all data, lineage, chronology, and safety gates pass.",
            statistics_reason_th="คำนวณสถิติผลลัพธ์ของ Pattern และ Cluster ที่ตรวจสอบย้อนหลังได้ โดยไม่เปลี่ยนการตัดสินใจซื้อขาย" if ready else "สถิติยังถูกบล็อกจนกว่าข้อมูล Lineage ลำดับเวลา และ Safety Gate จะผ่านครบ",
            expected_next_action_en="Continue to Milestone M Pack 6 — Pattern Validation." if ready else "Correct blocked validation inputs and evaluate again.",
            expected_next_action_th="ดำเนินการต่อ Milestone M Pack 6 — Pattern Validation" if ready else "แก้ข้อมูลที่ไม่ผ่านการตรวจสอบแล้วประเมินใหม่",
            broker="XM", symbol="GOLD#", lot_per_unit=0.01,
            execution_status="LOCKED_SIMULATION_ONLY", direct_execution=False,
            live_execution_enabled=False, order_status="NO_ORDER_SENT",
            broker_request_created=False, order_transmission_attempted=False,
            trading_logic_changed=False,
        )

    def _build_statistic(self, scope_id: str, scope_type: str, regime: str, items: Sequence[Mapping[str, Any]], lineages: Sequence[str], minimum_sample_size: int) -> PatternStatistic:
        values = [float(item["r_multiple"]) for item in items]
        accepted = sum(bool(item["accepted"]) for item in items)
        wins = sum(value > 0 for value in values)
        losses = sum(value < 0 for value in values)
        breakeven = len(values) - wins - losses
        gross_profit = sum(value for value in values if value > 0)
        gross_loss = abs(sum(value for value in values if value < 0))
        average = sum(values) / len(values)
        variance = sum((value - average) ** 2 for value in values) / len(values)
        if gross_loss == 0:
            profit_factor = 999.0 if gross_profit > 0 else 0.0
        else:
            profit_factor = gross_profit / gross_loss
        if len(values) >= minimum_sample_size * 2:
            tier = "HIGH"
        elif len(values) >= minimum_sample_size:
            tier = "MEDIUM"
        else:
            tier = "LOW_SAMPLE"
        return PatternStatistic(
            scope_id=scope_id, scope_type=scope_type, market_regime=regime,
            sample_count=len(values), accepted_count=accepted, rejected_count=len(values) - accepted,
            win_count=wins, loss_count=losses, breakeven_count=breakeven,
            win_rate=round(wins / len(values), 6), average_r_multiple=round(average, 6),
            expectancy_r=round(average, 6), gross_profit_r=round(gross_profit, 6),
            gross_loss_r=round(gross_loss, 6), profit_factor=round(profit_factor, 6),
            r_standard_deviation=round(sqrt(variance), 6), confidence_tier=tier,
            source_lineages=tuple(sorted(set(str(value).strip() for value in lineages if str(value).strip()))),
        )

    @staticmethod
    def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
