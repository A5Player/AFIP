from pathlib import Path
import json

from tools.afip_runtime_intelligence_audit import build_report


def test_duplicate_definitions(tmp_path: Path):
    (tmp_path / "afip").mkdir()
    (tmp_path / "afip" / "a.py").write_text(
        "def signal_engine():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "afip" / "b.py").write_text(
        "def signal_engine():\n    return 2\n", encoding="utf-8"
    )
    report = build_report(tmp_path)
    assert report["summary"]["repeated_definition_groups"] == 1


def test_shared_json(tmp_path: Path):
    (tmp_path / "afip").mkdir()
    (tmp_path / "afip" / "a.py").write_text(
        "from pathlib import Path\nPath('runtime/state.json').write_text('{}')\n",
        encoding="utf-8",
    )
    (tmp_path / "afip" / "b.py").write_text(
        "from pathlib import Path\nPath('runtime/state.json').write_text('{\"x\":1}')\n",
        encoding="utf-8",
    )
    report = build_report(tmp_path)
    assert report["summary"]["shared_json_target_groups"] == 1


def test_runtime_named_parent_does_not_exclude_project_source(tmp_path: Path):
    project = tmp_path / "runtime" / "pytest_case"
    (project / "afip").mkdir(parents=True)
    (project / "afip" / "a.py").write_text(
        "def decision_engine():\n    return 1\n", encoding="utf-8"
    )
    (project / "afip" / "b.py").write_text(
        "def decision_engine():\n    return 2\n", encoding="utf-8"
    )
    report = build_report(project)
    assert report["summary"]["python_files_scanned"] == 2
    assert report["summary"]["repeated_definition_groups"] == 1


def test_path_join_json_target(tmp_path: Path):
    (tmp_path / "afip").mkdir()
    source = (
        "from pathlib import Path\n"
        "(Path('runtime') / 'state.json').write_text('{}')\n"
    )
    (tmp_path / "afip" / "a.py").write_text(source, encoding="utf-8")
    (tmp_path / "afip" / "b.py").write_text(source + "# second\n", encoding="utf-8")
    report = build_report(tmp_path)
    assert report["summary"]["shared_json_target_groups"] == 1


def test_historical_boundaries(tmp_path: Path):
    directory = tmp_path / "runtime" / "historical_data"
    directory.mkdir(parents=True)
    (directory / "historical_dashboard.json").write_text(
        json.dumps(
            {
                "coverage_start_utc": "2026-04-01T00:00:00+00:00",
                "coverage_end_utc": "2026-07-01T00:00:00+00:00",
                "next_start_utc": "2026-07-01T00:01:00+00:00",
                "history_discovery": {
                    "earliest_available_utc": "2026-03-01T00:00:00+00:00"
                },
            }
        ),
        encoding="utf-8",
    )
    truth = build_report(tmp_path)["historical_data_truth"]
    assert truth["boundaries_are_separated"] is True



def test_production_scan_excludes_runtime_pytest_and_tests(tmp_path: Path):
    (tmp_path / "afip").mkdir()
    (tmp_path / "afip" / "live.py").write_text(
        "def execution_engine():\n    return 1\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_fake.py").write_text(
        "def execution_engine():\n    return 2\n", encoding="utf-8"
    )
    generated = tmp_path / "runtime" / "pytest_temp_case" / "afip"
    generated.mkdir(parents=True)
    (generated / "fake.py").write_text(
        "def execution_engine():\n    return 3\n", encoding="utf-8"
    )
    report = build_report(tmp_path)
    assert report["summary"]["python_files_scanned"] == 1
    assert report["summary"]["repeated_definition_groups"] == 0


def test_historical_truth_ignores_pytest_artifact(tmp_path: Path):
    fake = tmp_path / "runtime" / "pytest_temp_case" / "runtime" / "historical_data"
    fake.mkdir(parents=True)
    (fake / "historical_dashboard.json").write_text(
        json.dumps({
            "coverage_start_utc": "2000-01-01T00:00:00+00:00",
            "coverage_end_utc": "2000-01-02T00:00:00+00:00",
            "next_start_utc": "2000-01-02T00:01:00+00:00",
            "history_discovery": {"earliest_available_utc": "1999-01-01T00:00:00+00:00"},
        }), encoding="utf-8"
    )
    real = tmp_path / "runtime" / "historical_data"
    real.mkdir(parents=True)
    (real / "historical_dashboard.json").write_text(
        json.dumps({
            "status": "PAUSED",
            "quality_status": "PASS_WITH_GAPS",
            "coverage_start_utc": "2026-04-16T15:31:00+00:00",
            "coverage_end_utc": "2026-07-28T15:18:00+00:00",
            "next_start_utc": "2026-07-28T14:54:01+00:00",
            "history_discovery": {"earliest_available_utc": "2026-04-16T15:31:00+00:00"},
        }), encoding="utf-8"
    )
    truth = build_report(tmp_path)["historical_data_truth"]
    assert truth["source"] == "runtime/historical_data/historical_dashboard.json"
    assert truth["status"] == "PAUSED"
