# AFIP V1 Final Revision 2 — Replay Performance Certification

แก้ quadratic append path ใน AppendOnlyResearchDataset โดย cache record sequence และ chain checksum ต่อ dataset

สิ่งที่ไม่เปลี่ยน:
- Append-only historical/research data
- Chain checksum
- Chronological replay
- No look-ahead
- Resume
- Research-only authority
- Live execution authority

ติดตั้งโดยแตก ZIP ทับ C:\AFIP\source แล้วรัน RUN_AFIP_V1_FINAL_REVISION_2_REPLAY_PERFORMANCE.ps1
