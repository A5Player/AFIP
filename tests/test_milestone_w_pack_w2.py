from pathlib import Path
import json
import pytest
from afip.context_matching import ContextMatchingEngine, ContextValidationError, MarketContextSnapshot

def snap(**changes):
 d=dict(context_id="CTX-NOW",symbol="GOLD#",observed_at_utc="2026-07-30T00:00:00Z",timeframe="M15",pattern_family="BREAKOUT_RETEST",pattern_variant="V1",market_regime="TREND",volatility_class="NORMAL",session="LONDON",trend_state="BULLISH",momentum_state="STRONG",liquidity_state="NORMAL",atr_points=720,spread_points=28,trend_strength=84,timeframe_alignment=91,source_ids=("BAR-1",)); d.update(changes); return MarketContextSnapshot(**d)

def historical(context_id, **changes):
 d=dict(context_id=context_id,pattern_family="BREAKOUT_RETEST",pattern_variant="V1",market_regime="TREND",volatility_class="NORMAL",session="LONDON",trend_state="BULLISH",momentum_state="STRONG",liquidity_state="NORMAL",atr_points=700,spread_points=30,trend_strength=82,timeframe_alignment=90,evidence_quality="HIGH",sample_size=220,outcome="WIN",historical_mae_points=610,historical_mfe_points=2400,research_optimal_sl_points=780); d.update(changes); return d

def test_fingerprint_is_profile_independent_and_deterministic():
 s=snap(); assert "P1" not in s.fingerprint(); assert s.fingerprint()==snap().fingerprint()

def test_exact_context_ranks_above_different_context():
 e=ContextMatchingEngine(); ranked=e.rank(snap(),[historical("LOW",market_regime="RANGE",pattern_family="REVERSAL"),historical("HIGH")],100)
 assert ranked[0].historical_context_id=="HIGH"; assert ranked[0].similarity_score>ranked[1].similarity_score

def test_supported_top_limits_and_fail_closed_contract():
 e=ContextMatchingEngine(); assert len(e.rank(snap(),[historical("A")],100))==1
 with pytest.raises(ContextValidationError,match="supported_limits"): e.rank(snap(),[],10)

def test_context_matching_cannot_claim_execution_authority():
 with pytest.raises(ContextValidationError,match="context_execution_authority_forbidden"): snap(execution_authority=True).validate()
 with pytest.raises(ContextValidationError,match="context_order_send_forbidden"): snap(order_send_called=True).validate()

def test_contract_file_locks_research_only_authority():
 p=Path(__file__).resolve().parents[1]/"config/context_matching_contract.json"; c=json.loads(p.read_text(encoding="utf-8"))
 assert c["supported_rank_limits"]==[100,500,1000]; assert c["execution_authority"] is False; assert c["decision_authority"] is False
