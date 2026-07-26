# Revision 1

แก้ installer ให้รองรับการแตกแพ็กและคัดลอกไฟล์ลง `C:\AFIP` โดยตรง โดยจะไม่พยายาม Copy ไฟล์ทับตัวเอง

# AFIP V1 Final Production Certification Pack 2

## Objective

Repair the final dashboard layout regression:

```text
test_all_primary_pages_have_bottom_safety_space
```

The failure occurred because primary generated dashboard pages did not consistently contain the required bottom safety spacing after repository cleanup restored older tracked HTML snapshots.

## Patch scope

This pack:

- adds `afip/dashboard_bottom_safety.py`;
- binds the repair to the real `python -m afip.dashboard_ui` entry point;
- regenerates primary dashboards;
- guarantees `body` bottom safety spacing of `100px`;
- applies the contract idempotently;
- runs the exact failing regression;
- runs the complete dashboard layout certification file;
- runs `git diff --check`.

This pack does not modify:

- signal logic;
- confidence thresholds;
- lot authority;
- SL/TP;
- risk gates;
- MT5 ownership;
- order execution;
- runtime start/stop behavior.

## Installation

Extract this ZIP anywhere and copy all files over:

```text
C:\AFIP
```

Then run:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_FINAL_PRODUCTION_CERTIFICATION_PACK_2.ps1
```

After the pack reports PASS:

```powershell
python -m pytest
```

Expected final result:

```text
2762 passed
0 failed
```

Then:

```powershell
git add .
git status
git commit -m "AFIP V1 Final Production Certification"
git push origin main
```
