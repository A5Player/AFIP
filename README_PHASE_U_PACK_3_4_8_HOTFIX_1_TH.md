# AFIP Phase U Pack 3.4.8 Hotfix 1

## รูปแบบ Direct Overlay

ZIP นี้ไม่มีโฟลเดอร์ Pack ครอบด้านนอก และไม่มีโฟลเดอร์ PATCH

1. เปิด ZIP
2. เลือกไฟล์และโฟลเดอร์ทั้งหมดที่เห็นทันที
3. Copy ไปที่ `C:\AFIP`
4. เลือก Replace files in the destination
5. รัน `C:\AFIP\RUN_PHASE_U_PACK_3_4_8_COMMAND_CENTER.ps1`

หลังคัดลอก ตำแหน่งที่ถูกต้องต้องเป็น:

- `C:\AFIP\afip\dashboard_ui\home.py`
- `C:\AFIP\tests\test_phase_u_pack_3_4_8_command_center.py`
- `C:\AFIP\RUN_PHASE_U_PACK_3_4_8_COMMAND_CENTER.ps1`

Hotfix นี้ใช้ PowerShell script แบบ ASCII-only เพื่อหลีกเลี่ยงปัญหาการอ่าน encoding ของ Windows PowerShell 5.1
