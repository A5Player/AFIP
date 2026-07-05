"""Validate AFIP financial naming compliance."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "backup", "venv", ".venv"}
SKIP_PATH_PARTS = {"tools", "standards", "tests"}
PROHIBITED = [
    "Com" + "mander",
    "Ran" + "ger",
    "Sni" + "per",
    "Sco" + "ut",
    "Gu" + "ard",
    "Kill" + " Switch",
    "At" + "tack",
    "Def" + "ense",
    "Bat" + "tle",
    "Wea" + "pon",
    "Mis" + "sion",
    "Tac" + "tical",
]


def iter_runtime_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel_parts = set(path.relative_to(ROOT).parts)
        if rel_parts & SKIP_DIRS:
            continue
        if rel_parts & SKIP_PATH_PARTS:
            continue
        yield path


def main() -> int:
    findings = []
    for path in iter_runtime_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for term in PROHIBITED:
                if term in line:
                    findings.append((path.relative_to(ROOT), line_no, term))

    if findings:
        print("AFIP Financial Naming Validation: FAIL")
        for rel, line_no, term in findings[:100]:
            print(f"  - {rel}:{line_no} contains non-financial term: {term}")
        if len(findings) > 100:
            print(f"  ... {len(findings) - 100} more findings")
        return 1

    print("AFIP Financial Naming Validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
