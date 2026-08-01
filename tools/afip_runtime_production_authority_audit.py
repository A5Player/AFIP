from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SOURCE_ROOTS = {"afip", "tools", "scripts", "service", "services"}
EXCLUDED_PARTS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules",
    "dist", "build", "runtime", "tests", "test", "docs", "documentation",
    "examples", "backups", "backup",
}
ROLE_TERMS = {
    "intelligence", "engine", "decision", "signal", "regime", "pattern", "risk",
    "execution", "research", "historical", "collector", "loader", "gateway",
    "supervisor", "launcher", "runner", "router", "authority", "dashboard",
}
WRITE_METHODS = {"write_text", "write_bytes", "touch", "replace", "rename", "to_json"}
READ_METHODS = {"read_text", "read_bytes", "open", "load", "loads"}
PROCESS_NAMES = {"popen", "run", "call", "check_call", "check_output", "system"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def excluded(path: Path, root: Path) -> bool:
    parts = [part.lower() for part in path.relative_to(root).parts[:-1]]
    for part in parts:
        if part in EXCLUDED_PARTS:
            return True
        if part.startswith(("pytest_temp", "pytest-", "tmp_", "temp_", "pack_", "patch_")):
            return True
        if "certification_pack" in part:
            return True
    return False


def iter_sources(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".py", ".ps1", ".bat", ".cmd"}:
            continue
        if excluded(path, root):
            continue
        rel = path.relative_to(root)
        first = rel.parts[0].lower()
        if len(rel.parts) == 1 or first in SOURCE_ROOTS:
            yield path


def dotted(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        out=[]
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str): out.append(value.value)
            else: out.append("{dynamic}")
        return "".join(out)
    if isinstance(node, ast.Call) and dotted(node.func).lower() in {"path", "pathlib.path"} and node.args:
        return literal_string(node.args[0])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left, right = literal_string(node.left), literal_string(node.right)
        if left is not None and right is not None:
            left_clean = left.rstrip("/\\")
    right_clean = right.lstrip("/\\")
    return f"{left_clean}/{right_clean}"
    return None


def normalize_data_path(value: str | None) -> str | None:
    if not value: return None
    value=value.replace("\\", "/")
    if value.lower().endswith((".json", ".jsonl", ".csv", ".parquet")):
        return value
    return None


def module_name(path: Path, root: Path) -> str:
    rel=path.relative_to(root).with_suffix("")
    parts=list(rel.parts)
    if parts and parts[-1] == "__init__": parts=parts[:-1]
    return ".".join(parts)


def resolve_import(current_module: str, module: str | None, level: int) -> str:
    if level <= 0: return module or ""
    base=current_module.split(".")
    if base: base=base[:-1]
    if level > 1: base=base[:-(level-1)] if level-1 <= len(base) else []
    if module: base.extend(module.split("."))
    return ".".join(base)


def inspect_python(path: Path, root: Path) -> dict[str, Any]:
    rel=path.relative_to(root).as_posix()
    module=module_name(path, root)
    source=path.read_text(encoding="utf-8", errors="replace")
    item={
        "path": rel, "module": module, "sha256": sha256_text(source), "imports": [],
        "definitions": [], "data_access": [], "process_calls": [], "main_entrypoint": False,
        "parse_error": None,
    }
    try: tree=ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        item["parse_error"]=f"{exc.msg}:{exc.lineno}"; return item
    aliases: dict[str,str]={}
    handles: dict[str,str]={}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                item["imports"].append(a.name); aliases[a.asname or a.name.split('.')[0]]=a.name
        elif isinstance(node, ast.ImportFrom):
            resolved=resolve_import(module, node.module, node.level)
            if resolved: item["imports"].append(resolved)
            for a in node.names: aliases[a.asname or a.name]=f"{resolved}.{a.name}".strip('.')
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            item["definitions"].append({"name":node.name,"kind":type(node).__name__,"line":node.lineno})
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            name=dotted(node.value.func).lower(); leaf=name.rsplit('.',1)[-1]
            if leaf == 'open' and node.value.args:
                target=normalize_data_path(literal_string(node.value.args[0]))
                if target:
                    mode=literal_string(node.value.args[1]) if len(node.value.args)>1 else 'r'
                    for t in node.targets:
                        if isinstance(t, ast.Name): handles[t.id]=target
                    item['data_access'].append({'target':target,'role':'writer' if mode and any(x in mode for x in 'wax+') else 'reader','line':node.lineno,'via':'open'})
        elif isinstance(node, ast.Call):
            name=dotted(node.func).lower(); leaf=name.rsplit('.',1)[-1]
            if leaf in PROCESS_NAMES or any(x in name for x in ('subprocess.','multiprocessing.','os.system')):
                call = {'call': name, 'line': node.lineno}
                item['process_calls'].append(call)
                values = []
                for arg in node.args:
                    value = literal_string(arg)
                    if value:
                        values.append(value)
                    elif isinstance(arg, (ast.List, ast.Tuple)):
                        values.extend(filter(None, (literal_string(x) for x in arg.elts)))
                command = ' '.join(values)
                module_match = re.search(r'(?:python(?:\.exe)?|py)\s+(?:-[^ ]+\s+)*-m\s+([A-Za-z_][\w.]*)', command, re.I)
                file_match = re.search(r'([A-Za-z0-9_./\\-]+\.(?:py|ps1|bat|cmd))', command, re.I)
                if module_match:
                    item['invocation_targets'].append({'kind':'python_module','target':module_match.group(1),'line':node.lineno,'dynamic':'{dynamic}' in command})
                elif file_match:
                    item['invocation_targets'].append({'kind':'file','target':file_match.group(1).replace('\\','/'),'line':node.lineno,'dynamic':'{dynamic}' in command})
            if isinstance(node.func, ast.Attribute):
                owner=literal_string(node.func.value)
                target=normalize_data_path(owner)
                if target and leaf in WRITE_METHODS|READ_METHODS:
                    item['data_access'].append({'target':target,'role':'writer' if leaf in WRITE_METHODS else 'reader','line':node.lineno,'via':leaf})
            if leaf == 'open' and node.args:
                target=normalize_data_path(literal_string(node.args[0]))
                if target:
                    mode=literal_string(node.args[1]) if len(node.args)>1 else 'r'
                    item['data_access'].append({'target':target,'role':'writer' if mode and any(x in mode for x in 'wax+') else 'reader','line':node.lineno,'via':'open'})
            if leaf in {'dump','load'} and len(node.args)>1:
                handle=node.args[1]
                if isinstance(handle, ast.Name) and handle.id in handles:
                    item['data_access'].append({'target':handles[handle.id],'role':'writer' if leaf=='dump' else 'reader','line':node.lineno,'via':leaf})
            for arg in list(node.args)+[kw.value for kw in node.keywords]:
                target=normalize_data_path(literal_string(arg))
                if target and leaf in {'dump','to_json'}:
                    item['data_access'].append({'target':target,'role':'writer','line':node.lineno,'via':leaf})
        elif isinstance(node, ast.If):
            try: test=ast.unparse(node.test)
            except Exception: test=''
            if '__name__' in test and '__main__' in test: item['main_entrypoint']=True
    item['imports']=sorted(set(item['imports']))
    uniq={json.dumps(x,sort_keys=True):x for x in item['data_access']}; item['data_access']=sorted(uniq.values(), key=lambda x:(x['target'],x['role'],x['line']))
    return item


def inspect_script(path: Path, root: Path) -> dict[str, Any]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding='utf-8', errors='replace')
    calls: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    variables: dict[str, str] = {}
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        low = line.lower()
        assignment = re.match(r'^\s*\$([A-Za-z_][\w]*)\s*=\s*["\']([^"\']+)["\']', line)
        if assignment:
            variables[assignment.group(1).lower()] = assignment.group(2)
        if not any(x in low for x in ('start-process', 'python ', 'python.exe', 'pythonw', 'powershell -file', '& ', 'call ', '.ps1', '.bat')):
            continue
        calls.append({'line': no, 'text': line[:300]})
        expanded = line
        for key, value in variables.items():
            expanded = re.sub(rf'\${re.escape(key)}\b', lambda _m, replacement=value: replacement, expanded, flags=re.I)
        mm = re.search(r'(?:python(?:\.exe)?|py)\s+(?:-[^ ]+\s+)*-m\s+([A-Za-z_][\w.]*)', expanded, re.I)
        if mm:
            targets.append({'kind':'python_module','target':mm.group(1),'line':no,'dynamic':'$' in expanded or '%' in expanded})
        for fm in re.finditer(r'(?<![\w])([A-Za-z0-9_$%{}()./\\-]+\.(?:py|ps1|bat|cmd))(?![\w])', expanded, re.I):
            target=fm.group(1).strip('"\'').replace('\\','/')
            if target.lower() == Path(rel).name.lower():
                continue
            targets.append({'kind':'file','target':target,'line':no,'dynamic':any(x in target for x in ('$','%','{','('))})
    uniq={json.dumps(x,sort_keys=True):x for x in targets}
    return {'path':rel,'module':None,'sha256':sha256_text(text),'imports':[],'definitions':[],
            'data_access':[],'process_calls':calls,'invocation_targets':list(uniq.values()),
            'main_entrypoint':True,'parse_error':None}


