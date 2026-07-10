"""Deterministic, read-only AFIP Bank ledger runtime."""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from typing import Any
from .models import AFIPBankReport, BankTransaction

VERSION1_BROKER="XM"; VERSION1_SYMBOL="GOLD#"

def _text(v: Any, d: str="") -> str:
    s=str(v if v is not None else d).strip(); return s or d

def _upper(v: Any, d: str="") -> str: return _text(v,d).upper()
def _float(v: Any, d: float=0.0) -> float:
    try: return float(v)
    except (TypeError,ValueError): return float(d)
def _items(v: Any) -> tuple[Mapping[str,Any],...]:
    if isinstance(v,Mapping): return (v,)
    if isinstance(v,Iterable) and not isinstance(v,(str,bytes)): return tuple(x for x in v if isinstance(x,Mapping))
    return ()

class AFIPBankLiveRuntime:
    """Summarize deposits, withdrawals and paper profit without moving funds."""
    def evaluate_one(self, record: Mapping[str,Any]) -> AFIPBankReport:
        broker=_upper(record.get("broker",VERSION1_BROKER),VERSION1_BROKER)
        symbol=_upper(record.get("symbol",VERSION1_SYMBOL),VERSION1_SYMBOL)
        mode=_upper(record.get("mode",record.get("execution_mode","PAPER")),"PAPER")
        currency=_upper(record.get("base_currency",record.get("currency","USD")),"USD")
        initial=max(0.0,_float(record.get("initial_capital",record.get("paper_balance",1000.0)),1000.0))
        reserve=max(0.0,_float(record.get("reserve",0.0),0.0))
        closed=_float(record.get("closed_profit",0.0),0.0); floating=_float(record.get("floating_profit",0.0),0.0)
        txs=[]; deposits=0.0; withdrawals=0.0
        for i,item in enumerate(_items(record.get("bank_transactions",record.get("capital_transactions",()))),1):
            kind=_upper(item.get("transaction_type",item.get("type","DEPOSIT")),"DEPOSIT")
            amount=max(0.0,_float(item.get("amount",0.0),0.0))
            if kind=="DEPOSIT": deposits+=amount
            elif kind=="WITHDRAWAL": withdrawals+=amount
            else: kind="ADJUSTMENT"
            txs.append(BankTransaction(_text(item.get("transaction_id",f"BANK-{i:04d}"),f"BANK-{i:04d}"),kind,round(amount,2),currency,_text(item.get("occurred_at","not_provided"),"not_provided"),_text(item.get("reference","manual_capital_record"),"manual_capital_record"),_text(item.get("note_en","Capital ledger record."),"Capital ledger record."),_text(item.get("note_th","รายการบันทึกเงินทุน"),"รายการบันทึกเงินทุน")))
        deposits += max(0.0,_float(record.get("deposits",0.0),0.0)); withdrawals += max(0.0,_float(record.get("withdrawals",0.0),0.0))
        balance=initial+deposits-withdrawals+closed; equity=balance+floating; allocation=max(0.0,equity-reserve)
        net_contribution=initial+deposits-withdrawals
        roi=((equity-net_contribution)/net_contribution*100.0) if net_contribution>0 else 0.0
        validation=[]
        if broker!=VERSION1_BROKER: validation.append("version1_xm_only_required")
        if symbol!=VERSION1_SYMBOL: validation.append("version1_gold_only_required")
        if mode=="LIVE" or bool(record.get("live_execution_enabled",False)): validation.append("live_execution_blocked_for_afip_bank")
        if withdrawals>initial+deposits+max(0.0,closed): validation.append("withdrawal_exceeds_recorded_capital")
        if validation: status="BLOCKED"; reason="afip_bank_blocked_by_policy_or_ledger_validation"
        else: status="READY"; reason="afip_bank_live_read_only_ledger_ready"
        return AFIPBankReport(status,reason,broker,symbol,mode,currency,round(initial,2),round(deposits,2),round(withdrawals,2),round(closed,2),round(floating,2),round(balance,2),round(equity,2),round(reserve,2),round(allocation,2),round(roi,2),len(txs),tuple(txs),"Read-only capital ledger showing deposits, withdrawals, trading profit, reserve, balance, equity and available allocation.","บัญชีเงินทุนแบบอ่านอย่างเดียว แสดงเงินฝาก เงินถอน กำไรจากการเทรด เงินสำรอง ยอดคงเหลือ Equity และเงินที่จัดสรรได้",tuple(validation))
    def explain_one(self, record: Mapping[str,Any]) -> AFIPBankReport: return self.evaluate_one(record)
