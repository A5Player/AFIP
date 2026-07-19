# AFIP Phase U Pack 3.4.9
## การรับรองความถูกต้องของข้อมูลการเงินและ Intelligence Runtime

แพตช์นี้ลบค่าการเงินที่ระบบสร้างขึ้นเอง และเพิ่มการตรวจสอบแหล่งข้อมูลจริงสำหรับ P1-P4, Intelligence Sources และ Cross-Market Gold Research

### กฎความปลอดภัย

- ค่าที่ไม่มีข้อมูลจริงแสดง `DATA_UNAVAILABLE`
- สถานะ `READY`, `CONNECTED` หรือ `VERIFIED` ต้องมีหลักฐานจากแหล่งข้อมูลจริง
- Cross-Market Research ไม่มีสิทธิ์ส่งออเดอร์
- ความสัมพันธ์ทุกชนิดอยู่ในสถานะ `RESEARCH_ONLY` จนกว่าจะผ่าน Evidence Certification
- ไม่มีค่า Balance, Equity, Allocation หรือสถานะเชื่อมต่อจำลอง

### ลำดับข้อมูล

Raw Data -> Normalized Data -> Feature Engineering -> Research Database -> Knowledge Database -> Certification -> Trading Intelligence

Pack 3.4.9 เก็บข้อมูลไว้ที่ Research Database และไม่ข้ามขั้น Certification

### การเริ่มเก็บข้อมูลจริง

ตรวจ `config/cross_market_gold_intelligence.json` โดยเฉพาะชื่อ Symbol ของ Broker และ MT5 terminal path แล้วรัน

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\RUN_PHASE_U_PACK_3_4_9.ps1
```

ผลลัพธ์หลักอยู่ใน `runtime/certification`, `runtime/research/cross_market` และ Dashboard หน้า Cross-Market Intelligence

ข้อมูล COT, ETF, Macro, Geopolitical, Central Bank Gold Purchases และต้นทุนเหมืองทอง AISC จะไม่ถูกแสดงว่าเชื่อมต่อ จนกว่าจะมี Provider จริงส่ง Snapshot พร้อมเวลาและหลักฐานแหล่งข้อมูล
