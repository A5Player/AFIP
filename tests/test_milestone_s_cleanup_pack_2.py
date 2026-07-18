from tools import afip_architecture_responsibility_matrix as matrix


def test_preferred_owner_registry_is_explicit():
    assert matrix.PREFERRED_OWNER_PATHS["ORDER_SEND"] == (
        "afip/demo_execution_gateway/runtime.py"
    )
    assert matrix.PREFERRED_OWNER_PATHS["UNIT_ALLOCATION"] == (
        "afip/unit_allocation/runtime.py"
    )
    assert matrix.PREFERRED_OWNER_PATHS["PROTECTION_PLAN"] == (
        "afip/protection/sl_tp_planner.py"
    )


def test_paper_component_is_not_primary():
    classification, reasons = matrix._classify(
        "UNIT_ALLOCATION",
        "afip/paper_trading/paper_runtime.py",
        "afip/unit_allocation/runtime.py",
        {},
    )
    assert classification == "RESEARCH_OR_SIMULATION"
    assert "non_live_execution_namespace" in reasons


def test_dashboard_component_is_observer():
    classification, _ = matrix._classify(
        "POSITION_SIZING",
        "afip/dashboard_ui/runtime.py",
        "afip/adaptive_position_sizing/runtime.py",
        {},
    )
    assert classification == "OBSERVER_OR_MODEL"


def test_safety_component_is_guard():
    classification, _ = matrix._classify(
        "PROTECTION_PLAN",
        "afip/execution_safety/capital_aware_protection_guard.py",
        "afip/protection/sl_tp_planner.py",
        {},
    )
    assert classification == "SAFETY_GUARD"
