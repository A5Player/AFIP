# AFIP Phase U Packs 3.4.2–3.4.7

ชุดรวมนี้ติดตั้ง Pack งานวิจัยครบ 6 Pack:

- 3.4.2 Walk-Forward Research
- 3.4.3 Multi-Dimensional Ranking
- 3.4.4 Research Evidence Consumer
- 3.4.5 Research Dashboard
- 3.4.6 Production Research Certification
- 3.4.7 Blind Historical Replay

## หลักสำคัญ

- ไม่แก้ Trading Logic เดิม
- ไม่ปลดล็อกเงินจริง
- ไม่เปลี่ยน P1–P4
- Research ไม่สามารถส่งออเดอร์
- Drawdown เป็น Hard Limit ที่ Win Rate หรือกำไรไม่สามารถชดเชยได้
- ต้องใช้ข้อมูลที่ผ่าน Historical Dataset Certification
- ผลงานวิจัยจริงจะถูกเก็บใน Runtime และไม่ควร Commit เข้า Git

## ติดตั้ง

แตก ZIP ไว้ที่ตำแหน่งใดก็ได้ แล้วรัน:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\INSTALL_ALL_PHASE_U_PACK_3_4_2_TO_3_4_7.ps1
cd C:\AFIP
.\VALIDATE_ALL_PHASE_U_PACK_3_4_2_TO_3_4_7.ps1
```

หลังผลทั้งหมดผ่าน จึง Commit และ Push Git
