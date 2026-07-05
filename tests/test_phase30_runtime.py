from afip.runtime.runtime_v1 import RuntimeV1
def test_runtime():
    r=RuntimeV1().simulate()
    assert r["status"]=="OK"
    assert r["mode"]=="SIMULATION"
