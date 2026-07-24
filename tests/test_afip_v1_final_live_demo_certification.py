from __future__ import annotations

import ast
from pathlib import Path


def test_live_certification_is_read_only() -> None:
    path = Path("tools/afip_v1_final_live_demo_certification.py")
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "order_check" not in calls
    assert "order_send" not in calls
    assert '"order_check_called": False' in source
    assert '"order_send_called": False' in source


def test_live_certification_uses_real_isolation_authority() -> None:
    source = Path("tools/afip_v1_final_live_demo_certification.py").read_text(encoding="utf-8")
    assert "from tools.afip_verify_account_isolation import verify" in source
    assert "isolation = verify(CONFIG)" in source
    assert 'PROFILES = ("P1", "P2", "P3", "P4")' in source


def test_live_certification_fails_closed() -> None:
    source = Path("tools/afip_v1_final_live_demo_certification.py").read_text(encoding="utf-8")
    assert '"status": "PASS" if passed else "BLOCKED"' in source
    assert "return 2" in source
