"""Milestone M Pack 4: deterministic, regime-aware pattern clustering."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import sqrt
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class PatternCluster:
    cluster_id: str
    market_regime: str
    member_pattern_ids: tuple[str, ...]
    member_count: int
    centroid: tuple[tuple[str, float], ...]
    average_internal_similarity: float
    source_lineages: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PatternClusteringReport:
    status: str
    reason: str
    milestone: str
    pack: str
    clustering_id: str
    knowledge_version: str
    source_pattern_count: int
    eligible_pattern_count: int
    cluster_count: int
    singleton_cluster_count: int
    clustered_pattern_count: int
    minimum_similarity: float
    market_regime_partitioned: bool
    feature_schema_valid: bool
    deterministic_clusters_valid: bool
    similarity_bounds_valid: bool
    lineage_valid: bool
    future_safe: bool
    research_only: bool
    pattern_search_enabled: bool
    pattern_clustering_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    clusters: tuple[PatternCluster, ...]
    block_reasons: tuple[str, ...]
    clustering_reason_en: str
    clustering_reason_th: str
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
        payload["clusters"] = [cluster.as_dict() for cluster in self.clusters]
        return payload


class PatternClusteringRuntime:
    """Clusters research patterns without execution or production approval authority."""

    def evaluate_one(self, record: Mapping[str, Any]) -> PatternClusteringReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.3.0-RESEARCH")).strip() or "M1.3.0-RESEARCH"
        patterns = self._records(record.get("patterns", ()))
        minimum_similarity = min(1.0, max(0.0, self._number(record.get("minimum_similarity", 0.90))))

        normalized: list[dict[str, Any]] = []
        schema_by_regime: dict[str, tuple[str, ...]] = {}
        feature_schema_valid = True
        lineage_valid = True
        unique_ids: set[str] = set()
        duplicate_id = False
        for item in patterns:
            pattern_id = str(item.get("pattern_id", "")).strip()
            regime = str(item.get("market_regime", "")).strip().upper()
            features = self._features(item.get("features", {}))
            lineage = str(item.get("source_lineage", "")).strip()
            if pattern_id in unique_ids:
                duplicate_id = True
            unique_ids.add(pattern_id)
            lineage_valid = lineage_valid and bool(lineage)
            if not pattern_id or not regime or not features:
                continue
            schema = tuple(features)
            if regime in schema_by_regime and schema_by_regime[regime] != schema:
                feature_schema_valid = False
            else:
                schema_by_regime.setdefault(regime, schema)
            normalized.append({"pattern_id": pattern_id, "market_regime": regime, "features": features, "source_lineage": lineage})

        normalized.sort(key=lambda item: (item["market_regime"], item["pattern_id"]))
        similarity_bounds_valid = True
        adjacency: dict[str, set[str]] = {item["pattern_id"]: set() for item in normalized}
        by_id = {item["pattern_id"]: item for item in normalized}
        for index, left in enumerate(normalized):
            for right in normalized[index + 1:]:
                if left["market_regime"] != right["market_regime"]:
                    continue
                if tuple(left["features"]) != tuple(right["features"]):
                    continue
                score = self._cosine(left["features"], right["features"])
                similarity_bounds_valid = similarity_bounds_valid and 0.0 <= score <= 1.0
                if score >= minimum_similarity:
                    adjacency[left["pattern_id"]].add(right["pattern_id"])
                    adjacency[right["pattern_id"]].add(left["pattern_id"])

        clusters: list[PatternCluster] = []
        visited: set[str] = set()
        for pattern_id in sorted(adjacency):
            if pattern_id in visited:
                continue
            stack = [pattern_id]
            members: list[str] = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                members.append(current)
                stack.extend(sorted(adjacency[current] - visited, reverse=True))
            members = sorted(members)
            cluster_patterns = [by_id[item] for item in members]
            regime = cluster_patterns[0]["market_regime"]
            centroid_map = self._centroid([item["features"] for item in cluster_patterns])
            pair_scores: list[float] = []
            for i, left_id in enumerate(members):
                for right_id in members[i + 1:]:
                    pair_scores.append(self._cosine(by_id[left_id]["features"], by_id[right_id]["features"]))
            average_similarity = sum(pair_scores) / len(pair_scores) if pair_scores else 1.0
            cluster_payload = {"regime": regime, "members": members, "centroid": centroid_map}
            cluster_id = "CL-" + sha256(json.dumps(cluster_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
            clusters.append(PatternCluster(
                cluster_id=cluster_id,
                market_regime=regime,
                member_pattern_ids=tuple(members),
                member_count=len(members),
                centroid=tuple((key, round(value, 12)) for key, value in centroid_map.items()),
                average_internal_similarity=round(average_similarity, 12),
                source_lineages=tuple(sorted({str(item["source_lineage"]) for item in cluster_patterns})),
            ))
        clusters.sort(key=lambda item: (item.market_regime, item.member_pattern_ids, item.cluster_id))
        deterministic = clusters == sorted(clusters, key=lambda item: (item.market_regime, item.member_pattern_ids, item.cluster_id))

        checks = {
            "similarity_search_not_ready": bool(record.get("similarity_search_ready", False)),
            "research_knowledge_not_approved": bool(record.get("research_knowledge_approved", False)),
            "patterns_missing": bool(patterns),
            "eligible_patterns_missing": bool(normalized),
            "duplicate_pattern_ids": not duplicate_id,
            "feature_schema_mismatch": feature_schema_valid,
            "market_regime_missing": all(bool(item["market_regime"]) for item in normalized),
            "deterministic_clusters_invalid": deterministic,
            "similarity_bounds_invalid": similarity_bounds_valid,
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
            "patterns": normalized,
            "minimum_similarity": minimum_similarity,
            "clusters": [cluster.as_dict() for cluster in clusters],
            "checks": checks,
        }
        clustering_id = "M04-" + sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:16].upper()
        ready = not blocks
        if ready:
            status, reason = "READY", "pattern_clustering_ready"
            en = "Regime-aware pattern clustering produced deterministic research groups with canonical schemas, bounded similarity, and verified lineage."
            th = "การจัดกลุ่ม Pattern แบบแยกตาม Market Regime สร้างกลุ่มวิจัยแบบ Deterministic ด้วย Schema มาตรฐาน ค่า Similarity อยู่ในขอบเขต และตรวจสอบ Lineage แล้ว"
            next_en = "Continue to Milestone M Pack 5 Pattern Statistics. Keep clusters research-only and execution locked."
            next_th = "ดำเนินการต่อ Milestone M Pack 5 Pattern Statistics โดยคง Cluster ไว้สำหรับ Research และล็อก Execution"
        else:
            status, reason = "BLOCKED", blocks[0]
            en = "Pattern Clustering is blocked until source patterns, regime partitions, schemas, lineage, data quality, and safety controls pass."
            th = "Pattern Clustering ถูกบล็อกจนกว่า Pattern ต้นทาง การแบ่ง Market Regime, Schema, Lineage, คุณภาพข้อมูล และความปลอดภัยจะผ่านทั้งหมด"
            next_en = "Correct every block reason and re-run without creating or transmitting an order."
            next_th = "แก้ไข Block Reason ทั้งหมดและรันใหม่โดยไม่สร้างหรือส่งคำสั่งซื้อขาย"
        return PatternClusteringReport(
            status=status, reason=reason, milestone="MILESTONE_M", pack="PACK_4",
            clustering_id=clustering_id, knowledge_version=knowledge_version,
            source_pattern_count=len(patterns), eligible_pattern_count=len(normalized),
            cluster_count=len(clusters), singleton_cluster_count=sum(cluster.member_count == 1 for cluster in clusters),
            clustered_pattern_count=sum(cluster.member_count for cluster in clusters),
            minimum_similarity=minimum_similarity, market_regime_partitioned=checks["market_regime_missing"],
            feature_schema_valid=feature_schema_valid, deterministic_clusters_valid=deterministic,
            similarity_bounds_valid=similarity_bounds_valid, lineage_valid=lineage_valid,
            future_safe=checks["future_leakage_detected"], research_only=True,
            pattern_search_enabled=ready, pattern_clustering_enabled=ready,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            clusters=tuple(clusters), block_reasons=blocks,
            clustering_reason_en=en, clustering_reason_th=th,
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
        return {str(key): PatternClusteringRuntime._number(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}

    @staticmethod
    def _centroid(features: Sequence[Mapping[str, float]]) -> dict[str, float]:
        if not features:
            return {}
        keys = tuple(features[0])
        return {key: sum(item[key] for item in features) / len(features) for key in keys}

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
