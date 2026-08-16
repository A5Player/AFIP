from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "afip.a32.real_backtest_campaign.v1"
DISTANCES = (300, 500, 800, 1200)
HOLDS = (4, 8, 16, 32)


def _minimum_win_rate_for_rr(rr: float) -> float | None:
    if rr >= 4.0:
        return 27.0
    if rr >= 3.0:
        return 32.0
    if rr >= 2.0:
        return 42.0
    if rr >= 1.5:
        return 50.0
    if rr >= 1.0:
        return 60.0
    return None


def _walk_forward_pass(result: dict[str, Any], *, tp_points: int, sl_points: int) -> bool:
    required_win_rate = _minimum_win_rate_for_rr(tp_points / sl_points)
    return bool(
        result["samples"] >= 25
        and required_win_rate is not None
        and result["win_rate_pct"] >= required_win_rate
        and result["expectancy_r"] >= 0.15
        and result["profit_factor"] is not None
        and result["profit_factor"] >= 1.30
        and result["max_drawdown_r"] <= 10.0
    )


def _jsonl(path: Path, quality: dict[str, int]) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                quality["invalid_json_lines_excluded"] += 1


def _timeframe(record: dict[str, Any]) -> str | None:
    value = record.get("timeframe")
    if value:
        return str(value).upper()
    scenario = str(record.get("scenario_id", ""))
    for part in scenario.split("-"):
        if part.upper() in {"M1", "M5", "M15", "M30", "H1", "H4", "D1"}:
            return part.upper()
    return None


def _metrics(rows: list[tuple[str, float, str, int]]) -> dict[str, Any]:
    values = [row[1] for row in rows]
    wins = sum(value > 0 for value in values)
    gross_win = sum(value for value in values if value > 0)
    gross_loss = -sum(value for value in values if value < 0)
    equity = peak = drawdown = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return {
        "samples": len(values),
        "win_rate_pct": round(100 * wins / len(values), 4),
        "expectancy_r": round(sum(values) / len(values), 6),
        "profit_factor": round(gross_win / gross_loss, 6) if gross_loss else None,
        "max_drawdown_r": round(drawdown, 6),
        "tp_rate_pct": round(100 * sum(row[2] == "TP" for row in rows) / len(rows), 4),
        "sl_rate_pct": round(100 * sum(row[2] == "SL" for row in rows) / len(rows), 4),
        "average_holding_bars": round(sum(row[3] for row in rows) / len(rows), 4),
    }


