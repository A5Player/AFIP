import json
from pathlib import Path
import pytest
from afip.knowledge_evolution import EvidenceSnapshot, KnowledgeEvolutionEngine, snapshots_from_leaderboard_report, write_report

def snap(i=1, expectancy=20.0, samples=40, low=5.0, eligible=True, stability=80.0, group='g'):
    return EvidenceSnapshot(f's{i}',f'2026-07-{i:02d}T00:00:00Z',group,{'pattern_family':'BREAKOUT'},samples,expectancy,low,expectancy+10,60.0,stability,10.0,eligible,f'r{i}')

def test_policy_has_no_execution_authority():
    p=json.loads(Path('config/knowledge_evolution/evolution_policy.json').read_text())
    assert p['execution_authority']=='NONE' and p['promotion_to_execution']=='PROHIBITED'

def test_strong_repeatable_evidence_becomes_research_certified():
    r=KnowledgeEvolutionEngine(3,100,60,35).evolve([snap(1),snap(2),snap(3)])
    c=r.candidates[0]
    assert c.lifecycle_status=='RESEARCH_CERTIFIED' and c.execution_authority=='NONE'

def test_insufficient_history_remains_candidate():
    c=KnowledgeEvolutionEngine().evolve([snap(1)]).candidates[0]
    assert c.lifecycle_status=='CANDIDATE'
    assert 'MINIMUM_SNAPSHOTS_NOT_MET' in c.status_reasons

def test_non_positive_latest_ci_is_rejected():
    c=KnowledgeEvolutionEngine().evolve([snap(1),snap(2),snap(3,low=-1)]).candidates[0]
    assert c.lifecycle_status=='REJECTED'

def test_latest_ineligible_is_rejected():
    c=KnowledgeEvolutionEngine().evolve([snap(1),snap(2),snap(3,eligible=False)]).candidates[0]
    assert c.lifecycle_status=='REJECTED'

def test_drift_warning_detected():
    c=KnowledgeEvolutionEngine(drift_warning_threshold=20).evolve([snap(1,100),snap(2,90),snap(3,10)]).candidates[0]
    assert 'RECENCY_DRIFT_WARNING' in c.status_reasons

def test_duplicate_snapshot_is_deduplicated():
    x=snap(1)
    r=KnowledgeEvolutionEngine().evolve([x,x])
    assert r.generated_from_snapshots==1

def test_report_is_deterministic(tmp_path):
    r=KnowledgeEvolutionEngine().evolve([snap(1),snap(2),snap(3)])
    assert write_report(r,tmp_path/'a.json')==write_report(r,tmp_path/'b.json')
    assert (tmp_path/'a.json').read_bytes()==(tmp_path/'b.json').read_bytes()

def test_leaderboard_conversion_rejects_authority():
    with pytest.raises(ValueError,match='authority NONE'):
        snapshots_from_leaderboard_report({'execution_authority':'LIVE','promotion_to_execution':'PROHIBITED','report_id':'r'},'t')

def test_leaderboard_conversion():
    report={'execution_authority':'NONE','promotion_to_execution':'PROHIBITED','report_id':'r','ranked_rows':[{'group_values':{'market_regime':'TREND'},'ranking_score':4.0,'eligible_for_ranking':True,'metrics':{'sample_count':40,'expectancy_points':10,'confidence_interval_95_low':2,'confidence_interval_95_high':18,'win_rate':60,'stability_score':75}}]}
    s=snapshots_from_leaderboard_report(report,'2026-07-18T00:00:00Z')
    assert len(s)==1 and s[0].dimensions['market_regime']=='TREND'

def test_group_isolation():
    r=KnowledgeEvolutionEngine().evolve([snap(1,group='a'),snap(2,group='b')])
    assert len(r.candidates)==2

def test_invalid_percentage_rejected():
    with pytest.raises(ValueError):
        KnowledgeEvolutionEngine().evolve([EvidenceSnapshot('s','t','g',{},1,1,0,2,101,50,1,True,'r')])

def test_module_contains_no_order_or_broker_calls():
    source=Path('afip/knowledge_evolution/runtime.py').read_text()
    forbidden=('MetaTrader5','order_send','demo_execution_gateway','mt5.initialize','four_profile_demo.json')
    assert not any(x in source for x in forbidden)
