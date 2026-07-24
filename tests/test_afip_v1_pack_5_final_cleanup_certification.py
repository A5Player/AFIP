from pathlib import Path
from tools.afip_v1_pack_5_final_runtime_certification import certify
from tools.afip_v1_pack_5_repository_cleanup import IGNORE_LINES

def test_pack_5_generated_artifact_policy_is_explicit():
    assert "runtime/backups/" in IGNORE_LINES
    assert "runtime/execution/*.lock" in IGNORE_LINES
    assert any(x.startswith("payload/") for x in IGNORE_LINES)

def test_pack_5_source_certification_passes():
    report = certify(Path("."))
    assert report["source_certification"] == "PASS", report
    assert report["status"] in {"PASS", "READY_FOR_LIVE_CERTIFICATION"}
    assert [x["profile_id"] for x in report["profiles"]] == ["P1", "P2", "P3", "P4"]
