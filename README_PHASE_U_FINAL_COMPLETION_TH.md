# AFIP Phase U Final Completion — Dashboard First

ชุดนี้แก้ฐานสำคัญก่อน: Dashboard 4 หน้าอ่านสถานะ MT5 P1-P4 และข้อมูลบัญชีจริงแบบ read-only พร้อมลดเวลาสร้างหน้า Research ด้วย cache 5 นาที

## ความปลอดภัย
- MT5 เปิดไว้ได้ แต่ต้องหยุด AFIP execution/research PowerShell ก่อนลงไฟล์ทับ
- การตรวจ MT5 ไม่ส่ง order
- Dashboard ไม่เปลี่ยน execution authority
- ยังไม่ประกาศพร้อมเงินจริงจนกว่า full regression, research catch-up, single-intelligence audit และ lot-authority certification ผ่าน

## รันครั้งเดียว
`./BUILD_AFIP_PRODUCTION_DASHBOARD_ONCE.ps1`

## Live
`./START_AFIP_PRODUCTION_DASHBOARD.ps1`
