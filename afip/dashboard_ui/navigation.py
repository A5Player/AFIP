"""Shared presentation-only navigation for standalone AFIP dashboards."""
from __future__ import annotations
from html import escape

PAGES = (
    ("operations", "📊", "P1–P4 Operations", "afip_profiles_dashboard.html"),
    ("intelligence", "🧠", "Intelligence & Engines", "afip_intelligence_engine_dashboard.html"),
    ("pipeline", "🔗", "Execution Pipeline", "afip_execution_pipeline_dashboard.html"),
    ("orders", "🧾", "Order Evidence", "afip_order_evidence_dashboard.html"),
    ("mt5", "🖥️", "Live MT5", "afip_live_mt5_dashboard.html"),
    ("research", "🔬", "Research & Data", "afip_research_data_dashboard.html"),
    ("loading", "📡", "Research Operations", "afip_research_operations_dashboard.html"),
    ("observability", "🔎", "Research Observability", "afip_research_observability_dashboard.html"),
    ("control", "🎛️", "Control Center", "afip_control_center.html"),
    ("home", "🏠", "Dashboard Home", "afip_dashboard.html"),
)


def standalone_navigation(active: str) -> str:
    links = "".join(
        f'<a class="afip-side-link{" active" if page_id == active else ""}" href="{escape(filename)}">'
        f'<span>{icon}</span><strong>{escape(label)}</strong></a>'
        for page_id, icon, label, filename in PAGES
    )
    return (
        '<aside class="afip-standalone-sidebar" id="afipStandaloneSidebar">'
        '<div class="afip-side-brand"><b>AFIP Pro</b><small>Dashboard Navigation</small></div>'
        f'<nav>{links}</nav>'
        '<div class="afip-side-note">Read-only presentation<br>No execution authority</div>'
        '</aside>'
    )


def standalone_navigation_css() -> str:
    return """
.afip-standalone-shell{display:grid;grid-template-columns:238px minmax(0,1fr);min-height:100vh}
.afip-standalone-sidebar{position:sticky;top:0;height:100vh;overflow-y:auto;background:linear-gradient(180deg,#101a2b,#09111e);color:#eef5ff;border-right:1px solid #263850;padding-bottom:90px;z-index:20}
.afip-side-brand{padding:20px 16px 16px;border-bottom:1px solid #263850}.afip-side-brand b{display:block;font-size:18px}.afip-side-brand small{display:block;color:#9fb0c5;margin-top:4px}
.afip-standalone-sidebar nav{display:flex;flex-direction:column;gap:6px;padding:13px 10px}.afip-side-link{display:flex;align-items:center;gap:10px;padding:10px 11px;border:1px solid transparent;border-radius:9px;color:#edf4ff;text-decoration:none;font-size:12px}.afip-side-link:hover{background:#ffffff0b;border-color:#ffffff17}.afip-side-link.active{background:#182b47;border-color:#3c587a;box-shadow:inset 3px 0 0 #5aa3ff}.afip-side-link span{width:22px;text-align:center}.afip-side-note{position:sticky;top:calc(100vh - 80px);padding:12px 15px;border-top:1px solid #263850;color:#91a4bc;font-size:9px;line-height:1.45;background:#09111e}
.afip-standalone-content{min-width:0}.afip-menu-toggle{display:none;position:fixed;left:10px;top:10px;z-index:40;border:1px solid #bdc9d8;background:#fff;border-radius:8px;padding:7px 10px;cursor:pointer}
@media(max-width:900px){.afip-standalone-shell{grid-template-columns:1fr}.afip-standalone-sidebar{position:fixed;left:0;top:0;width:260px;transform:translateX(-100%);transition:transform .18s}.afip-standalone-sidebar.open{transform:translateX(0)}.afip-menu-toggle{display:block}.afip-standalone-content{padding-top:42px}}
html.afip-embedded-root,body.afip-embedded{min-height:100%;height:auto}body.afip-embedded .afip-standalone-shell{display:block;min-height:0}body.afip-embedded .afip-standalone-sidebar,body.afip-embedded .afip-menu-toggle{display:none!important}body.afip-embedded .afip-standalone-content{padding-top:0;min-height:0}
"""


def standalone_navigation_bootstrap() -> str:
    """Apply embedded mode before body paint when a dashboard is inside the home iframe."""
    return """<script>(function(){if(window.self!==window.top){document.documentElement.classList.add('afip-embedded-root');}})();</script>"""


def standalone_navigation_script() -> str:
    return """<script>(function(){function ready(){if(window.self!==window.top){document.documentElement.classList.add('afip-embedded-root');document.body.classList.add('afip-embedded');}var b=document.getElementById('afipMenuToggle'),s=document.getElementById('afipStandaloneSidebar');if(b&&s){b.addEventListener('click',function(){s.classList.toggle('open');});}}if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',ready,{once:true});}else{ready();}})();</script>"""
