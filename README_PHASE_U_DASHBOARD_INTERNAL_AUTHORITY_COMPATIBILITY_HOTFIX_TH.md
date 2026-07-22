# AFIP Phase U Dashboard Internal Authority Compatibility Hotfix

แก้ regression ที่ทำให้แถว `Positions / Orders` หายหลังติดตั้ง Internal Authority Overlay

- คืนสัญญาเดิมของ `_profile_rows`
- ใช้ข้อมูลจริงจาก `positions_total` และ `orders_total`
- ไม่เปลี่ยน execution, MT5 connection หรือ lot authority
