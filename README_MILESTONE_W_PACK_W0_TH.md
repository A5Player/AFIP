# AFIP Milestone W — Pack W0

ชุดนี้ล็อกสถาปัตยกรรม ขอบเขตอำนาจ Data Flow และจุดเชื่อมของ Milestone W จาก Source จริง โดยเป็นการเพิ่ม Contract และ Test เท่านั้น ไม่เปลี่ยนพฤติกรรมการเทรด

รันจากโฟลเดอร์ Patch ที่แตกไฟล์แล้ว:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_MILESTONE_W_PACK_W0.ps1 -ProjectRoot C:\AFIP\source
.\VALIDATE_MILESTONE_W_PACK_W0.ps1 -ProjectRoot C:\AFIP\source
```

ห้ามเริ่ม W1 จนกว่า Validation จะแสดง PASS
