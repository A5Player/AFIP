# Phase U Pack 2 — Dashboard แยกสองหน้า

แพตช์นี้เปลี่ยนการแสดงผลจากหน้าเดียวเป็น HTML สองไฟล์ โดยยังรักษา DashboardUIRuntime เดิมเพื่อความเข้ากันได้ย้อนหลัง

## Dashboard 1

`runtime/dashboard/afip_profiles_dashboard.html`

- เปรียบเทียบ P1-P4 แบบละเอียดในตารางแนวนอนเดียวกัน
- แต่ละข้อมูลอยู่หนึ่งแถว และ P1-P4 อยู่สี่คอลัมน์ตรงกัน
- แสดงบัญชี แผน นโยบายทุน Decision, Position, SL/TP, Position Care, กำไร การเชื่อมต่อ และความสดใหม่ของข้อมูล
- รีเฟรชอัตโนมัติทุก 5 วินาที

## Dashboard 2

`runtime/dashboard/afip_intelligence_research_dashboard.html`

- แสดง Intelligence, Engine, Runtime, Research, Data และ Certification ที่มีอยู่ทั้งหมด
- แยกหมวดหมู่ชัดเจน
- Top 10 เปิดแสดง และ Top 100 กดขยายได้เมื่อมีข้อมูลจัดอันดับ
- รีเฟรชด้วยปุ่มเท่านั้น ไม่มีการรีเฟรชอัตโนมัติ

ไม่มีการเปลี่ยน Trading Logic, Threshold, Position Sizing หรืออำนาจส่งคำสั่งซื้อขาย
