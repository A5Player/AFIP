"""Continuously regenerate the AFIP operational dashboard from runtime files."""
from __future__ import annotations

from pathlib import Path
import time

from .launcher import launch_dashboard


def run_live_dashboard(output_path: str | Path = "runtime/dashboard/afip_dashboard.html", interval_seconds: int = 5) -> None:
    interval = max(2, int(interval_seconds))
    while True:
        launch_dashboard(output_path)
        time.sleep(interval)
