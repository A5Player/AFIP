from __future__ import annotations
from dataclasses import asdict, dataclass
from math import sqrt
from typing import Any, Iterable, Mapping, Sequence

CONTRACT_VERSION = "AFIP-W2-CONTEXT-1.0"

class ContextValidationError(ValueError):
    pass

def _norm_text(value: Any) -> str:
    return str(value or "").strip().upper()

def _clamp_score(value: float) -> float:
    return round(max(0.0, min(100.0, float(value))), 4)

def _numeric_similarity(a: float, b: float, scale: float) -> float:
    if scale <= 0:
        raise ContextValidationError("numeric_scale_must_be_positive")
    return _clamp_score(100.0 * max(0.0, 1.0 - abs(float(a)-float(b))/scale))

def _categorical_similarity(a: Any, b: Any) -> float:
    return 100.0 if _norm_text(a) == _norm_text(b) and _norm_text(a) else 0.0

@dataclass(frozen=True)
class MarketContextSnapshot:
    context_id: str
    symbol: str
    observed_at_utc: str
    timeframe: str
    pattern_family: str
    pattern_variant: str
    market_regime: str
    volatility_class: str
    session: str
    trend_state: str
    momentum_state: str
    liquidity_state: str
    atr_points: float
    spread_points: float
    trend_strength: float
    timeframe_alignment: float
    source_ids: tuple[str, ...]
    contract_version: str = CONTRACT_VERSION
    execution_authority: bool = False
    order_send_called: bool = False

    def validate(self) -> None:
        if not self.context_id.strip(): raise ContextValidationError("context_id_required")
        if not self.symbol.strip(): raise ContextValidationError("symbol_required")
        if not self.timeframe.strip(): raise ContextValidationError("timeframe_required")
        if self.atr_points < 0 or self.spread_points < 0: raise ContextValidationError("negative_market_measurement")
        if not 0 <= self.trend_strength <= 100: raise ContextValidationError("trend_strength_out_of_range")
        if not 0 <= self.timeframe_alignment <= 100: raise ContextValidationError("timeframe_alignment_out_of_range")
        if not self.source_ids: raise ContextValidationError("source_ids_required")
        if self.execution_authority: raise ContextValidationError("context_execution_authority_forbidden")
        if self.order_send_called: raise ContextValidationError("context_order_send_forbidden")

    def as_dict(self) -> dict[str, Any]:
        self.validate(); return asdict(self)

    def fingerprint(self) -> str:
        self.validate()
        parts=(self.symbol,self.timeframe,self.pattern_family,self.pattern_variant,self.market_regime,
               self.volatility_class,self.session,self.trend_state,self.momentum_state,self.liquidity_state)
        return "|".join(_norm_text(p) for p in parts)

@dataclass(frozen=True)
class ContextMatch:
    historical_context_id: str
    similarity_score: float
    component_scores: Mapping[str, float]
    evidence_quality: str
    sample_size: int
    outcome: str
    historical_mae_points: float
    historical_mfe_points: float
    research_optimal_sl_points: int
    metadata: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]: return asdict(self)

DEFAULT_WEIGHTS={
    "pattern_family":0.16,"pattern_variant":0.08,"market_regime":0.14,"volatility_class":0.08,
    "session":0.06,"trend_state":0.10,"momentum_state":0.08,"liquidity_state":0.05,
    "atr_points":0.08,"spread_points":0.04,"trend_strength":0.07,"timeframe_alignment":0.06,
}

class ContextMatchingEngine:
    """Evidence-only historical context matcher. It cannot create trading decisions or orders."""
    def __init__(self, weights: Mapping[str,float]|None=None) -> None:
        self.weights=dict(weights or DEFAULT_WEIGHTS)
        if abs(sum(self.weights.values())-1.0)>1e-9: raise ContextValidationError("weights_must_sum_to_one")

    def compare(self, current: MarketContextSnapshot, historical: Mapping[str,Any]) -> ContextMatch:
        current.validate()
        components={
          "pattern_family":_categorical_similarity(current.pattern_family,historical.get("pattern_family")),
          "pattern_variant":_categorical_similarity(current.pattern_variant,historical.get("pattern_variant")),
          "market_regime":_categorical_similarity(current.market_regime,historical.get("market_regime")),
          "volatility_class":_categorical_similarity(current.volatility_class,historical.get("volatility_class")),
          "session":_categorical_similarity(current.session,historical.get("session")),
          "trend_state":_categorical_similarity(current.trend_state,historical.get("trend_state")),
          "momentum_state":_categorical_similarity(current.momentum_state,historical.get("momentum_state")),
          "liquidity_state":_categorical_similarity(current.liquidity_state,historical.get("liquidity_state")),
          "atr_points":_numeric_similarity(current.atr_points,float(historical.get("atr_points",0)),max(500.0,current.atr_points,1.0)),
          "spread_points":_numeric_similarity(current.spread_points,float(historical.get("spread_points",0)),max(50.0,current.spread_points,1.0)),
          "trend_strength":_numeric_similarity(current.trend_strength,float(historical.get("trend_strength",0)),100.0),
          "timeframe_alignment":_numeric_similarity(current.timeframe_alignment,float(historical.get("timeframe_alignment",0)),100.0),
        }
        score=_clamp_score(sum(components[k]*self.weights[k] for k in self.weights))
        return ContextMatch(
          historical_context_id=str(historical.get("context_id") or historical.get("opportunity_id") or "UNKNOWN"),
          similarity_score=score,component_scores=components,
          evidence_quality=_norm_text(historical.get("evidence_quality") or "UNKNOWN"),
          sample_size=int(historical.get("sample_size",0)),outcome=_norm_text(historical.get("outcome") or "UNKNOWN"),
          historical_mae_points=float(historical.get("historical_mae_points",0)),
          historical_mfe_points=float(historical.get("historical_mfe_points",0)),
          research_optimal_sl_points=int(historical.get("research_optimal_sl_points",0)),
          metadata={"contract_version":CONTRACT_VERSION,"execution_authority":False,"order_send_called":False})

    def rank(self,current:MarketContextSnapshot,historical_records:Iterable[Mapping[str,Any]],limit:int=100)->tuple[ContextMatch,...]:
        if limit not in {100,500,1000}: raise ContextValidationError("supported_limits_are_100_500_1000")
        matches=[self.compare(current,r) for r in historical_records]
        matches.sort(key=lambda m:(m.similarity_score,m.sample_size),reverse=True)
        return tuple(matches[:limit])