def find_historical_truth(root: Path) -> dict[str, Any]:
    runtime=root/'runtime'
    if not runtime.is_dir(): return {'source':None,'status':'NOT_FOUND','boundaries_are_separated':False}
    candidates=[]
    for p in runtime.rglob('*.json'):
        rel=[x.lower() for x in p.relative_to(root).parts]
        if any(x.startswith(('pytest_temp','pytest-','tmp_','test_')) or x in {'architecture_intelligence_certification','.pytest_cache'} for x in rel): continue
        try:
            if p.stat().st_size > 20_000_000: continue
            data=json.loads(p.read_text(encoding='utf-8'))
        except Exception: continue
        if not isinstance(data,dict): continue
        disc=data.get('history_discovery') if isinstance(data.get('history_discovery'),dict) else {}
        keys={*data.keys(),*disc.keys()}
        score=sum(k in keys for k in ('coverage_start_utc','coverage_end_utc','next_start_utc','earliest_available_utc','bars_observed','timeframe'))
        if score>=3: candidates.append((score,p.stat().st_mtime,p,data,disc))
    if not candidates: return {'source':None,'status':'NOT_FOUND','boundaries_are_separated':False}
    _,_,p,data,disc=max(candidates,key=lambda x:(x[0],x[1]))
    broker=disc.get('earliest_available_utc') or data.get('earliest_available_utc')
    dataset=data.get('coverage_start_utc'); checkpoint=data.get('next_start_utc')
    return {
        'source':p.relative_to(root).as_posix(),'status':data.get('status'),'quality_status':data.get('quality_status'),
        'broker_history_start_utc':broker,'dataset_start_utc':dataset,'dataset_end_utc':data.get('coverage_end_utc'),
        'checkpoint_next_start_utc':checkpoint,'boundaries_are_separated':all(v is not None for v in (broker,dataset,checkpoint)),
        'missing_intervals':data.get('missing_intervals') or data.get('missing_interval_count'),'batches_completed':data.get('batches_completed'),
        'total_dataset_bytes':data.get('total_dataset_bytes'),'selection_score':max(candidates,key=lambda x:(x[0],x[1]))[0],
    }