def run_campaign(project_root: Path, *, point_size: float = 0.01,
                 round_trip_cost_points: float = 35.0,
                 minimum_blind_samples: int = 30) -> dict[str, Any]:
    research = project_root / "runtime" / "research"
    automatic = research / "automatic" / "schema_v2"
    candidate_path = automatic / "candidates.jsonl"
    outcome_path = automatic / "adversarial_market_behaviour" / "outcomes.jsonl"
    lake = research / "historical_data_lake"
    required = (candidate_path, outcome_path, lake)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("A32 required AFIP evidence is missing: " + ", ".join(missing))

    quality = {"invalid_json_lines_excluded": 0}
    directions: dict[tuple[str, str], str] = {}
    for envelope in _jsonl(candidate_path, quality):
        record = envelope.get("record", envelope)
        timestamp, timeframe = record.get("replay_timestamp_utc"), _timeframe(record)
        direction = record.get("direction")
        if timestamp and timeframe and direction in {"BUY", "SELL"}:
            directions[(str(timestamp), timeframe)] = direction

    bars: dict[str, dict[str, tuple[float, float, float, float]]] = defaultdict(dict)
    for path in lake.rglob("records.jsonl"):
        for record in _jsonl(path, quality):
            payload = record.get("payload", {})
            timeframe = _timeframe(payload)
            timestamp = record.get("observed_at_utc")
            fields = (payload.get("open"), payload.get("high"), payload.get("low"), payload.get("close"))
            if (record.get("research_eligibility") == "ELIGIBLE" and payload.get("closed_bar") is True
                    and timeframe and timestamp and all(value is not None for value in fields)):
                bars[timeframe][str(timestamp)] = tuple(float(value) for value in fields)  # type: ignore[assignment]

    ordered = {timeframe: sorted(mapping.items()) for timeframe, mapping in bars.items()}
    positions = {timeframe: {timestamp: index for index, (timestamp, _) in enumerate(sequence)}
                 for timeframe, sequence in ordered.items()}
    events: list[tuple[str, str, str, str, int]] = []
    for record in _jsonl(outcome_path, quality):
        timeframe, timestamp = _timeframe(record), record.get("timestamp_utc")
        if not timeframe or not timestamp:
            continue
        direction = directions.get((str(timestamp), timeframe))
        index = positions.get(timeframe, {}).get(str(timestamp))
        if direction and index is not None and index + 1 < len(ordered[timeframe]):
            events.append((str(timestamp), timeframe, str(record.get("pattern_name", "UNKNOWN")), direction, index))
    events.sort()

    def trade(event: tuple[str, str, str, str, int], tp_points: int, sl_points: int,
              hold: int) -> tuple[float, str, int]:
        _, timeframe, _, direction, index = event
        sequence = ordered[timeframe]
        entry = sequence[index][1][3]
        sign = 1 if direction == "BUY" else -1
        tp_price = entry + sign * tp_points * point_size
        sl_price = entry - sign * sl_points * point_size
        exit_price = sequence[min(index + hold, len(sequence) - 1)][1][3]
        reason, used = "TIME", 0
        for used, (_, (_, high, low, close)) in enumerate(sequence[index + 1:index + hold + 1], 1):
            sl_hit = low <= sl_price if sign == 1 else high >= sl_price
            tp_hit = high >= tp_price if sign == 1 else low <= tp_price
            if sl_hit:
                exit_price, reason = sl_price, "SL"
                break
            if tp_hit:
                exit_price, reason = tp_price, "TP"
                break
            exit_price = close
        net_points = sign * (exit_price - entry) / point_size - round_trip_cost_points
        return net_points / sl_points, reason, used

    groups: dict[tuple[Any, ...], list[tuple[str, float, str, int]]] = defaultdict(list)
    for event in events:
        for tp_points in DISTANCES:
            for sl_points in DISTANCES:
                for hold in HOLDS:
                    result_r, reason, bars_used = trade(event, tp_points, sl_points, hold)
                    groups[(event[1], event[2], event[3], tp_points, sl_points, hold)].append(
                        (event[0], result_r, reason, bars_used))

    rows: list[dict[str, Any]] = []
    fields = ("timeframe", "pattern", "direction", "tp_points", "sl_points", "max_holding_bars")
    for key, observations in groups.items():
        observations.sort()
        training_count = int(len(observations) * 0.8)
        blind = observations[training_count:]
        if len(blind) < minimum_blind_samples:
            continue
        row = dict(zip(fields, key))
        row.update(_metrics(blind))
        row["training_samples"] = training_count
        # Anchored chronological walk-forward: the first 20% is the initial
        # anchor, followed by four untouched sequential validation windows.
        block = len(observations) // 5
        window_results = []
        if block:
            for window_number in range(1, 5):
                start = window_number * block
                end = (window_number + 1) * block if window_number < 4 else len(observations)
                result = _metrics(observations[start:end])
                result["window"] = window_number
                result["passed"] = _walk_forward_pass(
                    result, tp_points=int(row["tp_points"]), sl_points=int(row["sl_points"]))
                window_results.append(result)
        row["walk_forward_windows"] = len(window_results)
        row["walk_forward_passes"] = sum(result["passed"] for result in window_results)
        row["walk_forward_required"] = "3_OF_4"
        row["walk_forward_results"] = window_results
        rows.append(row)
    rows.sort(key=lambda row: (row["expectancy_r"], row["profit_factor"] or 0,
                               -row["max_drawdown_r"], row["samples"]), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BASELINE_RESEARCH_ONLY",
        "execution_authority": "NONE",
        "profile_strategy_selection": "NOT_DECIDED",
        "point_size": point_size,
        "point_definition": f"1 point = {point_size:g} GOLD# price",
        "round_trip_cost_points": round_trip_cost_points,
        "cost_definition": "explicit configurable cost deducted from every trade",
        "same_bar_collision_policy": "SL_FIRST",
        "split": "chronological first 80% train / final 20% blind-forward per exact segment",
        "minimum_blind_samples": minimum_blind_samples,
        "walk_forward_method": "first 20% anchor plus four sequential 20% validation windows",
        "walk_forward_window_gate": {
            "minimum_samples": 25,
            "minimum_expectancy_r": 0.15,
            "minimum_profit_factor": 1.30,
            "maximum_drawdown_r": 10.0,
            "win_rate_by_planned_rr": {"1:1": 60, "1:1.5": 50, "1:2": 42, "1:3": 32, "1:4": 27},
        },
        "matched_decision_events": len(events),
        "timeframes": {tf: sum(event[1] == tf for event in events) for tf in sorted({event[1] for event in events})},
        "quality": quality,
        "eligible_rank_rows": len(rows),
        "limitations": [
            "Fixed point-distance baseline; ATR±Buffer campaign is not yet included.",
            "Overlapping signals are not yet constrained by daily participation policy.",
            "Results are research evidence and cannot assign P1-P4 or send orders.",
        ],
        "rows": rows,
    }


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "a32_real_backtest_campaign.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = report["rows"]
    if rows:
        with (output_dir / "a32_real_backtest_ranking.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    cards = []
    for row in rows[:100]:
        pf = "∞" if row["profit_factor"] is None else f'{row["profit_factor"]:.2f}'
        cards.append(f'''<article class="card"><h2>🏆 Rank {row["rank"]}: {html.escape(row["pattern"])}</h2>
<p>🕒 <b>{row["timeframe"]}</b> · 🧭 <b>{row["direction"]}</b> · ตัวอย่าง Blind-forward <b>{row["samples"]}</b></p>
<p>🛡️ SL <b>{row["sl_points"]:,} จุด</b> · 🎯 TP <b>{row["tp_points"]:,} จุด</b> · ⏳ ถือสูงสุด <b>{row["max_holding_bars"]} แท่ง</b> (เฉลี่ย {row["average_holding_bars"]:.2f} แท่ง)</p>
<p>✅ Win rate <b>{row["win_rate_pct"]:.2f}%</b> · 📈 Expectancy <b>{row["expectancy_r"]:+.3f}R</b> · ⚖️ Profit factor <b>{pf}</b></p>
<p>📉 Max drawdown <b>{row["max_drawdown_r"]:.2f}R</b> · TP hit {row["tp_rate_pct"]:.2f}% · SL hit {row["sl_rate_pct"]:.2f}%</p></article>''')
    document = f'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AFIP A32 Real Backtest</title>
<style>body{{font:16px system-ui;background:#eef3f8;color:#132238;margin:0}}main{{max-width:1100px;margin:auto;padding:24px}}.notice,.card{{background:white;border:1px solid #d6e0ea;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 4px 14px #1231}}.card h2{{margin:0 0 12px;color:#123d70}}p{{line-height:1.55}}</style><main><h1>📊 AFIP A32 Real Backtest Ranking</h1>
<section class="notice"><b>{report["status"]}</b><p>ต้นทุน {report["round_trip_cost_points"]} จุด/รายการ · 1 จุด = {report["point_size"]} ราคา GOLD# · Train 80% / Blind-forward 20% · Same-bar = SL first</p><p>Matched events {report["matched_decision_events"]:,} · Eligible rankings {report["eligible_rank_rows"]:,} · P1–P4: NOT_DECIDED · Execution authority: NONE</p></section>{''.join(cards)}</main></html>'''
    (output_dir / "a32_real_backtest_ranking.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP A32 real historical baseline backtest")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--point-size", type=float, default=0.01)
    parser.add_argument("--round-trip-cost-points", type=float, default=35.0)
    parser.add_argument("--minimum-blind-samples", type=int, default=30)
    args = parser.parse_args()
    report = run_campaign(args.project_root.resolve(), point_size=args.point_size,
                          round_trip_cost_points=args.round_trip_cost_points,
                          minimum_blind_samples=args.minimum_blind_samples)
    output = args.project_root.resolve() / "runtime" / "research" / "a32_real_backtest"
    write_outputs(report, output)
    print(json.dumps({key: report[key] for key in ("status", "execution_authority", "matched_decision_events",
                                                    "eligible_rank_rows", "timeframes", "limitations")}, indent=2))
    print(f"A32 JSON: {output / 'a32_real_backtest_campaign.json'}")
    print(f"A32 CSV:  {output / 'a32_real_backtest_ranking.csv'}")
    print(f"A32 HTML: {output / 'a32_real_backtest_ranking.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
