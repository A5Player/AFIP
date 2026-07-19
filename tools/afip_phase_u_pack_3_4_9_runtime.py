from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Direct script execution sets sys.path[0] to <repo>/tools rather than the
# repository root. Add the actual root before importing AFIP packages so the
# runtime works from PowerShell, cmd.exe, schedulers, and arbitrary cwd values.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from afip.cross_market_gold_intelligence import CrossMarketGoldResearchRuntime
from afip.financial_intelligence_certification import (
    FinancialIntegrityRuntime,
    IntelligenceSourceCertificationRuntime,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AFIP Phase U Pack 3.4.9 real-source certification"
    )
    parser.add_argument("--root", default=".")
    parser.add_argument("--skip-cross-market", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    outputs = [
        FinancialIntegrityRuntime(root).write(),
        IntelligenceSourceCertificationRuntime(root).write(),
    ]
    if not args.skip_cross_market:
        outputs.append(CrossMarketGoldResearchRuntime(root).write())

    print(
        json.dumps(
            {
                "status": "COMPLETE",
                "outputs": [str(path) for path in outputs],
                "execution_authority": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
