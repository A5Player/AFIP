# AFIP V1 Final Sequential Router Startup Fix

แก้ปัญหา `START_AFIP_SAFE.ps1` รายงานว่าเริ่มแล้ว ทั้งที่ `router.pid = null` และ `router.running = false`

การแก้ไข:
- รอ startup handshake จาก Router สูงสุด 20 วินาที
- ถ้า Router ออกหรือไม่สร้าง PID จะ BLOCK และคืน exit code ผิดพลาด
- แสดงท้าย log เมื่อ Router เริ่มไม่ได้
- ล้างสถานะ binding เก่าของ P2/P3 ก่อนเริ่ม
- สถานะ `connected_account_login` และ `connected_terminal_folder` ใช้ผล Account Isolation ล่าสุดเป็น authority
- แยก `last_execution_*` สำหรับข้อมูลรอบส่งคำสั่งล่าสุด
- Router ไม่หยุดทั้งระบบเมื่อ Profile ใด Profile หนึ่งเกิด exception
- ไม่เริ่ม AFIP อัตโนมัติหลังติดตั้ง
