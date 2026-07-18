# AFIP Milestone S Cleanup Pack 4.2

## จุดประสงค์

แก้ Full Regression ที่เหลือ 2 จุดหลัง Pack 4.1 โดยไม่ลดเกณฑ์ Confidence ของ Demo Execution สำหรับ P1-P3

## สิ่งที่แก้ไข

1. เปลี่ยนคำในเอกสารจาก `Protection Control` เป็น `Protection Control` เพื่อให้ผ่าน Financial Naming Validation
2. คืนความเข้ากันได้ของเส้นทาง Simulation เดิม เมื่อ Confidence Calibration และ Risk Assessment ผ่านแล้ว
3. เกณฑ์ปกติของ P1-P3 ยังคงเดิม:
   - ต่ำกว่า 98.00: 0 Unit สำหรับเส้นทาง Execution ปกติ
   - 98.00-98.49: สูงสุด 1 Unit
   - 98.50-99.49: สูงสุด 2 Units
   - 99.50-100.00: สูงสุด 3 Units
4. Compatibility อนุญาตเพียง 1 Unit เฉพาะ Legacy `SIMULATION` ที่ถูกระบุชัดเจนและ Risk ผ่านแล้วเท่านั้น
5. Risk ไม่ผ่าน, Spread สูง, Action เป็น WAIT และการเรียก Builder โดยตรงยัง Fail-Closed
6. Order Simulation บันทึกแหล่งที่มาของ Unit Allocation
7. ตัวติดตั้งลบ `patch_payload` หลังติดตั้ง ป้องกัน pytest import-file mismatch

หลังติดตั้ง Demo Execution ยังคง STOPPED

