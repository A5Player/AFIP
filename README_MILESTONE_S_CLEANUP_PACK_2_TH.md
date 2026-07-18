# Milestone S Cleanup Pack 2 — Responsibility & Dependency Matrix

Pack 1 พบว่า:

- Components: 999
- Unit Allocation authorities/candidates: 24
- Position Sizing authorities/candidates: 69
- Protection Plan authorities/candidates: 7
- `order_send` และ `order_check` อยู่ที่ Demo Gateway จุดเดียว

อย่างไรก็ตาม จำนวนที่ตรวจพบเป็น keyword authority candidates ไม่ได้แปลว่า
ทุกไฟล์ตัดสินใจซ้ำจริง Pack 2 จึงตรวจ import/dependency เพื่อแยกบทบาทให้แม่นขึ้น

## Candidate Owners

- Order Send: `afip/demo_execution_gateway/runtime.py`
- Order Check: `afip/demo_execution_gateway/runtime.py`
- Unit Allocation: `afip/unit_allocation/runtime.py`
- Position Sizing: `afip/adaptive_position_sizing/runtime.py`
- Protection Plan: `afip/protection/sl_tp_planner.py`
- Risk Approval: `afip/portfolio/portfolio_risk.py`

ทั้งหมดเป็นเพียง Candidate ยังไม่ถูกเปลี่ยนเส้นทาง Runtime

## การจัดประเภท

- PRIMARY_CANDIDATE
- SUPPORTING_CANDIDATE
- SAFETY_GUARD
- OBSERVER_OR_MODEL
- RESEARCH_OR_SIMULATION
- CERTIFICATION_OBSERVER
- LEGACY_OR_UNUSED_CANDIDATE
- BLOCKED_PENDING_REVIEW

## วิธีรัน

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\AFIP
.\RUN_MILESTONE_S_CLEANUP_PACK_2.ps1
```

คำสั่งหยุดระบบถูกแก้ให้ใช้ module invocation จึงไม่เกิด
`ModuleNotFoundError: No module named 'afip'` จากการรันไฟล์ tool โดยตรงอีก
