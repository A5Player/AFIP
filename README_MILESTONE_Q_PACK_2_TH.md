# AFIP Milestone Q Pack 2 — การทำ Market Intent State ให้เป็นมาตรฐาน

## วัตถุประสงค์

แพตช์นี้ทำ Market Intent Observation ที่ผ่านเกณฑ์จาก Milestone Q Pack 1 ให้เป็น schema กลางสำหรับงานวิจัยแบบ deterministic และ immutable

## ผลลัพธ์ที่ทำให้เป็นมาตรฐาน

- Intent State และ Direction แบบมาตรฐาน
- แรงกดดันหลัก
- ระดับความเข้มของ Intent
- สมดุลระหว่าง Continuation และ Reversal
- ความสอดคล้องของ Direction
- Source lineage และลำดับเวลา

## การควบคุมความปลอดภัย

ระบบต้องตรวจ Pack 1 lineage, คุณภาพข้อมูล, future-safe chronology, Market Regime before Intent, Market Behaviour before Intent, ป้ายกำกับและช่วงค่าที่ถูกต้อง รวมถึง XM Only, GOLD# Only และ frozen execution policy

แพตช์นี้ไม่มีสิทธิ์ปรับ parameter เปลี่ยน trading logic เลื่อนข้อมูลเป็น production knowledge แก้ไข position ติดต่อ broker หรือส่งคำสั่งซื้อขาย

## การติดตั้ง

แตกไฟล์แพตช์ทับที่ root ของ AFIP repository ห้ามแทนที่ repository ทั้งชุดและห้ามลบไฟล์อื่น

## การตรวจสอบ

รัน `RUN_MILESTONE_Q_PACK_2.ps1` หรือ `RUN_MILESTONE_Q_PACK_2.bat`
