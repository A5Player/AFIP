"""Dashboard-ready macro market reporting for AFIP."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class MacroDashboardComponent:
    """One normalized component row for a macro market dashboard."""

    name: str
    status: str
    score: float
    bias: str
    detail: str

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "score": self.score,
            "bias": self.bias,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class MacroMarketDashboard:
    """Compact report payload for macro-aware financial runtime displays."""

    status: str
    headline: str
    summary_line: str
    exposure_instruction: str
    gold_market_bias: str
    decision_confidence: float
    macro_score: float
    position_horizon: str
    event_risk_state: str
    conflict_level: str
    component_rows: Sequence[MacroDashboardComponent]
    key_risks: Sequence[str]
    report_lines: Sequence[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "headline": self.headline,
            "summary_line": self.summary_line,
            "exposure_instruction": self.exposure_instruction,
            "gold_market_bias": self.gold_market_bias,
            "decision_confidence": self.decision_confidence,
            "macro_score": self.macro_score,
            "position_horizon": self.position_horizon,
            "event_risk_state": self.event_risk_state,
            "conflict_level": self.conflict_level,
            "component_rows": [row.as_dict() for row in self.component_rows],
            "key_risks": list(self.key_risks),
            "report_lines": list(self.report_lines),
        }


class MacroMarketDashboardBuilder:
    """Build dashboard-ready reporting from the integrated macro consensus runtime state."""

    def build(self, runtime_state: Mapping[str, object]) -> MacroMarketDashboard:
        consensus = self._mapping(runtime_state.get("consensus"))
        profile = self._mapping(runtime_state.get("decision_profile"))
        calendar_state = self._mapping(runtime_state.get("calendar_state"))
        news_state = self._mapping(runtime_state.get("news_state"))
        market_factor_state = self._mapping(runtime_state.get("market_factor_state"))

        macro_score = self._to_float(consensus.get("macro_score"), 0.0)
        decision_confidence = self._to_float(consensus.get("decision_confidence"), 0.0)
        gold_market_bias = str(consensus.get("gold_market_bias", "NEUTRAL"))
        exposure_instruction = str(profile.get("exposure_instruction", "REVIEW_ONLY"))
        position_horizon = str(profile.get("position_horizon", "INTRADAY_REVIEW"))
        event_risk_state = str(consensus.get("event_risk_state", calendar_state.get("event_risk_state", "CLEAR")))
        conflict_level = str(consensus.get("conflict_level", "MEDIUM"))

        headline = self._headline(exposure_instruction, gold_market_bias, decision_confidence)
        summary_line = (
            f"Macro Score {macro_score:.2f} | Bias {gold_market_bias} | "
            f"Instruction {exposure_instruction} | Confidence {decision_confidence:.2f}"
        )
        component_rows = self._component_rows(consensus, calendar_state, news_state, market_factor_state)
        key_risks = self._key_risks(event_risk_state, conflict_level, news_state, market_factor_state)
        report_lines = self._report_lines(headline, summary_line, component_rows, key_risks, position_horizon)

        return MacroMarketDashboard(
            status="MACRO_MARKET_DASHBOARD_READY",
            headline=headline,
            summary_line=summary_line,
            exposure_instruction=exposure_instruction,
            gold_market_bias=gold_market_bias,
            decision_confidence=round(decision_confidence, 2),
            macro_score=round(macro_score, 2),
            position_horizon=position_horizon,
            event_risk_state=event_risk_state,
            conflict_level=conflict_level,
            component_rows=component_rows,
            key_risks=key_risks,
            report_lines=report_lines,
        )

    def build_dict(self, runtime_state: Mapping[str, object]) -> dict[str, object]:
        return self.build(runtime_state).as_dict()

    def _component_rows(
        self,
        consensus: Mapping[str, object],
        calendar_state: Mapping[str, object],
        news_state: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> tuple[MacroDashboardComponent, ...]:
        component_scores = self._mapping(consensus.get("component_scores"))
        calendar_detail = str(calendar_state.get("next_event", calendar_state.get("reason", "calendar_clear")))
        news_detail = str(news_state.get("reason", "news_balanced"))
        factor_detail = str(market_factor_state.get("reason", "market_factors_balanced"))
        market_bias_state = self._mapping(market_factor_state.get("gold_market_bias"))
        factor_bias = str(market_bias_state.get("bias", market_factor_state.get("gold_bias", "NEUTRAL")))

        return (
            MacroDashboardComponent(
                name="Economic Calendar",
                status=str(calendar_state.get("status", "READY")),
                score=round(self._to_float(component_scores.get("calendar"), 0.0), 2),
                bias=str(consensus.get("event_risk_state", "CLEAR")),
                detail=calendar_detail,
            ),
            MacroDashboardComponent(
                name="Macro News",
                status=str(news_state.get("status", "READY")),
                score=round(self._to_float(component_scores.get("news"), 0.0), 2),
                bias=str(news_state.get("gold_bias", "NEUTRAL")),
                detail=news_detail,
            ),
            MacroDashboardComponent(
                name="Market Factors",
                status=str(market_factor_state.get("status", "READY")),
                score=round(self._to_float(component_scores.get("market_factors"), 0.0), 2),
                bias=factor_bias,
                detail=factor_detail,
            ),
        )

    def _key_risks(
        self,
        event_risk_state: str,
        conflict_level: str,
        news_state: Mapping[str, object],
        market_factor_state: Mapping[str, object],
    ) -> tuple[str, ...]:
        risks: list[str] = []
        if event_risk_state == "RESTRICTED":
            risks.append("high_impact_calendar_window")
        elif event_risk_state == "ELEVATED":
            risks.append("elevated_calendar_risk")
        if conflict_level in {"HIGH", "CALENDAR_RESTRICTED"}:
            risks.append("macro_input_conflict")
        if str(news_state.get("gold_bias", "NEUTRAL")) == "MIXED":
            risks.append("mixed_macro_news")
        if str(market_factor_state.get("data_quality", "READY")) == "REVIEW":
            risks.append("market_factor_quality_review")
        if not risks:
            risks.append("standard_macro_review")
        return tuple(risks)

    def _report_lines(
        self,
        headline: str,
        summary_line: str,
        component_rows: Sequence[MacroDashboardComponent],
        key_risks: Sequence[str],
        position_horizon: str,
    ) -> tuple[str, ...]:
        lines = [headline, summary_line, f"Position Horizon: {position_horizon}"]
        lines.extend(f"{row.name}: {row.score:.2f} | {row.bias} | {row.detail}" for row in component_rows)
        lines.append("Key Risks: " + ", ".join(key_risks))
        return tuple(lines)

    @staticmethod
    def _headline(exposure_instruction: str, gold_market_bias: str, decision_confidence: float) -> str:
        if exposure_instruction == "NO_NEW_EXPOSURE":
            return "Macro dashboard recommends no new exposure"
        if exposure_instruction == "REVIEW_ONLY":
            return "Macro dashboard recommends financial review"
        return f"Macro dashboard supports {gold_market_bias.lower()} exposure with {decision_confidence:.2f} confidence"

    @staticmethod
    def _mapping(value: object) -> Mapping[str, object]:
        if isinstance(value, Mapping):
            return value
        return {}

    @staticmethod
    def _to_float(value: object, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
