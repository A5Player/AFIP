from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    command = [sys.executable, "-m", "tools.afip_demo_execution_control", "stop-all"]
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        print("WARNING: normal stop-all failed.")
        print("Cleanup remains fail-closed: do not restart AFIP execution.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
