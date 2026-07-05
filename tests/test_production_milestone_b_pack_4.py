from __future__ import annotations

from afip.fusion.confidence_reconciliation import ConfidenceReconciliation
from afip.fusion.conflict_priority_resolver import ConflictPriorityResolver
from afip.fusion.intelligence_conflict_analyzer import IntelligenceConflictAnalyzer
from afip.fusion.intelligence_consensus_engine import IntelligenceConsensusEngine
from afip.runtime.production_milestone_b_conflict_runtime import ProductionMilestoneBConflictRuntime


def test_conflict_analyzer_detects_low_conflict_buy_alignment() -> None:
    result = IntelligenceConflictAnalyzer().analyze(
        [
            {"direction": "BUY", "confidence": 0.90, "weight": 0.35},
            {"direction": "BUY", "confidence": 0.82, "weight": 0.30},
            {"direction": "SELL", "confidence": 0.24, "weight": 0.08},
        ]
    )
    assert result.status == "CONFLICT_ANALYSIS_READY"
    assert result.dominant_direction == "BUY"
    assert result.conflict_level == "LOW"


def test_conflict_analyzer_detects_high_conflict_pressure() -> None:
    result = IntelligenceConflictAnalyzer().analyze(
        [
            {"direction": "BUY", "confidence": 0.91, "weight": 0.35},
            {"direction": "SELL", "confidence": 0.88, "weight": 0.34},
        ]
    )
    assert result.conflict_level == "HIGH"
    assert result.conflict_ratio >= 0.42


def test_consensus_engine_reports_high_consensus() -> None:
    result = IntelligenceConsensusEngine().evaluate(
        [
            {"direction": "BUY", "confidence": 0.88, "weight": 0.30},
            {"direction": "BUY", "confidence": 0.86, "weight": 0.28},
            {"direction": "BUY", "confidence": 0.80, "weight": 0.22},
            {"direction": "FLAT", "confidence": 0.20, "weight": 0.05},
        ]
    )
    assert result.status == "CONSENSUS_READY"
    assert result.consensus_level == "HIGH"
    assert result.consensus_direction == "BUY"


def test_consensus_engine_handles_empty_inputs() -> None:
    result = IntelligenceConsensusEngine().evaluate([])
    assert result.consensus_direction == "FLAT"
    assert result.participation_count == 0


def test_priority_resolver_accepts_risk_priority_wait() -> None:
    result = ConflictPriorityResolver().resolve(
        [
            {"category": "TREND", "direction": "BUY", "confidence": 0.80, "weight": 0.20},
            {"category": "RISK", "direction": "FLAT", "confidence": 0.95, "weight": 0.45},
            {"category": "EXECUTION", "direction": "FLAT", "confidence": 0.75, "weight": 0.25},
        ]
    )
    assert result.status == "CONFLICT_PRIORITY_READY"
    assert result.resolution_action == "WAIT"
    assert result.priority_category == "RISK"


def test_priority_resolver_accepts_dominant_direction() -> None:
    result = ConflictPriorityResolver().resolve(
        [
            {"category": "TREND", "direction": "SELL", "confidence": 0.87, "weight": 0.32},
            {"category": "MARKET_STRUCTURE", "direction": "SELL", "confidence": 0.90, "weight": 0.30},
            {"category": "MOMENTUM", "direction": "BUY", "confidence": 0.35, "weight": 0.10},
        ]
    )
    assert result.resolution_action == "SELL"
    assert result.priority_score >= 0.58


def test_confidence_reconciliation_adjusts_for_conflict() -> None:
    result = ConfidenceReconciliation().reconcile(
        [
            {"category": "TREND", "direction": "BUY", "confidence": 0.92, "weight": 0.32},
            {"category": "LIQUIDITY", "direction": "SELL", "confidence": 0.90, "weight": 0.30},
            {"category": "RISK", "direction": "FLAT", "confidence": 0.50, "weight": 0.12},
        ]
    )
    assert result.status == "CONFIDENCE_RECONCILIATION_READY"
    assert result.decision_quality in {"REVIEW", "MODERATE"}
    assert result.reconciled_confidence <= 0.72


def test_milestone_b_conflict_runtime_produces_decision_profile() -> None:
    result = ProductionMilestoneBConflictRuntime().run()
    assert result.status == "MILESTONE_B_CONFLICT_RUNTIME_READY"
    assert result.action in {"BUY", "SELL", "WAIT", "FLAT"}
    assert result.confidence >= 0.0
    assert result.priority_category