def role_categories(path: str, definitions: list[dict[str,Any]]) -> list[str]:
    text=' '.join([path]+[x['name'] for x in definitions]).lower()
    return sorted(term for term in ROLE_TERMS if term in text)



PRIMARY_RUNTIME_ROOTS = {
    "START_AFIP.ps1", "START_AFIP_SAFE.ps1", "START_AFIP_LONG_RUN.ps1",
    "RUN_AFIP_V1_FINAL_OPERATIONAL_RUNTIME.ps1", "RUN.ps1", "RUN.bat", "afip.py",
}
CONTROL_COMMAND_NAMES = {
    "STOP_AFIP.ps1", "STOP_AFIP_EMERGENCY.ps1", "STATUS_AFIP.ps1",
    "STOP_AFIP_LONG_RUN.ps1", "STATUS_AFIP_LONG_RUN.ps1",
}

def domain_for_path(path: str) -> str:
    low = path.lower(); name = Path(path).name.lower()
    if low.startswith('tests/') or '/test_' in low or name.startswith('test_'): return 'TEST'
    if name.startswith(('install_', 'apply_', 'rollback_')) or low.startswith(('installer/', 'installers/')): return 'INSTALLER_MIGRATION'
    if 'certif' in low or name.startswith(('validate_', 'verify_')): return 'CERTIFICATION'
    if 'dashboard' in low: return 'DASHBOARD'
    if 'historical' in low or 'backfill' in low or 'replay' in low: return 'HISTORICAL_DATA'
    if 'research' in low or 'collector' in low: return 'RESEARCH'
    if any(x in low for x in ('execution','router','gateway','mt5','order_','position_')): return 'LIVE_EXECUTION'
    if low.startswith('tools/') or name.startswith(('run_milestone_','run_phase_','run_production_','build_','clean_','collect_')): return 'DEVELOPMENT_TOOL'
    if low.startswith('afip/') or name in {'start_afip.ps1','run.ps1','run.bat','afip.py'}: return 'PRODUCTION_RUNTIME'
    return 'SUPPORT'

