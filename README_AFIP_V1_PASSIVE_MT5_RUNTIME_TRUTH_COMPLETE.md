# AFIP V1 Passive MT5 Runtime Truth Complete Pack

## ขอบเขต

แพ็กนี้แก้ Health Check และ Dashboard ให้เป็น Passive Monitoring โดยค่าเริ่มต้น

- ไม่เรียก MetaTrader5.initialize()
- ไม่เปิด terminal64.exe
- ไม่ Login หรือ Reconnect
- ตรวจ Process ของ Terminal ตาม path ของแต่ละ Profile
- แยก Runtime RUNNING ออกจาก MT5 CONNECTED/DISCONNECTED
- เก็บ Balance/Bid/Ask เดิมเป็น LAST_SNAPSHOT เมื่อ Terminal ปิด
- Dashboard Live MT5 แสดง Monitoring Mode, Terminal Process, Evidence และ Snapshot UTC
- Active diagnostic ยังใช้งานได้ด้วย --active
- ไม่เปลี่ยน Trading Logic, Lot, SL, TP หรือ Execution Authority

## ติดตั้ง

แตก ZIP แล้ว Copy ทุกไฟล์ทับที่ C:\AFIP

## ทดสอบ

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
python -m pytest tests\test_afip_v1_passive_mt5_monitoring.py -q
python -m pytest -q
```

## ตรวจแบบ Passive — ไม่เปิด MT5

```powershell
python tools\afip_mt5_multi_terminal_check.py
```

เมื่อปิด P3/P4 ควรเห็น:

```text
P3 connection_status = DISCONNECTED
P4 connection_status = DISCONNECTED
monitoring_mode = PASSIVE
process_alive = false
```

## ตรวจแบบ Active — อนุญาตเปิด/เชื่อม MT5

```powershell
python tools\afip_mt5_multi_terminal_check.py --active
```

ใช้เฉพาะการวินิจฉัยหรือ Recovery ที่ตั้งใจให้เปิด Terminal

## สร้าง Dashboard

```powershell
python -m afip.dashboard_ui
```

หรือ Live Refresh:

```powershell
.\RUN_AFIP_V1_DASHBOARD_LIVE_COMPLETE.ps1 -IntervalSeconds 10
```

## Validation

Source ที่ใช้สร้างแพ็ก:

```text
2742 passed
```
