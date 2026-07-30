from pathlib import Path
import py_compile

TARGETS = (
    Path("tools/afip_runtime_intelligence_audit.py"),
    Path("tools/afip_runtime_intelligence_role_audit.py"),
)


def test_audit_tools_compile() -> None:
    for path in TARGETS:
        py_compile.compile(str(path), doraise=True)


def test_audit_join_helper_is_python311_compatible() -> None:
    for path in TARGETS:
        text = path.read_text(encoding="utf-8")
        assert 'left_clean = left.rstrip("/\\\\")' in text
        assert 'right_clean = right.lstrip("/\\\\")' in text
        assert 'return f"{left_clean}/{right_clean}"' in text