def operational_role(path: str, process_launcher: bool, main_entrypoint: bool) -> str:
    name = Path(path).name.upper(); low = path.lower(); domain = domain_for_path(path)
    if path in PRIMARY_RUNTIME_ROOTS or name in {x.upper() for x in PRIMARY_RUNTIME_ROOTS}:
        return 'PRIMARY_RUNTIME_ROOT'
    if name in {x.upper() for x in CONTROL_COMMAND_NAMES} or name.startswith(('STOP_', 'STATUS_')):
        return 'CONTROL_COMMAND'
    if domain in {'INSTALLER_MIGRATION','CERTIFICATION','DEVELOPMENT_TOOL','TEST'}:
        return 'CERTIFICATION_ONLY' if domain == 'CERTIFICATION' else 'NON_RUNTIME_TOOL'
    if domain == 'DASHBOARD':
        return 'DASHBOARD_BUILDER' if any(x in name for x in ('BUILD','ONCE')) else ('BACKGROUND_WORKER' if process_launcher else 'ONE_SHOT_TOOL')
    if any(x in name for x in ('ONCE', 'CHECK', 'VERIFY', 'AUDIT', 'CERTIFY')):
        return 'ONE_SHOT_TOOL'
    if process_launcher and domain in {'PRODUCTION_RUNTIME','LIVE_EXECUTION','RESEARCH','HISTORICAL_DATA'}:
        return 'BACKGROUND_WORKER'
    if main_entrypoint:
        return 'ONE_SHOT_TOOL'
    return 'LIBRARY_COMPONENT'

def authority_terms(path: str, categories: list[str]) -> list[str]:
    text=(' '.join([path]+categories)).lower(); out=[]
    mapping={'RUNTIME_AUTHORITY':('supervisor','operational_runtime','runtime_authority'), 'EXECUTION_AUTHORITY':('execution','router','gateway'), 'CAPITAL_AUTHORITY':('capital','lot','position_sizing'), 'HISTORICAL_AUTHORITY':('historical','backfill'), 'RESEARCH_AUTHORITY':('research','collector'), 'DASHBOARD_AUTHORITY':('dashboard',)}
    for key, terms in mapping.items():
        if any(t in text for t in terms): out.append(key)
    return out

def reachable_from(root_path: str, edges: dict[str, set[str]]) -> set[str]:
    seen={root_path}; q=deque([root_path])
    while q:
        cur=q.popleft()
        for nxt in edges.get(cur,()):
            if nxt not in seen:
                seen.add(nxt); q.append(nxt)
    seen.discard(root_path)
    return seen


