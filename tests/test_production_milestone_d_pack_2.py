from afip.data_pipeline import (
    DataPipelineContract,
    DataPipelineQualityPolicy,
    DataPipelineRuntime,
    FinancialDataRecord,
)
from afip.runtime.production_milestone_d_data_pipeline_runtime import build_production_milestone_d_data_pipeline_state


def _ready_records():
    return [
        {"source_key": "market_data", "market_regime": "trending", "timeframe": "h1", "close_price": 2350.0, "spread_points": 24, "liquidity_score": 82, "completeness_ratio": 0.96},
        {"source_key": "regime_state", "market_regime": "trending", "timeframe": "h1", "close_price": 2350.0, "spread_points": 24, "liquidity_score": 80, "completeness_ratio": 0.94},
        {"source_key": "decision_state", "market_regime": "trending", "timeframe": "h1", "close_price": 2350.0, "spread_points": 24, "liquidity_score": 78, "completeness_ratio": 0.92},
        {"source_key": "execution_state", "market_regime": "trending", "timeframe": "h1", "close_price": 2350.0, "spread_points": 24, "liquidity_score": 76, "completeness_ratio": 0.91},
    ]


def test_financial_data_record_normalizes_market_regime_first_key():
    record = FinancialDataRecord.from_mapping({"source": " market_data ", "regime": " trending ", "tf": " h1 ", "close": 2350, "spread": 24, "liquidity": 80, "completeness": 0.95})
    assert record.source_key == "MARKET_DATA"
    assert record.market_regime == "TRENDING"
    assert record.timeframe == "H1"
    assert record.is_usable is True


def test_financial_data_record_blocks_incomplete_data():
    record = FinancialDataRecord.from_mapping({"source_key": "MARKET_DATA", "market_regime": "TRENDING", "close_price": 0, "liquidity_score": 80, "completeness_ratio": 0.95})
    assert record.is_usable is False


def test_data_pipeline_contract_orders_sources_deterministically():
    contract = DataPipelineContract.from_records(reversed(_ready_records()))
    assert contract.source_keys == ("MARKET_DATA", "REGIME_STATE", "DECISION_STATE", "EXECUTION_STATE")


def test_data_pipeline_contract_reports_missing_required_source():
    contract = DataPipelineContract.from_records(_ready_records()[:3])
    assert contract.missing_sources == ("EXECUTION_STATE",)
    assert contract.is_integrated is False


def test_data_pipeline_contract_uses_regime_state_before_signal_flow():
    contract = DataPipelineContract.from_records(_ready_records())
    assert contract.active_market_regime == "TRENDING"
    assert contract.sequence_is_valid is True


def test_data_pipeline_contract_uses_data_derived_readiness():
    contract = DataPipelineContract.from_records(_ready_records())
    assert contract.average_completeness == 0.9325
    assert contract.average_liquidity == 79.0
    assert contract.readiness_score == 86.8375


def test_data_quality_policy_waits_for_missing_source():
    decision = DataPipelineQualityPolicy().decide(DataPipelineContract.from_records(_ready_records()[:2]))
    assert decision.status == "DATA_PIPELINE_WAIT"
    assert decision.action == "WAIT"


def test_data_quality_policy_blocks_unusable_record():
    records = _ready_records()
    records[0] = {**records[0], "completeness_ratio": 0.2}
    decision = DataPipelineQualityPolicy().decide(DataPipelineContract.from_records(records))
    assert decision.status == "DATA_PIPELINE_BLOCKED"
    assert decision.reason == "financial_data_record_not_usable"


def test_data_quality_policy_confirms_ready_pipeline():
    decision = DataPipelineQualityPolicy().decide(DataPipelineContract.from_records(_ready_records()))
    assert decision.status == "DATA_PIPELINE_READY"
    assert decision.action == "INTEGRATE_DATA"


def test_data_pipeline_runtime_builds_audit_report():
    report = DataPipelineRuntime().run(_ready_records())
    assert report.status == "DATA_PIPELINE_READY"
    assert report.source_count == 4
    assert report.record_count == 4
    assert report.usable_record_count == 4
    assert report.active_market_regime == "TRENDING"


def test_production_milestone_d_data_pipeline_runtime_is_deterministic():
    first = build_production_milestone_d_data_pipeline_state()
    second = build_production_milestone_d_data_pipeline_state()
    assert first == second
    assert first["status"] == "DATA_PIPELINE_READY"
