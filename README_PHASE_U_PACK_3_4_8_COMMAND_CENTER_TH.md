# AFIP Phase U Pack 3.4.8 — Unified Dashboard Command Center

แพตช์นี้เปลี่ยน `runtime/dashboard/afip_dashboard.html` เป็นศูนย์บัญชาการหน้าเดียว
มีเมนูสลับระหว่าง:

- P1–P4 Operations
- Intelligence & Engines
- Research & Data

แต่ละหน้าจะถูกโหลดในกรอบเดียวโดยไม่เปิดแท็บใหม่ ไฟล์ Dashboard แยกทั้งสามยังคงอยู่เพื่อความเข้ากันได้ย้อนหลัง

## ขอบเขตความปลอดภัย

- Presentation only
- ไม่แก้ Trading Engine
- ไม่แก้ Lot Size, Position Sizing, SL หรือ TP
- ไม่เชื่อม MT5 เพิ่มเติม
- ไม่เปลี่ยน Execution Authority
- ไม่สั่ง Automatic Research ระหว่างการสลับหน้า

## ติดตั้งที่เครื่องหลัก

แตก ZIP ลง `C:\AFIP` โดยตรง แล้วรัน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process Bypass
.\INSTALL_PHASE_U_PACK_3_4_8_COMMAND_CENTER.ps1
.\RUN_PHASE_U_PACK_3_4_8_COMMAND_CENTER.ps1
```

เปิด:

```text
C:\AFIP\runtime\dashboard\afip_dashboard.html
```

## นำไปใช้ที่ VPS

หลังทดสอบที่เครื่องหลักผ่าน ให้นำ ZIP เดียวกันไปไว้ที่ VPS แตกลง `C:\AFIP` แล้วใช้คำสั่งติดตั้งและทดสอบชุดเดียวกัน
