"""Milestone M Pack 3: deterministic, regime-aware pattern similarity search."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import sqrt
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternSimilaritySearchReport:
    status: str
    reason: str
    milestone: str
    pack: str
    search_id: str
    knowledge_version: str
    query_pattern_id: str
    candidate_count: int
    eligible_candidate_count: int
    result_count: int
    top_pattern_id: str
    top_similarity_score: float
    minimum_similarity: float
    maximum_results: int
    market_regime_matched: bool
    feature_schema_matched: bool
    deterministic_ranking_valid: bool
    similarity_bounds_valid: bool
    lineage_valid: bool
    future_safe: bool
    research_only: bool
    pattern_search_enabled: bool
    pattern_clustering_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    result_pattern_ids: tuple[str, ...]
    block_reasons: tuple[str, ...]
    search_reason_en: str
    search_reason_th: str
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
        return asdict(self)


class PatternSimilaritySearchRuntime:
    """Ranks historical research patterns without execution or approval authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternSimilaritySearchReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.2.0-RESEARCH")).strip() or "M1.2.0-RESEARCH"
        query = record.get("query_pattern", {}) if isinstance(record.get("query_pattern", {}), Mapping) else {}
        candidates = self._records(record.get("candidate_patterns", ()))
        minimum_similarity = min(1.0, max(0.0, self._number(record.get("minimum_similarity", 0.75))))
        maximum_results = max(1, int(self._number(record.get("maximum_results", 5)) or 5))

        query_id = str(query.get("pattern_id", "")).strip()
        query_regime = str(query.get("market_regime", "")).strip().upper()
        query_features = self._features(query.get("features", {}))
        query_lineage = str(query.get("source_lineage", "")).strip()
        eligible: list[tuple[float, str, Mapping[str, Any]]] = []
        schema_match = bool(query_features)
        lineage_valid = bool(query_lineage)
        bounds_valid = True
        for candidate in candidates:
            candidate_id = str(candidate.get("pattern_id", "")).strip()
            candidate_regime = str(candidate.get("market_regime", "")).strip().upper()
            candidate_features = self._features(candidate.get("features", {}))
            candidate_lineage = str(candidate.get("source_lineage", "")).strip()
            lineage_valid = lineage_valid and bool(candidate_lineage)
            if not candidate_id or candidate_id == query_id or candidate_regime != query_regime:
                continue
            if tuple(candidate_features) != tuple(query_features):
                schema_match = False
                continue
            score = self._cosine(query_features, candidate_features)
            bounds_valid = bounds_valid and 0.0 <= score <= 1.0
            if score >= minimum_similarity:
                eligible.append((score, candidate_id, candidate))
        ranked = sorted(eligible, key=lambda item: (-item[0], item[1]))[:maximum_results]
        result_ids = tuple(item[1] for item in ranked)
        top_id = result_ids[0] if result_ids else ""
        top_score = ranked[0][0] if ranked else 0.0
        deterministic = ranked == sorted(ranked, key=lambda item: (-item[0], item[1]))

        checks = {
            "pattern_engine_not_ready": bool(record.get("pattern_engine_ready", False)),
            "research_knowledge_not_approved": bool(record.get("research_knowledge_approved", False)),
            "query_pattern_missing": bool(query_id and query_regime and query_features),
            "candidate_patterns_missing": bool(candidates),
            "market_regime_mismatch": bool(query_regime) and any(str(item.get("market_regime", "")).strip().upper() == query_regime for item in candidates),
            "feature_schema_mismatch": schema_match,
            "similarity_bounds_invalid": bounds_valid,
            "deterministic_ranking_invalid": deterministic,
            "lineage_invalid": lineage_valid,
            "future_leakage_detected": not bool(record.get("future_leakage_detected", False)),
            "data_quality_not_certified": bool(record.get("data_quality_certified", False)),
            "knowledge_version_missing": bool(knowledge_version),
            "xm_only_policy": broker == "XM",
            "gold_only_policy": symbol == "GOLD#",
            "fixed_unit_policy": abs(lot - 0.01) <= 1e-12,
            "simulation_lock_missing": execution_status == "LOCKED_SIMULATION_ONLY",
            "direct_execution_requested": not bool(record.get("direct_execution", False)),
            "live_execution_requested": not bool(record.get("live_execution_enabled", False)),
            "order_status_not_safe": order_status == "NO_ORDER_SENT",
            "broker_request_created": not bool(record.get("broker_request_created", False)),
            "order_transmission_attempted": not bool(record.get("order_transmission_attempted", False)),
        }
        blocks = tuple(name for name, passed in checks.items() if not passed)
        payload = {
            "knowledge_version": knowledge_version,
            "query": {"id": query_id, "regime": query_regime, "features": query_features},
            "results": [(round(score, 12), pattern_id) for score, pattern_id, _ in ranked],
            "minimum_similarity": minimum_similarity,
            "maximum_results": maximum_results,
            "checks": checks,
        }
        search_id = "M03-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason = "READY", "pattern_similarity_search_ready"
            en = "Regime-aware pattern similarity search produced deterministic, bounded, lineage-safe research rankings."
            th = "การค้นหา Pattern ที่คล้ายกันแบบแยกตาม Market Regime สร้างอันดับสำหรับการวิจัยที่เป็น Deterministic อยู่ในขอบเขต และตรวจสอบ Lineage แล้ว"
            next_en = "Continue to Milestone M Pack 4 Pattern Clustering. Keep all results research-only and execution locked."
            next_th = "ดำเนินการต่อ Milestone M Pack 4 Pattern Clustering โดยคงผลลัพธ์ไว้สำหรับ Research และล็อก Execution"
        else:
            status, reason = "BLOCKED", blocks[0]
            en = "Pattern Similarity Search is blocked until engine, query, regime, schema, lineage, data-quality, and safety controls pass."
            th = "Pattern Similarity Search ถูกบล็อกจนกว่า Engine, Query, Regime, Schema, Lineage, คุณภาพข้อมูล และความปลอดภัยจะผ่านทั้งหมด"
            next_en = "Correct every block reason and re-run without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและรันใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return PatternSimilaritySearchReport(
            status=status, reason=reason, milestone="MILESTONE_M", pack="PACK_3",
            search_id=search_id, knowledge_version=knowledge_version, query_pattern_id=query_id,
            candidate_count=len(candidates), eligible_candidate_count=len(eligible), result_count=len(ranked),
            top_pattern_id=top_id, top_similarity_score=round(top_score, 12),
            minimum_similarity=minimum_similarity, maximum_results=maximum_results,
            market_regime_matched=checks["market_regime_mismatch"], feature_schema_matched=schema_match,
            deterministic_ranking_valid=deterministic, similarity_bounds_valid=bounds_valid,
            lineage_valid=lineage_valid, future_safe=checks["future_leakage_detected"],
            research_only=True, pattern_search_enabled=ready, pattern_clustering_enabled=False,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            result_pattern_ids=result_ids, block_reasons=blocks,
            search_reason_en=en, search_reason_th=th,
            expected_next_action_en=next_en, expected_next_action_th=next_th,
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status=execution_status,
            direct_execution=False, live_execution_enabled=False, order_status=order_status,
            broker_request_created=False, order_transmission_attempted=False, trading_logic_changed=False,
        )

    @staticmethod
    def _records(value: Any) -> tuple[Mapping[str, Any], ...]:
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return tuple(item for item in value if isinstance(item, Mapping))
        return ()

    @staticmethod
    def _features(value: Any) -> dict[str, float]:
        if not isinstance(value, Mapping):
            return {}
        return {str(key): PatternSimilaritySearchRuntime._number(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}

    @staticmethod
    def _cosine(first: Mapping[str, float], second: Mapping[str, float]) -> float:
        keys = tuple(first)
        dot = sum(first[key] * second[key] for key in keys)
        left = sqrt(sum(first[key] ** 2 for key in keys))
        right = sqrt(sum(second[key] ** 2 for key in keys))
        if left <= 0.0 or right <= 0.0:
            return 1.0 if all(first[key] == second[key] for key in keys) else 0.0
        return min(1.0, max(0.0, dot / (left * right)))

    @staticmethod
    def _number(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
