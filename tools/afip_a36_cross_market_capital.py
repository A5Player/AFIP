"""A36 active-readonly cross-market intake and offline capital suitability research."""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "afip.a36.cross_market_capital_suitability.v1.1"
SOURCES = {
    "EURUSD": ("EURUSD", "EURUSD#"),
    "GBPUSD": ("GBPUSD", "GBPUSD#"),
    "USDJPY": ("USDJPY", "USDJPY#"),
    "USDCHF": ("USDCHF", "USDCHF#"),
    "USDCNH": ("USDCNH", "USDCNH#"),
    "DXY": ("DXY", "USDX", "USDIDX"),
    "WTI": ("OILCash#", "OIL.WTI", "WTI", "USOIL", "USOIL#", "XTIUSD", "OILCash", "OIL-Cash"),
    "BRENT": ("BRENTCash#", "OIL.BRENT", "BRENT", "UKOIL", "UKOIL#", "XBRUSD", "BRENTCash", "BRENT-Cash"),
    "SP500": ("US500Cash#", "US500", "US500#", "US500Cash", "US500-Cash", "SPX500", "SP500", "S&P500"),
    "NASDAQ100": ("US100Cash#", "US100", "US100#", "US100Cash", "US100-Cash", "NAS100", "USTEC"),
    "DOW30": ("US30Cash#", "US30", "US30#", "US30Cash", "US30-Cash", "DJ30", "DJI"),
    "RUSSELL2000": ("US2000Cash#", "US2000", "US2000#", "US2000Cash", "US2000-Cash", "RUS2000", "RTY"),
    "VIX": ("VIX", "VIX#", "VIXCash", "VIX-Cash", "USVIX"),
    "AAPL": ("Apple", "AAPL", "AAPL#", "AAPL.US", "AAPL.OQ"),
    "MSFT": ("Microsoft", "MSFT", "MSFT#", "MSFT.US", "MSFT.OQ"),
    "NVDA": ("Nvidia", "NVDA", "NVDA#", "NVDA.US", "NVDA.OQ"),
    "AMZN": ("Amazon", "AMZN", "AMZN#", "AMZN.US", "AMZN.OQ"),
    "META": ("Facebook", "META", "META#", "META.US", "META.OQ"),
    "TSLA": ("Tesla", "TSLA", "TSLA#", "TSLA.US", "TSLA.OQ"),
    "BTCUSD": ("BTCUSD", "BTCUSD#", "BTCUSD.", "BITCOIN"),
    "ETHUSD": ("ETHUSD", "ETHUSD#", "ETHUSD.", "ETHEREUM"),
    "SILVER": ("SILVER", "SILVER#", "XAGUSD", "XAGUSD#"),
    "COPPER": ("COPPER", "COPPER#", "COPPERCash", "COPPER-Cash", "XCUUSD", "HG"),
    "US02Y": ("US02Y", "US2Y", "UST2Y", "US02Y#"),
    "US10Y": ("US10Y", "UST10Y", "US10Y#", "TNX"),
    "SHY_1_3Y_BOND_ETF": ("SHY",),
    "IEF_7_10Y_BOND_ETF": ("IEF",),
    "TLT_20Y_BOND_ETF": ("TLT",),
}
FUTURES_PREFIXES = {"DXY": "USDX-", "VIX": "VIX-", "COPPER": "HGCOP-"}
SOURCE_CATEGORIES = {
    **{key: "FX_USD" for key in ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCNH", "DXY")},
    **{key: "ENERGY" for key in ("WTI", "BRENT")},
    **{key: "US_INDEX" for key in ("SP500", "NASDAQ100", "DOW30", "RUSSELL2000")},
    "VIX": "VOLATILITY",
    **{key: "US_EQUITY" for key in ("AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA")},
    **{key: "CRYPTO" for key in ("BTCUSD", "ETHUSD")},
    **{key: "METAL" for key in ("SILVER", "COPPER")},
    **{key: "US_YIELD" for key in ("US02Y", "US10Y")},
    **{key: "US_BOND_ETF_PROXY" for key in ("SHY_1_3Y_BOND_ETF", "IEF_7_10Y_BOND_ETF", "TLT_20Y_BOND_ETF")},
}


def _value(obj: Any, name: str, default: Any = None) -> Any:
    return obj.get(name, default) if isinstance(obj, dict) else getattr(obj, name, default)


def _corr(xs: list[float], ys: list[float]) -> float | None:
    count = min(len(xs), len(ys))
    if count < 30:
        return None
    xs, ys = xs[-count:], ys[-count:]
    mx, my = fmean(xs), fmean(ys)
    dx, dy = [x - mx for x in xs], [y - my for y in ys]
    denominator = math.sqrt(sum(x*x for x in dx) * sum(y*y for y in dy))
    return sum(x*y for x, y in zip(dx, dy)) / denominator if denominator else None


def _returns(rows: list[dict[str, Any]]) -> dict[int, float]:
    result = {}
    for prior, current in zip(rows, rows[1:]):
        if prior["close"]:
            result[int(current["time"])] = current["close"] / prior["close"] - 1.0
    return result


def _normal(value: Any) -> str:
    return "".join(character for character in str(value or "").upper() if character.isalnum())


def _catalog(mt5: Any) -> list[dict[str, Any]]:
    values = mt5.symbols_get() or ()
    return [{"name": str(_value(item, "name", "")), "path": str(_value(item, "path", "")),
             "description": str(_value(item, "description", "")),
             "currency_base": str(_value(item, "currency_base", "")),
             "currency_profit": str(_value(item, "currency_profit", "")),
             "visible": bool(_value(item, "visible", False)),
             "expiration_time": int(_value(item, "expiration_time", 0) or 0)}
            for item in values if _value(item, "name")]


def _resolve_with_evidence(mt5: Any, aliases: Iterable[str], catalog: list[dict[str, Any]]) -> dict[str, Any]:
    for alias in aliases:
        info = mt5.symbol_info(alias)
        if info is not None:
            if not bool(_value(info, "visible", False)):
                mt5.symbol_select(alias, True)
            return {"symbol": alias, "method": "EXACT_ALIAS", "matched_alias": alias}
    alias_norms = [(_normal(alias), alias) for alias in aliases if len(_normal(alias)) >= 3]
    candidates: list[tuple[int, str, str]] = []
    safe_suffixes = {"CASH", "OQ", "US", "NY", "NAS", "NYSE", "MINI", "MICRO"}
    for item in catalog:
        name, normalized = item["name"], _normal(item["name"])
        for alias_normalized, alias in alias_norms:
            if normalized == alias_normalized:
                candidates.append((100, name, alias))
            elif normalized.startswith(alias_normalized) and normalized[len(alias_normalized):] in safe_suffixes:
                candidates.append((90, name, alias))
    if not candidates:
        return {"symbol": None, "method": "UNAVAILABLE", "matched_alias": None}
    by_symbol: dict[str, tuple[int, str]] = {}
    for score, name, alias in candidates:
        previous = by_symbol.get(name)
        if previous is None or score > previous[0] or (score == previous[0] and alias < previous[1]):
            by_symbol[name] = (score, alias)
    best_score = max(score for score, _ in by_symbol.values())
    best = sorted((name, alias) for name, (score, alias) in by_symbol.items() if score == best_score)
    if len(best) != 1:
        return {"symbol": None, "method": "AMBIGUOUS_BLOCKED", "matched_alias": None,
                "candidates": [name for name, _ in best]}
    name, alias = best[0]
    info = mt5.symbol_info(name)
    if info is None:
        return {"symbol": None, "method": "UNAVAILABLE", "matched_alias": alias}
    if not bool(_value(info, "visible", False)):
        mt5.symbol_select(name, True)
    return {"symbol": name, "method": "NORMALIZED_CATALOG", "matched_alias": alias}


def _resolve(mt5: Any, aliases: Iterable[str], catalog: list[dict[str, Any]] | None = None) -> str | None:
    return _resolve_with_evidence(mt5, aliases, catalog or _catalog(mt5))["symbol"]


def _resolve_source(mt5: Any, source_id: str, catalog: list[dict[str, Any]]) -> dict[str, Any]:
    result = _resolve_with_evidence(mt5, SOURCES[source_id], catalog)
    if result["symbol"] is not None or source_id not in FUTURES_PREFIXES:
        return result
    prefix = FUTURES_PREFIXES[source_id].upper()
    now = int(datetime.now(timezone.utc).timestamp())
    contracts = [item for item in catalog if item["name"].upper().startswith(prefix)]
    active = [item for item in contracts if int(item.get("expiration_time") or 0) > now]
    pool = active or contracts
    if not pool:
        return result
    dated = [item for item in pool if int(item.get("expiration_time") or 0) > 0]
    chosen = min(dated, key=lambda item: int(item["expiration_time"])) if dated else sorted(pool, key=lambda item: item["name"])[0]
    name = chosen["name"]
    info = mt5.symbol_info(name)
    if info is None:
        return result
    if not bool(_value(info, "visible", False)):
        mt5.symbol_select(name, True)
    return {"symbol": name, "method": "ACTIVE_FUTURES_CONTRACT", "matched_alias": prefix,
            "expiration_time": int(chosen.get("expiration_time") or 0)}


def _rates(mt5: Any, symbol: str, count: int) -> list[dict[str, Any]]:
    values = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 1, count)
    if values is None:
        return []
    rows = []
    for item in values:
        get = (lambda key: item[key]) if hasattr(item, "dtype") else (lambda key: getattr(item, key, None))
        try:
            rows.append({"time": int(get("time")), "open": float(get("open")), "high": float(get("high")),
                         "low": float(get("low")), "close": float(get("close")),
                         "tick_volume": float(get("tick_volume") or 0)})
        except (TypeError, ValueError, KeyError):
            continue
    return rows


