# AFIP Phase U Pack 3.3.1.1 — Documentation Runner Hotfix

แก้ปัญหา `RUN_PHASE_U_PACK_3_3_1.ps1` หยุดหรือรายงาน `Documentation update failed` หลังการ append เอกสาร

## สาเหตุ

1. Runner เดิมตรวจ `$LASTEXITCODE` หลังเรียก PowerShell script โดยตรง ซึ่งค่านี้อาจเป็นค่าค้างจาก native command ก่อนหน้า
2. Updater เดิมใช้ `Get-Content -Raw` กับเอกสารหลัก ทำให้ช้าหรือใช้หน่วยความจำมากเมื่อไฟล์มีขนาดใหญ่

## การแก้ไข

- ใช้ exception handling สำหรับ PowerShell script แทน `$LASTEXITCODE`
- ตรวจ marker แบบอ่านทีละบรรทัด
- append ผ่าน .NET stream
- รันซ้ำได้โดยไม่เพิ่ม section ซ้ำ
- ไม่แก้ Python, trading policy, execution, risk, lot, SL หรือ TP
