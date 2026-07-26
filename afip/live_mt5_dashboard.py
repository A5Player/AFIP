"""Read-only live MT5 observability dashboard."""
from __future__ import annotations
from html import escape
from pathlib import Path
from typing import Any, Mapping

FILENAME = "afip_live_mt5_dashboard.html"


def _v(m: Mapping[str, Any], *keys: str, default: Any = "DATA_UNAVAILABLE") -> Any:
    for key in keys:
        value = m.get(key)
        if value not in (None, "", []):
            return value
    return default


def _observation_state(profile: Mapping[str, Any]) -> str:
    truth = profile.get("authoritative_runtime_truth")
    if isinstance(truth, Mapping):
        return "CURRENT" if truth.get("observation_current") else "STALE"
    metadata = profile.get("source_metadata")
    if isinstance(metadata, Mapping):
        mt5 = metadata.get("mt5_health")
        if isinstance(mt5, Mapping):
            if mt5.get("fresh") is True:
                return "CURRENT"
            if mt5.get("fresh") is False:
                return "STALE"
    return "DATA_UNAVAILABLE"


def _financial_state(profile: Mapping[str, Any]) -> str:
    truth = profile.get("authoritative_runtime_truth")
    if isinstance(truth, Mapping) and truth.get("financial_state"):
        return str(truth.get("financial_state"))
    explicit = profile.get("financial_state")
    if explicit not in (None, ""):
        return str(explicit)
    evidence = str(profile.get("evidence_kind", "")).upper()
    if evidence == "LIVE":
        return "LIVE"
    if evidence == "LAST_VERIFIED_SNAPSHOT":
        return "SNAPSHOT"
    return "DATA_UNAVAILABLE"


def render(contract: Mapping[str, Any]) -> str:
    cards = []
    for profile in contract.get("profiles", []):
        if not isinstance(profile, Mapping):
            continue
        pid = escape(str(profile.get("profile_id", "UNKNOWN")))
        rows = [
            ("Operational State", _v(profile, "operational_state", "runtime_state")),
            ("AFIP Runtime", _v(profile, "runtime_state", "status")),
            ("MT5 Process", _v(profile, "process_state", default="DATA_UNAVAILABLE")),
            ("Broker Session", _v(profile, "session_state", default="DATA_UNAVAILABLE")),
            ("Connection", _v(profile, "connection_status", "mt5_status", "status")),
            ("Monitoring Mode", _v(profile, "monitoring_mode", "mt5_monitoring_mode")),
            ("Terminal Process", "RUNNING" if profile.get("process_alive") is True else "STOPPED" if profile.get("process_alive") is False else "DATA_UNAVAILABLE"),
            ("Connection Evidence", _observation_state(profile)),
            ("Financial State", _financial_state(profile)),
            ("Account", _v(profile, "account", "login", "account_login")),
            ("Server", _v(profile, "server")),
            ("Symbol", _v(profile, "symbol", default="GOLD#")),
            ("Balance", _v(profile, "balance")),
            ("Equity", _v(profile, "equity")),
            ("Free Margin", _v(profile, "free_margin", "margin_free")),
            ("Floating P/L", _v(profile, "floating_profit", "profit")),
            ("Positions / Orders", f"{_v(profile, 'positions_total', default=0)} / {_v(profile, 'orders_total', default=0)}"),
            ("Bid / Ask", f"{_v(profile, 'bid')} / {_v(profile, 'ask')}"),
            ("Spread", _v(profile, "spread_points", "spread")),
            ("Digits / Point", f"{_v(profile, 'digits')} / {_v(profile, 'point_size')}"),
            ("Latency ms", _v(profile, "latency_ms", "ping_ms")),
            ("Trade Allowed", _v(profile, "trade_allowed")),
            ("Execution", _v(profile, "execution")),
            ("Order Status", _v(profile, "order_status")),
            ("Checked UTC", _v(profile, "checked_at_utc", "last_tick_time_utc", "tick_time_utc")),
            ("Snapshot UTC", _v(profile, "snapshot_checked_at_utc")),
            ("Snapshot Age sec", _v(profile, "snapshot_age_seconds")),
            ("Observation State", _observation_state(profile)),
        ]
        body = "".join(
            f'<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>'
            for label, value in rows
        )
        cards.append(f'<section><h2>{pid}</h2><table>{body}</table></section>')

    return f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AFIP Live MT5</title><style>
:root{{font-family:Arial,"Noto Sans Thai",sans-serif;color:#172033;background:#eef2f7}}*{{box-sizing:border-box}}body{{margin:0;padding:14px 14px 110px;min-width:1120px}}.top{{display:flex;align-items:end;justify-content:space-between;gap:12px;margin-bottom:10px}}h1{{font-size:22px;margin:0}}.subtitle{{font-size:11px;color:#64748b;margin:3px 0 0}}.note{{background:#fff6d8;border:1px solid #f0dd91;padding:8px 10px;border-radius:9px;font-size:11px;white-space:nowrap}}main{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;align-items:start}}section{{min-width:0;background:white;border:1px solid #d6deea;border-radius:12px;padding:12px;box-shadow:0 4px 12px #1720330c}}h2{{font-size:18px;margin:0 0 8px}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{padding:6px 5px;border-bottom:1px solid #edf1f6;text-align:left;font-size:10px;vertical-align:top;overflow-wrap:anywhere}}th{{color:#607089;width:42%}}td{{font-weight:600}}tr:last-child th,tr:last-child td{{border-bottom:0}}@media(max-width:1300px){{body{{min-width:1040px;padding:10px}}main{{gap:7px}}section{{padding:9px}}th,td{{font-size:9px;padding:5px 4px}}}}
</style><script>
(function(){{const key='afip_mt5_scroll';window.addEventListener('beforeunload',()=>sessionStorage.setItem(key,String(window.scrollY)));window.addEventListener('load',()=>{{const y=Number(sessionStorage.getItem(key)||0);if(y>0)window.scrollTo(0,y);}});setInterval(()=>{{sessionStorage.setItem(key,String(window.scrollY));location.reload();}},5000);}})();
</script></head><body><div class="top"><div><h1>Live MT5 Dashboard · P1–P4 Comparison</h1><p class="subtitle">Four-column passive MT5 process truth and labelled financial evidence · refresh every 5 seconds</p></div><div class="note">Passive monitoring never opens or reconnects MT5. Snapshot values are not live values.</div></div><main>{''.join(cards) or '<section>No profile evidence available.</section>'}</main></body></html>'''


def write(contract: Mapping[str, Any], output_directory: str | Path = "runtime/dashboard") -> Path:
    path = Path(output_directory) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(contract), encoding="utf-8")
    return path
