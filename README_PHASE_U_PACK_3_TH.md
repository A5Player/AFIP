# Phase U Pack 3 — แยกสาม Dashboard และความถูกต้องของข้อมูลจริง

สร้าง Dashboard แยกเป็นสามไฟล์:

1. `afip_profiles_dashboard.html` — P1-P4 แบบละเอียด รวมข้อมูลบัญชีและการเงินทั้งหมด รีเฟรชทุก 5 วินาที
2. `afip_intelligence_engine_dashboard.html` — Intelligence และ Engine รีเฟรชด้วยตนเอง
3. `afip_research_data_dashboard.html` — ข้อมูลวิจัย ชุดข้อมูล จำนวนข้อมูล Top 10 และ Top 100 รีเฟรชด้วยตนเอง

ลบตัวเลขการเงินตัวอย่างออกจากค่าเริ่มต้นของ Dashboard แล้ว หากไม่มีข้อมูลจริงจะแสดง `DATA_UNAVAILABLE` โดยไม่แทนด้วยเลขศูนย์หรือเลขสมมติ

แพตช์นี้ไม่เปลี่ยน Trading Logic และไม่เพิ่มสิทธิ์ส่งคำสั่ง
