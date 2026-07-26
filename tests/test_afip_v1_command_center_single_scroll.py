from afip.dashboard_ui.home import render_dashboard_home


def test_command_center_uses_independent_sidebar_and_content_scroll():
    html = render_dashboard_home()
    assert 'html,body{height:100%;margin:0;overflow:hidden}' in html
    assert 'scrolling="yes"' in html
    assert 'iframe{display:block;width:100%;height:100%' in html
    assert 'overflow-y:auto' in html
    assert 'function resizeFrame()' not in html


def test_command_center_keeps_sidebar_bottom_safe_area():
    html = render_dashboard_home()
    assert 'padding-bottom:140px' in html
    assert 'scrollbar-gutter:stable' in html
