from afip.runtime.runtime_v1 import RuntimeV1


FINANCIAL_DISPLAY_NAMES = {
    "MomentumQualityIntelligence": "MomentumIntelligence",
    "VolumeIntelligence": "VolumeAnalysisIntelligence",
    "VolatilityRiskIntelligence": "VolatilityIntelligence",
    "CorrelationIntelligence": "CrossAssetCorrelationIntelligence",
}


INSTITUTIONAL_INTELLIGENCE_NAMES = [
    "FairValueGapIntelligence",
    "ImbalanceIntelligence",
    "OrderBlockIntelligence",
    "LiquiditySweepIntelligence",
    "SmartMoneyConceptIntelligence",
]


def _display_intelligence_name(name: str) -> str:
    compatibility_names = {
        "MomentumQualityIntelligence": "MomentumIntelligence",
        "LiquidityQualityIntelligence": "LiquidityIntelligence",
        "VolumeIntelligence": "VolumeAnalysisIntelligence",
        "CorrelationIntelligence": "CrossAssetCorrelationIntelligence",
        "VolatilityRiskIntelligence": "VolatilityIntelligence",
    }
    if name in compatibility_names:
        return compatibility_names[name]
    return FINANCIAL_DISPLAY_NAMES.get(name, name)


def _find_intelligence(modular: dict, name: str) -> dict:
    for item in modular.get("intelligence", []):
        if item.get("name") == name:
            return item
    return {
        "name": name,
        "status": "INITIALIZING",
        "direction": "NEUTRAL",
        "confidence": 0,
        "reason": "intelligence_not_available_yet",
    }


def _print_institutional_intelligence(modular: dict) -> None:
    print("Institutional Intelligence:")
    for name in INSTITUTIONAL_INTELLIGENCE_NAMES:
        item = _find_intelligence(modular, name)
        display_name = _display_intelligence_name(item.get("name", name))
        detail = item.get("institutional_bias")
        if not detail:
            detail = item.get("gap_state")
        if not detail:
            detail = item.get("imbalance_state")
        if not detail:
            detail = item.get("order_block_state")
        if not detail:
            detail = item.get("sweep_type")
        if not detail:
            detail = item.get("reason", "-")
        print(
            f" - {display_name}: "
            f"{item.get('direction', '-')} "
            f"{item.get('confidence', '-')} "
            f"({item.get('status', '-')}) "
            f"{detail}"
        )
    print("")


def main():
    result = RuntimeV1().simulate()
    modular = result.get("modular_intelligence", {"module_count": 0, "intelligence": []})
    decision = result.get("decision", {})

    print("=== AFIP Runtime V1 - Modular Intelligence ===")
    print(f"Status : {result.get('status', '-')}")
    print(f"Mode   : {result.get('mode', '-')}")
    print(f"Symbol : {result.get('symbol', '-')}")
    print(f"Execution : {result.get('execution', 'LOCKED_SIMULATION_ONLY')}")
    print("")

    print("Market Data Intelligence:")
    print(f" - Status    : {result.get('data_status', '-')}")
    print(f" - Source    : {result.get('data_source', '-')}")
    print(f" - Primary TF: {result.get('primary_timeframe', '-')}")
    print("")

    confluence = result.get("multi_timeframe_confluence", {})
    print("Multi-Timeframe Confluence Intelligence:")
    print(f" - Status      : {confluence.get('status', '-')}")
    print(f" - Direction   : {confluence.get('direction', '-')}")
    print(f" - Confidence  : {confluence.get('confidence', '-')}")
    print(f" - TFs         : {', '.join(confluence.get('available_timeframes', [])) or '-'}")
    print(f" - Aligned TFs : {confluence.get('aligned_timeframes', '-')}")
    print("")

    market_structure = _find_intelligence(modular, "MarketStructureIntelligence")
    print("Market Structure Intelligence:")
    print(f" - Status    : {market_structure.get('status', '-')}")
    print(f" - Direction : {market_structure.get('direction', '-')}")
    print(f" - Confidence: {market_structure.get('confidence', '-')}")
    print(f" - Structure : {market_structure.get('structure_state', '-')}")
    print(f" - Reason    : {market_structure.get('reason', '-')}")
    print("")

    liquidity = _find_intelligence(modular, "LiquidityIntelligence")
    print("Liquidity Intelligence:")
    print(f" - Status    : {liquidity.get('status', '-')}")
    print(f" - Direction : {liquidity.get('direction', '-')}")
    print(f" - Confidence: {liquidity.get('confidence', '-')}")
    print(f" - Liquidity : {liquidity.get('liquidity_state', '-')}")
    print(f" - Sweep     : {liquidity.get('sweep_type', '-')}")
    print(f" - Reason    : {liquidity.get('reason', '-')}")
    print("")

    _print_institutional_intelligence(modular)

    print("Modular Intelligence:")
    print(f" - Intelligence : {modular.get('module_count', 0)}")
    print(f" - Action       : {decision.get('action', '-')}")
    print(f" - Confidence   : {decision.get('confidence', '-')}")
    print(f" - Buy Score    : {decision.get('buy_score', '-')}")
    print(f" - Sell Score   : {decision.get('sell_score', '-')}")
    print(f" - Reason       : {decision.get('reason', '-')}")
    print("")

    print("Market Intelligence Summary:")
    ranked = sorted(
        modular.get("intelligence", []),
        key=lambda x: x.get("confidence", 0),
        reverse=True,
    )[:8]
    for item in ranked:
        display_name = _display_intelligence_name(item.get("name", "-"))
        print(
            f" - {display_name}: "
            f"{item.get('direction', '-')} "
            f"{item.get('confidence', '-')} "
            f"({item.get('status', '-')})"
        )
    print("")

    trading_cost = result.get("trading_cost_intelligence", {})
    print("Trading Cost Intelligence:")
    print(f" - Status : {trading_cost.get('status', '-')}")
    print(f" - Spread : {trading_cost.get('spread_points', '-')} pts")
    print(f" - Limit  : {trading_cost.get('max_spread_points', '-')} pts")
    print(f" - Reason : {trading_cost.get('reason', '-')}")
    print("")

    risk = result.get("risk", {"allowed": False, "reasons": ["risk_not_available"]})
    print("Risk Intelligence:")
    print(f" - Allowed : {risk.get('allowed', False)}")
    print(f" - Reasons : {', '.join(risk.get('reasons', [])) or '-'}")
    print("")

    order = result.get("order", {"status": "NO_ORDER"})
    print("Execution Decision:")
    print(f" - Status : {order.get('status', '-')}")
    print(f" - Action : {order.get('action', '-')}")
    print(f" - Lot    : {order.get('lot', '-')}")
    print("")

    report = result.get("report", {})
    summary = report.get("summary", {})
    drawdown = report.get("drawdown", {})
    print("Report:")
    print(f" - Total Trades : {summary.get('total_trades', '-')}")
    print(f" - Win Rate     : {summary.get('win_rate', '-')}%")
    print(f" - Net Profit   : {summary.get('net_profit', '-')}")
    print(f" - Drawdown     : {drawdown.get('max_drawdown', '-')}")


if __name__ == "__main__":
    main()
