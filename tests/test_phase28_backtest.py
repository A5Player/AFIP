from afip.backtest.backtest_runner import BacktestRunner

def snap(v):
    return {"closes":[v,v+1,v+2,v+3,v+4],
            "highs":[v+.5,v+1.5,v+2.5,v+3.5,v+4.5],
            "lows":[v-.5,v+.5,v+1.5,v+2.5,v+3.5]}

def test_backtest():
    r=BacktestRunner().run([snap(2300),snap(2310)])
    assert r["mode"]=="SIMULATION"
    assert r["snapshots"]==2
