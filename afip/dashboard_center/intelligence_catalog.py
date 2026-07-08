"""Dashboard taxonomy for AFIP intelligence modules.

The catalog is presentation metadata only. It does not change trading logic,
execution decisions, risk controls, or runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .status_icon import status_icon


@dataclass(frozen=True)
class IntelligenceCard:
    """Bilingual dashboard card for one intelligence module."""

    key: str
    category: str
    icon: str
    status: str
    status_label_en: str
    status_label_th: str
    name_en: str
    name_th: str
    function_en: str
    function_th: str
    explanation_en: str
    explanation_th: str
    input_summary: str
    output_summary: str
    confidence: float

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "IntelligenceCard":
        marker = status_icon(str(value.get("status", "READY")))
        confidence = _ratio(value.get("confidence", 0.0))
        return cls(
            key=str(value.get("key", value.get("name_en", "UNKNOWN"))).strip().lower().replace(" ", "_"),
            category=str(value.get("category", "Market Intelligence")).strip() or "Market Intelligence",
            icon=marker.icon,
            status=marker.status,
            status_label_en=marker.label_en,
            status_label_th=marker.label_th,
            name_en=str(value.get("name_en", "Unnamed Intelligence")).strip(),
            name_th=str(value.get("name_th", "ระบบวิเคราะห์")).strip(),
            function_en=str(value.get("function_en", "Analyze market evidence.")).strip(),
            function_th=str(value.get("function_th", "วิเคราะห์ข้อมูลตลาด")).strip(),
            explanation_en=str(value.get("explanation_en", "Summarizes evidence for dashboard review.")).strip(),
            explanation_th=str(value.get("explanation_th", "สรุปข้อมูลเพื่อให้ตรวจสอบบน Dashboard")).strip(),
            input_summary=str(value.get("input_summary", "Market data")).strip(),
            output_summary=str(value.get("output_summary", "Direction, confidence, reason")).strip(),
            confidence=confidence,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "category": self.category,
            "icon": self.icon,
            "status": self.status,
            "status_label_en": self.status_label_en,
            "status_label_th": self.status_label_th,
            "name_en": self.name_en,
            "name_th": self.name_th,
            "function_en": self.function_en,
            "function_th": self.function_th,
            "explanation_en": self.explanation_en,
            "explanation_th": self.explanation_th,
            "input_summary": self.input_summary,
            "output_summary": self.output_summary,
            "confidence": self.confidence,
        }


def default_intelligence_catalog(records: Iterable[Mapping[str, Any]] | None = None) -> list[IntelligenceCard]:
    """Return dashboard cards ordered by category then English name."""
    source = list(records) if records is not None else _DEFAULT_INTELLIGENCE
    cards = [IntelligenceCard.from_mapping(item) for item in source]
    return sorted(cards, key=lambda item: (item.category, item.name_en))


def _ratio(value: Any) -> float:
    number = float(value)
    if number > 1.0:
        number = number / 100.0
    return round(min(max(number, 0.0), 1.0), 6)


_DEFAULT_INTELLIGENCE: tuple[dict[str, Any], ...] = (
    {
        "key": "market_data_intelligence",
        "category": "Data Intelligence",
        "name_en": "Market Data Intelligence",
        "name_th": "ระบบข้อมูลตลาด",
        "function_en": "Validate market data readiness before analysis.",
        "function_th": "ตรวจความพร้อมของข้อมูลตลาดก่อนการวิเคราะห์",
        "explanation_en": "Checks OHLC source, primary timeframe, and data availability.",
        "explanation_th": "ตรวจแหล่งข้อมูล OHLC, Timeframe หลัก และความพร้อมของข้อมูล",
        "input_summary": "MT5 OHLC, symbol, timeframe",
        "output_summary": "READY / REVIEW with source reason",
        "confidence": 1.0,
    },
    {
        "key": "multi_timeframe_confluence",
        "category": "Market Intelligence",
        "name_en": "Multi-Timeframe Confluence Intelligence",
        "name_th": "ระบบวิเคราะห์หลาย Timeframe",
        "function_en": "Compare directional alignment across timeframes.",
        "function_th": "เปรียบเทียบทิศทางจากหลาย Timeframe",
        "explanation_en": "Highlights whether short and higher timeframes support the same market direction.",
        "explanation_th": "แสดงว่า Timeframe สั้นและยาวสนับสนุนทิศทางเดียวกันหรือไม่",
        "input_summary": "M1, M5, M15, H1, H4, D1",
        "output_summary": "Direction, aligned timeframes, confidence",
        "confidence": 0.92,
    },
    {
        "key": "market_structure",
        "category": "Market Intelligence",
        "name_en": "Market Structure Intelligence",
        "name_th": "ระบบวิเคราะห์โครงสร้างตลาด",
        "function_en": "Classify structure before signal review.",
        "function_th": "จำแนกโครงสร้างตลาดก่อนพิจารณาสัญญาณ",
        "explanation_en": "Evaluates higher highs, lower lows, and balanced structure.",
        "explanation_th": "ตรวจ Higher High, Lower Low และโครงสร้างสมดุล",
        "input_summary": "Swing points, OHLC sequence",
        "output_summary": "BUY / SELL / FLAT with reason",
        "confidence": 0.86,
    },
    {
        "key": "liquidity_intelligence",
        "category": "Liquidity Intelligence",
        "name_en": "Liquidity Intelligence",
        "name_th": "ระบบวิเคราะห์สภาพคล่อง",
        "function_en": "Evaluate liquidity pools and sweep context.",
        "function_th": "วิเคราะห์แหล่งสภาพคล่องและบริบทการกวาดสภาพคล่อง",
        "explanation_en": "Shows whether liquidity evidence supports, warns, or remains balanced.",
        "explanation_th": "แสดงว่าสภาพคล่องสนับสนุน เตือน หรือยังสมดุล",
        "input_summary": "Highs, lows, equal levels, sweep state",
        "output_summary": "Liquidity bias, sweep status, confidence",
        "confidence": 0.74,
    },
    {
        "key": "fair_value_gap",
        "category": "Institutional Intelligence",
        "name_en": "Fair Value Gap Intelligence",
        "name_th": "ระบบวิเคราะห์ช่องว่างมูลค่ายุติธรรม",
        "function_en": "Detect fair value gap evidence.",
        "function_th": "ตรวจหลักฐานช่องว่างมูลค่ายุติธรรม",
        "explanation_en": "Reports active imbalance zones that may influence market behavior.",
        "explanation_th": "รายงานโซนความไม่สมดุลที่อาจมีผลต่อพฤติกรรมราคา",
        "input_summary": "Candle displacement, gap structure",
        "output_summary": "Active / inactive evidence and direction",
        "confidence": 0.88,
    },
    {
        "key": "order_block",
        "category": "Institutional Intelligence",
        "name_en": "Order Block Intelligence",
        "name_th": "ระบบวิเคราะห์โซนคำสั่งราคา",
        "function_en": "Identify order block evidence.",
        "function_th": "ระบุหลักฐานโซนคำสั่งราคา",
        "explanation_en": "Summarizes whether order block context supports a directional decision.",
        "explanation_th": "สรุปว่าโซนคำสั่งราคาสนับสนุนทิศทางใดหรือไม่",
        "input_summary": "Structure break, origin candle, price reaction",
        "output_summary": "Order block status and confidence",
        "confidence": 0.84,
    },
    {
        "key": "smart_money_concept",
        "category": "Institutional Intelligence",
        "name_en": "Smart Money Concept Intelligence",
        "name_th": "ระบบวิเคราะห์พฤติกรรมเงินทุนหลัก",
        "function_en": "Aggregate institutional-style context.",
        "function_th": "รวบรวมบริบทพฤติกรรมเงินทุนหลัก",
        "explanation_en": "Combines structure, liquidity, and displacement evidence for dashboard review.",
        "explanation_th": "รวมข้อมูลโครงสร้าง สภาพคล่อง และแรงเคลื่อนราคาเพื่อการตรวจสอบ",
        "input_summary": "Structure, liquidity, displacement",
        "output_summary": "Institutional bias and confidence",
        "confidence": 0.9,
    },
    {
        "key": "risk_intelligence",
        "category": "Risk Intelligence",
        "name_en": "Risk Intelligence",
        "name_th": "ระบบบริหารความเสี่ยง",
        "function_en": "Check whether a decision is allowed by risk rules.",
        "function_th": "ตรวจว่าการตัดสินใจผ่านเงื่อนไขความเสี่ยงหรือไม่",
        "explanation_en": "Keeps execution controlled by margin, size, drawdown, and safety limits.",
        "explanation_th": "ควบคุมการทำงานด้วย Margin, ขนาดออเดอร์, Drawdown และขอบเขตความปลอดภัย",
        "input_summary": "Account, margin, drawdown, proposed lot",
        "output_summary": "Allowed flag and risk reasons",
        "confidence": 1.0,
    },
    {
        "key": "trading_cost_intelligence",
        "category": "Risk Intelligence",
        "name_en": "Trading Cost Intelligence",
        "name_th": "ระบบตรวจต้นทุนการเทรด",
        "function_en": "Evaluate spread and trading cost conditions.",
        "function_th": "ตรวจ Spread และต้นทุนการเทรด",
        "explanation_en": "Warns when spread is near or above the configured cost limit.",
        "explanation_th": "เตือนเมื่อ Spread ใกล้หรือเกินขอบเขตต้นทุนที่กำหนด",
        "input_summary": "Spread, cost limit, symbol",
        "output_summary": "PASS / CAUTION / BLOCKED",
        "confidence": 1.0,
    },
)
