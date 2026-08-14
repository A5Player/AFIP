"""Explicitly authorized P4 Demo open-only proof through DemoExecutionGateway."""
from __future__ import annotations
from dataclasses import asdict
import json,os
from pathlib import Path
from types import SimpleNamespace
import sys
from typing import Any,Iterable,Mapping

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from afip.demo_execution_gateway import DemoExecutionGateway,DemoExecutionRunner

class SingleOrderGuardMT5:
    """Proxy the established MT5 adapter and reject unsafe/multiple requests."""
    def __init__(self,inner:Any):self.inner=inner;self.checked:dict[str,Any]|None=None;self.check_calls=0;self.send_calls=0
    def __getattr__(self,name:str)->Any:return getattr(self.inner,name)
    @staticmethod
    def _validate(request:Mapping[str,Any])->None:
        if str(request.get("symbol"))!="GOLD#":raise RuntimeError("a27_symbol_must_be_gold_hash")
        if abs(float(request.get("volume",0))-0.01)>1e-12:raise RuntimeError("a27_volume_must_equal_0_01")
        if float(request.get("sl",0) or 0)<=0 or float(request.get("tp",0) or 0)<=0:raise RuntimeError("a27_sl_tp_required")
        if request.get("position") not in (None,0,""):raise RuntimeError("a27_open_only_position_field_forbidden")
    def order_check(self,request:Mapping[str,Any])->Any:
        self._validate(request);self.check_calls+=1
        if self.check_calls!=1:return SimpleNamespace(retcode=-27001,comment="a27_exactly_one_order_guard")
        self.checked=dict(request);return self.inner.order_check(request)
    def order_send(self,request:Mapping[str,Any])->Any:
        self._validate(request)
        if self.check_calls!=1 or self.send_calls!=0 or self.checked!=dict(request):raise RuntimeError("a27_unchecked_or_multiple_send_blocked")
        self.send_calls+=1;return self.inner.order_send(request)

def run(root:Path,approve:bool,acknowledge_manual_close:bool)->dict[str,Any]:
    if not approve or not acknowledge_manual_close:raise ValueError("both explicit approval flags are required")
    config=root.resolve()/"config/four_profile_demo.json";profile,policy=DemoExecutionRunner._load(config,"P4")
    if profile.profile_id!="P4" or profile.symbol!="GOLD#":raise RuntimeError("a27_p4_gold_profile_required")
    import MetaTrader5 as mt5
    guarded=SingleOrderGuardMT5(mt5);previous={name:os.environ.get(name) for name in
      ("AFIP_DEMO_EXECUTION_ARMED","AFIP_P1_DEMO_ARMED","AFIP_P2_DEMO_ARMED","AFIP_P3_DEMO_ARMED","AFIP_P4_DEMO_ARMED")}
    os.environ.update({"AFIP_DEMO_EXECUTION_ARMED":"YES","AFIP_P1_DEMO_ARMED":"NO","AFIP_P2_DEMO_ARMED":"NO","AFIP_P3_DEMO_ARMED":"NO","AFIP_P4_DEMO_ARMED":"YES"})
    try:report=DemoExecutionGateway(profile,policy,mt5=guarded).run_cycle()
    finally:
        for name,value in previous.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
    value=report.as_dict();status=str(value.get("status"));sent=int(value.get("sent_units",0) or 0)
    proof_status="BROKER_OPEN_ACKNOWLEDGED_MANUAL_CLOSE_REQUIRED" if status=="ORDER_SENT" and sent==1 and guarded.send_calls==1 else "NO_ORDER_SENT_GATES_OR_GUARD_BLOCKED"
    return {"schema":"afip.a27.p4_demo_open_only_proof.v1","status":proof_status,
      "gateway_status":status,"gateway_reason":value.get("reason"),"profile_id":"P4","symbol":"GOLD#",
      "maximum_authorized_orders":1,"maximum_authorized_volume":0.01,"order_check_calls":guarded.check_calls,
      "order_send_calls":guarded.send_calls,"sent_units":sent,"tickets":value.get("tickets",()),
      "mt5_result_code":value.get("mt5_result_code"),"mt5_result_comment":value.get("mt5_result_comment"),
      "sl_tp_required":True,"automatic_close_performed":False,"manual_close_required":proof_status.startswith("BROKER_OPEN"),
      "execution_path":"afip.demo_execution_gateway.DemoExecutionGateway","gateway_report":value}

def main(argv:Iterable[str]|None=None)->int:
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--project-root",required=True);p.add_argument("--output")
    p.add_argument("--approve-p4-demo-open",action="store_true");p.add_argument("--acknowledge-manual-close",action="store_true");a=p.parse_args(argv)
    try:r=run(Path(a.project_root),a.approve_p4_demo_open,a.acknowledge_manual_close)
    except Exception as exc:print(json.dumps({"status":"BLOCKED","reason":f"{type(exc).__name__}:{exc}"},indent=2));return 2
    encoded=json.dumps(r,indent=2,ensure_ascii=False,default=str)
    if a.output:path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(encoded+"\n",encoding="utf-8")
    print(encoded);return 0
if __name__=="__main__":raise SystemExit(main())
