"""Dashboard status icon normalization for AFIP Milestone H Pack 1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardStatusIcon:
    """Human-friendly deterministic status icon metadata."""

    status: str
    icon: str
    label_en: str
    label_th: str
    priority: int


def normalize_status(value: str) -> str:
    text = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    if text in {"PASS", "PASSED", "OK", "READY", "RUNNING", "ACTIVE"}:
        return "READY"
    if text in {"WAIT", "WAITING", "PENDING", "REVIEW", "REVIEW_REQUIRED", "CAUTION"}:
        return "REVIEW"
    if text in {"OFF", "DISABLED", "INACTIVE"}:
        return "OFF"
    if text in {"BLOCK", "BLOCKED", "FAIL", "FAILED", "ERROR"}:
        return "BLOCKED"
    return text or "REVIEW"


def status_icon(value: str) -> DashboardStatusIcon:
    status = normalize_status(value)
    mapping = {
        "READY": DashboardStatusIcon("READY", "🟢", "Ready", "พร้อม", 1),
        "REVIEW": DashboardStatusIcon("REVIEW", "🟡", "Review", "รอตรวจสอบ", 2),
        "OFF": DashboardStatusIcon("OFF", "⚪", "Off", "ปิดใช้งาน", 3),
        "BLOCKED": DashboardStatusIcon("BLOCKED", "🔴", "Blocked", "ถูกระงับ", 4),
    }
    return mapping.get(status, DashboardStatusIcon(status, "🟡", "Review", "รอตรวจสอบ", 2))
