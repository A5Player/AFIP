# AFIP V1 Final Live Demo Certification

## ติดตั้ง
แตก ZIP แล้ว Copy ทุกไฟล์ไปวางทับ `C:\AFIP\source`

## รัน
```powershell
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_FINAL_LIVE_DEMO_CERTIFICATION.ps1
```

สคริปต์ตรวจ Terminal, Login และ Server ของ P1-P4 แบบอ่านอย่างเดียวผ่าน Runtime Authority เดิม ไม่มีการเรียก order_check หรือ order_send จากนั้นรัน Full Regression ต่อทันที
