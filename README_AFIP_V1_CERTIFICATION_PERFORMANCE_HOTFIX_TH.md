# AFIP V1 Certification Performance Hotfix

แก้ Financial Naming timeout จาก 180 เป็น 900 วินาที และแสดง heartbeat ทุก 15 วินาที

- ไม่ลดจำนวน Source file ที่ตรวจ
- ไม่เปลี่ยน Financial Naming policy
- ไม่เปลี่ยน Trading Runtime
- แสดงชื่อและผลแต่ละ certification stage
- เมื่อ PASS แล้วจะสร้าง cache และรอบถัดไปใช้ CACHE_HIT
