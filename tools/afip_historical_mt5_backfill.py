"""Run AFIP GOLD# historical backfill against one explicitly selected, already-open MT5 terminal."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from afip.mt5_historical_integration import HistoricalDataDashboard, ResumableMT5HistoricalProvider
from afip.mt5_historical_integration.mt5_gateway import MetaTrader5ReadOnlyGateway, write_json_atomic
from afip.runtime_standard_adapter import BackfillRequest


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--project-root", default=".")
    value.add_argument("--profile", default="P1", choices=("P1", "P2", "P3", "P4"))
    value.add_argument("--config", default="config/four_profile_demo.json")
    value.add_argument("--terminal-path")
    value.add_argument("--symbol")
    value.add_argument("--timeframe", default="M1", choices=("M1", "M5", "M15", "M30", "H1", "H4", "D1"))
    value.add_argument("--start-utc")
    value.add_argument("--end-utc")
    value.add_argument("--maximum-bars-per-batch", type=int, default=50000)
    value.add_argument("--maximum-batches", type=int)
    value.add_argument("--request-id")
    return value


def _load_profile(root: Path, config_value: str, profile_id: str) -> dict[str, Any]:
    config_path = Path(config_value)
    if not config_path.is_absolute():
        config_path = root / config_path
    payload = json.loads(config_path.read_text(encoding="utf-8-sig"))
    profiles = payload.get("profiles", [])
    for profile in profiles:
        if str(profile.get("profile_id", "")).upper() == profile_id.upper():
            return dict(profile)
    raise ValueError(f"Profile not found in {config_path}: {profile_id}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = Path(args.project_root).resolve()
    dataset = root / "runtime" / "research" / "historical_data"
    dashboard_path = root / "runtime" / "dashboard" / "historical_data_status.json"
    try:
        profile = _load_profile(root, args.config, args.profile)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        payload = {"status": "BLOCKED", "reason": "profile_configuration_unavailable", "detail": str(exc)}
        write_json_atomic(dashboard_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    terminal_path = args.terminal_path or profile.get("mt5_terminal")
    symbol = args.symbol or profile.get("symbol") or "GOLD#"
    request_id = args.request_id or f"{symbol.replace('#','')}-{args.timeframe}-{args.profile}"
    gateway = MetaTrader5ReadOnlyGateway()
    bound, bind_reason = gateway.bind_running_terminal(str(terminal_path or ""), portable=True)
    if not bound:
        payload = {
            "status": "BLOCKED", "reason": bind_reason, "profile_id": args.profile,
            "terminal_path": str(terminal_path or ""),
            "operator_action": "Open the configured MT5 terminal manually, log in, then rerun this command.",
        }
        write_json_atomic(dashboard_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2

    try:
        evidence = gateway.terminal_evidence()
        if evidence.status != "READY":
            payload = {"status": "BLOCKED", "reason": evidence.reason, "profile_id": args.profile,
                       "terminal": evidence.as_dict()}
            write_json_atomic(dashboard_path, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2
        configured_server = str(profile.get("server") or "")
        if configured_server and evidence.server and configured_server != evidence.server:
            payload = {"status": "BLOCKED", "reason": "configured_server_mismatch", "profile_id": args.profile,
                       "expected_server": configured_server, "terminal": evidence.as_dict()}
            write_json_atomic(dashboard_path, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2
        request = BackfillRequest(request_id, symbol, args.timeframe, args.start_utc, args.end_utc,
                                  args.maximum_bars_per_batch)
        result = ResumableMT5HistoricalProvider(dataset).run(request, gateway, args.maximum_batches)
        snapshot = HistoricalDataDashboard(dataset).snapshot(request_id)
        snapshot["profile_id"] = args.profile
        snapshot["terminal"] = evidence.as_dict()
        snapshot["binding_reason"] = bind_reason
        snapshot["broker_time_offset_seconds"] = gateway.broker_time_offset_seconds
        snapshot["history_discovery"] = gateway.last_history_discovery
        write_json_atomic(dashboard_path, snapshot)
        print(json.dumps({"result": result.as_dict(), "dashboard": snapshot}, ensure_ascii=False, indent=2))
        return 0 if result.status in {"COMPLETED", "PAUSED"} else 2
    finally:
        gateway.close()


if __name__ == "__main__":
    sys.exit(main())