def build_report(root: Path) -> dict[str, Any]:
    root=root.resolve(); files=[]; module_to_path={}; path_to_module={}; hashes=defaultdict(list)
    for p in iter_sources(root):
        item=inspect_python(p,root) if p.suffix.lower()=='.py' else inspect_script(p,root)
        files.append(item); hashes[item['sha256']].append(item['path'])
        if item['module']: module_to_path[item['module']]=item['path']; path_to_module[item['path']]=item['module']
    edges=defaultdict(set); reverse=defaultdict(set)
    for item in files:
        if item['module']:
            for imp in item['imports']:
                target=imp
                while target and target not in module_to_path: target=target.rsplit('.',1)[0] if '.' in target else ''
                if target:
                    dst=module_to_path[target]; edges[item['path']].add(dst); reverse[dst].add(item['path'])
        for inv in item.get('invocation_targets', []):
            dst = None
            if inv['kind'] == 'python_module':
                target = inv['target']
                while target and target not in module_to_path:
                    target = target.rsplit('.',1)[0] if '.' in target else ''
                if target: dst = module_to_path[target]
            elif not inv.get('dynamic'):
                raw = inv['target'].replace('\\','/').lstrip('./')
                candidates = [raw, Path(raw).name]
                for candidate in candidates:
                    matches=[x['path'] for x in files if x['path'].lower()==candidate.lower() or Path(x['path']).name.lower()==candidate.lower()]
                    if len(matches)==1: dst=matches[0]; break
            if dst and dst != item['path']:
                edges[item['path']].add(dst); reverse[dst].add(item['path'])
    all_entrypoints=sorted({x['path'] for x in files if x['main_entrypoint']})
    entrypoint_classification=[]
    for x in files:
        if x['main_entrypoint']:
            entrypoint_classification.append({'path':x['path'],'domain':domain_for_path(x['path']),'operational_role':operational_role(x['path'],bool(x['process_calls']),True),'process_launcher':bool(x['process_calls']),'invocation_target_count':len(x.get('invocation_targets',[]))})
    primary_roots=sorted(x['path'] for x in files if x['main_entrypoint'] and operational_role(x['path'],bool(x['process_calls']),True)=='PRIMARY_RUNTIME_ROOT')
    entrypoints=primary_roots
    reachable=set(entrypoints); q=deque(entrypoints)
    while q:
        cur=q.popleft()
        for nxt in edges.get(cur,()):
            if nxt not in reachable: reachable.add(nxt); q.append(nxt)
    access=defaultdict(lambda:{'readers':[],'writers':[]})
    for item in files:
        for a in item['data_access']:
            access[a['target']]['writers' if a['role']=='writer' else 'readers'].append({'path':item['path'],'line':a['line'],'via':a['via']})
    shared=[]
    for target,roles in sorted(access.items()):
        readers={x['path'] for x in roles['readers']}; writers={x['path'] for x in roles['writers']}
        if len(readers|writers)>1:
            shared.append({'target':target,'readers':roles['readers'],'writers':roles['writers'],'reader_file_count':len(readers),'writer_file_count':len(writers),'risk':'HIGH' if len(writers)>1 else ('MEDIUM' if len(writers)==1 else 'LOW')})
    defs=defaultdict(list)
    for item in files:
        for d in item['definitions']:
            key=d['name'].lower()
            if any(t in key for t in ROLE_TERMS): defs[key].append({'path':item['path'],'line':d['line'],'kind':d['kind']})
    repeats=[]
    for name,locs in sorted(defs.items()):
        if len(locs)>1:
            modules={x['path'].rsplit('/',1)[0] for x in locs}
            repeats.append({'definition':name,'locations':locs,'count':len(locs),'classification':'REVIEW' if len(modules)>1 else 'LIKELY_LOCAL_PATTERN'})
    components=[]
    for item in files:
        cats=role_categories(item['path'],item['definitions'])
        if not cats: continue
        incoming=len(reverse.get(item['path'],set())); outgoing=len(edges.get(item['path'],set()))
        state='KEEP_CANDIDATE' if item['path'] in reachable else ('UTILITY_OR_LIBRARY' if incoming else 'LEGACY_CANDIDATE')
        domain=domain_for_path(item['path']); tier=operational_role(item['path'], bool(item['process_calls']), item['main_entrypoint'])
        confidence='LOW'
        if state=='LEGACY_CANDIDATE':
            confidence='HIGH' if incoming==0 and domain in {'PRODUCTION_RUNTIME','LIVE_EXECUTION'} and not item['process_calls'] else ('MEDIUM' if incoming==0 else 'LOW')
        components.append({'path':item['path'],'domain':domain,'categories':cats,'authority_roles':authority_terms(item['path'],cats),'reachable_from_production_entrypoint':item['path'] in reachable,'incoming_importers':incoming,'outgoing_dependencies':outgoing,'main_entrypoint':item['main_entrypoint'],'operational_role':tier,'process_launcher':bool(item['process_calls']),'classification':state,'legacy_confidence':confidence})
    duplicate_groups=[]
    for digest,paths in hashes.items():
        if len(paths)>1:
            nonempty=[]
            for p in paths:
                fp=root/p
                try: size=fp.stat().st_size
                except OSError: size=0
                nonempty.append((p,size))
            duplicate_groups.append({'sha256':digest,'files':[{'path':p,'size':s} for p,s in sorted(nonempty)],'count':len(paths),'classification':'BENIGN_EMPTY_PACKAGE_FILES' if all(s==0 for _,s in nonempty) else 'REVIEW'})
    multiwriters=[x for x in shared if x['writer_file_count']>1]
    legacy=[x for x in components if x['classification']=='LEGACY_CANDIDATE']
    domain_summary=defaultdict(lambda:{'files':0,'entrypoints':0,'production_reachable':0,'legacy_candidates':0})
    authority_map=defaultdict(list)
    for x in components:
        d=domain_summary[x['domain']]; d['files']+=1; d['entrypoints']+=int(bool(x['main_entrypoint'])); d['production_reachable']+=int(bool(x['reachable_from_production_entrypoint'])); d['legacy_candidates']+=int(x['classification']=='LEGACY_CANDIDATE')
        for role in x['authority_roles']: authority_map[role].append(x['path'])
    authority_review=[{'authority':k,'candidates':sorted(v),'candidate_count':len(v),'status':'REVIEW' if len(v)>1 else 'SINGLE_CANDIDATE'} for k,v in sorted(authority_map.items())]
    heat=sorted(({'path':x['path'],'domain':x['domain'],'score':(50 if x['operational_role']=='PRIMARY_RUNTIME_ROOT' else 20 if x['operational_role']=='BACKGROUND_WORKER' else 0)+10*x['incoming_importers']+3*x['outgoing_dependencies']+(15 if x['process_launcher'] else 0),'incoming_importers':x['incoming_importers'],'outgoing_dependencies':x['outgoing_dependencies'],'operational_role':x['operational_role']} for x in components),key=lambda z:(-z['score'],z['path']))[:100]
    return {
        'schema_version':'afip-runtime-production-authority-audit.v3.1','generated_at_utc':utc_now(),'project_root':str(root),
        'status':'REVIEW_REQUIRED' if multiwriters or repeats or legacy else 'PASS',
        'summary':{'source_files_scanned':len(files),'python_files_scanned':sum(x['path'].endswith('.py') for x in files),'script_files_scanned':sum(not x['path'].endswith('.py') for x in files),'all_detected_entrypoints':len(all_entrypoints),'primary_runtime_roots':len(entrypoints),'classified_entrypoints':len(entrypoint_classification),'reachable_files':len(reachable),'component_files':len(components),'legacy_candidates':len(legacy),'exact_duplicate_groups':len(duplicate_groups),'repeated_definition_groups':len(repeats),'shared_data_targets':len(shared),'multiple_writer_targets':len(multiwriters)},
        'historical_data_truth':find_historical_truth(root),'all_detected_entrypoints':all_entrypoints,'primary_runtime_roots':entrypoints,'entrypoint_classification':sorted(entrypoint_classification,key=lambda x:x['path']),'domain_summary':dict(sorted(domain_summary.items())),'authority_map':authority_review,'runtime_heat_map':heat,'components':sorted(components,key=lambda x:x['path']),
        'data_authority':shared,'multiple_writer_targets':multiwriters,'repeated_role_definitions':repeats,'exact_duplicate_files':duplicate_groups,
        'authority_chains':[{'root':root_path,'reachable_targets':sorted(reachable_from(root_path, edges))} for root_path in entrypoints],
        'invocation_edges':[{'source':src,'target':dst,'kind':'IMPORT_OR_PROCESS'} for src in sorted(edges) for dst in sorted(edges[src])],
        'classification_contract':{
            'KEEP_CANDIDATE':'Reachable from a detected runtime entrypoint; verify operational authority before changing.',
            'UTILITY_OR_LIBRARY':'Imported by production source but not reached by the static entrypoint graph; dynamic imports may exist.',
            'LEGACY_CANDIDATE':'No static importer and not an entrypoint; never remove without runtime evidence and regression certification.',
            'HIGH':'More than one production source statically writes the same data target.',
        },
    }


