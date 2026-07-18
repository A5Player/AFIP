from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence
import json


class IntegrityStatus(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CORRUPTED = "CORRUPTED"
    QUARANTINED = "QUARANTINED"


@dataclass(frozen=True)
class IntegrityFinding:
    code: str
    severity: str
    path: str
    detail: str


@dataclass(frozen=True)
class IntegrityReport:
    report_id: str
    dataset_id: str
    status: str
    checked_at: str
    file_count: int
    findings: tuple[IntegrityFinding, ...]
    execution_authority: str = "NONE"
    automatic_data_repair: str = "PROHIBITED"
    automatic_strategy_change: str = "PROHIBITED"
    human_review_required: bool = True

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["findings"] = [asdict(item) for item in self.findings]
        return payload


class KnowledgeIntegrityAuditor:
    """Research-only integrity auditor. It never repairs or executes trades."""

    REQUIRED_DATASET_FIELDS = {
        "dataset_id",
        "schema_version",
        "created_at",
        "producer",
        "data_classification",
    }

    def __init__(self, policy: Mapping[str, object] | None = None) -> None:
        self.policy = dict(policy or {})
        self._validate_policy()

    @classmethod
    def from_policy_file(cls, path: str | Path) -> "KnowledgeIntegrityAuditor":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def _validate_policy(self) -> None:
        if self.policy.get("execution_authority", "NONE") != "NONE":
            raise ValueError("execution_authority_must_be_none")
        if self.policy.get("automatic_data_repair", "PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_data_repair_must_be_prohibited")
        if self.policy.get("automatic_strategy_change", "PROHIBITED") != "PROHIBITED":
            raise ValueError("automatic_strategy_change_must_be_prohibited")

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _stable_report_id(dataset_id: str, findings: Sequence[IntegrityFinding], file_count: int) -> str:
        canonical = {
            "dataset_id": dataset_id,
            "file_count": file_count,
            "findings": [asdict(item) for item in findings],
        }
        raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "iar_" + sha256(raw).hexdigest()[:24]

    def audit_dataset(
        self,
        dataset_root: str | Path,
        manifest: Mapping[str, object] | None = None,
        required_guides: Iterable[str] | None = None,
        lineage_records: Sequence[Mapping[str, object]] | None = None,
    ) -> IntegrityReport:
        base = Path(dataset_root)
        findings: list[IntegrityFinding] = []
        dataset_info_path = base / "dataset_info.json"
        dataset_id = base.name

        if not base.exists() or not base.is_dir():
            findings.append(IntegrityFinding(
                "DATASET_ROOT_MISSING", "ERROR", str(base), "Dataset directory does not exist."
            ))
            return self._build_report(dataset_id, 0, findings)

        files = sorted(path for path in base.rglob("*") if path.is_file())
        relative_paths = {path.relative_to(base).as_posix(): path for path in files}

        if not dataset_info_path.exists():
            findings.append(IntegrityFinding(
                "DATASET_INFO_MISSING", "ERROR", "dataset_info.json", "Required dataset metadata is missing."
            ))
        else:
            try:
                info = json.loads(dataset_info_path.read_text(encoding="utf-8"))
                dataset_id = str(info.get("dataset_id") or dataset_id)
                missing = sorted(self.REQUIRED_DATASET_FIELDS.difference(info))
                for field in missing:
                    findings.append(IntegrityFinding(
                        "METADATA_FIELD_MISSING", "ERROR", "dataset_info.json", f"Missing field: {field}"
                    ))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                findings.append(IntegrityFinding(
                    "DATASET_INFO_INVALID", "ERROR", "dataset_info.json", f"Invalid metadata: {exc}"
                ))

        for guide in sorted(set(required_guides or ())):
            if guide not in relative_paths:
                findings.append(IntegrityFinding(
                    "GUIDE_MISSING", "WARNING", guide, "Required guide or data dictionary is missing."
                ))

        manifest_files = {}
        if manifest:
            raw_files = manifest.get("files", [])
            if not isinstance(raw_files, list):
                findings.append(IntegrityFinding(
                    "MANIFEST_INVALID", "ERROR", "manifest", "Manifest files must be a list."
                ))
            else:
                for item in raw_files:
                    if not isinstance(item, Mapping):
                        findings.append(IntegrityFinding(
                            "MANIFEST_ENTRY_INVALID", "ERROR", "manifest", "Manifest entry must be an object."
                        ))
                        continue
                    rel = str(item.get("path", ""))
                    if not rel:
                        findings.append(IntegrityFinding(
                            "MANIFEST_ENTRY_INVALID", "ERROR", "manifest", "Manifest entry path is missing."
                        ))
                        continue
                    if rel in manifest_files:
                        findings.append(IntegrityFinding(
                            "MANIFEST_DUPLICATE_PATH", "ERROR", rel, "Duplicate path in manifest."
                        ))
                    manifest_files[rel] = item

                for rel, item in sorted(manifest_files.items()):
                    actual_path = relative_paths.get(rel)
                    if actual_path is None:
                        findings.append(IntegrityFinding(
                            "FILE_MISSING", "ERROR", rel, "Manifest file is missing from dataset."
                        ))
                        continue
                    expected_hash = str(item.get("sha256", ""))
                    if expected_hash and self._hash_file(actual_path) != expected_hash:
                        findings.append(IntegrityFinding(
                            "HASH_MISMATCH", "ERROR", rel, "File content differs from manifest."
                        ))

                if self.policy.get("warn_on_unmanifested_files", True):
                    for rel in sorted(set(relative_paths).difference(manifest_files)):
                        findings.append(IntegrityFinding(
                            "UNMANIFESTED_FILE", "WARNING", rel, "File exists but is not present in manifest."
                        ))

        self._audit_lineage(lineage_records or (), findings)
        return self._build_report(dataset_id, len(files), findings)

    def _audit_lineage(
        self,
        records: Sequence[Mapping[str, object]],
        findings: list[IntegrityFinding],
    ) -> None:
        if not records:
            return
        ids = [str(item.get("knowledge_id", "")) for item in records]
        duplicate_ids = sorted({item for item in ids if item and ids.count(item) > 1})
        for knowledge_id in duplicate_ids:
            findings.append(IntegrityFinding(
                "LINEAGE_DUPLICATE_ID", "ERROR", knowledge_id, "Duplicate knowledge_id in lineage."
            ))
        known = {item for item in ids if item}
        for record in records:
            current = str(record.get("knowledge_id", ""))
            parent = record.get("parent_id")
            if parent and str(parent) not in known:
                findings.append(IntegrityFinding(
                    "LINEAGE_PARENT_MISSING", "ERROR", current, f"Missing parent_id: {parent}"
                ))

    def _build_report(
        self,
        dataset_id: str,
        file_count: int,
        findings: Sequence[IntegrityFinding],
    ) -> IntegrityReport:
        ordered = tuple(sorted(findings, key=lambda x: (x.severity, x.code, x.path, x.detail)))
        severities = {item.severity for item in ordered}
        if "ERROR" in severities:
            status = IntegrityStatus.CORRUPTED.value
        elif "WARNING" in severities:
            status = IntegrityStatus.WARNING.value
        else:
            status = IntegrityStatus.HEALTHY.value
        return IntegrityReport(
            report_id=self._stable_report_id(dataset_id, ordered, file_count),
            dataset_id=dataset_id,
            status=status,
            checked_at=datetime.now(timezone.utc).isoformat(),
            file_count=file_count,
            findings=ordered,
        )

    @staticmethod
    def append_audit_ledger(report: IntegrityReport, ledger_path: str | Path) -> None:
        path = Path(ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":"))
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")

    @staticmethod
    def quarantine_recommendation(report: IntegrityReport) -> dict:
        return {
            "report_id": report.report_id,
            "recommended": report.status == IntegrityStatus.CORRUPTED.value,
            "automatic_action_taken": False,
            "destination": "data/governance/integrity/quarantine/",
            "reason": "human_review_required" if report.status != IntegrityStatus.HEALTHY.value else "none",
        }
