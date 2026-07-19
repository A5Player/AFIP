"""AFIP unified dashboard command center.

Presentation-only shell for the three standalone AFIP dashboards.  It does not
start research, connect to MT5, mutate runtime state, or change execution
permission.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

HOME_FILENAME = "afip_dashboard.html"


def render_dashboard_home() -> str:
    """Render a single-window command center around the split dashboards."""
    generated = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    pages = (
        (
            "operations",
            "📊",
            "Operations",
            "P1–P4 Operations",
            "afip_profiles_dashboard.html",
        ),
        (
            "intelligence",
            "🧠",
            "Intelligence",
            "Intelligence & Engines",
            "afip_intelligence_engine_dashboard.html",
        ),
        (
            "research",
            "🔬",
            "Research",
            "Research & Data",
            "afip_research_data_dashboard.html",
        ),
    )
    navigation = "".join(
        f'<button class="nav-item{" active" if index == 0 else ""}" '
        f'data-page="{escape(page_id)}" data-src="{escape(filename)}" '
        f'data-title="{escape(title)}" type="button">'
        f'<span class="nav-icon">{icon}</span>'
        f'<span><strong>{escape(short_title)}</strong><small>{escape(title)}</small></span>'
        f'</button>'
        for index, (page_id, icon, short_title, title, filename) in enumerate(pages)
    )
    page_map = ",".join(
        f'"{escape(page_id)}":{{src:"{escape(filename)}",title:"{escape(title)}"}}'
        for page_id, _icon, _short, title, filename in pages
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AFIP Command Center</title><!-- AFIP Dashboard Home -->
<style>
:root{{font-family:Arial,"Noto Sans Thai",sans-serif;color-scheme:dark;--side:#101a2b;--side2:#16243b;--line:#2c3b53;--text:#edf4ff;--muted:#9aabc1;--accent:#5aa3ff;--canvas:#eef2f7}}
*{{box-sizing:border-box}} html,body{{height:100%;margin:0;overflow:hidden}} body{{background:var(--side);color:var(--text)}}
.shell{{display:grid;grid-template-columns:270px minmax(0,1fr);height:100vh}}
.sidebar{{display:flex;flex-direction:column;background:linear-gradient(180deg,var(--side),#0a1220);border-right:1px solid var(--line);min-width:0}}
.brand{{padding:22px 20px 18px;border-bottom:1px solid var(--line)}} .brand-badge{{display:inline-block;padding:5px 9px;border-radius:999px;background:#1f6f4a;font-size:10px;font-weight:800;letter-spacing:.07em}}
.brand h1{{font-size:20px;margin:12px 0 5px}} .brand p{{font-size:12px;color:var(--muted);margin:0;line-height:1.45}}
.navigation{{display:flex;flex-direction:column;gap:7px;padding:16px 12px}}
.nav-item{{display:flex;align-items:center;gap:12px;width:100%;border:1px solid transparent;border-radius:11px;background:transparent;color:var(--text);padding:12px;text-align:left;cursor:pointer}}
.nav-item:hover{{background:#ffffff0b;border-color:#ffffff12}} .nav-item.active{{background:var(--side2);border-color:#3b536f;box-shadow:inset 3px 0 0 var(--accent)}}
.nav-icon{{width:28px;text-align:center;font-size:21px}} .nav-item strong{{display:block;font-size:14px}} .nav-item small{{display:block;color:var(--muted);font-size:10px;margin-top:3px}}
.side-footer{{margin-top:auto;padding:14px 18px;border-top:1px solid var(--line);font-size:10px;line-height:1.55;color:var(--muted)}}
.workspace{{display:grid;grid-template-rows:58px minmax(0,1fr);min-width:0;background:var(--canvas)}}
.toolbar{{display:flex;align-items:center;gap:12px;padding:0 18px;background:#fff;color:#172033;border-bottom:1px solid #d7dfeb}}
.mobile-menu{{display:none;border:0;background:#eef2f7;border-radius:8px;padding:8px 10px;cursor:pointer}} .toolbar h2{{margin:0;font-size:17px}}
.toolbar-actions{{margin-left:auto;display:flex;gap:8px}} .toolbar button,.toolbar a{{border:1px solid #ced8e5;background:#fff;color:#26364c;border-radius:8px;padding:7px 10px;font-size:12px;text-decoration:none;cursor:pointer}}
.frame-wrap{{position:relative;min-height:0;background:#fff}} iframe{{display:block;width:100%;height:100%;border:0;background:#fff}}
.loading{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:#eef2f7;color:#53647a;font-weight:700;z-index:2}} .loading.hidden{{display:none}}
@media(max-width:820px){{.shell{{grid-template-columns:1fr}} .sidebar{{position:fixed;inset:0 auto 0 0;width:270px;z-index:20;transform:translateX(-100%);transition:.18s transform}} .sidebar.open{{transform:translateX(0)}} .mobile-menu{{display:inline-block}}}}
</style></head><body>
<div class="shell"><aside class="sidebar" id="sidebar"><div class="brand"><span class="brand-badge">AFIP · COMMAND CENTER</span><h1>AFIP Gold</h1><p>Operations · Intelligence · Research<br>ศูนย์บัญชาการ Dashboard แบบหน้าเดียว</p></div>
<nav class="navigation" aria-label="AFIP dashboards">{navigation}</nav>
<div class="side-footer">Presentation-only shell<br>No MT5 or execution-authority mutation<br>Generated {escape(generated)}</div></aside>
<main class="workspace"><header class="toolbar"><button class="mobile-menu" id="mobileMenu" type="button" aria-label="Open menu">☰</button><h2 id="pageTitle">P1–P4 Operations</h2><div class="toolbar-actions"><button id="refresh" type="button">↻ Refresh</button><a id="openStandalone" href="afip_profiles_dashboard.html" target="_blank" rel="noopener">Open standalone</a></div></header>
<section class="frame-wrap"><div class="loading" id="loading">Loading AFIP Dashboard…</div><iframe id="dashboardFrame" title="AFIP P1–P4 Operations" src="afip_profiles_dashboard.html"></iframe></section></main></div>
<script>
const pages={{{page_map}}};
const frame=document.getElementById('dashboardFrame'); const title=document.getElementById('pageTitle'); const loading=document.getElementById('loading'); const standalone=document.getElementById('openStandalone'); const sidebar=document.getElementById('sidebar');
function selectPage(id,push=true){{const page=pages[id]||pages.operations; document.querySelectorAll('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.page===id)); title.textContent=page.title; frame.title='AFIP '+page.title; loading.classList.remove('hidden'); frame.src=page.src; standalone.href=page.src; if(push) history.replaceState(null,'','#'+id); sidebar.classList.remove('open');}}
document.querySelectorAll('.nav-item').forEach(button=>button.addEventListener('click',()=>selectPage(button.dataset.page)));
frame.addEventListener('load',()=>loading.classList.add('hidden'));
document.getElementById('refresh').addEventListener('click',()=>{{loading.classList.remove('hidden'); frame.contentWindow.location.reload();}});
document.getElementById('mobileMenu').addEventListener('click',()=>sidebar.classList.toggle('open'));
const initial=location.hash.slice(1); if(initial&&pages[initial]) selectPage(initial,false);
</script></body></html>'''


def write_dashboard_home(output_directory: str | Path = "runtime/dashboard") -> Path:
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / HOME_FILENAME
    path.write_text(render_dashboard_home(), encoding="utf-8")
    return path
