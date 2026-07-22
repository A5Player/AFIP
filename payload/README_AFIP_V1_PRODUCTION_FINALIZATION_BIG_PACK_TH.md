# AFIP V1 Production Finalization Big Pack

Pack รวมสำหรับปิดงาน Production Core ก่อนปรับ Dashboard เชิงรายละเอียด

## ขอบเขต

- รวม P1 Conservative, P2 Balanced, P3 Aggressive และ P4 Experimental เข้าสู่ execution pipeline เดียว
- P4 ยังคงเก็บข้อมูลวิจัยผ่าน Research Runtime และ Data Lake แต่ไม่มี execution path พิเศษ
- Sequential Router ใช้ child process อายุสั้นหนึ่ง process ต่อหนึ่ง profile
- ตรวจ ownership ก่อน order_check, ก่อน order_send และหลัง order_send
- กู้คืน routing lock เฉพาะเมื่อ process เจ้าของตายแล้วและ lock เก่าเกินเกณฑ์
- ล้างเฉพาะ stale PID, stale lock และ temporary files โดยไม่ลบ financial/research evidence
- Dashboard อ่าน profile/runtime data ผ่าน Production Runtime Authority snapshot เดียว

## Safety

Pack นี้ไม่เปิดเงินจริง ไม่แก้ค่า `live_execution` และไม่ ARM ระบบอัตโนมัติ การส่งคำสั่งยังต้องผ่าน demo arming, account binding, capital authority, confidence, risk, spread และ order validation เดิมทั้งหมด

## การติดตั้ง

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_PRODUCTION_FINALIZATION_BIG_PACK.ps1 -ProjectRoot C:\AFIP\source
```

## การตรวจสอบ

```powershell
cd C:\AFIP\source
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_PRODUCTION_FINALIZATION_BIG_PACK.ps1
```

## หลังติดตั้ง

ยังไม่ควรเริ่ม 24-hour demo certification จนกว่าชุด regression ทั้งหมดผ่านและตรวจ environment credentials/terminal mappings ครบ P1-P4
