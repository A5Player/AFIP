# AFIP V1 Final Lightweight Realtime Dashboard

Patch Only / Backward Compatible / Read Only / No Execution Authority

## รอบอัปเดต

- หน้าแรก: 10 วินาที
- หน้าวิจัย: 10 วินาที
- หน้าโหลดข้อมูลและ Research Operations: 10 วินาที
- Profiles, Intelligence, Cross Market, Control Center และหน้าอื่น: 60 วินาที
- ไม่มีการเรียก MT5 และไม่มีสิทธิ์ส่ง Order

Dashboard monitor จะ rebuild เฉพาะ 3 หน้าสำคัญใน fast cycle และ rebuild ครบทุกหน้าใน full cycle ลด CPU และ disk I/O เทียบกับการ rebuild ทุกหน้าทุก 2 วินาที

## ติดตั้ง

```powershell
cd C:\AFIP_V1_FINAL_LIGHTWEIGHT_REALTIME_DASHBOARD_PATCH
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_LIGHTWEIGHT_REALTIME_DASHBOARD.ps1 -ProjectRoot C:\AFIP
.\RUN_AFIP_V1_FINAL_LIGHTWEIGHT_REALTIME_DASHBOARD.ps1 -ProjectRoot C:\AFIP
```

## ทดสอบจริง

```powershell
cd C:\AFIP
.\.venv\Scripts\Activate.ps1
.\START_AFIP.ps1
Start-Sleep -Seconds 70
.\STATUS_AFIP.ps1
.\STOP_AFIP.ps1
```

ตรวจ `runtime\dashboard\dashboard_monitor_status.json`:

- `fast_refresh_interval_seconds = 10`
- `full_refresh_interval_seconds = 60`
- `fast_cycles` เพิ่มทุกประมาณ 10 วินาที
- `full_cycles` เพิ่มทุกประมาณ 60 วินาที
- `execution_authority = false`
- `order_send_called = false`
