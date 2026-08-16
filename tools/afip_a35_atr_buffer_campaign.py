from __future__ import annotations

import argparse
import csv
import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "afip.a35.atr_buffer_real_backtest.v1"
ATR_PERIOD = 14
SL_ATR_MULTIPLIERS = (1.0, 1.5, 2.0)
TP_ATR_MULTIPLIERS = (1.0, 2.0, 3.0)
BUFFER_POINTS = (-200, 0, 200)
HOLDS = (4, 8, 16, 32)
MINIMUM_SL_POINTS = 500


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


def _metrics(rows: list[tuple[str, float, str, int, int, int, float]]) -> dict[str, Any]:
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
        "average_sl_points": round(sum(row[4] for row in rows) / len(rows), 2),
        "average_tp_points": round(sum(row[5] for row in rows) / len(rows), 2),
        "average_atr_points": round(sum(row[6] for row in rows) / len(rows), 2),
        "average_planned_rr": round(sum(row[5] / row[4] for row in rows) / len(rows), 4),
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
        raise FileNotFoundError("A35 required AFIP evidence is missing: " + ", ".join(missing))

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
    atr_values: dict[str, list[float | None]] = {}
    for timeframe, sequence in ordered.items():
        true_ranges: list[float] = []
        values: list[float | None] = []
        previous_close: float | None = None
        for _, (_, high, low, close) in sequence:
            true_range = high - low if previous_close is None else max(
                high - low, abs(high - previous_close), abs(low - previous_close))
            true_ranges.append(true_range / point_size)
            values.append(round(sum(true_ranges[-ATR_PERIOD:]) / ATR_PERIOD, 8)
                          if len(true_ranges) >= ATR_PERIOD else None)
            previous_close = close
        atr_values[timeframe] = values
    events: list[tuple[str, str, str, str, int, float]] = []
    for record in _jsonl(outcome_path, quality):
        timeframe, timestamp = _timeframe(record), record.get("timestamp_utc")
        if not timeframe or not timestamp:
            continue
        direction = directions.get((str(timestamp), timeframe))
        index = positions.get(timeframe, {}).get(str(timestamp))
        atr_points = atr_values.get(timeframe, [])[index] if index is not None else None
        if direction and index is not None and atr_points is not None and index + 1 < len(ordered[timeframe]):
            events.append((str(timestamp), timeframe, str(record.get("pattern_name", "UNKNOWN")),
                           direction, index, atr_points))
    events.sort()

    def trade(event: tuple[str, str, str, str, int, float], tp_points: int, sl_points: int,
              hold: int) -> tuple[float, str, int]:
        _, timeframe, _, direction, index, _ = event
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

    groups: dict[tuple[Any, ...], list[tuple[str, float, str, int, int, int, float]]] = defaultdict(list)
    for event in events:
        atr_points = event[5]
        for sl_multiplier in SL_ATR_MULTIPLIERS:
            for sl_buffer_points in BUFFER_POINTS:
                sl_points = max(MINIMUM_SL_POINTS, round(atr_points * sl_multiplier + sl_buffer_points))
                for tp_multiplier in TP_ATR_MULTIPLIERS:
                    for tp_buffer_points in BUFFER_POINTS:
                        tp_points = max(100, round(atr_points * tp_multiplier + tp_buffer_points))
                        for hold in HOLDS:
                            result_r, reason, bars_used = trade(event, tp_points, sl_points, hold)
                            groups[(event[1], event[2], event[3], sl_multiplier, sl_buffer_points,
                                    tp_multiplier, tp_buffer_points, hold)].append(
                                (event[0], result_r, reason, bars_used, sl_points, tp_points, atr_points))

    rows: list[dict[str, Any]] = []
    fields = ("timeframe", "pattern", "direction", "sl_atr_multiplier", "sl_buffer_points",
              "tp_atr_multiplier", "tp_buffer_points", "max_holding_bars")
    for key, observations in groups.items():
        observations.sort()
        training_count = int(len(observations) * 0.8)
        blind = observations[training_count:]
        if len(blind) < minimum_blind_samples:
            continue
        row = dict(zip(fields, key))
        row.update(_metrics(blind))
        row["sl_points"] = row["average_sl_points"]
        row["tp_points"] = row["average_tp_points"]
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
                    result, tp_points=max(1, round(result["average_tp_points"])),
                    sl_points=max(1, round(result["average_sl_points"])))
                window_results.append(result)
        row["walk_forward_windows"] = len(window_results)
        row["walk_forward_passes"] = sum(result["passed"] for result in window_results)
        row["walk_forward_required"] = "3_OF_4"
        row["walk_forward_results"] = window_results
        rows.append(row)
    for row in rows:
        required_win = _minimum_win_rate_for_rr(row["average_planned_rr"])
        reasons = []
        if row["average_sl_points"] < MINIMUM_SL_POINTS:
            reasons.append("SL_BELOW_500")
        if row["samples"] < 100:
            reasons.append("BLIND_SAMPLES_BELOW_100")
        if row["expectancy_r"] < 0.15:
            reasons.append("EXPECTANCY_BELOW_0_15R")
        if row["profit_factor"] is None or row["profit_factor"] < 1.30:
            reasons.append("PROFIT_FACTOR_BELOW_1_30")
        if row["max_drawdown_r"] > 10.0:
            reasons.append("DRAWDOWN_ABOVE_10R")
        if required_win is None or row["win_rate_pct"] < required_win:
            reasons.append("WIN_RATE_BELOW_RR_GATE")
        if row["walk_forward_passes"] < 3:
            reasons.append("WALK_FORWARD_BELOW_3_OF_4")
        row["eligibility"] = "ELIGIBLE_RESEARCH" if not reasons else "NOT_ELIGIBLE"
        row["eligibility_reasons"] = reasons
        row["minimum_win_rate_for_rr_pct"] = required_win
    rows.sort(key=lambda row: (row["eligibility"] == "ELIGIBLE_RESEARCH", row["expectancy_r"],
                               row["profit_factor"] or 0, -row["max_drawdown_r"],
                               row["win_rate_pct"], row["samples"]), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank

    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ATR_BUFFER_RESEARCH_ONLY",
        "execution_authority": "NONE",
        "profile_strategy_selection": "NOT_DECIDED",
        "point_size": point_size,
        "point_definition": f"1 point = {point_size:g} GOLD# price",
        "round_trip_cost_points": round_trip_cost_points,
        "cost_definition": "explicit configurable cost deducted from every trade",
        "same_bar_collision_policy": "SL_FIRST",
        "split": "chronological first 80% train / final 20% blind-forward per exact segment",
        "minimum_blind_samples": minimum_blind_samples,
        "atr_method": "ATR_14_SIMPLE_TRUE_RANGE_CLOSED_BARS_ONLY",
        "candidate_grid": {
            "sl_atr_multipliers": SL_ATR_MULTIPLIERS,
            "tp_atr_multipliers": TP_ATR_MULTIPLIERS,
            "buffer_points": BUFFER_POINTS,
            "holding_bars": HOLDS,
            "minimum_sl_points": MINIMUM_SL_POINTS,
        },
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
        "eligible_research_rows": sum(row["eligibility"] == "ELIGIBLE_RESEARCH" for row in rows),
        "limitations": [
            "Overlapping signals are not yet constrained by daily participation policy.",
            "Results are research evidence and cannot assign P1-P4 or send orders.",
        ],
        "rows": rows,
    }


