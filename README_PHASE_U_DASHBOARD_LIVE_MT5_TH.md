# AFIP Phase U — Dashboard Live MT5 Complete

แพตช์นี้แก้หน้า Dashboard 1 ให้ดึงข้อมูลสดจาก MT5 P1–P4 และแสดงสถานะด้วยไอคอน การ์ด ตัวเลข และ Progress Bar

ข้อมูลสดที่เพิ่ม: Balance, Equity, Margin, Free Margin, Floating P/L, Currency, Trade Allowed, Positions, Orders, Bid, Ask, Spread, Digits, Point Size และ Financial Source

## ติดตั้ง
แตกไฟล์ทับที่ `C:\AFIP\source`

## ทดสอบ
```powershell
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pytest tests\test_phase_u_dashboard_live_mt5_fields.py -v
```

## Build ครั้งเดียว
```powershell
.\BUILD_AFIP_DASHBOARD_LIVE_ONCE.ps1
```

## Live ทุก 10 วินาที
```powershell
.\START_AFIP_DASHBOARD_LIVE_MT5.ps1
```

MT5 ทั้ง 4 Terminal ต้องเปิดอยู่ และ Environment credentials ของ P1–P4 ต้องพร้อม
Dashboard เป็น Read-only และไม่มีสิทธิ์ส่งคำสั่งซื้อขาย
