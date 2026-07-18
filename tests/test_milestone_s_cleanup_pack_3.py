from tools import afip_cleanup_pack_3_source_evidence as evidence


def test_target_set_contains_execution_path():
    assert "afip/demo_execution_gateway/runtime.py" in evidence.TARGETS
    assert "afip/unit_allocation/runtime.py" in evidence.TARGETS
    assert "afip/protection/sl_tp_planner.py" in evidence.TARGETS


def test_keywords_cover_known_failure():
    assert "allocated_units" in evidence.KEYWORDS
    assert "maximum_units" in evidence.KEYWORDS
    assert "sl_points" in evidence.KEYWORDS
    assert "tp_points" in evidence.KEYWORDS
    assert "atr" in evidence.KEYWORDS
