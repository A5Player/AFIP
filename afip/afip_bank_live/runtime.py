"""Deterministic, read-only AFIP Bank ledger runtime."""
from __future__ import annotations
from collections.abc import Iterable, Mapping
from typing import Any
from .models import AFIPBankReport, BankTransaction

VERSION1_BROKER="XM"; VERSION1_SYMBOL="GOLD#"

def _text(v: Any, d: str="") -> str:
    s=str(v if v is not None else d).strip(); return s or d

def _upper(v: Any, d: str="") -> str: return _text(v,d).upper()
def _float(v: Any, d: float | None=None) -> float | None:
    try: return float(v)
    except (TypeError,ValueError): return d
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
        initial_raw=_float(record.get("initial_capital",record.get("paper_balance")),None)
        reserve_raw=_float(record.get("reserve"),None)
        closed_raw=_float(record.get("closed_profit"),None); floating_raw=_float(record.get("floating_profit"),None)
        financial_source=_text(record.get("financial_data_source",record.get("account_data_source","")),"")
        connection=_upper(record.get("financial_connection_status",record.get("connection_status","UNKNOWN")),"UNKNOWN")
        explicit_record=any(key in record for key in ("initial_capital","paper_balance","balance","equity"))
        verified=(bool(financial_source) and connection in {"CONNECTED","VERIFIED","AVAILABLE"}) or explicit_record
        if explicit_record and not financial_source: financial_source="CALLER_SUPPLIED_RECORD"
        initial=max(0.0,initial_raw) if verified and initial_raw is not None else 0.0
        reserve=max(0.0,reserve_raw) if verified and reserve_raw is not None else 0.0
        closed=closed_raw if verified and closed_raw is not None else 0.0
        floating=floating_raw if verified and floating_raw is not None else 0.0
        txs=[]; deposits=0.0; withdrawals=0.0
        for i,item in enumerate(_items(record.get("bank_transactions",record.get("capital_transactions",()))),1):
            kind=_upper(item.get("transaction_type",item.get("type","DEPOSIT")),"DEPOSIT")
            amount=max(0.0,_float(item.get("amount",0.0),0.0))
            if kind=="DEPOSIT": deposits+=amount
            elif kind=="WITHDRAWAL": withdrawals+=amount
            else: kind="ADJUSTMENT"
            txs.append(BankTransaction(_text(item.get("transaction_id",f"BANK-{i:04d}"),f"BANK-{i:04d}"),kind,round(amount,2),currency,_text(item.get("occurred_at","not_provided"),"not_provided"),_text(item.get("reference","manual_capital_record"),"manual_capital_record"),_text(item.get("note_en","Capital ledger record."),"Capital ledger record."),_text(item.get("note_th","รายการบันทึกเงินทุน"),"รายการบันทึกเงินทุน")))
        deposits_value=_float(record.get("deposits"),None); withdrawals_value=_float(record.get("withdrawals"),None)
        if verified and deposits_value is not None: deposits += max(0.0,deposits_value)
        if verified and withdrawals_value is not None: withdrawals += max(0.0,withdrawals_value)
        balance=initial+deposits-withdrawals+closed; equity=balance+floating; allocation=max(0.0,equity-reserve)
        net_contribution=initial+deposits-withdrawals
        roi=((equity-net_contribution)/net_contribution*100.0) if net_contribution>0 else 0.0
        validation=[]
        if broker!=VERSION1_BROKER: validation.append("version1_xm_only_required")
        if symbol!=VERSION1_SYMBOL: validation.append("version1_gold_only_required")
        if mode=="LIVE" or bool(record.get("live_execution_enabled",False)): validation.append("live_execution_blocked_for_afip_bank")
        if withdrawals>initial+deposits+max(0.0,closed): validation.append("withdrawal_exceeds_recorded_capital")
        if not verified: validation.append("financial_source_not_verified")
        if validation: status="BLOCKED"; reason="financial_data_unavailable" if "financial_source_not_verified" in validation else "afip_bank_blocked_by_policy_or_ledger_validation"
        else: status="READY"; reason="afip_bank_live_read_only_ledger_ready"
        return AFIPBankReport(status,reason,broker,symbol,mode,currency,round(initial,2),round(deposits,2),round(withdrawals,2),round(closed,2),round(floating,2),round(balance,2),round(equity,2),round(reserve,2),round(allocation,2),round(roi,2),len(txs),tuple(txs),"Read-only capital ledger showing deposits, withdrawals, trading profit, reserve, balance, equity and available allocation.","บัญชีเงินทุนแบบอ่านอย่างเดียว แสดงเงินฝาก เงินถอน กำไรจากการเทรด เงินสำรอง ยอดคงเหลือ Equity และเงินที่จัดสรรได้",tuple(validation))
    def explain_one(self, record: Mapping[str,Any]) -> AFIPBankReport: return self.evaluate_one(record)
