# AFIP Phase U Pack 3.3.6
## การเชื่อม Research Consumer และการควบคุม Execution แยกตามโปรไฟล์

แพ็กนี้แยกสถานะการเปิดโปรไฟล์เพื่อข้อมูล/วิจัย ออกจากสิทธิ์เริ่ม Execution Worker อย่างชัดเจน

สถานะหลังติดตั้ง:

- P1: เปิดโปรไฟล์ เปิด Execution และเปิด Research
- P2: เปิดโปรไฟล์ ปิดเฉพาะ Execution และเปิด Research
- P3: เปิดโปรไฟล์ ปิดเฉพาะ Execution และเปิด Research
- P4: เปิดโปรไฟล์ เปิด Execution และเปิด Research

P2 และ P3 ยังคง Configuration, Runtime path, Historical data, Research ledger และสามารถเปิด Execution กลับได้ภายหลังโดยไม่ต้อง Migration ตัว Demo Gateway จะหยุดก่อนเข้าถึง MT5 และก่อน order_check/order_send

M30 ยังคงพร้อมให้ Research Consumer ใช้ผ่าน Universal Timeframe Registry และผลวิจัยจะไม่เปลี่ยน Live Trading Policy อัตโนมัติ

แพ็กนี้ไม่แก้ Lot sizing, Capital gating, Maximum units, SL, TP, Risk threshold หรือ Order construction
