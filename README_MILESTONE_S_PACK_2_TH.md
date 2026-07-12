# AFIP Version 1.0 — Milestone S Pack 2
## การตั้งค่า Demo 4 โปรไฟล์สำหรับใช้งานจริงบน VPS

Pack 2 เพิ่มระบบควบคุม P1–P4 แบบแยกข้อมูลออกจากกัน โดยทุกโปรไฟล์ยังคงเป็น `LOCKED_SIMULATION_ONLY`, `direct_execution=False`, `live_execution=False` และ `NO_ORDER_SENT`

ค่าเริ่มต้นคือ P1 และ P4 เปิดใช้งาน ส่วน P2 และ P3 ปิดใช้งาน โฟลเดอร์ MT5 ตรงตาม `C:\XM Global MT5 P1` ถึง `P4` และใช้ Server ตามที่กำหนดใน `config/four_profile_demo.json`

เพื่อความปลอดภัย ไม่มีเลขบัญชีหรือรหัสผ่านอยู่ใน Git และ Patch ZIP ให้รัน `SET_AFIP_PROFILE_CREDENTIALS_LOCAL.ps1` บน VPS แล้วกรอกข้อมูลทั้ง 4 บัญชี สคริปต์จะเก็บไว้ใน Environment Variables ของ Windows User เท่านั้น หลังตั้งค่าให้ปิดและเปิด PowerShell ใหม่

คำสั่งสำคัญ:

```powershell
python tools/afip_four_profile_control.py status
python tools/afip_four_profile_control.py prepare --profiles P1 P4
python tools/afip_four_profile_control.py start-selected --profiles P1 P4
python tools/afip_four_profile_control.py stop-selected --profiles P1 P4
python tools/afip_four_profile_control.py restart-selected --profiles P1 P4
python tools/afip_four_profile_control.py start-all
python tools/afip_four_profile_control.py stop-all
```

ค่า `launch_mt5` เริ่มต้นเป็น `false` หมายถึง AFIP เชื่อมกับ MT5 ที่ผู้ใช้เปิดไว้แล้ว หากต้องการให้เปิดอัตโนมัติจึงเปลี่ยนเป็น `true` รายโปรไฟล์

ข้อมูล Runtime, Database, Logs, Dashboard, Learning, Knowledge และ Statistics แยกอยู่ใต้ `runtime/profiles/p1` ถึง `p4` และระบบจะบล็อกค่าที่ซ้ำกันก่อนเริ่มทำงาน
