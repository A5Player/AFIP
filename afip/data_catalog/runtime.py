from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import json


@dataclass(frozen=True)
class DatasetRecord:
    dataset_id: str
    name: str
    category: str
    schema_version: str
    storage_path: str
    owner: str
    producer: str
    classification: str
    lifecycle_status: str
    retention_policy: str
    lineage_parents: tuple[str, ...]
    guides: tuple[str, ...]
    tags: tuple[str, ...]
    execution_authority: str = "NONE"

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["lineage_parents"] = list(self.lineage_parents)
        payload["guides"] = list(self.guides)
        payload["tags"] = list(self.tags)
        return payload


@dataclass(frozen=True)
class CatalogValidation:
    status: str
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


class CentralDataCatalog:
    """Deterministic registry for AFIP datasets. Research/governance only."""

    ALLOWED_LIFECYCLE = {"ACTIVE", "DEPRECATED", "ARCHIVED", "QUARANTINED"}
    REQUIRED_METADATA_FIELDS = {
        "dataset_id",
        "schema_version",
        "producer",
        "data_classification",
    }

    def __init__(self, policy: Mapping[str, object] | None = None) -> None:
        self.policy = dict(policy or {})
        self._records: dict[str, DatasetRecord] = {}
        self._validate_policy()

    def _validate_policy(self) -> None:
        if self.policy.get("execution_authority", "NONE") != "NONE":
            raise ValueError("execution_authority_must_be_none")
        if self.policy.get("automatic_strategy_change", "PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_strategy_change_must_be_prohibited")
        if self.policy.get("registry_mutation_mode", "EXPLICIT_ONLY") != "EXPLICIT_ONLY":
            raise ValueError("registry_mutation_mode_must_be_explicit_only")

    @classmethod
    def from_policy_file(cls, path: str | Path) -> "CentralDataCatalog":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def register(self, record: DatasetRecord, replace: bool = False) -> None:
        validation = self.validate_record(record)
        if validation.status == "INVALID":
            raise ValueError(";".join(validation.errors))
        if record.dataset_id in self._records and not replace:
            raise ValueError("dataset_already_registered")
        self._records[record.dataset_id] = record

    def get(self, dataset_id: str) -> DatasetRecord | None:
        return self._records.get(dataset_id)

    def list_records(
        self,
        category: str | None = None,
        lifecycle_status: str | None = None,
        tag: str | None = None,
    ) -> tuple[DatasetRecord, ...]:
        records = list(self._records.values())
        if category is not None:
            records = [item for item in records if item.category == category]
        if lifecycle_status is not None:
            records = [item for item in records if item.lifecycle_status == lifecycle_status]
        if tag is not None:
            records = [item for item in records if tag in item.tags]
        return tuple(sorted(records, key=lambda item: item.dataset_id))

    def validate_record(self, record: DatasetRecord) -> CatalogValidation:
        errors: list[str] = []
        warnings: list[str] = []
        if not record.dataset_id.strip():
            errors.append("dataset_id_missing")
        if not record.storage_path.startswith("data/"):
            errors.append("storage_path_must_be_under_data")
        if record.lifecycle_status not in self.ALLOWED_LIFECYCLE:
            errors.append("invalid_lifecycle_status")
        if record.execution_authority != "NONE":
            errors.append("execution_authority_must_be_none")
        if not record.guides:
            warnings.append("guides_missing")
        if not record.retention_policy:
            warnings.append("retention_policy_missing")
        return CatalogValidation(
            status="INVALID" if errors else ("WARNING" if warnings else "VALID"),
            errors=tuple(sorted(errors)),
            warnings=tuple(sorted(warnings)),
        )

    def discover_dataset_info(self, data_root: str | Path) -> tuple[DatasetRecord, ...]:
        root = Path(data_root)
        discovered: list[DatasetRecord] = []
        for info_path in sorted(root.rglob("dataset_info.json")):
            try:
                payload = json.loads(info_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not self.REQUIRED_METADATA_FIELDS.issubset(payload):
                continue
            rel_parent = info_path.parent.as_posix()
            try:
                rel_parent = "data/" + info_path.parent.relative_to(root).as_posix()
            except ValueError:
                pass
            record = DatasetRecord(
                dataset_id=str(payload["dataset_id"]),
                name=str(payload.get("name") or payload["dataset_id"]),
                category=str(payload.get("category") or "UNCLASSIFIED"),
                schema_version=str(payload["schema_version"]),
                storage_path=rel_parent,
                owner=str(payload.get("owner") or "AFIP"),
                producer=str(payload["producer"]),
                classification=str(payload["data_classification"]),
                lifecycle_status=str(payload.get("lifecycle_status") or "ACTIVE"),
                retention_policy=str(payload.get("retention_policy") or "UNSPECIFIED"),
                lineage_parents=tuple(sorted(str(x) for x in payload.get("lineage_parents", []))),
                guides=tuple(sorted(str(x) for x in payload.get("guides", []))),
                tags=tuple(sorted(str(x) for x in payload.get("tags", []))),
            )
            discovered.append(record)
        return tuple(sorted(discovered, key=lambda item: item.dataset_id))

    def validate_lineage(self) -> CatalogValidation:
        errors: list[str] = []
        warnings: list[str] = []
        known = set(self._records)
        for record in self._records.values():
            for parent in record.lineage_parents:
                if parent not in known:
                    warnings.append(f"missing_lineage_parent:{record.dataset_id}:{parent}")
        return CatalogValidation(
            status="WARNING" if warnings else "VALID",
            errors=tuple(errors),
            warnings=tuple(sorted(warnings)),
        )

    def build_snapshot(self) -> dict:
        records = [item.to_dict() for item in self.list_records()]
        canonical = json.dumps(records, sort_keys=True, separators=(",", ":"))
        return {
            "catalog_id": "cdc_" + sha256(canonical.encode("utf-8")).hexdigest()[:24],
            "schema_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "record_count": len(records),
            "records": records,
            "execution_authority": "NONE",
            "automatic_strategy_change": "PROHIBITED",
        }

    def write_snapshot(self, path: str | Path) -> dict:
        snapshot = self.build_snapshot()
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        return snapshot
