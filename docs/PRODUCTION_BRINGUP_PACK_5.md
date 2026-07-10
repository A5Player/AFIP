# Production Bring-up Pack 5 — Explainable Order Center

## Purpose

Pack 5 adds a read-only Explainable Order Center for the AFIP dashboard. The goal is to remove black-box order management by showing every important paper-order decision reason in English and Thai.

## Scope

This patch adds dashboard explainability for:

- Waiting Reason
- Entry Reason
- Holding Reason
- Stop Loss Move Reason
- Take Profit Change Reason
- Trailing Stop Reason
- Partial Close Reason
- Exit Reason
- Expected Next Action
- Confidence
- Risk
- Next Review Time

## Safety Policy

- Live execution remains disabled.
- Broker policy remains XM only.
- Symbol policy remains GOLD# only.
- The unit system remains 1 unit = 0.01 lot.
- Lot size is never increased directly. The runtime displays unit count and derived total lot only.
- The module is read-only and does not send broker orders.
- Trading logic is not changed.

## Runtime

New runtime:

```text
afip.explainable_order_center.ExplainableOrderCenterRuntime
```

The runtime accepts existing dashboard and paper order records and returns a deterministic report containing bilingual explanations. Unsupported broker, unsupported symbol, and live execution are blocked at the explanation layer.

## Dashboard Integration

The dashboard now includes a dedicated panel:

```text
Explainable Order Center / ศูนย์คำสั่งแบบอธิบายได้
```

The panel displays the order status, units, total lot, confidence, risk, next action, next review time, and bilingual explanations for each important order-management reason.

## Compatibility

This patch is backward compatible. It adds a new module and a dashboard panel without replacing existing paper trading, decision, execution, or market calendar modules.

## Validation

Run:

```powershell
pytest tests/test_production_bringup_pack_5.py -v
pytest
python tools/afip_local_quality_check.py
python -m afip.dashboard_ui
```

Expected status:

```text
Production Bring-up Pack 5: PASS
Live execution: disabled
Dashboard: generated
```
