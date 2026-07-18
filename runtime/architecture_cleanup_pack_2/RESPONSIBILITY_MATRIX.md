# AFIP Responsibility Matrix

This report selects candidates only. It does not redirect runtime calls yet.

## ORDER_CHECK

- Preferred owner: `afip/demo_execution_gateway/runtime.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- PRIMARY_CANDIDATE: **1**

## ORDER_SEND

- Preferred owner: `afip/demo_execution_gateway/runtime.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- PRIMARY_CANDIDATE: **1**

## POSITION_SIZING

- Preferred owner: `afip/adaptive_position_sizing/runtime.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- CERTIFICATION_OBSERVER: **9**
- LEGACY_OR_UNUSED_CANDIDATE: **19**
- OBSERVER_OR_MODEL: **4**
- PRIMARY_CANDIDATE: **1**
- RESEARCH_OR_SIMULATION: **9**
- SUPPORTING_CANDIDATE: **27**

## PROTECTION_PLAN

- Preferred owner: `afip/protection/sl_tp_planner.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- LEGACY_OR_UNUSED_CANDIDATE: **2**
- RESEARCH_OR_SIMULATION: **2**
- SAFETY_GUARD: **1**
- SUPPORTING_CANDIDATE: **2**

## RISK_APPROVAL

- Preferred owner: `afip/portfolio/portfolio_risk.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- LEGACY_OR_UNUSED_CANDIDATE: **5**
- PRIMARY_CANDIDATE: **1**
- SUPPORTING_CANDIDATE: **2**

## UNIT_ALLOCATION

- Preferred owner: `afip/unit_allocation/runtime.py`
- Exists: **True**
- Status: **CANDIDATE_NOT_CERTIFIED**

- LEGACY_OR_UNUSED_CANDIDATE: **6**
- OBSERVER_OR_MODEL: **6**
- PRIMARY_CANDIDATE: **1**
- RESEARCH_OR_SIMULATION: **2**
- SAFETY_GUARD: **1**
- SUPPORTING_CANDIDATE: **8**

## Next Gate

Cleanup Pack 3 may redirect Unit Allocation only after the preferred owner and its direct consumers are inspected. No module deletion is permitted.
