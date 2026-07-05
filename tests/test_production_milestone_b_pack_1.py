"""Tests for AFIP Production Milestone B Pack 1."""

from afip.fusion.intelligence_conflict_resolution import IntelligenceConflictResolution
from afip.fusion.intelligence_fusion_core import IntelligenceFusionCore
from afip.fusion.intelligence_priority_matrix import IntelligencePriorityMatrix
from afip.fusion.intelligence_score_fusion import IntelligenceScoreFusion
from afip.runtime.production_milestone_b_fusion_runtime import ProductionMilestoneBFusionRuntime


def test_intelligence_score_fusion_accepts_weighted_buy_direction() -> None:
    result = IntelligenceScoreFusion().fuse(
        [
            {"direction": "BUY", "confidence": 0.92, "weight": 0.34},
            {"direction": "BUY", "confidence": 0.86, "weight": 0.28},
            {"direction": "SELL", "confidence": 0.40, "weight": 0.10},
            {"direction": "FLAT", "confidence": 0.30, "weight": 0.08},
        ]
    )
    assert result.status == "FUSION_SCORE_READY"
    assert result.action == "ACCEPT_FUSED_FINANCIAL_DIRECTION"
    assert result.direction == "BUY"
    assert result.confidence >= 70.0


def test_intelligence_score_fusion_keeps_simulation_when_empty() -> None:
    result = IntelligenceScoreFusion().fuse([])
    assert result.status == "FUSION_INPUT_EMPTY"
    assert result.action == "KEEP_SIMULATION_ONLY"
    assert result.direction == "FLAT"


def test_intelligence_priority_matrix_ready_status() -> None:
    result = IntelligencePriorityMatrix().evaluate(
        {
            "market": 0.91,
            "risk": 0.88,
            "execution": 0.86,
            "portfolio": 0.84,
            "learning": 0.82,
        }
    )
    assert result.status == "PRIORITY_MATRIX_READY"
    assert result.action == "ACCEPT_PRIORITY_ALLOCATION"
    assert result.priority_score >= 78.0


def test_intelligence_priority_matrix_not_ready_when_inputs_are_low() -> None:
    result = IntelligencePriorityMatrix().evaluate(
        {
            "market": 0.25,
            "risk": 0.28,
            "execution": 0.22,
            "portfolio": 0.20,
            "learning": 0.18,
        }
    )
    assert result.status == "PRIORITY_MATRIX_NOT_READY"
    assert result.action == "KEEP_SIMULATION_ONLY"


def test_intelligence_conflict_resolution_resolves_dominant_priority() -> None:
    result = IntelligenceConflictResolution().resolve(
        [
            {"direction": "BUY", "confidence": 0.93, "priority": 0.95},
            {"direction": "BUY", "confidence": 0.88, "priority": 0.80},
            {"direction": "SELL", "confidence": 0.62, "priority": 0.30},
        ]
    )
    assert result.status == "CONFLICT_RESOLVED"
    assert result.action == "ACCEPT_RESOLVED_FINANCIAL_DIRECTION"
    assert result.resolved_direction == "BUY"


def test_intelligence_conflict_resolution_blocks_high_conflict() -> None:
    result = IntelligenceConflictResolution().resolve(
        [
            {"direction": "BUY", "confidence": 0.92, "priority": 0.90},
            {"direction": "SELL", "confidence": 0.91, "priority": 0.90},
        ]
    )
    assert result.status == "CONFLICT_HIGH"
    assert result.action == "KEEP_SIMULATION_ONLY"
    assert result.resolved_direction == "FLAT"


def test_intelligence_fusion_core_returns_unified_direction() -> None:
    result = IntelligenceFusionCore().evaluate(
        signals=[
            {"direction": "BUY", "confidence": 0.94, "weight": 0.35, "priority": 0.95},
            {"direction": "BUY", "confidence": 0.88, "weight": 0.30, "priority": 0.86},
            {"direction": "SELL", "confidence": 0.42, "weight": 0.05, "priority": 0.20},
        ],
        priority_metrics={
            "market": 0.92,
            "risk": 0.88,
            "execution": 0.86,
            "portfolio": 0.84,
            "learning": 0.82,
        },
    )
    assert result.status == "UNIFIED_INTELLIGENCE_READY"
    assert result.action == "ACCEPT_UNIFIED_FINANCIAL_DIRECTION"
    assert result.direction == "BUY"
    assert result.confidence >= 74.0


def test_production_milestone_b_fusion_runtime_preserves_simulation_mode() -> None:
    result = ProductionMilestoneBFusionRuntime().evaluate(
        signals=[
            {"direction": "BUY", "confidence": 0.94, "weight": 0.35, "priority": 0.95},
            {"direction": "BUY", "confidence": 0.88, "weight": 0.30, "priority": 0.86},
            {"direction": "SELL", "confidence": 0.42, "weight": 0.05, "priority": 0.20},
        ],
        priority_metrics={
            "market": 0.92,
            "risk": 0.88,
            "execution": 0.86,
            "portfolio": 0.84,
            "learning": 0.82,
        },
    )
    assert result.status == "MILESTONE_B_FUSION_READY"
    assert result.action == "PREPARE_SIMULATION_ORDER_REVIEW"
    assert result.execution_mode == "LOCKED_SIMULATION_ONLY"