def collect(project_root: Path, approved: bool, maximum_bars: int = 5000) -> dict[str, Any]:
    if not approved:
        raise ValueError("A36 collection requires --approve-active-readonly")
    from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager
    manager = MT5MultiTerminalConnectionManager(project_root / "config/four_profile_demo.json")
    profiles = manager.operations.load()
    profile = next((item for item in profiles if item.profile_id == "P4" and item.enabled), None)
    if profile is None:
        raise ValueError("enabled P4 profile is required")
    import MetaTrader5 as mt5
    initialized = False
    try:
        password = os.environ.get(profile.password_env, "")
        initialized = bool(mt5.initialize(path=str(profile.mt5_terminal), login=int(profile.login),
                                          password=password, server=profile.server, portable=True))
        account = mt5.account_info() if initialized else None
        terminal = mt5.terminal_info() if initialized else None
        demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", None)
        identity_ok = bool(initialized and account is not None and terminal is not None
                           and str(_value(account, "login", "")) == str(profile.login)
                           and str(_value(account, "server", "")).casefold() == profile.server.casefold()
                           and demo_mode is not None
                           and int(_value(account, "trade_mode", -1)) == int(demo_mode)
                           and bool(_value(terminal, "connected", False)))
        if not identity_ok:
            return {"schema": SCHEMA, "status": "BLOCKED", "reason": "P4_DEMO_IDENTITY_NOT_VERIFIED",
                    "execution_authority": "NONE", "orders_sent": False}
        catalog = _catalog(mt5)
        gold_resolution = _resolve_with_evidence(mt5, (profile.symbol, "GOLD#", "XAUUSD"), catalog)
        gold_symbol = gold_resolution["symbol"]
        if not gold_symbol:
            return {"schema": SCHEMA, "status": "BLOCKED", "reason": "GOLD_SYMBOL_UNAVAILABLE",
                    "execution_authority": "NONE", "orders_sent": False}
        all_rows: dict[str, list[dict[str, Any]]] = {"GOLD": _rates(mt5, gold_symbol, maximum_bars)}
        resolutions = {"GOLD": gold_resolution}
        for source_id, aliases in SOURCES.items():
            resolution = _resolve_source(mt5, source_id, catalog)
            symbol = resolution["symbol"]
            resolutions[source_id] = resolution
            all_rows[source_id] = _rates(mt5, symbol, maximum_bars) if symbol else []
        info = mt5.symbol_info(gold_symbol)
        tick = mt5.symbol_info_tick(gold_symbol)
        volume = max(float(_value(info, "volume_min", 0.01) or 0.01), 0.01)
        ask = float(_value(tick, "ask", 0.0) or 0.0)
        order_type = getattr(mt5, "ORDER_TYPE_BUY", 0)
        margin = mt5.order_calc_margin(order_type, gold_symbol, volume, ask) if ask > 0 else None
        broker = {
            "symbol": gold_symbol, "volume": volume,
            "point": _value(info, "point"), "trade_tick_size": _value(info, "trade_tick_size"),
            "trade_tick_value": _value(info, "trade_tick_value"),
            "trade_tick_value_loss": _value(info, "trade_tick_value_loss"),
            "trade_contract_size": _value(info, "trade_contract_size"),
            "margin_for_volume": margin, "account_currency": _value(account, "currency"),
            "calculation_source": "MT5_SYMBOL_INFO_AND_ORDER_CALC_MARGIN_READONLY",
        }
        output = project_root / "runtime/research/a36_cross_market_capital"
        bars_dir = output / "bars"
        bars_dir.mkdir(parents=True, exist_ok=True)
        (output / "a36_broker_symbol_catalog.json").write_text(json.dumps({
            "schema": "afip.a36.broker_symbol_catalog.v1", "profile_id": "P4",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(), "symbol_count": len(catalog),
            "symbols": catalog, "resolutions": resolutions, "execution_authority": "NONE",
            "orders_sent": False,
        }, indent=2), encoding="utf-8")
        for source_id, rows in all_rows.items():
            (bars_dir / f"{source_id}_H1.json").write_text(json.dumps(rows), encoding="utf-8")
        snapshot = {
            "schema": SCHEMA, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "ACTIVE_READONLY_COLLECTION_PASS", "profile_id": "P4",
            "demo_identity_verified": True, "timeframe": "H1", "maximum_bars": maximum_bars,
            "broker_catalog_symbol_count": len(catalog), "resolutions": resolutions,
            "sample_counts": {key: len(value) for key, value in all_rows.items()},
            "broker_contract": broker, "execution_authority": "NONE", "orders_sent": False,
            "order_check_called": False, "order_send_called": False,
        }
        output.mkdir(parents=True, exist_ok=True)
        (output / "a36_collection.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        return snapshot
    finally:
        if initialized:
            try:
                mt5.shutdown()
            except Exception:
                pass


def _relationship(source_id: str, gold_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> dict[str, Any]:
    gold_returns, source_returns = _returns(gold_rows), _returns(source_rows)
    timestamps = sorted(set(gold_returns) & set(source_returns))
    xs, ys = [source_returns[t] for t in timestamps], [gold_returns[t] for t in timestamps]
    correlation = _corr(xs, ys)
    next_gold = {int(row["time"]): gold_rows[index + 1]["close"] / row["close"] - 1
                 for index, row in enumerate(gold_rows[:-1]) if row["close"]}
    up, down = [], []
    for timestamp in timestamps:
        if timestamp not in next_gold:
            continue
        (up if source_returns[timestamp] > 0 else down).append(next_gold[timestamp])
    def condition(values: list[float]) -> dict[str, Any]:
        return {"samples": len(values), "gold_next_bar_up_pct": round(100*sum(x > 0 for x in values)/len(values), 4),
                "gold_next_bar_mean_return_pct": round(100*fmean(values), 6)} if values else {
                    "samples": 0, "gold_next_bar_up_pct": None, "gold_next_bar_mean_return_pct": None}
    lag_relationships = []
    gold_by_time = {int(row["time"]): index for index, row in enumerate(gold_rows)}
    for lag in range(1, 5):
        lag_x, lag_y = [], []
        for timestamp in timestamps:
            index = gold_by_time.get(timestamp)
            if index is None or index + lag >= len(gold_rows) or not gold_rows[index]["close"]:
                continue
            lag_x.append(source_returns[timestamp])
            lag_y.append(gold_rows[index + lag]["close"] / gold_rows[index]["close"] - 1)
        value = _corr(lag_x, lag_y)
        lag_relationships.append({"lag_closed_bars": lag, "samples": len(lag_x),
                                  "correlation": round(value, 6) if value is not None else None})
    return {"source_id": source_id, "category": SOURCE_CATEGORIES[source_id], "aligned_samples": len(timestamps),
            "same_bar_return_correlation": round(correlation, 6) if correlation is not None else None,
            "when_source_up": condition(up), "when_source_down_or_flat": condition(down),
            "lead_lag_h1": lag_relationships,
            "status": "RESEARCH_READY" if len(timestamps) >= 1000 else "INSUFFICIENT_SAMPLES"}


def _capital(row: dict[str, Any], broker: dict[str, Any], cost_points: float) -> dict[str, Any]:
    tick_size = float(broker.get("trade_tick_size") or 0)
    tick_value = float(broker.get("trade_tick_value_loss") or broker.get("trade_tick_value") or 0)
    point = float(broker.get("point") or 0)
    volume = float(broker.get("volume") or 0.01)
    if min(tick_size, tick_value, point, volume) <= 0:
        return {"status": "DATA_UNAVAILABLE", "reason": "broker_tick_value_or_size_missing"}
    value_per_point = point / tick_size * tick_value * volume
    risk_money = (float(row.get("average_sl_points") or 0) + cost_points) * value_per_point
    drawdown_money = float(row.get("max_drawdown_r") or 0) * risk_money
    margin = float(broker.get("margin_for_volume") or 0)
    return {
        "status": "CALCULATED_RESEARCH_ONLY", "currency": broker.get("account_currency") or "UNKNOWN",
        "lot": volume, "value_per_point": round(value_per_point, 6),
        "risk_per_order": round(risk_money, 2), "historical_drawdown_money": round(drawdown_money, 2),
        "equity_at_0_5_pct_risk": round(risk_money / .005, 2),
        "equity_at_1_pct_risk": round(risk_money / .01, 2),
        "equity_at_2_pct_risk": round(risk_money / .02, 2),
        "equity_for_drawdown_within_10_pct": round(drawdown_money / .10, 2),
        "margin_for_lot": round(margin, 2),
        "technical_floor_with_margin_reserve": round(max(risk_money/.02, margin*1.5), 2),
        "recommended_starting_equity": round(max(risk_money/.01, drawdown_money/.10, margin*1.5), 2),
        "automatic_capital_authority": False,
    }


def analyze(project_root: Path) -> dict[str, Any]:
    root = project_root / "runtime/research/a36_cross_market_capital"
    collection_path = root / "a36_collection.json"
    a35_path = project_root / "runtime/research/a35_atr_buffer/a35_atr_buffer_campaign.json"
    if not collection_path.exists() or not a35_path.exists():
        raise FileNotFoundError("A36 collection and A35 report are required")
    collection = json.loads(collection_path.read_text(encoding="utf-8"))
    a35 = json.loads(a35_path.read_text(encoding="utf-8"))
    bars_dir = root / "bars"
    gold = json.loads((bars_dir / "GOLD_H1.json").read_text(encoding="utf-8"))
    relationships = []
    for source_id in SOURCES:
        path = bars_dir / f"{source_id}_H1.json"
        rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        relationships.append(_relationship(source_id, gold, rows) if rows else {
            "source_id": source_id, "category": SOURCE_CATEGORIES[source_id],
            "status": "DATA_UNAVAILABLE", "aligned_samples": 0, "lead_lag_h1": []})
    cost = float(a35.get("round_trip_cost_points") or 35)
    candidates = []
    for row in a35.get("rows", []):
        if row.get("eligibility") != "ELIGIBLE_RESEARCH":
            continue
        item = {key: row.get(key) for key in ("rank", "pattern", "timeframe", "direction",
                "sl_atr_multiplier", "sl_buffer_points", "tp_atr_multiplier", "tp_buffer_points",
                "average_sl_points", "average_tp_points", "average_planned_rr", "samples",
                "win_rate_pct", "expectancy_r", "profit_factor", "max_drawdown_r", "walk_forward_passes")}
        item["capital_suitability"] = _capital(row, collection.get("broker_contract", {}), cost)
        candidates.append(item)
    report = {
        "schema": SCHEMA, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CROSS_MARKET_AND_CAPITAL_RESEARCH_ONLY", "relationships": relationships,
        "eligible_research_candidates": candidates, "candidate_count": len(candidates),
        "profile_strategy_selection": "NOT_DECIDED", "execution_authority": "NONE",
        "capital_truth_notice": "Candidate-specific estimate; never a deposit requirement or automatic sizing authority.",
        "cross_market_truth_notice": "Relationship evidence is contextual research, not causal proof or execution authority.",
    }
    (root / "a36_cross_market_capital_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    _write_html(report, root / "a36_cross_market_capital_dashboard.html")
    return report


def _write_html(report: dict[str, Any], path: Path) -> None:
    relations = "".join(f"<tr><td>{html.escape(str(x['category']))}</td><td>{html.escape(str(x['source_id']))}</td><td>{x.get('status')}</td><td>{x.get('aligned_samples',0):,}</td><td>{x.get('same_bar_return_correlation')}</td><td>{x.get('when_source_up',{}).get('gold_next_bar_up_pct')}</td><td>{x.get('when_source_down_or_flat',{}).get('gold_next_bar_up_pct')}</td><td>{', '.join('L'+str(y['lag_closed_bars'])+': '+str(y['correlation']) for y in x.get('lead_lag_h1',[])) or 'DATA_UNAVAILABLE'}</td></tr>" for x in report["relationships"])
    cards = []
    for index, row in enumerate(report["eligible_research_candidates"], 1):
        cap = row["capital_suitability"]
        cards.append(f'''<article><h2>🏆 Candidate {index} · {html.escape(str(row["pattern"]))}</h2>
<p>🕒 {row["timeframe"]} · 🧭 {row["direction"]} · Win {row["win_rate_pct"]:.2f}% · Expectancy {row["expectancy_r"]:+.3f}R · DD {row["max_drawdown_r"]:.2f}R</p>
<p>🛡️ SL เฉลี่ย {row["average_sl_points"]:,.2f} จุด · 🎯 TP เฉลี่ย {row["average_tp_points"]:,.2f} จุด · RR 1:{row["average_planned_rr"]:.2f}</p>
<p>💵 ความเสี่ยง 0.01 lot: {cap.get("risk_per_order", "DATA_UNAVAILABLE")} {cap.get("currency", "")} · ทุนที่ความเสี่ยง 1%: {cap.get("equity_at_1_pct_risk", "DATA_UNAVAILABLE")} · ทุนแนะนำ: <b>{cap.get("recommended_starting_equity", "DATA_UNAVAILABLE")}</b></p>
<p>📉 Historical DD เป็นเงิน: {cap.get("historical_drawdown_money", "DATA_UNAVAILABLE")} · Margin: {cap.get("margin_for_lot", "DATA_UNAVAILABLE")}</p></article>''')
    path.write_text(f'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AFIP A36</title><style>body{{font:16px system-ui;background:#eef3f8;color:#14243a;margin:0}}main{{max-width:1400px;margin:auto;padding:24px}}article,.panel{{background:white;border:1px solid #d7e0e9;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 4px 14px #1231}}.scroll{{overflow:auto}}table{{width:100%;border-collapse:collapse;min-width:1100px}}th,td{{padding:9px;border:1px solid #dde5ec;text-align:left}}th{{background:#edf4fb}}</style><main><h1>🌍💰 A36 Cross-market & Capital Suitability</h1><div class="panel"><b>Research only · P1–P4 NOT_DECIDED · Execution authority NONE</b></div><section class="panel"><h2>Cross-market H1 relationships</h2><div class="scroll"><table><tr><th>หมวด</th><th>ตลาด</th><th>สถานะ</th><th>ตัวอย่าง</th><th>Same-bar correlation</th><th>ตลาดขึ้น → Gold ขึ้น%</th><th>ตลาดลง → Gold ขึ้น%</th><th>Lead/Lag H1 correlation</th></tr>{relations}</table></div></section><section><h1>Capital suitability by A35 candidate</h1>{''.join(cards) or '<article>ไม่มี A35 candidate ที่ผ่าน Research gate</article>'}</section></main></html>''', encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("collect", "analyze"))
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--approve-active-readonly", action="store_true")
    parser.add_argument("--maximum-bars", type=int, default=5000)
    args = parser.parse_args()
    try:
        result = collect(args.project_root.resolve(), args.approve_active_readonly, args.maximum_bars) if args.mode == "collect" else analyze(args.project_root.resolve())
    except (ValueError, FileNotFoundError) as exc:
        print(str(exc)); return 2
    print(json.dumps({key: result.get(key) for key in ("status", "candidate_count", "execution_authority", "orders_sent") if key in result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