def write_markdown(report: dict[str,Any], path: Path) -> None:
    s=report['summary']; lines=['# AFIP Production Root & Authority Precision Audit','',f"Status: **{report['status']}**",'', '## Summary','']
    for k,v in s.items(): lines.append(f'- {k}: {v}')
    lines += ['', '## Historical Data Truth','', '```json', json.dumps(report['historical_data_truth'],ensure_ascii=False,indent=2), '```', '', '## Multiple Writer Targets','']
    if report['multiple_writer_targets']:
        for x in report['multiple_writer_targets']: lines.append(f"- `{x['target']}` — {x['writer_file_count']} writers")
    else: lines.append('- None detected statically.')
    lines += ['', '## Safety Note','', 'Domain, authority, LEGACY_CANDIDATE and REVIEW findings are investigation candidates only. This audit never disables, deletes, or rewires AFIP components.']
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--project-root',default='.'); args=ap.parse_args(); root=Path(args.project_root)
    out=root/'runtime'/'architecture_intelligence_certification'; out.mkdir(parents=True,exist_ok=True)
    report=build_report(root); jp=out/'production_authority_audit_report.json'; mp=out/'production_authority_audit_summary.md'
    jp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); write_markdown(report,mp)
    print(json.dumps({'status':report['status'],'summary':report['summary'],'historical_data_truth':report['historical_data_truth'],'report_path':str(jp),'summary_path':str(mp)},ensure_ascii=False,indent=2)); return 0

if __name__=='__main__': raise SystemExit(main())

