# AFIP Milestone T Pack 10

## ระบบจัดอันดับหลายเป้าหมายแบบปรับตามสถานการณ์ พร้อม Capital Preservation Gate

Pack นี้เปลี่ยนการจัดอันดับจากการดูค่าเดียว เช่น Win Rate หรือ Net Profit มาเป็นการตัดสินใจหลายชั้นแบบ Deterministic

ลำดับการเลือก:

1. ผ่าน Capital Preservation Gate
2. ผ่าน Evidence Reliability Gate
3. ตรงกับ Context ปัจจุบันมากที่สุด
4. Adaptive Composite Score
5. Drawdown และ Tail Risk ต่ำกว่า
6. Risk-Adjusted Return สูงกว่า
7. Stability สูงกว่า
8. Sample Size มากกว่า
9. Conservative Win Rate สูงกว่า
10. Normalized Profit สูงกว่า
11. ใช้ชื่อแผนและ Plan ID เป็น Tie-breaker สุดท้าย

กำไรหรือ Win Rate สูงไม่สามารถชนะข้อกำหนดรักษาเงินทุนได้

P1-P4 มีน้ำหนักต่างกัน แต่ทุก Profile ยังต้องผ่าน Safety Gate และ Evidence Gate ก่อน

ระบบรองรับข้อมูล Top 10, กางดู Top 100 และจำนวนข้อมูลที่เก็บไว้เกิน Top 100 สำหรับ Dashboard Intelligence ในอนาคต

โมดูลนี้ไม่อนุญาต Execution และไม่เรียก MT5 order_send
