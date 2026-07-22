วิธีติดตั้ง
1. ปิด Long Run เดิมด้วย Ctrl+C
2. แตก ZIP นี้ลงทับ C:\AFIP\source
3. เลือก Replace files in destination
4. เปิด PowerShell แล้วรัน:

cd C:\AFIP\source
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\.venv\Scripts\Activate.ps1
.\RUN_AFIP_V1_FINAL_REVISION_2_2.ps1

ไฟล์ที่ลงทับ:
afip\dashboard_ui\research_operations.py
