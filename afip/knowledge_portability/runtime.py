"""AFIP knowledge portability, recovery, and reuse framework.

Research/data-governance only. This module has no execution, broker, terminal,
position, or order authority.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
import json
import shutil
import zipfile

SCHEMA_VERSION = "afip.knowledge.portability.v1"
EXECUTION_AUTHORITY = "NONE"
PROMOTION_TO_EXECUTION = "PROHIBITED"


@dataclass(frozen=True)
class ManifestEntry:
    relative_path: str
    size_bytes: int
    sha256: str
    category: str


@dataclass(frozen=True)
class IntegrityIssue:
    relative_path: str
    issue: str
    expected: str | None = None
    observed: str | None = None


@dataclass(frozen=True)
class PortabilityManifest:
    schema_version: str
    bundle_id: str
    dataset_name: str
    source_root: str
    created_at_utc: str
    file_count: int
    total_size_bytes: int
    entries: tuple[ManifestEntry, ...]
    metadata: dict[str, Any]
    execution_authority: str = EXECUTION_AUTHORITY
    promotion_to_execution: str = PROMOTION_TO_EXECUTION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entries"] = [asdict(entry) for entry in self.entries]
        return data


@dataclass(frozen=True)
class BundleImportResult:
    status: str
    bundle_id: str
    verified_file_count: int
    destination: str | None
    issues: tuple[IntegrityIssue, ...]
    execution_authority: str = EXECUTION_AUTHORITY


class KnowledgePortabilityEngine:
    """Build, verify, export, and safely import reusable AFIP datasets."""

    def __init__(self, *, policy: dict[str, Any] | None = None) -> None:
        self.policy = policy or {}
        if self.policy.get("execution_authority", EXECUTION_AUTHORITY) != EXECUTION_AUTHORITY:
            raise ValueError("knowledge portability cannot receive execution authority")
        if self.policy.get("promotion_to_execution", PROMOTION_TO_EXECUTION) != PROMOTION_TO_EXECUTION:
            raise ValueError("promotion to execution must remain prohibited")

    @staticmethod
    def _hash_file(path: Path) -> str:
        digest = sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    @staticmethod
    def _category(relative_path: str) -> str:
        parts = PurePosixPath(relative_path).parts
        return parts[0] if len(parts) > 1 else "root"

    @staticmethod
    def _safe_relative(value: str) -> PurePosixPath:
        candidate = PurePosixPath(value)
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
            raise ValueError(f"unsafe relative path: {value}")
        return candidate

    def build_manifest(
        self,
        source_root: str | Path,
        *,
        dataset_name: str,
        metadata: dict[str, Any] | None = None,
        created_at_utc: str | None = None,
    ) -> PortabilityManifest:
        source = Path(source_root).resolve()
        if not source.is_dir():
            raise FileNotFoundError(f"dataset root not found: {source}")
        entries: list[ManifestEntry] = []
        excluded_names = set(self.policy.get("excluded_names", [".DS_Store", "Thumbs.db"]))
        for path in sorted((p for p in source.rglob("*") if p.is_file()), key=lambda p: p.as_posix()):
            if path.name in excluded_names:
                continue
            relative = path.relative_to(source).as_posix()
            entries.append(ManifestEntry(relative, path.stat().st_size, self._hash_file(path), self._category(relative)))
        if not entries and not self.policy.get("allow_empty_dataset", False):
            raise ValueError("dataset contains no portable files")
        identity_payload = {
            "schema_version": SCHEMA_VERSION,
            "dataset_name": dataset_name,
            "entries": [asdict(item) for item in entries],
            "metadata": metadata or {},
        }
        bundle_id = sha256(json.dumps(identity_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]
        return PortabilityManifest(
            schema_version=SCHEMA_VERSION,
            bundle_id=bundle_id,
            dataset_name=dataset_name,
            source_root=source.as_posix(),
            created_at_utc=created_at_utc or datetime.now(timezone.utc).isoformat(),
            file_count=len(entries),
            total_size_bytes=sum(item.size_bytes for item in entries),
            entries=tuple(entries),
            metadata=metadata or {},
        )

    @staticmethod
    def write_manifest(manifest: PortabilityManifest, destination: str | Path) -> Path:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @staticmethod
    def load_manifest(path: str | Path) -> PortabilityManifest:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported portability manifest schema")
        entries = tuple(ManifestEntry(**entry) for entry in raw.get("entries", []))
        return PortabilityManifest(
            schema_version=raw["schema_version"], bundle_id=raw["bundle_id"], dataset_name=raw["dataset_name"],
            source_root=raw.get("source_root", ""), created_at_utc=raw["created_at_utc"],
            file_count=raw["file_count"], total_size_bytes=raw["total_size_bytes"], entries=entries,
            metadata=raw.get("metadata", {}), execution_authority=raw.get("execution_authority", EXECUTION_AUTHORITY),
            promotion_to_execution=raw.get("promotion_to_execution", PROMOTION_TO_EXECUTION),
        )

    def verify_dataset(self, source_root: str | Path, manifest: PortabilityManifest) -> tuple[IntegrityIssue, ...]:
        source = Path(source_root).resolve()
        issues: list[IntegrityIssue] = []
        expected = {entry.relative_path: entry for entry in manifest.entries}
        for relative, entry in expected.items():
            try:
                safe = self._safe_relative(relative)
            except ValueError:
                issues.append(IntegrityIssue(relative, "unsafe_manifest_path")); continue
            path = source.joinpath(*safe.parts)
            if not path.is_file():
                issues.append(IntegrityIssue(relative, "missing_file", entry.sha256, None)); continue
            size = path.stat().st_size
            if size != entry.size_bytes:
                issues.append(IntegrityIssue(relative, "size_mismatch", str(entry.size_bytes), str(size))); continue
            observed = self._hash_file(path)
            if observed != entry.sha256:
                issues.append(IntegrityIssue(relative, "checksum_mismatch", entry.sha256, observed))
        if self.policy.get("reject_unmanifested_files", False):
            observed_files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
            for extra in sorted(observed_files - set(expected)):
                issues.append(IntegrityIssue(extra, "unmanifested_file"))
        return tuple(issues)

    def export_bundle(self, source_root: str | Path, destination_dir: str | Path, *, dataset_name: str,
                      metadata: dict[str, Any] | None = None) -> tuple[Path, PortabilityManifest]:
        source = Path(source_root).resolve()
        manifest = self.build_manifest(source, dataset_name=dataset_name, metadata=metadata)
        destination = Path(destination_dir); destination.mkdir(parents=True, exist_ok=True)
        archive = destination / f"afip-knowledge-{manifest.bundle_id}.zip"
        manifest_bytes = (json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n").encode("utf-8")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("manifest.json", manifest_bytes)
            for entry in manifest.entries:
                safe = self._safe_relative(entry.relative_path)
                bundle.write(source.joinpath(*safe.parts), arcname=f"payload/{safe.as_posix()}")
        return archive, manifest

    def inspect_bundle(self, bundle_path: str | Path) -> tuple[PortabilityManifest, tuple[IntegrityIssue, ...]]:
        issues: list[IntegrityIssue] = []
        with zipfile.ZipFile(bundle_path, "r") as bundle:
            names = set(bundle.namelist())
            if "manifest.json" not in names:
                raise ValueError("bundle has no manifest.json")
            raw = json.loads(bundle.read("manifest.json").decode("utf-8-sig"))
            if raw.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("unsupported portability manifest schema")
            entries = tuple(ManifestEntry(**entry) for entry in raw.get("entries", []))
            manifest = PortabilityManifest(raw["schema_version"], raw["bundle_id"], raw["dataset_name"], raw.get("source_root", ""),
                raw["created_at_utc"], raw["file_count"], raw["total_size_bytes"], entries, raw.get("metadata", {}),
                raw.get("execution_authority", EXECUTION_AUTHORITY), raw.get("promotion_to_execution", PROMOTION_TO_EXECUTION))
            for entry in manifest.entries:
                try: safe = self._safe_relative(entry.relative_path)
                except ValueError:
                    issues.append(IntegrityIssue(entry.relative_path, "unsafe_manifest_path")); continue
                member = f"payload/{safe.as_posix()}"
                if member not in names:
                    issues.append(IntegrityIssue(entry.relative_path, "missing_bundle_member")); continue
                payload = bundle.read(member)
                if len(payload) != entry.size_bytes:
                    issues.append(IntegrityIssue(entry.relative_path, "size_mismatch", str(entry.size_bytes), str(len(payload)))); continue
                observed = sha256(payload).hexdigest()
                if observed != entry.sha256:
                    issues.append(IntegrityIssue(entry.relative_path, "checksum_mismatch", entry.sha256, observed))
        return manifest, tuple(issues)

    def import_bundle(self, bundle_path: str | Path, destination_root: str | Path, *, verify_only: bool = True) -> BundleImportResult:
        manifest, issues = self.inspect_bundle(bundle_path)
        if issues:
            return BundleImportResult("REJECTED", manifest.bundle_id, manifest.file_count - len(issues), None, issues)
        if verify_only:
            return BundleImportResult("VERIFIED_ONLY", manifest.bundle_id, manifest.file_count, None, ())
        destination = Path(destination_root).resolve() / manifest.bundle_id
        if destination.exists():
            raise FileExistsError(f"import destination already exists: {destination}")
        destination.mkdir(parents=True, exist_ok=False)
        with zipfile.ZipFile(bundle_path, "r") as bundle:
            for entry in manifest.entries:
                safe = self._safe_relative(entry.relative_path)
                target = destination.joinpath(*safe.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(f"payload/{safe.as_posix()}") as source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
            (destination / "manifest.json").write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return BundleImportResult("IMPORTED_TO_ISOLATED_DESTINATION", manifest.bundle_id, manifest.file_count, destination.as_posix(), ())
