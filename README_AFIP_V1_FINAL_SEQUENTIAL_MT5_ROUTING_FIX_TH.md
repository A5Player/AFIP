# AFIP V1 Final Sequential MT5 Routing Fix

สาเหตุจริง: MetaTrader5 Python bridge เป็น session ระดับ process และ worker หลาย process ที่เริ่มพร้อมกันสามารถ attach ไปยัง terminal ตัวเดียวกันได้ แม้ config ของแต่ละ Profile ถูกต้อง

การแก้ไข:
- ยกเลิก worker P1/P2/P3 ที่ทำงานพร้อมกัน
- ใช้ router process เดียว
- ประมวลผล P1 -> shutdown MT5 -> P2 -> shutdown MT5 -> P3 ตามลำดับ
- ตรวจ P1-P4 ทุกบัญชี รวม P4 Research-only
- ไม่มี fallback ไป P1
- ถ้า binding ไม่ตรง จะ BLOCK ก่อน order_check/order_send
- สถานะแสดง `router_mode = SINGLE_PROCESS_SEQUENTIAL_MT5`

แพตช์ไม่เปิด AFIP อัตโนมัติหลังติดตั้ง
