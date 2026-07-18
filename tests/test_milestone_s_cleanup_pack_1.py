from pathlib import Path

from tools import afip_architecture_inventory as inventory


def test_legacy_patterns_are_strict():
    assert inventory.LEGACY_PATTERNS["LEGACY_TP_500"].search("tp_points = 500")
    assert not inventory.LEGACY_PATTERNS["LEGACY_TP_500"].search("history_limit = 500")
    assert inventory.LEGACY_PATTERNS["LEGACY_SL_3000"].search("stop_loss_points: 3000.0")
    assert not inventory.LEGACY_PATTERNS["LEGACY_SL_3000"].search("sample_size = 3000")


def test_forced_units_pattern():
    assert inventory.LEGACY_PATTERNS["FORCED_THREE_UNITS"].search("allocated_units = 3")
    assert not inventory.LEGACY_PATTERNS["FORCED_THREE_UNITS"].search("maximum_units = 3")


def test_infer_responsibility():
    path = Path("afip/unit_allocation/runtime.py")
    assert inventory.infer_responsibility(path, "") == "UNIT_ALLOCATION"


def test_ast_details():
    tree = inventory.parse_ast(
        "import os\n"
        "class Engine: pass\n"
        "def main(): pass\n"
        "def calculate(): pass\n"
    )
    classes, functions, imports, entries = inventory.ast_details(tree)
    assert "Engine" in classes
    assert "main" in functions
    assert "os" in imports
    assert "main" in entries
