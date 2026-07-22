from __future__ import annotations
from datetime import datetime, timezone
import json, os
from pathlib import Path
from typing import Any, Mapping

def utc_now()->str: return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def read_json(path:Path)->dict[str,Any]:
 try:
  value=json.loads(path.read_text(encoding='utf-8-sig'))
  return value if isinstance(value,dict) else {}
 except (OSError,ValueError,TypeError,UnicodeError): return {}
def atomic_json(path:Path,payload:Mapping[str,Any])->None:
 path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
 tmp.write_text(json.dumps(dict(payload),ensure_ascii=False,indent=2,default=str),encoding='utf-8'); tmp.replace(path)
def pid_running(pid:int|None)->bool:
 if not pid or pid<1:return False
 try: os.kill(pid,0); return True
 except OSError:return False
