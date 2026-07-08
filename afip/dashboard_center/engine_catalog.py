"""Dashboard taxonomy for AFIP runtime engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .status_icon import status_icon


@dataclass(frozen=True)
class EngineCard:
    key: str
    category: str
    icon: str
    status: str
    name_en: str
    name_th: str
    function_en: str
    function_th: str
    explanation_en: str
    explanation_th: str
    dependency_summary: str
    performance_summary: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "EngineCard":
        marker = status_icon(str(value.get("status", "READY")))
        return cls(
            key=str(value.get("key", value.get("name_en", "UNKNOWN"))).strip().lower().replace(" ", "_"),
            category=str(value.get("category", "Runtime Engine")).strip() or "Runtime Engine",
            icon=marker.icon,
            status=marker.status,
            name_en=str(value.get("name_en", "Unnamed Engine")).strip(),
            name_th=str(value.get("name_th", "ระบบประมวลผล")).strip(),
            function_en=str(value.get("function_en", "Process runtime evidence.")).strip(),
            function_th=str(value.get("function_th", "ประมวลผลข้อมูลระบบ")).strip(),
            explanation_en=str(value.get("explanation_en", "Supports dashboard review without changing trading logic.")).strip(),
            explanation_th=str(value.get("explanation_th", "สนับสนุนการตรวจสอบ Dashboard โดยไม่เปลี่ยนตรรกะการเทรด")).strip(),
            dependency_summary=str(value.get("dependency_summary", "None")).strip(),
            performance_summary=str(value.get("performance_summary", "Measured by runtime metrics")).strip(),
        )

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def default_engine_catalog(records: Iterable[Mapping[str, Any]] | None = None) -> list[EngineCard]:
    source = list(records) if records is not None else _DEFAULT_ENGINES
    cards = [EngineCard.from_mapping(item) for item in source]
    return sorted(cards, key=lambda item: (item.category, item.name_en))


_DEFAULT_ENGINES: tuple[dict[str, Any], ...] = (
    {
        "key": "decision_engine",
        "category": "Trading Runtime",
        "name_en": "Decision Engine",
        "name_th": "ระบบตัดสินใจ",
        "function_en": "Convert validated evidence into BUY, SELL, or WAIT.",
        "function_th": "แปลงหลักฐานที่ผ่านการตรวจสอบเป็น BUY, SELL หรือ WAIT",
        "explanation_en": "Uses the existing deterministic decision path and is only displayed by the dashboard.",
        "explanation_th": "ใช้เส้นทางการตัดสินใจเดิมแบบ deterministic และแสดงผลบน Dashboard เท่านั้น",
        "dependency_summary": "Market regime, intelligence outputs, risk state",
    },
    {
        "key": "walk_forward_engine",
        "category": "Simulation Runtime",
        "name_en": "Walk-Forward Simulation Engine",
        "name_th": "ระบบจำลองเดินกราฟย้อนหลัง",
        "function_en": "Simulate historical decisions one step at a time without future data.",
        "function_th": "จำลองการตัดสินใจย้อนหลังทีละขั้นโดยไม่ใช้ข้อมูลอนาคต",
        "explanation_en": "Protects standards from look-ahead bias before live adaptation.",
        "explanation_th": "ป้องกันมาตรฐานการเทรดจากการรู้อนาคตก่อนปรับจากข้อมูลจริง",
        "dependency_summary": "Historical candles, signal context, outcome tracker",
    },
    {
        "key": "paper_trading_engine",
        "category": "Simulation Runtime",
        "name_en": "Paper Trading Engine",
        "name_th": "ระบบทดลองเทรดจำลอง",
        "function_en": "Record simulated decisions without sending live orders.",
        "function_th": "บันทึกการตัดสินใจจำลองโดยไม่ส่งคำสั่งจริง",
        "explanation_en": "Supports trial evaluation and controlled learning.",
        "explanation_th": "รองรับการทดลองและการเรียนรู้แบบควบคุม",
        "dependency_summary": "Decision output, risk state, simulated account",
    },
    {
        "key": "experience_engine",
        "category": "Knowledge Runtime",
        "name_en": "Experience Knowledge Engine",
        "name_th": "ระบบความรู้จากประสบการณ์",
        "function_en": "Summarize repeated outcomes into reusable knowledge.",
        "function_th": "สรุปผลลัพธ์ซ้ำให้เป็นความรู้ที่นำกลับมาใช้ได้",
        "explanation_en": "Turns trading situations and results into reviewable evidence.",
        "explanation_th": "แปลงสถานการณ์และผลลัพธ์การเทรดให้เป็นหลักฐานที่ตรวจสอบได้",
        "dependency_summary": "Closed outcomes, market regime, confidence history",
    },
    {
        "key": "dashboard_engine",
        "category": "Dashboard Runtime",
        "name_en": "Dashboard Foundation Engine",
        "name_th": "ระบบฐาน Dashboard",
        "function_en": "Prepare bilingual cards, status icons, and top ranking sections.",
        "function_th": "เตรียมการ์ดสองภาษา ไอคอนสถานะ และส่วนจัดอันดับ Top",
        "explanation_en": "Presentation-only layer for user review.",
        "explanation_th": "เป็นชั้นแสดงผลเพื่อให้ผู้ใช้ตรวจสอบเท่านั้น",
        "dependency_summary": "Catalog metadata, trial metrics, dashboard policy",
    },
)
