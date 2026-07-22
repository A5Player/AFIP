# AFIP Phase U Pack 3.5 Revision 1

การแก้ไข packaging compatibility สำหรับ Full Regression collection error

## Root cause

`tests/test_phase_u_dashboard_live_progress.py` import:

`afip.dashboard_ui.live_research_dashboard`

แต่ไฟล์ `live_research_dashboard.py` ถูกวางอยู่นอก `source/afip/dashboard_ui` ใน baseline ZIP จึงเกิด `ModuleNotFoundError`.

## Change

เพิ่มไฟล์ที่ตำแหน่งถูกต้อง:

- `afip/dashboard_ui/live_research_dashboard.py`

ไม่เปลี่ยน Lot Authority, Execution, SL/TP, broker policy, credentials หรือ runtime data.

## Validation

รัน:

```powershell
.\RUN_PHASE_U_PACK_3_5_REVISION_1.ps1
```

Expected:

```text
1 passed
```

จากนั้นรัน full regression ใหม่:

```powershell
python -m pytest
```
