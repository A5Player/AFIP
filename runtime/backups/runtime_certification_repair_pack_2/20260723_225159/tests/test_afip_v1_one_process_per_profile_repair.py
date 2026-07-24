from pathlib import Path


def test_control_reports_one_process_per_profile():
    text = Path("tools/afip_demo_execution_control.py").read_text(encoding="utf-8")
    assert '"router_mode": "ONE_PROCESS_PER_PROFILE"' in text
    assert '"mode": "ONE_PROCESS_PER_PROFILE"' in text
    assert 'worker_pid' in text


def test_supervisor_spawns_persistent_profile_workers():
    text = Path("tools/afip_profile_sequential_execution_router.py").read_text(encoding="utf-8")
    assert 'tools.afip_profile_execution_worker' in text
    assert '"mode": "ONE_PROCESS_PER_PROFILE"' in text
    assert 'profile_worker_exited' in text
    assert '_spawn(profile_id' in text


def test_worker_never_changes_profile():
    text = Path("tools/afip_profile_execution_worker.py").read_text(encoding="utf-8")
    assert 'run_once(profile_id, config)' in text
    assert 'while not _stop' in text
    assert 'afip-profile-execution-worker.v1' in text
