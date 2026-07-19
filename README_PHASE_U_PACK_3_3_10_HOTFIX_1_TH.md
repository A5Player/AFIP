# Phase U Pack 3.3.10 Hotfix 1

แก้ไขสองปัญหาเฉพาะจุด:

1. PowerShell parser error ใน `APPLY_PHASE_U_PACK_3_3_10_DOC_UPDATES.ps1`
   - เปลี่ยน marker เป็น ASCII-safe text
   - จัดรูปแบบคำสั่งแบบ multiline ที่ตรวจสอบง่าย

2. Local Quality Check ค้างที่ `AFIP Simulation`
   - เดิมเรียก `python afip.py simulate` ซึ่งเริ่ม Automatic Research ก่อน simulation
   - เปลี่ยนเป็น deterministic one-shot simulation ผ่าน `python -m afip.cli.simulate`
   - ไม่เปลี่ยน Trading Logic, Signal Logic, Risk Logic หรือ Execution Authority

หลังแตกไฟล์ทับ repository ให้รัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_PHASE_U_PACK_3_3_10_DOC_UPDATES.ps1
.\RUN_PHASE_U_PACK_3_3_10.ps1
```
