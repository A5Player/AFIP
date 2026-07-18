from pathlib import Path
import pytest
from afip.data_foundation import DataFoundationCertifier
def all_checks(): return {k:True for k in DataFoundationCertifier.REQUIRED}
def test_no_execution(): assert DataFoundationCertifier().policy.get("execution_authority","NONE")=="NONE"
def test_rejects_execution():
    with pytest.raises(ValueError): DataFoundationCertifier({"execution_authority":"LIVE"})
def test_rejects_auto_promotion():
    with pytest.raises(ValueError): DataFoundationCertifier({"automatic_promotion":"ALLOWED"})
def test_full_certification(): assert DataFoundationCertifier().certify(all_checks()).status=="CERTIFIED_RESEARCH_FOUNDATION"
def test_missing_check_blocks():
    c=all_checks();c["quality"]=False;assert DataFoundationCertifier().certify(c).status=="NOT_CERTIFIED"
def test_failed_list(): 
    c=all_checks();c["usage"]=False;assert "usage" in DataFoundationCertifier().certify(c).failed_checks
def test_passed_sorted(): assert DataFoundationCertifier().certify(all_checks()).passed_checks==tuple(sorted(DataFoundationCertifier.REQUIRED))
def test_id_deterministic():
    c=DataFoundationCertifier();assert c.certify(all_checks()).certification_id==c.certify(all_checks()).certification_id
def test_no_auto_promotion_result(): assert DataFoundationCertifier().certify(all_checks()).automatic_promotion=="PROHIBITED"
def test_execution_none_result(): assert DataFoundationCertifier().certify(all_checks()).execution_authority=="NONE"
def test_unknown_checks_ignored():
    c=all_checks();c["extra"]=False;assert DataFoundationCertifier().certify(c).status=="CERTIFIED_RESEARCH_FOUNDATION"
def test_write_report(tmp_path):
    p=tmp_path/"r.json";DataFoundationCertifier.write_report(DataFoundationCertifier().certify(all_checks()),p);assert p.exists()
def test_no_broker_calls():
    s=Path("afip/data_foundation/runtime.py").read_text().lower(); assert not any(x in s for x in ("metatrader5","order_send(","order_check(","mt5."))
