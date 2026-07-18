from pathlib import Path
import pytest
from afip.experiment_replay import ExperimentReplayRegistry, ExperimentSpec
def spec():
    return ExperimentSpec("e1",("d1","d2"),"abc","cfg",42,(("x","1"),))
def test_no_execution(): assert ExperimentReplayRegistry().policy.get("execution_authority","NONE")=="NONE"
def test_rejects_live():
    with pytest.raises(ValueError): ExperimentReplayRegistry({"live_execution":"ALLOWED"})
def test_fingerprint_deterministic():
    r=ExperimentReplayRegistry(); assert r.fingerprint(spec())==r.fingerprint(spec())
def test_ready_plan(): assert ExperimentReplayRegistry().build_replay_plan(spec(),["d1","d2"])["status"]=="READY_FOR_REPLAY"
def test_missing_blocks(): assert ExperimentReplayRegistry().build_replay_plan(spec(),["d1"])["status"]=="BLOCKED"
def test_missing_sorted(): assert ExperimentReplayRegistry().build_replay_plan(spec(),[])["missing_datasets"]==["d1","d2"]
def test_offline_only(): assert ExperimentReplayRegistry().build_replay_plan(spec(),["d1","d2"])["execution_mode"]=="OFFLINE_RESEARCH_ONLY"
def test_no_auto_execution(): assert ExperimentReplayRegistry().build_replay_plan(spec(),[])["automatic_execution"] is False
def test_parameter_order_affects_explicit_spec():
    a=spec(); b=ExperimentSpec("e1",("d1","d2"),"abc","cfg",42,(("y","1"),)); assert ExperimentReplayRegistry().fingerprint(a)!=ExperimentReplayRegistry().fingerprint(b)
def test_seed_affects_fingerprint():
    b=ExperimentSpec("e1",("d1","d2"),"abc","cfg",43,(("x","1"),)); assert ExperimentReplayRegistry().fingerprint(spec())!=ExperimentReplayRegistry().fingerprint(b)
def test_write_manifest(tmp_path):
    p=tmp_path/"m.json"; ExperimentReplayRegistry.write_manifest({"a":1},p); assert p.exists()
def test_dataset_order_is_part_of_spec():
    b=ExperimentSpec("e1",("d2","d1"),"abc","cfg",42,(("x","1"),)); assert ExperimentReplayRegistry().fingerprint(spec())!=ExperimentReplayRegistry().fingerprint(b)
def test_no_broker_calls():
    s=Path("afip/experiment_replay/runtime.py").read_text().lower(); assert not any(x in s for x in ("metatrader5","order_send(","order_check(","mt5."))
