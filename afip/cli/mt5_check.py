from afip.market.mt5_market_data_provider import MT5MarketDataProvider


def main(symbol: str = "GOLD#") -> dict:
    provider = MT5MarketDataProvider.from_installed_package(enabled=True)
    result = provider.connection_check(symbol=symbol)
    timeframe_result = provider.timeframe_snapshots(symbol=symbol, count=20)
    result["timeframes"] = {
        timeframe: {
            "source": snapshot.get("source"),
            "candle_count": snapshot.get("candle_count", len(snapshot.get("closes", []))),
        }
        for timeframe, snapshot in timeframe_result["timeframes"].items()
    }
    result["fallback_reasons"] = timeframe_result["fallback_reasons"]

    print("=== AFIP Production Sprint 3 — MT5 Data Check ===")
    print(f"Status    : {result['status']}")
    print(f"Symbol    : {result['symbol']}")
    print(f"Requested : {result.get('requested_symbol', result['symbol'])}")
    print(f"Execution : {result['execution']}")
    print(f"Init      : {result['initialize'].get('reason')}")
    print(f"Select    : {result['symbol_select'].get('reason')}")
    print(f"Tick      : {result['tick'].get('reason', 'available')}")
    print(f"Account   : {result['account_info'].get('server', result['account_info'].get('reason'))}")
    print("")
    print("Timeframes:")
    for timeframe, info in result["timeframes"].items():
        print(f" - {timeframe}: {info['source']} candles={info['candle_count']}")
    return result


if __name__ == "__main__":
    main()
