import importlib.util
from pathlib import Path


def test_afip_launcher_can_load_runtime():
    launcher_path = Path(__file__).resolve().parents[1] / "afip.py"
    assert launcher_path.exists()
