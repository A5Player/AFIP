"""Internet and broker latency monitor for Production Bring-up Pack 3."""

from __future__ import annotations

import socket
import time
from typing import Any, Mapping

from .models import InternetConnectivityReport

VERSION1_BROKER = "XM"
VERSION1_SYMBOL = "GOLD#"
_DEFAULT_DNS_HOST = "8.8.8.8"
_DEFAULT_DNS_PORT = 53
_DEFAULT_BROKER_HOST = "google.com"
_DEFAULT_BROKER_PORT = 443


def _text(value: Any, default: str = "UNKNOWN") -> str:
    text = str(value if value is not None else default).strip()
    return text or default


def _upper(value: Any, default: str = "") -> str:
    return _text(value, default).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


class InternetMonitorRuntime:
    """Check internet and broker reachability without touching trading logic."""

    def evaluate_one(self, record: Mapping[str, Any] | None = None) -> InternetConnectivityReport:
        record = record or {}
        broker = _upper(record.get("broker", VERSION1_BROKER), VERSION1_BROKER)
        symbol = _upper(record.get("symbol", VERSION1_SYMBOL), VERSION1_SYMBOL)
        live = bool(record.get("live_execution_enabled", False)) or _upper(record.get("mode", ""), "") == "LIVE"
        if live:
            return self._blocked("live_execution_blocked_for_internet_monitor")
        if broker != VERSION1_BROKER:
            return self._blocked("version1_xm_only_required_for_internet_monitor")
        if symbol != VERSION1_SYMBOL:
            return self._blocked("version1_gold_only_required_for_internet_monitor")

        broker_host = _text(record.get("broker_host", record.get("latency_host", _DEFAULT_BROKER_HOST)), _DEFAULT_BROKER_HOST)
        broker_port = _int(record.get("broker_port", _DEFAULT_BROKER_PORT), _DEFAULT_BROKER_PORT)
        dns_host = _text(record.get("dns_host", _DEFAULT_DNS_HOST), _DEFAULT_DNS_HOST)
        dns_port = _int(record.get("dns_port", _DEFAULT_DNS_PORT), _DEFAULT_DNS_PORT)
        timeout = max(0.1, _float(record.get("connect_timeout_seconds", 1.5), 1.5))

        if "internet_status" in record or "broker_latency_ms" in record or "dns_latency_ms" in record:
            internet_status = _upper(record.get("internet_status", "READY"), "READY")
            broker_status = _upper(record.get("broker_status", internet_status), internet_status)
            dns_status = _upper(record.get("dns_status", internet_status), internet_status)
            broker_latency = round(max(0.0, _float(record.get("broker_latency_ms"), 0.0)), 2)
            dns_latency = round(max(0.0, _float(record.get("dns_latency_ms"), 0.0)), 2)
        elif bool(record.get("internet_monitor_enabled", False)):
            dns_status, dns_latency = self._probe(dns_host, dns_port, timeout)
            broker_status, broker_latency = self._probe(broker_host, broker_port, timeout)
            internet_status = "READY" if dns_status == "READY" or broker_status == "READY" else "WAITING"
        else:
            internet_status = "READY"
            broker_status = "READY"
            dns_status = "READY"
            broker_latency = 0.0
            dns_latency = 0.0

        disconnect_count = max(0, _int(record.get("internet_disconnect_count", record.get("disconnect_count", 0)), 0))
        reconnect_count = max(0, _int(record.get("reconnect_count", 0), 0))
        disconnect_duration = max(0, _int(record.get("internet_disconnect_duration_seconds", record.get("disconnect_duration_seconds", 0)), 0))
        latency_limit = max(1.0, _float(record.get("latency_review_limit_ms", 750.0), 750.0))

        status = "READY"
        reason = "internet_and_broker_connectivity_ready"
        gate = "INTERNET_CONNECTIVITY_READY"
        if internet_status not in {"READY", "ONLINE", "CONNECTED"}:
            status = "WAITING"
            reason = "internet_connectivity_waiting"
            gate = "INTERNET_WAITING"
        elif broker_status not in {"READY", "ONLINE", "CONNECTED"}:
            status = "WAITING"
            reason = "broker_connectivity_waiting"
            gate = "BROKER_WAITING"
        elif max(broker_latency, dns_latency) >= latency_limit:
            status = "REVIEW"
            reason = "internet_latency_review_required"
            gate = "LATENCY_REVIEW"
        elif disconnect_count > reconnect_count and disconnect_duration > 0:
            status = "REVIEW"
            reason = "internet_disconnect_recovery_review_required"
            gate = "RECOVERY_REVIEW"

        return InternetConnectivityReport(
            status=status,
            reason=reason,
            internet_status=internet_status,
            broker_status=broker_status,
            dns_status=dns_status,
            broker_host=broker_host,
            broker_port=broker_port,
            broker_latency_ms=broker_latency,
            dns_latency_ms=dns_latency,
            disconnect_count=disconnect_count,
            reconnect_count=reconnect_count,
            disconnect_duration_seconds=disconnect_duration,
            connection_gate=gate,
            dashboard_message_th="แสดงสถานะอินเทอร์เน็ตและความหน่วงของโบรกเกอร์แบบอ่านอย่างเดียว",
            dashboard_message_en="Displays read-only internet and broker latency status.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )

    def explain_one(self, record: Mapping[str, Any] | None = None) -> InternetConnectivityReport:
        return self.evaluate_one(record)

    def _probe(self, host: str, port: int, timeout: float) -> tuple[str, float]:
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=timeout):
                elapsed = round((time.perf_counter() - start) * 1000.0, 2)
                return "READY", elapsed
        except OSError:
            elapsed = round((time.perf_counter() - start) * 1000.0, 2)
            return "WAITING", elapsed

    def _blocked(self, reason: str) -> InternetConnectivityReport:
        return InternetConnectivityReport(
            status="BLOCKED",
            reason=reason,
            internet_status="BLOCKED",
            broker_status="BLOCKED",
            dns_status="BLOCKED",
            broker_host="BLOCKED",
            broker_port=0,
            broker_latency_ms=0.0,
            dns_latency_ms=0.0,
            disconnect_count=0,
            reconnect_count=0,
            disconnect_duration_seconds=0,
            connection_gate="LIVE_EXECUTION_BLOCKED" if "live" in reason else "VERSION1_POLICY_BLOCKED",
            dashboard_message_th="บล็อกการตรวจสอบเครือข่ายตามนโยบายความปลอดภัย Version 1",
            dashboard_message_en="Blocks connectivity telemetry according to Version 1 safety policy.",
            trading_logic_changed=False,
            live_execution_enabled=False,
        )
