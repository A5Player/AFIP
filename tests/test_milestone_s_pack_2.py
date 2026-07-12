from __future__ import annotations
import json
from pathlib import Path
import pytest
from afip.four_profile_operations import FourProfileOperationalRuntime, FourProfileSupervisor, ProfileOperationalConfig


def _payload(root: Path):
    profiles=[]
    for number, name in enumerate(("High Safety","Balanced","High Risk Within Plan","Research"),1):
        pid=f"P{number}"; base=root/pid.lower()
        profiles.append({
            "profile_id":pid,"profile_name":name,"enabled":pid in {"P1","P4"},"launch_mt5":False,
            "mt5_folder":str(root/f"XM {pid}"),"mt5_terminal":str(root/f"XM {pid}"/"terminal64.exe"),
            "broker":"XM","server":"XMGlobal-MT5 6" if number<3 else "XMGlobal-MT5 5","symbol":"GOLD#",
            "login_env":f"AFIP_{pid}_LOGIN","password_env":f"AFIP_{pid}_PASSWORD",
            "runtime_directory":str(base),"database_path":str(base/"database"/f"{pid}.sqlite3"),
            "logs_directory":str(base/"logs"),"dashboard_path":str(base/"dashboard"/"afip_dashboard.html"),
            "learning_directory":str(base/"learning"),"knowledge_directory":str(base/"knowledge"),
            "statistics_directory":str(base/"statistics"),"execution":"LOCKED_SIMULATION_ONLY",
            "direct_execution":False,"live_execution":False,
        })
    return {"profiles":profiles}

@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    path=tmp_path/"profiles.json"; path.write_text(json.dumps(_payload(tmp_path)),encoding="utf-8"); return path


def test_repository_default_configuration_has_four_isolated_profiles():
    runtime=FourProfileOperationalRuntime()
    profiles=runtime.load()
    assert [p.profile_id for p in profiles]==["P1","P2","P3","P4"]
    assert [p.enabled for p in profiles]==[True,False,False,True]
    assert len({str(p.mt5_folder).casefold() for p in profiles})==4
    assert len({str(p.runtime_directory).casefold() for p in profiles})==4
    assert len({str(p.database_path).casefold() for p in profiles})==4


def test_policy_is_immutable_locked_simulation(config_path: Path):
    report=FourProfileOperationalRuntime(config_path).prepare_isolation()
    assert report.status=="READY" and not report.validation_errors
    assert report.execution=="LOCKED_SIMULATION_ONLY"
    assert report.order_status=="NO_ORDER_SENT"
    assert report.direct_execution is False and report.live_execution is False
    assert all(p["execution"]=="LOCKED_SIMULATION_ONLY" for p in report.profiles)


def test_prepare_creates_only_enabled_profile_isolation(config_path: Path):
    runtime=FourProfileOperationalRuntime(config_path)
    report=runtime.prepare_isolation()
    assert report.status=="READY"
    profiles=runtime.load()
    for p in profiles:
        assert p.runtime_directory.exists() is p.enabled
        assert p.database_path.parent.exists() is p.enabled
        assert p.logs_directory.exists() is p.enabled
        assert p.learning_directory.exists() is p.enabled
        assert p.knowledge_directory.exists() is p.enabled
        assert p.statistics_directory.exists() is p.enabled


def test_selected_combinations_are_supported(config_path: Path):
    runtime=FourProfileOperationalRuntime(config_path)
    runtime.prepare_isolation(["P1","P2","P4"])
    profiles={p.profile_id:p for p in runtime.load()}
    assert profiles["P1"].runtime_directory.exists()
    assert profiles["P2"].runtime_directory.exists()
    assert not profiles["P3"].runtime_directory.exists()
    assert profiles["P4"].runtime_directory.exists()


def test_duplicate_mt5_folder_is_blocked(config_path: Path):
    payload=json.loads(config_path.read_text())
    payload["profiles"][1]["mt5_folder"]=payload["profiles"][0]["mt5_folder"]
    config_path.write_text(json.dumps(payload))
    errors=FourProfileOperationalRuntime(config_path).validate()
    assert any(error.startswith("duplicate_mt5_folder") for error in errors)


def test_duplicate_account_is_blocked_when_environment_is_configured(config_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AFIP_P1_LOGIN","123")
    monkeypatch.setenv("AFIP_P2_LOGIN","123")
    errors=FourProfileOperationalRuntime(config_path).validate()
    assert "duplicate_account:P1:P2" in errors


def test_credentials_are_environment_only_and_masked(config_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AFIP_P1_LOGIN","99990000369")
    monkeypatch.setenv("AFIP_P1_PASSWORD","secret")
    profile=FourProfileOperationalRuntime(config_path).load()[0]
    record=profile.status_record()
    assert record["account"]=="****0369"
    assert record["credentials_configured"] is True
    assert "secret" not in json.dumps(record)


def test_unsafe_broker_or_execution_is_blocked(tmp_path: Path):
    raw=_payload(tmp_path)["profiles"][0]
    raw["broker"]="OTHER"; raw["execution"]="LIVE"; raw["direct_execution"]=True
    errors=ProfileOperationalConfig.from_mapping(raw).validate_policy()
    assert "broker_must_be_xm" in errors
    assert "execution_must_remain_locked_simulation_only" in errors
    assert "direct_execution_must_be_false" in errors


def test_supervisor_worker_command_uses_locked_runner(config_path: Path):
    profile=FourProfileOperationalRuntime(config_path).load()[0]
    command=FourProfileSupervisor._worker_command(profile)
    text=" ".join(command)
    assert "LockedSimulationRunner" in text
    assert "runtime_directory" in text
    assert "order_send" not in text.lower()
