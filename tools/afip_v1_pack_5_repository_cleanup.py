"""AFIP V1 Pack 5: safely untrack generated Pack/runtime artifacts."""
from __future__ import annotations
import subprocess
from pathlib import Path

IGNORE_LINES = (
    "runtime/backups/",
    "runtime/execution/*.lock",
    "runtime/certification/afip_v1_pack_*_certification.json",
    "payload/afip/demo_execution_gateway/runtime.py",
    "payload/afip/protection/sl_tp_planner.py",
    "payload/tests/test_afip_v1_pack_4_production_certification_repair.py",
    "payload/tests/test_phase25_position_protection.py",
    "payload/tools/afip_demo_execution_control.py",
    "payload/tools/afip_v1_pack_4_demo_execution_certification.py",
)
UNTRACK = (
    "runtime/backups",
    "runtime/execution/account_routing.lock",
    "runtime/certification/afip_v1_pack_4_demo_execution_certification.json",
    "payload/afip/demo_execution_gateway/runtime.py",
    "payload/afip/protection/sl_tp_planner.py",
    "payload/tests/test_afip_v1_pack_4_production_certification_repair.py",
    "payload/tests/test_phase25_position_protection.py",
    "payload/tools/afip_demo_execution_control.py",
    "payload/tools/afip_v1_pack_4_demo_execution_certification.py",
)

def update_gitignore(root: Path) -> None:
    path = root / ".gitignore"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    suffix = [line for line in IGNORE_LINES if line not in text.splitlines()]
    if suffix:
        text = text.rstrip() + "\n\n# AFIP V1 Pack 5 - generated artifact isolation\n" + "\n".join(suffix) + "\n"
        path.write_text(text, encoding="utf-8")

def untrack(root: Path) -> list[str]:
    if not (root / ".git").exists():
        return []
    removed: list[str] = []
    for relative in UNTRACK:
        result = subprocess.run(
            ["git", "rm", "-r", "--cached", "--ignore-unmatch", "--", relative],
            cwd=root, text=True, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"git rm failed: {relative}")
        if result.stdout.strip():
            removed.append(relative)
    return removed

def main() -> int:
    root = Path.cwd()
    update_gitignore(root)
    removed = untrack(root)
    print("AFIP V1 Pack 5 repository cleanup: PASS")
    print(f"Untracked generated paths: {len(removed)}")
    print("Local files are preserved; only Git tracking is removed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
