from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "patch_payload"

FILES = {
    PAYLOAD / "afip" / "risk" / "confidence_calibrator.py": ROOT / "afip" / "risk" / "confidence_calibrator.py",
    PAYLOAD / "afip" / "execution" / "protected_simulation_order_builder.py": ROOT / "afip" / "execution" / "protected_simulation_order_builder.py",
    PAYLOAD / "tests" / "test_milestone_s_cleanup_pack_4_2.py": ROOT / "tests" / "test_milestone_s_cleanup_pack_4_2.py",
}


def main() -> None:
    missing = [str(source) for source in FILES if not source.exists()]
    if missing:
        raise FileNotFoundError("Missing Pack 4.2 payload: " + ", ".join(missing))

    for source, destination in FILES.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    documentation_source = PAYLOAD / "docs" / "README_MILESTONE_S_PACK_4_9_TH.md"
    documentation_destination = ROOT / "README_MILESTONE_S_PACK_4_9_TH.md"
    if documentation_destination.exists():
        shutil.copy2(documentation_source, documentation_destination)
    else:
        # The user's regression output confirms this document exists on the
        # production checkout. Fail closed if the local checkout differs.
        raise FileNotFoundError(
            "Expected documentation file not found: "
            f"{documentation_destination}. Do not continue with a partial patch."
        )

    # Prevent pytest import-file mismatch after installation.
    shutil.rmtree(PAYLOAD, ignore_errors=True)

    print("AFIP Milestone S Cleanup Pack 4.2 applied.")
    print("Temporary patch_payload removed to prevent duplicate pytest collection.")
    print("Execution remains STOPPED.")


if __name__ == "__main__":
    main()
