# AFIP V1 — MT5 Research Collection Repair

แพตช์นี้แก้ Source จริงใน `afip/automatic_research_runtime/runtime.py`

## ปัญหาที่แก้

เดิมระบบตรวจเพียงจำนวน OHLC รวม:

```python
len(bars) < 100
```

เมื่อมี M1 จำนวน 722 bars ระบบจึงถือว่าข้อมูลเพียงพอ และข้าม MT5 Collection แม้ M5, M15, M30, H1, H4 และ D1 ไม่มีข้อมูล

## พฤติกรรมหลังแก้

- ตรวจความครบถ้วนและ Freshness แยกแต่ละ Timeframe
- M1 ที่มีข้อมูลจะไม่ทำให้ระบบข้าม Timeframe อื่นที่หายไป
- พยายามดึง MT5 เมื่อข้อมูลรวมต่ำกว่าเกณฑ์ หรือ Timeframe ใดไม่มี/เก่า
- ดึงสูงสุดอย่างน้อย 5,000 closed bars ต่อ Timeframe
- บันทึกเหตุผลในสถานะ:
  - `mt5_collection_reasons`
  - `mt5_timeframes_requested`
- คง Research เป็น Data Only และไม่มี Execution Authority

## ติดตั้ง

หยุด AFIP ก่อน:

```powershell
cd C:\AFIP
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\STOP_AFIP.ps1
```

แตก ZIP แพตช์ แล้วรันจากโฟลเดอร์แพตช์:

```powershell
.\INSTALL_AFIP_V1_MT5_RESEARCH_COLLECTION_REPAIR.ps1 -ProjectRoot C:\AFIP
.\RUN_AFIP_V1_MT5_RESEARCH_COLLECTION_REPAIR.ps1 -ProjectRoot C:\AFIP
```

เริ่ม AFIP ใหม่:

```powershell
cd C:\AFIP
.\START_AFIP.ps1
Start-Sleep -Seconds 90
```

ตรวจสถานะ:

```powershell
Get-Content .\runtime\research\automatic_research_status.json |
ConvertFrom-Json |
Select-Object status,reason,mt5_collection_attempted,mt5_bars_collected,usable_bars,mt5_collection_reasons,mt5_timeframes_requested
```

ค่าที่ควรเห็นในรอบแรกหลังติดตั้ง:

```text
mt5_collection_attempted : True
mt5_bars_collected       : มากกว่า 0
```

หาก `attempted=True` แต่ `collected=0` หมายถึง Source เรียก MT5 แล้ว แต่ MT5 Python session/symbol/history ยังไม่ส่งข้อมูลกลับ ต้องตรวจ terminal binding ต่อ ไม่ใช่ปัญหาเงื่อนไข `dataset_already_current` เดิม
