# AFIP V1 Final Execution Ownership Fix

แพตช์นี้แก้ปัญหาคำสั่ง P2/P3 ไปรวมที่บัญชี P1 โดยบังคับ ownership ตลอดเส้นทางส่งคำสั่ง

- MT5 critical section ทำงานทีละ Profile ผ่าน `runtime/execution/account_routing.lock`
- ตรวจ Login, Server และ Terminal folder ตอน preflight
- ตรวจซ้ำก่อน `order_check`
- ตรวจซ้ำทันที ก่อนและหลัง `order_send`
- ตรวจ Magic Number และ Comment ว่าเป็นของ Profile นั้นจริง
- หากข้อมูลใดไม่ตรง จะ BLOCK และไม่ส่งคำสั่ง
- `START_AFIP_SAFE.ps1` คืน PowerShell prompt หลังเริ่ม worker
- ตัวติดตั้งไม่เริ่ม AFIP อัตโนมัติ

## ติดตั้ง

```powershell
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_EXECUTION_OWNERSHIP_FIX.ps1
```

เมื่อผลตรวจ PASS และเปิด Algo Trading แล้ว:

```powershell
.\START_AFIP_SAFE.ps1
```

หยุดฉุกเฉิน:

```powershell
.\STOP_AFIP_EMERGENCY.ps1
```
