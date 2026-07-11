# Milestone N Pack 4 — Capital Allocation

เพิ่ม Runtime สำหรับจัดสรรทุนแบบ Deterministic และ Research Only โดยจัดสรรเฉพาะความสามารถด้าน Portfolio Risk, Unit ขนาดคงที่ 0.01 Lot และ Margin ที่ยังเหลือให้แผนการเทรดอิสระตามลำดับความสำคัญ

Runtime รักษาเงินสำรอง Free Margin, Lineage จาก Portfolio Risk Engine, Exposure ของ Protected Runner, วงจรชีวิต Position ที่แยกอิสระ และนโยบายห้าม Traditional DCA, Averaging Down, Martingale, Grid Trading และ Recovery Trading อย่างถาวร

Execution ยังคงเป็น `LOCKED_SIMULATION_ONLY`, Direct Execution และ Live Execution ปิดอยู่ และต้องคง `NO_ORDER_SENT`
