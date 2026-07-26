from afip.dashboard_ui.home import render_dashboard_home


def test_workspace_is_fixed_viewport_and_iframe_owns_page_scroll():
    html = render_dashboard_home()
    assert '.workspace{display:grid;grid-template-rows:58px minmax(0,1fr)' in html
    assert '.frame-wrap{position:relative;background:#fff;overflow:hidden;min-height:0;height:100%}' in html
    assert 'scrolling="yes"' in html
    assert 'height:calc(100vh - 58px)' not in html


def test_sidebar_can_scroll_to_last_menu_item():
    html = render_dashboard_home()
    assert 'height:100vh;overflow-x:hidden;overflow-y:auto' in html
    assert 'padding-bottom:140px' in html
