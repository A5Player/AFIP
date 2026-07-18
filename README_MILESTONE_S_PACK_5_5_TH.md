# AFIP Milestone S Pack 5.5 — การรับรองนโยบาย Position

Patch นี้ทำให้ Simulation และ Demo Gateway ใช้นโยบาย Confidence-to-Unit จากแหล่งเดียวกัน

## นโยบายที่ล็อก

- Confidence ต่ำกว่า 98.0: 0 Unit
- 98.0–98.49: สูงสุด 1 Unit
- 98.5–99.49: สูงสุด 2 Units
- 99.5–100.0: สูงสุด 3 Units
- Confidence เป็นเพียงเพดาน ห้ามบังคับเปิดครบทุก Unit
- จำนวนสุดท้ายต้องผ่านข้อจำกัดทุน โปรไฟล์ ความเสี่ยง Margin Trading Cost และ Execution Capacity
- ห้าม Martingale

## การรับรองโปรไฟล์

- P1 ถึง 0.10 lot ต่อ Unit ที่ Balance 15,000 และไม่เพิ่มเกิน 0.10
- P2 ตรวจลำดับ Tier และเพดานถาวร 1.00 lot
- P3 หลัง 0.02 lot เพิ่ม 0.01 ทุก Balance 450 และหยุดที่ 10.00 lots
- P4 คงที่ 0.01 สำหรับงานวิจัย ไม่มีการเพิ่ม Lot ตามทุน

## ความปลอดภัย

Pack นี้ไม่เปิดเงินจริง และไม่เปลี่ยน Execution Lock เดิม
