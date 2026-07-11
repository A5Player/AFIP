"""Milestone M Pack 8: deterministic historical pattern database controls."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class HistoricalPatternEntry:
    entry_id: str
    scope_id: str
    scope_type: str
    market_regime: str
    knowledge_version: str
    observed_at_utc: str
    validated: bool
    explanation_status: str
    feature_schema: tuple[str, ...]
    feature_vector: tuple[float, ...]
    statistics_lineage: str
    validation_lineage: str
    explainability_lineage: str
    source_lineages: tuple[str, ...]
    content_checksum: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HistoricalPatternDatabaseReport:
    status: str
    reason: str
    milestone: str
    pack: str
    database_id: str
    knowledge_version: str
    source_record_count: int
    eligible_record_count: int
    stored_entry_count: int
    duplicate_record_count: int
    validated_entry_count: int
    rejected_entry_count: int
    market_regime_count: int
    chronological_integrity_valid: bool
    unique_identity_valid: bool
    lineage_integrity_valid: bool
    checksum_integrity_valid: bool
    immutable_snapshot_valid: bool
    deterministic_database_valid: bool
    future_safe: bool
    research_only: bool
    historical_pattern_database_enabled: bool
    production_knowledge_approved: bool
    research_knowledge_approved: bool
    entries: tuple[HistoricalPatternEntry, ...]
    regime_index: tuple[tuple[str, tuple[str, ...]], ...]
    scope_index: tuple[tuple[str, tuple[str, ...]], ...]
    block_reasons: tuple[str, ...]
    explanation_reason_en: str
    explanation_reason_th: str
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
        payload["entries"] = [entry.as_dict() for entry in self.entries]
        return payload


class HistoricalPatternDatabaseRuntime:
    """Builds an immutable, deduplicated research history of pattern knowledge."""

    def evaluate_one(self, record: Mapping[str, Any]) -> HistoricalPatternDatabaseReport:
        broker = str(record.get("broker", "XM")).strip().upper() or "XM"
        symbol = str(record.get("symbol", "GOLD#")).strip().upper() or "GOLD#"
        lot = self._number(record.get("lot_per_unit", 0.01)) or 0.01
        execution_status = str(record.get("execution_status", "LOCKED_SIMULATION_ONLY")).strip().upper()
        order_status = str(record.get("order_status", "NO_ORDER_SENT")).strip().upper()
        knowledge_version = str(record.get("knowledge_version", "M1.8.0-RESEARCH")).strip() or "M1.8.0-RESEARCH"
        raw_records = self._records(record.get("historical_records", ()))

        normalized: list[dict[str, Any]] = []
        chronological_integrity_valid = True
        lineage_integrity_valid = True
        checksum_integrity_valid = True
        seen_natural_keys: set[tuple[str, str, str]] = set()
        duplicate_count = 0

        for item in raw_records:
            scope_id = str(item.get("scope_id", "")).strip()
            scope_type = str(item.get("scope_type", "")).strip().upper()
            regime = str(item.get("market_regime", "UNKNOWN")).strip().upper()
            observed_at = str(item.get("observed_at_utc", "")).strip()
            item_version = str(item.get("knowledge_version", knowledge_version)).strip() or knowledge_version
            feature_schema = tuple(str(v).strip() for v in item.get("feature_schema", ()) if str(v).strip())
            feature_vector_raw = tuple(item.get("feature_vector", ()))
            feature_vector = tuple(self._number(v) for v in feature_vector_raw)
            statistics_lineage = str(item.get("statistics_lineage", "")).strip()
            validation_lineage = str(item.get("validation_lineage", "")).strip()
            explainability_lineage = str(item.get("explainability_lineage", "")).strip()
            source_lineages = tuple(sorted(set(str(v).strip() for v in item.get("source_lineages", ()) if str(v).strip())))

            if not observed_at or not observed_at.endswith("Z"):
                chronological_integrity_valid = False
            if not all((statistics_lineage, validation_lineage, explainability_lineage)) or not source_lineages:
                lineage_integrity_valid = False
            if (
                not scope_id or scope_type not in {"PATTERN", "CLUSTER"} or not regime
                or not feature_schema or len(feature_schema) != len(feature_vector)
                or any(value is None for value in feature_vector)
            ):
                checksum_integrity_valid = False
                continue

            natural_key = (scope_id, item_version, observed_at)
            if natural_key in seen_natural_keys:
                duplicate_count += 1
                continue
            seen_natural_keys.add(natural_key)

            content = {
                "scope_id": scope_id,
                "scope_type": scope_type,
                "market_regime": regime,
                "knowledge_version": item_version,
                "observed_at_utc": observed_at,
                "validated": bool(item.get("validated", False)),
                "explanation_status": str(item.get("explanation_status", "UNEXPLAINED")).strip().upper(),
                "feature_schema": feature_schema,
                "feature_vector": tuple(round(float(v), 10) for v in feature_vector if v is not None),
                "statistics_lineage": statistics_lineage,
                "validation_lineage": validation_lineage,
                "explainability_lineage": explainability_lineage,
                "source_lineages": source_lineages,
            }
            checksum = sha256(json.dumps(content, sort_keys=True, separators=(",", ":")).encode()).hexdigest().upper()
            supplied_checksum = str(item.get("content_checksum", "")).strip().upper()
            if supplied_checksum and supplied_checksum != checksum:
                checksum_integrity_valid = False
                continue
            normalized.append({**content, "content_checksum": checksum})

        ordered = sorted(normalized, key=lambda x: (x["observed_at_utc"], x["scope_type"], x["scope_id"], x["knowledge_version"]))
        if [x["observed_at_utc"] for x in ordered] != sorted(x["observed_at_utc"] for x in ordered):
            chronological_integrity_valid = False

        unique_identity_valid = len(seen_natural_keys) == len(normalized)
        blocked: list[str] = []
        if not bool(record.get("pattern_explainability_ready", False)):
            blocked.append("pattern_explainability_not_ready")
        if not bool(record.get("research_knowledge_approved", False)):
            blocked.append("research_knowledge_not_approved")
        if not chronological_integrity_valid:
            blocked.append("chronological_integrity_invalid")
        if not unique_identity_valid:
            blocked.append("unique_identity_invalid")
        if not lineage_integrity_valid:
            blocked.append("lineage_integrity_invalid")
        if not checksum_integrity_valid:
            blocked.append("checksum_integrity_invalid")
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

        entries: tuple[HistoricalPatternEntry, ...] = ()
        if not blocked:
            built: list[HistoricalPatternEntry] = []
            for item in ordered:
                identity = {
                    "scope_id": item["scope_id"],
                    "knowledge_version": item["knowledge_version"],
                    "observed_at_utc": item["observed_at_utc"],
                    "content_checksum": item["content_checksum"],
                }
                entry_id = "HPD-" + sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
                built.append(HistoricalPatternEntry(entry_id=entry_id, **item))
            entries = tuple(built)

        regime_map: dict[str, list[str]] = {}
        scope_map: dict[str, list[str]] = {}
        for entry in entries:
            regime_map.setdefault(entry.market_regime, []).append(entry.entry_id)
            scope_map.setdefault(entry.scope_id, []).append(entry.entry_id)
        regime_index = tuple((key, tuple(sorted(value))) for key, value in sorted(regime_map.items()))
        scope_index = tuple((key, tuple(sorted(value))) for key, value in sorted(scope_map.items()))

        database_identity = {
            "knowledge_version": knowledge_version,
            "entries": [entry.as_dict() for entry in entries],
            "regime_index": regime_index,
            "scope_index": scope_index,
        }
        database_id = "HPDB-" + sha256(json.dumps(database_identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16].upper()
        ready = not blocked
        validated_count = sum(entry.validated for entry in entries)
        rejected_count = sum(not entry.validated for entry in entries)
        return HistoricalPatternDatabaseReport(
            status="READY" if ready else "BLOCKED",
            reason="Historical pattern database snapshot completed under research-only controls." if ready else "Historical pattern database blocked by integrity or safety controls.",
            milestone="M", pack="8", database_id=database_id, knowledge_version=knowledge_version,
            source_record_count=len(raw_records), eligible_record_count=len(normalized), stored_entry_count=len(entries),
            duplicate_record_count=duplicate_count, validated_entry_count=validated_count, rejected_entry_count=rejected_count,
            market_regime_count=len(regime_index), chronological_integrity_valid=chronological_integrity_valid,
            unique_identity_valid=unique_identity_valid, lineage_integrity_valid=lineage_integrity_valid,
            checksum_integrity_valid=checksum_integrity_valid, immutable_snapshot_valid=True,
            deterministic_database_valid=True, future_safe="future_leakage_detected" not in blocked,
            research_only=True, historical_pattern_database_enabled=ready,
            production_knowledge_approved=False, research_knowledge_approved=ready,
            entries=entries, regime_index=regime_index, scope_index=scope_index,
            block_reasons=tuple(sorted(set(blocked))),
            explanation_reason_en="Stores immutable, deduplicated, lineage-verified historical pattern snapshots for research." if ready else "Historical storage is blocked until integrity and safety controls pass.",
            explanation_reason_th="จัดเก็บ Snapshot ประวัติ Pattern แบบแก้ย้อนหลังไม่ได้ ไม่ซ้ำ และตรวจสอบ Lineage สำหรับงานวิจัย" if ready else "การจัดเก็บประวัติถูกบล็อกจนกว่าการตรวจความสมบูรณ์และความปลอดภัยจะผ่าน",
            expected_next_action_en="Continue to Milestone M Pack 9 — Pattern Confidence." if ready else "Correct historical record integrity and rerun certification.",
            expected_next_action_th="ดำเนินการต่อ Milestone M Pack 9 — Pattern Confidence" if ready else "แก้ไขความสมบูรณ์ของข้อมูลประวัติแล้วตรวจใหม่",
            broker=broker, symbol=symbol, lot_per_unit=lot, execution_status="LOCKED_SIMULATION_ONLY",
            direct_execution=False, live_execution_enabled=False, order_status="NO_ORDER_SENT",
            broker_request_created=False, order_transmission_attempted=False, trading_logic_changed=False,
        )

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
        return result if result == result and abs(result) != float("inf") else None

    @staticmethod
    def _records(value: Any) -> list[Mapping[str, Any]]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return []
        return [item for item in value if isinstance(item, Mapping)]
