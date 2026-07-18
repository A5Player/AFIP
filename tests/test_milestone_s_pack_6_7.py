from pathlib import Path
import pytest
from afip.archive_retention import ArchiveRetentionPlanner

def test_no_execution_authority(): assert ArchiveRetentionPlanner().policy.get("execution_authority","NONE")=="NONE"
def test_rejects_execution_authority():
    with pytest.raises(ValueError): ArchiveRetentionPlanner({"execution_authority":"LIVE"})
def test_rejects_auto_delete():
    with pytest.raises(ValueError): ArchiveRetentionPlanner({"automatic_deletion":"ALLOWED"})
def test_keep_active(): assert ArchiveRetentionPlanner().evaluate("d",10,"ACTIVE").action=="KEEP_ACTIVE"
def test_archive_old(): assert ArchiveRetentionPlanner({"archive_after_days":30}).evaluate("d",31,"ACTIVE").action=="ARCHIVE"
def test_legal_hold_wins(): assert ArchiveRetentionPlanner().evaluate("d",1000,"ACTIVE",True).action=="LEGAL_HOLD"
def test_corrupted_goes_review(): assert ArchiveRetentionPlanner().evaluate("d",1,"ACTIVE",False,"CORRUPTED").action=="QUARANTINE_REVIEW"
def test_archived_stays_cold(): assert ArchiveRetentionPlanner().evaluate("d",1,"ARCHIVED").target_tier=="COLD_ARCHIVE"
def test_negative_age_rejected():
    with pytest.raises(ValueError): ArchiveRetentionPlanner().evaluate("d",-1,"ACTIVE")
def test_no_auto_action(): assert ArchiveRetentionPlanner().evaluate("d",999,"ACTIVE").automatic_action_taken is False
def test_id_deterministic():
    p=ArchiveRetentionPlanner(); assert p.evaluate("d",1,"ACTIVE").decision_id==p.evaluate("d",1,"ACTIVE").decision_id
def test_append_ledger(tmp_path):
    p=ArchiveRetentionPlanner(); d=p.evaluate("d",1,"ACTIVE"); f=tmp_path/"l.jsonl"; p.append_ledger(d,f); p.append_ledger(d,f); assert len(f.read_text().splitlines())==2
def test_no_broker_calls():
    s=Path("afip/archive_retention/runtime.py").read_text().lower(); assert not any(x in s for x in ("metatrader5","order_send(","order_check(","mt5."))
