"""VPS Health Monitor runtime for Production Bring-up Pack 1."""

from __future__ import annotations

import os
import platform
import shutil
import socket
import sys
import time
from typing import Any, Mapping

from .models import VPSHealthReport

_BYTES_PER_GB = 1024 ** 3


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _clamp_percent(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def _text(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


class VPSHealthMonitorRuntime:
    """Build deterministic VPS health telemetry for Dashboard System.

    The runtime accepts explicit values for deterministic tests. If values are
    not supplied, it uses safe standard-library collectors so the VPS dashboard
    can show real machine health without adding third-party dependencies.
    """

    def evaluate_one(self, record: Mapping[str, Any] | None = None) -> VPSHealthReport:
        record = record or {}
        live = bool(record.get("live_execution_enabled", False)) or str(record.get("mode", "")).upper() == "LIVE"
        hostname = _text(record.get("hostname"), socket.gethostname())
        operating_system = _text(record.get("operating_system"), platform.system() or "Windows")
        windows_version = _text(record.get("windows_version"), platform.version() or platform.release())
        architecture = _text(record.get("architecture"), platform.machine() or "AMD64")
        python_version = _text(record.get("python_version"), platform.python_version())
        uptime_seconds = max(0, _int(record.get("uptime_seconds"), int(time.monotonic())))
        disk_total_gb, disk_free_gb, disk_percent = self._disk_metrics(record)
        cpu_percent = _clamp_percent(_float(record.get("cpu_percent", record.get("cpu", 0.0)), 0.0))
        ram_percent = _clamp_percent(_float(record.get("ram_percent", record.get("ram", 0.0)), 0.0))
        disk_percent = _clamp_percent(_float(record.get("disk_percent", record.get("disk", disk_percent)), disk_percent))
        status = "READY"
        reason = "vps_health_ready"
        gate = "VPS_HEALTH_READY"
        if live:
            status = "BLOCKED"
            reason = "live_execution_blocked_for_vps_health_monitor"
            gate = "LIVE_EXECUTION_BLOCKED"
        elif max(cpu_percent, ram_percent, disk_percent) >= 95.0:
            status = "REVIEW"
            reason = "vps_resource_pressure_review_required"
            gate = "VPS_HEALTH_REVIEW"
        elif not hostname or hostname == "UNKNOWN":
            status = "WAITING"
            reason = "vps_hostname_waiting_for_collection"
            gate = "VPS_HEALTH_WAITING"
        return VPSHealthReport(
            status=status,
            reason=reason,
            hostname=hostname,
            operating_system=operating_system,
            windows_version=windows_version,
            architecture=architecture,
            python_version=python_version,
            uptime_seconds=uptime_seconds,
            cpu_percent=cpu_percent,
            ram_percent=ram_percent,
            disk_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            disk_total_gb=disk_total_gb,
            health_gate=gate,
            dashboard_message_th="แสดงสุขภาพของ Windows VPS โดยไม่เปลี่ยนตรรกะการเทรด",
            dashboard_message_en="Displays Windows VPS health without changing trading logic.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any] | None = None) -> VPSHealthReport:
        return self.evaluate_one(record)

    def _disk_metrics(self, record: Mapping[str, Any]) -> tuple[float, float, float]:
        if "disk_total_gb" in record or "disk_free_gb" in record:
            total = round(max(0.0, _float(record.get("disk_total_gb"), 0.0)), 2)
            free = round(max(0.0, _float(record.get("disk_free_gb"), 0.0)), 2)
            used_percent = 0.0 if total <= 0 else _clamp_percent(((total - free) / total) * 100.0)
            return total, free, used_percent
        try:
            usage = shutil.disk_usage(record.get("disk_path", os.getcwd()))
            total = round(usage.total / _BYTES_PER_GB, 2)
            free = round(usage.free / _BYTES_PER_GB, 2)
            used_percent = _clamp_percent((usage.used / usage.total) * 100.0) if usage.total else 0.0
            return total, free, used_percent
        except (OSError, ValueError):
            return 0.0, 0.0, 0.0
