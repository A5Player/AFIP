AFIP V1 Final Runtime & Dashboard Fix — Installer V2

แก้ปัญหา Copy-Item เขียนทับไฟล์ตัวเองเมื่อแตก Pack ลงใน C:\AFIP\source โดยตรง
และทำให้ Financial Naming เป็น audit แบบ background/non-blocking ไม่ขวางการเปิด AFIP

รัน:
cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_AFIP_V1_FINAL_RUNTIME_DASHBOARD_FIX.ps1
