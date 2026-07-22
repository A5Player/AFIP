from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .incremental_financial_naming import run_incremental_financial_naming
from .io import atomic_write_json


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CertificationResult:
    name: str
    status: str
    duration_seconds: float
    command: list[str]
    return_code: int
    stdout_tail: str = ""
    stderr_tail: str = ""


class ProductionCertificationRuntime:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.runtime_dir = self.root / "runtime" / "certification"
        self.python = self._python_executable()

    def _python_executable(self) -> str:
        candidate = self.root / ".venv" / "Scripts" / "python.exe"
        return str(candidate) if candidate.exists() else sys.executable

    def _run(self, name: str, args: Iterable[str], timeout: int = 900) -> CertificationResult:
        command = [self.python, *args]
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return CertificationResult(
                name=name,
                status="PASS" if completed.returncode == 0 else "FAIL",
                duration_seconds=round(time.perf_counter() - started, 3),
                command=command,
                return_code=completed.returncode,
                stdout_tail=completed.stdout[-16000:],
                stderr_tail=completed.stderr[-16000:],
            )
        except subprocess.TimeoutExpired as exc:
            return CertificationResult(
                name=name,
                status="FAIL",
                duration_seconds=round(time.perf_counter() - started, 3),
                command=command,
                return_code=124,
                stdout_tail=(exc.stdout or "")[-16000:] if isinstance(exc.stdout, str) else "",
                stderr_tail="TIMEOUT\n" + ((exc.stderr or "")[-16000:] if isinstance(exc.stderr, str) else ""),
            )

    def certify(
        self,
        *,
        full_regression: bool = False,
        force_financial_naming: bool = False,
        mt5_check: bool = False,
    ) -> dict[str, Any]:
        started_at = utc_now()
        checks: list[CertificationResult] = []

        checks.append(self._run(
            "final_consolidation",
            ["-m", "pytest", "tests/test_afip_v1_final_consolidation.py", "-q"],
            timeout=300,
        ))

        optional_tests = [
            "tests/test_revision_4_research_separation.py",
            "tests/test_revision_3_replay_throughput.py",
            "tests/test_afip_v1_final_runtime_observatory.py",
            "tests/test_afip_v1_production_certification.py",
        ]
        existing = [path for path in optional_tests if (self.root / path).exists()]
        if existing:
            checks.append(self._run("compatibility_certification", ["-m", "pytest", *existing, "-q"], timeout=600))

        checks.append(self._run(
            "architecture",
            ["-m", "tools.afip_final_integration", "architecture", "--root", str(self.root)],
            timeout=180,
        ))
        checks.append(self._run(
            "dashboard",
            ["-m", "tools.afip_final_integration", "dashboard", "--root", str(self.root)],
            timeout=180,
        ))

        naming = run_incremental_financial_naming(
            self.root, force=force_financial_naming, timeout_seconds=180
        )
        checks.append(CertificationResult(
            name="financial_naming",
            status=str(naming.get("status", "FAIL")),
            duration_seconds=float(naming.get("duration_seconds", 0.0)),
            command=[self.python, "tools/validate_financial_naming.py"],
            return_code=0 if naming.get("status") == "PASS" else 1,
            stdout_tail=json.dumps(naming, ensure_ascii=False, indent=2)[-16000:],
        ))

        local_quality = self.root / "tools" / "afip_local_quality_check.py"
        if local_quality.exists():
            checks.append(self._run("local_quality", [str(local_quality)], timeout=900))

        if mt5_check:
            checks.append(self._run("mt5_check", ["afip.py", "mt5-check"], timeout=300))

        if full_regression:
            checks.append(self._run("full_regression", ["-m", "pytest", "-q"], timeout=10800))

        status = "PASS" if checks and all(item.status == "PASS" for item in checks) else "FAIL"
        report = {
            "schema_version": "afip-production-certification.v1",
            "status": status,
            "started_at_utc": started_at,
            "completed_at_utc": utc_now(),
            "full_regression_requested": full_regression,
            "mt5_check_requested": mt5_check,
            "checks": [asdict(item) for item in checks],
            "production_ready": status == "PASS" and full_regression,
            "note": (
                "Production ready requires PASS with full_regression_requested=true. "
                "MT5 operational readiness is certified separately when -Mt5Check is requested."
            ),
        }
        atomic_write_json(self.runtime_dir / "production_certification.json", report)
        self._write_text_report(report)
        return report

    def _write_text_report(self, report: dict[str, Any]) -> None:
        lines = [
            "AFIP V1 PRODUCTION CERTIFICATION",
            f"STATUS: {report['status']}",
            f"STARTED: {report['started_at_utc']}",
            f"COMPLETED: {report['completed_at_utc']}",
            f"FULL REGRESSION: {report['full_regression_requested']}",
            f"PRODUCTION READY: {report['production_ready']}",
            "",
        ]
        for item in report["checks"]:
            lines.append(
                f"{item['name']}: {item['status']} "
                f"({item['duration_seconds']}s, rc={item['return_code']})"
            )
        path = self.runtime_dir / "production_certification.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
