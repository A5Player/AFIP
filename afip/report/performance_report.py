class PerformanceReport:
    def generate(self, backtest_result:dict)->dict:
        return {
            "mode":backtest_result.get("mode"),
            "snapshots":backtest_result.get("snapshots",0),
            "signals":backtest_result.get("signals",0),
            "signal_rate":backtest_result.get("signal_rate",0),
            "status":"REPORT_READY"
        }
