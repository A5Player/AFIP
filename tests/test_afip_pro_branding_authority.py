from __future__ import annotations

from pathlib import Path

from afip.branding import CONTROL_CENTER_NAME, PRODUCT_NAME, display_name
from afip.dashboard_ui.control_center import render_control_center


def test_branding_authority_is_afip_pro() -> None:
    assert PRODUCT_NAME == "AFIP Pro"
    assert CONTROL_CENTER_NAME == "AFIP Pro Control Center"
    assert display_name() == "AFIP Pro"
    assert display_name("Runtime") == "AFIP Pro Runtime"


def test_control_center_uses_canonical_brand(tmp_path: Path) -> None:
    html = render_control_center(tmp_path)
    assert "AFIP Pro Control Center" in html
    assert "AFIP V1 Control Center" not in html


def test_home_source_does_not_use_legacy_display_brand() -> None:
    source = Path("afip/dashboard_ui/home.py").read_text(encoding="utf-8")
    assert "AFIP Gold" not in source
    assert "AFIP · COMMAND CENTER" not in source
    assert "PRODUCT_NAME" in source
    assert "CONTROL_CENTER_NAME" in source
