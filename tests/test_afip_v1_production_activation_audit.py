from pathlib import Path

from tools.afip_production_activation_audit import TARGETS, audit


def test_activation_audit_has_ten_level_contract():
    report = audit(Path('.').resolve())
    assert report['schema_version'] == 'afip-production-activation-audit.v1'
    assert report['audit_levels'] == 10
    assert len(report['modules']) == len(TARGETS)


def test_critical_modules_are_found_in_source():
    report = audit(Path('.').resolve())
    rows = {row['module']: row for row in report['modules']}
    for name in ('CompleteTradePlan', 'PositionCare', 'TradeLifecycle', 'LotAuthority', 'DemoExecutionGateway'):
        assert rows[name]['exists'], name


def test_position_care_is_not_falsely_certified_active_without_runtime_call():
    report = audit(Path('.').resolve())
    row = next(row for row in report['modules'] if row['module'] == 'PositionCare')
    assert row['status'] in {'ORPHAN', 'DEAD_CODE', 'NO_EFFECT', 'PARTIAL', 'ACTIVE'}
    if not row['called']:
        assert row['status'] != 'ACTIVE'
    if row['execution_neutral']:
        assert row['called'] is True
        assert row['affects_runtime'] is True


def test_descriptive_execution_neutral_comment_does_not_hide_real_runtime_effect():
    report = audit(Path('.').resolve())
    rows = {row['module']: row for row in report['modules']}
    assert rows['CompleteTradePlan']['called'] is True
    assert rows['CompleteTradePlan']['affects_runtime'] is True
    assert rows['CompleteTradePlan']['status'] == 'ACTIVE'
    assert rows['PositionCare']['called'] is True
    assert rows['PositionCare']['affects_runtime'] is True
    assert rows['PositionCare']['status'] == 'ACTIVE'


def test_report_exposes_production_certification_boolean():
    report = audit(Path('.').resolve())
    assert isinstance(report['production_activation_certified'], bool)
    assert isinstance(report['critical_blockers'], list)
