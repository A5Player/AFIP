from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

DEFAULT_INCLUDE_DIRS = ("afip", "config", "tools", "tests")
DEFAULT_ROOT_FILES = ("afip.py", "pyproject.toml", "pytest.ini", "requirements.txt")
TEXT_SUFFIXES = {
    ".py", ".json", ".toml", ".ini", ".cfg", ".yaml", ".yml",
    ".md", ".txt", ".ps1", ".bat",
}
EXCLUDED_PARTS = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "runtime", "installation_backups", "node_modules", "dist", "build",
}


def iter_relevant_files(root: Path) -> Iterable[Path]:
    seen: set[Path] = set()
    for directory in DEFAULT_INCLUDE_DIRS:
        base = root / directory
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(root)
            if any(part.lower() in EXCLUDED_PARTS for part in relative.parts):
                continue
            if relative not in seen:
                seen.add(relative)
                yield path
    for filename in DEFAULT_ROOT_FILES:
        path = root / filename
        if path.is_file():
            yield path


def repository_fingerprint(root: Path) -> tuple[str, list[str]]:
    digest = hashlib.sha256()
    relative_paths: list[str] = []
    for path in sorted(iter_relevant_files(root), key=lambda item: str(item).lower()):
        relative = path.relative_to(root)
        relative_text = relative.as_posix()
        stat = path.stat()
        digest.update(relative_text.encode("utf-8"))
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
        relative_paths.append(relative_text)
    return digest.hexdigest(), relative_paths
