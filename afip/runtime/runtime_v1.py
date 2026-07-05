from afip.pipeline.protected_signal_workflow import ProtectedSignalWorkflow
from afip.pipeline.modular_intelligence_pipeline import ModularIntelligencePipeline
from afip.pipeline.real_market_data_intelligence_wiring import RealMarketDataIntelligenceWiring
from afip.report.analytics_report import AnalyticsReport
from afip.risk.confidence_calibrator import ConfidenceCalibrator


def _candles(start: float):
    return [
        {"time": 1, "open": start, "high": start + 0.8, "low": start - 0.3, "close": start + 0.4, "tick_volume": 100},
        {"time": 2, "open": start + 0.4, "high": start + 1.1, "low": start + 0.1, "close": start + 0.8, "tick_volume": 120},
        {"time": 3, "open": start + 0.8, "high": start + 1.6, "low": start + 0.4, "close": start + 1.2, "tick_volume": 130},
        {"time": 4, "open": start + 1.2, "high": start + 2.0, "low": start + 0.9, "close": start + 1.7, "tick_volume": 150},
        {"time": 5, "open": start + 1.7, "high": start + 2.5, "low": start + 1.3, "close": start + 2.2, "tick_volume": 160},
    ]


def _snapshot_to_candles(snapshot: dict) -> list:
    opens = snapshot.get("opens", [])
    highs = snapshot.get("highs", [])
    lows = snapshot.get("lows", [])
    closes = snapshot.get("closes", [])
    volumes = snapshot.get("volumes", [])
    length = min(len(opens), len(highs), len(lows), len(closes))
    candles = []
    for index in range(length):
        candles.append(
            {
                "time": index + 1,
                "open": opens[index],
                "high": highs[index],
                "low": lows[index],
                "close": closes[index],
                "tick_volume": volumes[index] if index < len(volumes) else 0,
            }
        )
    return candles


class RuntimeV1:
    def simulate(self):
        symbol = "GOLD#"
        real_wiring = RealMarketDataIntelligenceWiring().run(symbol=symbol, count=100)
        market_data = real_wiring.get("market_data", {})
        snapshots = market_data.get("timeframes", {})
        primary_snapshot = real_wiring.get("primary_snapshot", {})

        timeframe_candles = {
            timeframe: _snapshot_to_candles(snapshot)
            for timeframe, snapshot in snapshots.items()
            if snapshot.get("closes")
        }
        if not timeframe_candles:
            timeframe_candles = {
                "M5": _candles(2300.0),
                "M15": _candles(2301.0),
                "H1": _candles(2302.0),
            }

        protected = ProtectedSignalWorkflow().run(
            symbol=real_wiring.get("symbol", symbol),
            timeframe_candles=timeframe_candles,
            spread=primary_snapshot.get("spread", 18),
            balance=1000.0,
        )

        modular = real_wiring.get("modular_intelligence")
        if not modular:
            first_snapshot = next(iter(protected["base"]["signal"]["snapshots"].values()))
            modular = ModularIntelligencePipeline().run(first_snapshot)

        protected = ConfidenceCalibrator().calibrate(protected, modular, balance=1000.0)
        trading_cost_intelligence = real_wiring.get("trading_cost_intelligence", {})
        if not trading_cost_intelligence.get("allowed", True):
            protected = self._apply_trading_cost_block(protected, trading_cost_intelligence)

        decision = modular["decision"]
        risk_decision = protected["base"]["decision"]
        order = protected["protected_order"]

        demo_trades = [
            {"symbol": symbol, "action": "BUY", "profit": 10, "reason": "simulation_sample_win"},
            {"symbol": symbol, "action": "SELL", "profit": -4, "reason": "simulation_sample_loss"},
            {"symbol": symbol, "action": decision.get("action", "WAIT"), "profit": 6 if order.get("status") == "SIMULATION_ORDER_READY" else 0, "reason": "real_market_data_intelligence"},
        ]
        report = AnalyticsReport().generate(demo_trades, starting_equity=1000.0)

        return {
            "status": "OK",
            "mode": "SIMULATION",
            "symbol": real_wiring.get("symbol", symbol),
            "requested_symbol": symbol,
            "execution": "LOCKED_SIMULATION_ONLY",
            "data_status": real_wiring.get("status"),
            "data_source": modular.get("data_source", "UNKNOWN"),
            "primary_timeframe": modular.get("primary_timeframe", real_wiring.get("primary_timeframe")),
            "protected_workflow": protected,
            "real_market_data_wiring": real_wiring,
            "multi_timeframe_confluence": real_wiring.get("multi_timeframe_confluence"),
            "trading_cost_intelligence": real_wiring.get("trading_cost_intelligence"),
            "modular_intelligence": modular,
            "decision": decision,
            "risk_decision": risk_decision,
            "order": order,
            "risk": protected["base"]["risk"],
            "score": protected["base"]["signal"]["score"],
            "confidence_calibration": protected.get("confidence_calibration"),
            "report": report,
        }

    @staticmethod
    def _apply_trading_cost_block(protected: dict, trading_cost: dict) -> dict:
        base = dict(protected.get("base", {}))
        risk = dict(base.get("risk", {}))
        reasons = list(risk.get("reasons", []))
        block_reason = trading_cost.get("reason", "trading_cost_block")
        if block_reason not in reasons:
            reasons.append(block_reason)
        risk["allowed"] = False
        risk["reasons"] = [reason for reason in reasons if reason != "risk_pass"] or [block_reason]

        decision = dict(base.get("decision", {}))
        decision["action"] = "WAIT"
        decision["reason"] = block_reason

        order = {"status": "NO_ORDER", "reason": block_reason, "trading_cost_intelligence": trading_cost}
        base["risk"] = risk
        base["decision"] = decision
        base["order"] = order

        return {
            **protected,
            "base": base,
            "protected_order": order,
            "trading_cost_block": trading_cost,
        }