def write_outputs(report: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "a35_atr_buffer_campaign.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = report["rows"]
    if rows:
        with (output_dir / "a35_atr_buffer_ranking.csv").open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    cards = []
    for row in rows[:100]:
        pf = "∞" if row["profit_factor"] is None else f'{row["profit_factor"]:.2f}'
        cards.append(f'''<article class="card"><h2>🏆 Rank {row["rank"]}: {html.escape(row["pattern"])}</h2>
<p>🕒 <b>{row["timeframe"]}</b> · 🧭 <b>{row["direction"]}</b> · ตัวอย่าง Blind-forward <b>{row["samples"]}</b></p>
<p>📐 ATR(14) เฉลี่ย <b>{row["average_atr_points"]:,.2f} จุด</b> · RR เฉลี่ย <b>1:{row["average_planned_rr"]:.2f}</b></p>
<p>🛡️ SL = ATR×{row["sl_atr_multiplier"]} {row["sl_buffer_points"]:+} จุด → เฉลี่ย <b>{row["average_sl_points"]:,.2f} จุด</b> (ขั้นต่ำ 500)</p>
<p>🎯 TP = ATR×{row["tp_atr_multiplier"]} {row["tp_buffer_points"]:+} จุด → เฉลี่ย <b>{row["average_tp_points"]:,.2f} จุด</b></p>
<p>⏳ ถือสูงสุด <b>{row["max_holding_bars"]} แท่ง</b> (เฉลี่ย {row["average_holding_bars"]:.2f} แท่ง) · Walk-forward <b>{row["walk_forward_passes"]}/4</b></p>
<p>✅ Win rate <b>{row["win_rate_pct"]:.2f}%</b> · 📈 Expectancy <b>{row["expectancy_r"]:+.3f}R</b> · ⚖️ Profit factor <b>{pf}</b></p>
<p>📉 Max drawdown <b>{row["max_drawdown_r"]:.2f}R</b> · TP hit {row["tp_rate_pct"]:.2f}% · SL hit {row["sl_rate_pct"]:.2f}%</p>
<p><b>สถานะ: {row["eligibility"]}</b> · {html.escape(', '.join(row["eligibility_reasons"]) or 'ผ่าน Research gate')}</p></article>''')
    document = f'''<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>AFIP A35 ATR Buffer Backtest</title>
<style>body{{font:16px system-ui;background:#eef3f8;color:#132238;margin:0}}main{{max-width:1100px;margin:auto;padding:24px}}.notice,.card{{background:white;border:1px solid #d6e0ea;border-radius:14px;padding:18px;margin:14px 0;box-shadow:0 4px 14px #1231}}.card h2{{margin:0 0 12px;color:#123d70}}p{{line-height:1.55}}</style><main><h1>📊 AFIP A35 ATR±Buffer Ranking</h1>
<section class="notice"><b>{report["status"]}</b><p>ATR(14) จากแท่งปิด · SL ขั้นต่ำ 500 จุด · ต้นทุน {report["round_trip_cost_points"]} จุด/รายการ · Train/Blind-forward + Walk-forward 4 ช่วง</p><p>Matched events {report["matched_decision_events"]:,} · Candidate {report["eligible_rank_rows"]:,} · ELIGIBLE_RESEARCH {report["eligible_research_rows"]:,}</p><p>⚠️ Research eligibility ไม่ใช่ Demo/Live promotion · P1–P4: NOT_DECIDED · Execution authority: NONE</p></section>{''.join(cards)}</main></html>'''
    (output_dir / "a35_atr_buffer_ranking.html").write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="AFIP A35 ATR±Buffer real historical backtest")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--point-size", type=float, default=0.01)
    parser.add_argument("--round-trip-cost-points", type=float, default=35.0)
    parser.add_argument("--minimum-blind-samples", type=int, default=30)
    args = parser.parse_args()
    report = run_campaign(args.project_root.resolve(), point_size=args.point_size,
                          round_trip_cost_points=args.round_trip_cost_points,
                          minimum_blind_samples=args.minimum_blind_samples)
    output = args.project_root.resolve() / "runtime" / "research" / "a35_atr_buffer"
    write_outputs(report, output)
    print(json.dumps({key: report[key] for key in ("status", "execution_authority", "matched_decision_events",
                                                    "eligible_rank_rows", "timeframes", "limitations")}, indent=2))
    print(f"A35 JSON: {output / 'a35_atr_buffer_campaign.json'}")
    print(f"A35 CSV:  {output / 'a35_atr_buffer_ranking.csv'}")
    print(f"A35 HTML: {output / 'a35_atr_buffer_ranking.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
