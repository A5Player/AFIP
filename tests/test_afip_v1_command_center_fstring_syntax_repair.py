from pathlib import Path

from afip.dashboard_ui.home import render_dashboard_home


def test_command_center_home_renders_after_scroll_repair():
    html = render_dashboard_home()
    assert 'AFIP Command Center' in html
    assert 'scrolling="yes"' in html
    assert 'function resizeFrame()' not in html


def test_home_module_compiles_without_fstring_brace_error():
    compile(Path('afip/dashboard_ui/home.py').read_text(encoding='utf-8'), 'home.py', 'exec')
