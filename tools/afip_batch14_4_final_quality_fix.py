from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def patch_display_name() -> None:
    path = PROJECT_ROOT / "afip" / "cli" / "simulate.py"
    text = read(path)

    marker = "def _display_intelligence_name"
    if marker not in text:
        print("skip: afip/cli/simulate.py has no _display_intelligence_name")
        return

    if "LiquidityQualityIntelligence\": \"LiquidityIntelligence" in text:
        print("ok: display-name compatibility already includes LiquidityQualityIntelligence")
        return

    lines = text.splitlines()
    output: list[str] = []
    inserted = False
    for line in lines:
        output.append(line)
        if (not inserted) and line.startswith("def _display_intelligence_name") and line.rstrip().endswith(":"):
            output.extend([
                "    compatibility_names = {",
                "        \"MomentumQualityIntelligence\": \"MomentumIntelligence\",",
                "        \"LiquidityQualityIntelligence\": \"LiquidityIntelligence\",",
                "        \"VolumeIntelligence\": \"VolumeAnalysisIntelligence\",",
                "        \"CorrelationIntelligence\": \"CrossAssetCorrelationIntelligence\",",
                "        \"VolatilityRiskIntelligence\": \"VolatilityIntelligence\",",
                "    }",
                "    if name in compatibility_names:",
                "        return compatibility_names[name]",
            ])
            inserted = True

    if not inserted:
        raise RuntimeError("Unable to patch _display_intelligence_name")

    write(path, "\n".join(output) + "\n")
    print("patched: afip/cli/simulate.py display-name compatibility")


def patch_market_data_wiring() -> None:
    path = PROJECT_ROOT / "afip" / "pipeline" / "real_market_data_intelligence_wiring.py"
    text = read(path)

    old = "connection = self.market_data_provider.connection_check(symbol=symbol)"
    if old not in text:
        if "hasattr(self.market_data_provider, \"connection_check\")" in text:
            print("ok: real market data wiring already has provider compatibility")
            return
        raise RuntimeError("Unable to find connection_check assignment in real_market_data_intelligence_wiring.py")

    new = """if hasattr(self.market_data_provider, \"connection_check\"):\n            connection = self.market_data_provider.connection_check(symbol=symbol)\n        else:\n            connection = {\n                \"status\": \"READY\",\n                \"symbol\": symbol,\n                \"requested\": symbol,\n                \"execution\": \"LOCKED_SIMULATION_ONLY\",\n                \"init\": \"provider_compatibility_mode\",\n                \"select\": \"provider_connection_check_unavailable\",\n                \"tick\": \"provider_connection_check_unavailable\",\n            }"""

    text = text.replace(old, new, 1)
    write(path, text)
    print("patched: afip/pipeline/real_market_data_intelligence_wiring.py provider compatibility")


def main() -> None:
    print("AFIP Production Batch 14.4 Final Quality Fix")
    print(f"Project root: {PROJECT_ROOT}")
    patch_display_name()
    patch_market_data_wiring()
    print("Done. Now run: python tools/afip_local_quality_check.py")


if __name__ == "__main__":
    main()
