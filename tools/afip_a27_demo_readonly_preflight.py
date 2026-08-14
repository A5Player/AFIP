"""A27 passive four-profile demo preflight; never attaches to MT5 or writes runtime."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Iterable

# Direct execution from ``C:\AFIP\tools`` otherwise exposes only the tools
# directory on sys.path.  Resolve the repository root from this file itself.
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from afip.four_profile_operations.mt5_connection import MT5MultiTerminalConnectionManager


def capture(project_root: Path) -> dict[str, Any]:
    root=project_root.resolve()
    manager=MT5MultiTerminalConnectionManager(root/"config/four_profile_demo.json")
    # The established manager normally publishes health telemetry.  A27 is an
    # audit, so suppress every writer before passive process observation.
    manager._write_health=lambda *_args,**_kwargs: None
    manager._write_live_snapshot=lambda *_args,**_kwargs: None
    result=manager.check(active=False)
    profiles=[]
    for item in result.get("profiles",()):
        profiles.append({
          "profile_id":item.get("profile_id"),"connection_status":item.get("connection_status"),
          "terminal_exists":item.get("terminal_exists"),"process_alive":item.get("process_alive"),
          "terminal_path":item.get("terminal_path"),"configured_server":item.get("server"),
          "configured_account":item.get("account"),"symbol":"GOLD#",
          "monitoring_mode":item.get("monitoring_mode"),"evidence_kind":item.get("evidence_kind"),
          "demo_identity_verified":False,"order_sent":False,
        })
    expected={"P1","P2","P3","P4"};observed={str(item["profile_id"]) for item in profiles}
    passive_ready=(result.get("status")=="READY" and observed==expected and
                   all(item["terminal_exists"] and item["process_alive"] for item in profiles))
    return {"schema":"afip.a27.demo_readonly_preflight.v1",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),"project_root":str(root),
      "status":"DEMO_IDENTITY_PROOF_REQUIRED" if passive_ready else "PASSIVE_PREFLIGHT_BLOCKED",
      "passive_process_mapping_ready":passive_ready,"demo_identity_verified":False,
      "broker_session_attached":False,"mt5_initialized":False,"orders_sent":False,
      "runtime_telemetry_written":False,"execution_authority":"NONE",
      "reason":"passive_terminal_mapping_ready_active_demo_identity_still_required" if passive_ready
               else "open_configured_p1_p4_terminals_and_recheck_mapping",
      "profiles":profiles,"validation_errors":result.get("validation_errors",[]),
      "next_required_proof":"explicit_active_readonly_demo_identity_and_gold_tick_check"}


def main(argv: Iterable[str]|None=None)->int:
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument("--project-root",required=True);parser.add_argument("--output")
    args=parser.parse_args(argv);report=capture(Path(args.project_root));encoded=json.dumps(report,indent=2,ensure_ascii=False)
    if args.output:
        path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded+"\n",encoding="utf-8")
    print(encoded);return 0


if __name__=="__main__":raise SystemExit(main())
