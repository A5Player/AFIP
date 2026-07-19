import json
from pathlib import Path
from afip.continuous_research_runtime import ContinuousResearchRuntime, EvidenceResearchEngine

def test_evidence_empty_is_research_only(tmp_path):
    r=EvidenceResearchEngine(tmp_path).build();assert r['execution_authority'] is False;assert r['relationships']==[]

def test_evidence_never_trading_eligible(tmp_path):
    p=tmp_path/'runtime/research/cross_market';p.mkdir(parents=True)
    row={'generated_at':'2026-01-01T00:00:00Z','sources':[{'source_id':'DXY','horizons':{'24H':{'magnitude_percent':1.0}}}]}
    (p/'observations.jsonl').write_text(json.dumps(row)+'\n'*0,encoding='utf-8')
    out=EvidenceResearchEngine(tmp_path).build();assert out['relationships'][0]['trading_eligible'] is False

def test_interval_floor(tmp_path): assert ContinuousResearchRuntime(tmp_path,1).interval==60
