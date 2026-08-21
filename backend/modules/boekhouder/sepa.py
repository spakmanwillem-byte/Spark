"""v13_boekhouding_sepa_001 — Lokale SEPA import/export (geen cloud).

Import: CAMT.053 XML (ISO 20022) + MT940 SWIFT tekst afschriften.
Export: pain.001.001.03 SEPA credit-transfer XML voor uitgaande betalingen.

Zuiver parsen/genereren in Python. Geen HTTP-calls, geen bank-API.
"""
from __future__ import annotations

import re
import secrets
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional


# ============================================================
# CAMT.053 import (bank-afschrift)
# ============================================================

CAMT_NS = "{urn:iso:std:iso:20022:tech:xsd:camt.053.001.02}"


def parse_camt053(xml_text: str) -> Dict:
    """Parse CAMT.053 XML naar lijst van transacties.
    Returnt {statements: [...], transactions: [...]}
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {"error": f"Ongeldige XML: {e}", "transactions": []}

    # Find all statements. CAMT gebruikt namespaced tags; strip ze robuust.
    def tag(el):
        return el.tag.split("}")[-1] if "}" in el.tag else el.tag

    transactions: List[Dict] = []
    statements: List[Dict] = []

    for stmt in root.iter():
        if tag(stmt) != "Stmt":
            continue
        stmt_info = {
            "id": _findtxt(stmt, "Id"),
            "iban": _findtxt(stmt, "Acct/Id/IBAN"),
            "currency": _findtxt(stmt, "Acct/Ccy") or "EUR",
            "n_entries": 0,
        }

        for ntry in stmt.iter():
            if tag(ntry) != "Ntry":
                continue
            amt_el = _find(ntry, "Amt")
            amount = float(amt_el.text) if amt_el is not None and amt_el.text else 0.0
            cdt_dbt = _findtxt(ntry, "CdtDbtInd") or "CRDT"
            signed = amount if cdt_dbt == "CRDT" else -amount
            booking_date = _findtxt(ntry, "BookgDt/Dt")
            value_date = _findtxt(ntry, "ValDt/Dt")
            # Counterparty
            counter_iban = _findtxt(ntry, "NtryDtls/TxDtls/RltdPties/CdtrAcct/Id/IBAN") or \
                           _findtxt(ntry, "NtryDtls/TxDtls/RltdPties/DbtrAcct/Id/IBAN")
            counter_name = _findtxt(ntry, "NtryDtls/TxDtls/RltdPties/Cdtr/Nm") or \
                           _findtxt(ntry, "NtryDtls/TxDtls/RltdPties/Dbtr/Nm")
            remittance = _findtxt(ntry, "NtryDtls/TxDtls/RmtInf/Ustrd")

            transactions.append({
                "id": "camt-" + secrets.token_hex(4),
                "ts": booking_date or value_date,
                "value_date": value_date,
                "amount_eur": signed,
                "type": "sepa_credit" if signed > 0 else "sepa_debit",
                "tegenrekening_iban": counter_iban,
                "tegenrekening_naam": counter_name,
                "naam": counter_name or remittance or "SEPA transactie",
                "note": remittance or "",
                "source": "camt053",
                "iban_account": stmt_info["iban"],
            })
            stmt_info["n_entries"] += 1
        statements.append(stmt_info)

    return {"statements": statements, "transactions": transactions}


def _find(el, path: str):
    for part in path.split("/"):
        found = None
        for child in el:
            t = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if t == part:
                found = child
                break
        if found is None:
            return None
        el = found
    return el


def _findtxt(el, path: str) -> Optional[str]:
    f = _find(el, path)
    return f.text.strip() if f is not None and f.text else None


# ============================================================
# MT940 import (SWIFT tekst)
# ============================================================

def parse_mt940(text: str) -> Dict:
    """Basale MT940 parser — pakt :61: (transaction) en :86: (remittance)."""
    transactions: List[Dict] = []
    lines = text.splitlines()
    iban = None
    curr_tx = None
    for i, line in enumerate(lines):
        if line.startswith(":25:"):
            iban = line[4:].strip().split("/")[-1] if "/" in line[4:] else line[4:].strip()
        elif line.startswith(":61:"):
            # bv :61:2606210621D50,00N195NONREF//abc
            body = line[4:]
            # datum YYMMDD
            m = re.match(r"^(\d{6})(\d{4})?([CD])[NR]?([\d,\.]+)", body)
            if m:
                yymmdd, valdt, cd, amt_s = m.group(1), m.group(2), m.group(3), m.group(4)
                amt = float(amt_s.replace(",", "."))
                sign = 1 if cd == "C" else -1
                yr = 2000 + int(yymmdd[:2])
                ts = f"{yr:04d}-{yymmdd[2:4]}-{yymmdd[4:6]}T00:00:00Z"
                curr_tx = {
                    "id": "mt940-" + secrets.token_hex(4),
                    "ts": ts,
                    "amount_eur": sign * amt,
                    "type": "sepa_credit" if sign > 0 else "sepa_debit",
                    "source": "mt940",
                    "iban_account": iban,
                    "naam": "",
                    "note": "",
                }
                transactions.append(curr_tx)
        elif line.startswith(":86:") and curr_tx is not None:
            curr_tx["note"] = line[4:].strip()
            curr_tx["naam"] = curr_tx["note"][:80]
    return {"transactions": transactions, "iban": iban}


# ============================================================
# SEPA-XML export (pain.001.001.03 — Credit Transfer)
# ============================================================

def generate_pain001(
    debtor_naam: str,
    debtor_iban: str,
    payments: List[Dict],
    message_id: Optional[str] = None,
    initiator_naam: Optional[str] = None,
) -> str:
    """Genereer een SEPA credit transfer XML batch.
    payments = [{amount_eur, creditor_naam, creditor_iban, remittance, end_to_end_id?}, ...]
    """
    msg_id = message_id or ("SPARK-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    total = sum(float(p["amount_eur"]) for p in payments)
    initiator = initiator_naam or debtor_naam

    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    tx_blocks = []
    for i, p in enumerate(payments):
        end_to_end = p.get("end_to_end_id") or f"E2E-{msg_id}-{i+1:04d}"
        tx_blocks.append(f"""      <CdtTrfTxInf>
        <PmtId><EndToEndId>{esc(end_to_end)}</EndToEndId></PmtId>
        <Amt><InstdAmt Ccy="EUR">{float(p['amount_eur']):.2f}</InstdAmt></Amt>
        <Cdtr><Nm>{esc(p['creditor_naam'])}</Nm></Cdtr>
        <CdtrAcct><Id><IBAN>{esc(p['creditor_iban'])}</IBAN></Id></CdtrAcct>
        <RmtInf><Ustrd>{esc(p.get('remittance', ''))}</Ustrd></RmtInf>
      </CdtTrfTxInf>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>{msg_id}</MsgId>
      <CreDtTm>{now}</CreDtTm>
      <NbOfTxs>{len(payments)}</NbOfTxs>
      <CtrlSum>{total:.2f}</CtrlSum>
      <InitgPty><Nm>{esc(initiator)}</Nm></InitgPty>
    </GrpHdr>
    <PmtInf>
      <PmtInfId>{msg_id}-P1</PmtInfId>
      <PmtMtd>TRF</PmtMtd>
      <NbOfTxs>{len(payments)}</NbOfTxs>
      <CtrlSum>{total:.2f}</CtrlSum>
      <ReqdExctnDt>{datetime.now(timezone.utc).strftime('%Y-%m-%d')}</ReqdExctnDt>
      <Dbtr><Nm>{esc(debtor_naam)}</Nm></Dbtr>
      <DbtrAcct><Id><IBAN>{esc(debtor_iban)}</IBAN></Id></DbtrAcct>
      <DbtrAgt><FinInstnId><Othr><Id>NOTPROVIDED</Id></Othr></FinInstnId></DbtrAgt>
{chr(10).join(tx_blocks)}
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>
"""
