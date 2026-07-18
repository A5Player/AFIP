from pathlib import Path
import pytest
from afip.dataset_usage import DatasetUsageLedger
def test_rejects_execution():
    with pytest.raises(ValueError): DatasetUsageLedger("LIVE")
def test_ready_allowed(): assert DatasetUsageLedger().record("d","analysis","r","RESEARCH_READY").allowed
def test_conditional_allowed(): assert DatasetUsageLedger().record("d","analysis","r","CONDITIONALLY_READY").allowed
def test_review_blocked(): assert not DatasetUsageLedger().record("d","analysis","r","REVIEW_REQUIRED").allowed
def test_not_ready_blocked(): assert not DatasetUsageLedger().record("d","analysis","r","NOT_READY").allowed
def test_reason_allowed(): assert DatasetUsageLedger().record("d","a","r","RESEARCH_READY").reason=="research_use_allowed"
def test_reason_blocked(): assert DatasetUsageLedger().record("d","a","r","NOT_READY").reason=="dataset_not_ready"
def test_evidence_sorted(): assert DatasetUsageLedger().record("d","a","r","RESEARCH_READY",("z","a")).evidence_refs==("a","z")
def test_id_deterministic():
    l=DatasetUsageLedger(); assert l.record("d","a","r","RESEARCH_READY").event_id==l.record("d","a","r","RESEARCH_READY").event_id
def test_experiment_preserved(): assert DatasetUsageLedger().record("d","a","r","RESEARCH_READY",(), "e1").experiment_id=="e1"
def test_append(tmp_path):
    l=DatasetUsageLedger();e=l.record("d","a","r","RESEARCH_READY");p=tmp_path/"u.jsonl";l.append(e,p);l.append(e,p);assert len(p.read_text().splitlines())==2
def test_execution_authority_none(): assert DatasetUsageLedger().record("d","a","r","RESEARCH_READY").execution_authority=="NONE"
def test_no_broker_calls():
    s=Path("afip/dataset_usage/runtime.py").read_text().lower(); assert not any(x in s for x in ("metatrader5","order_send(","order_check(","mt5."))
