# AFIP Phase U Pack 3.3.2 — การเชื่อม M30 Historical Collection และ Data Lake

เพิ่มการจัดเก็บแท่ง OHLC ที่ปิดแล้วจาก MT5 ลง Financial Data Lake แบบ append-only รวม M30 และปรับ Historical Coverage ให้ใช้ Timeframe Registry กลาง

แพ็กนี้เป็นงานข้อมูลและวิจัยเท่านั้น ไม่เปลี่ยน Execution, Risk, Lot Size, SL, TP หรือนโยบาย Profile

## ความปลอดภัย
หยุด AFIP Runtime ที่กำลังเขียนข้อมูล Research ก่อนติดตั้งหรือรันตรวจสอบ
