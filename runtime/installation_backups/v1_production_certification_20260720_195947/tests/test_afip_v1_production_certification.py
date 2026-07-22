from pathlib import Path

from afip.production_certification.fingerprint import iter_relevant_files
from afip.production_certification.runtime import ProductionCertificationRuntime


def test_runtime_directory_is_excluded(tmp_path: Path) -> None:
    (tmp_path / "afip").mkdir()
    (tmp_path / "afip" / "module.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "runtime").mkdir()
    (tmp_path / "runtime" / "large.json").write_text("{}\n", encoding="utf-8")
    names = {path.relative_to(tmp_path).as_posix() for path in iter_relevant_files(tmp_path)}
    assert "afip/module.py" in names
    assert "runtime/large.json" not in names


def test_certification_runtime_prefers_venv_python(tmp_path: Path) -> None:
    python = tmp_path / ".venv" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True)
    python.write_bytes(b"")
    runtime = ProductionCertificationRuntime(tmp_path)
    assert runtime.python == str(python)


def test_certification_output_location(tmp_path: Path) -> None:
    runtime = ProductionCertificationRuntime(tmp_path)
    assert runtime.runtime_dir == tmp_path / "runtime" / "certification"
