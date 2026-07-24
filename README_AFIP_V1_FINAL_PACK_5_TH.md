# AFIP V1 Final Pack 5

Production Repository Cleanup & Final Runtime Certification

## ติดตั้ง
แตก ZIP แล้ว Copy ทุกไฟล์ในโฟลเดอร์นี้ไปวางทับ `C:\AFIP\source`

## รันคำสั่งเดียว
```powershell
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_FINAL_PACK_5.ps1
```

สคริปต์จะทำ Git cleanup แบบไม่ลบไฟล์ local, รัน Focused Certification, Pack 4 Certification, Final Runtime Certification และ Full Regression

## Git
เมื่อ PASS ให้รัน:
```powershell
git add .
git commit -m "Complete AFIP V1 Pack 5 production cleanup and final certification"
git push origin main
```
