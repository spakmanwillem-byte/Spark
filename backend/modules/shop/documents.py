"""v14_shop_documenten_001 (Willem 20-10-2026) — factuur, pakbon en leveranciersmail (concept) per bestelling.

Bouwt op wat er is:
  • boekhouder.shop_hooks.record_shop_sale → netto/BTW/bruto, bonnen-JSON, Spark-fee (eigen boekhoudsysteem; later Moneybird)
  • user_archive → PDF's in het Archief van koper (factuur) en winkeleigenaar (factuur-kopie + pakbon)
Flow Willem: bestelling → hij bestelt bij Promotex (mail-concept, haalt zelf af, krijgt hun factuur per mail)
            → verpakt (pakbon = bestelbon) → verzendt of laat afhalen.
Mail wordt NIET verstuurd (concept-modus) tot er een mailverbinding in Connections staat.
PDF lokaal via fpdf2 — geen externe dienst.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fpdf import FPDF

from modules.core.storage import load_json, save_json

DATA = Path(__file__).parent.parent.parent / "data"


def _eur(x) -> str:
    return f"EUR {float(x or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _profile(user_id: str) -> Dict:
    return load_json(DATA / "users" / user_id / "profile.json", default={})


def afzender(owner_id: str, shop: Dict) -> Dict:
    """Factuur-afzender uit Mijn Profiel → Zakelijk (valt terug op privé-velden)."""
    p = _profile(owner_id)
    return {
        "naam": p.get("bedrijfsnaam") or shop.get("naam") or "",
        "adres": p.get("zakelijk_adres") or p.get("adres") or "",
        "postcode": p.get("zakelijk_postcode") or p.get("postcode") or "",
        "plaats": p.get("zakelijk_plaats") or p.get("plaats") or "",
        "email": p.get("zakelijke_email") or p.get("email") or "",
        "telefoon": p.get("zakelijk_telefoon") or p.get("telefoon") or "",
        "kvk": p.get("kvk") or "", "btw": p.get("btw_nummer") or "",
        "iban": p.get("zakelijk_iban") or p.get("iban") or "",
        "groet": p.get("display_name") or p.get("naam") or "Willem Spakman",
    }


def _pdf(title: str, afz: Dict) -> FPDF:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, afz["naam"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for line in [f"{afz['adres']}, {afz['postcode']} {afz['plaats']}".strip(", "),
                 f"{afz['email']}  |  {afz['telefoon']}".strip(" |"),
                 f"KvK {afz['kvk']}  |  BTW {afz['btw']}  |  IBAN {afz['iban']}"]:
        pdf.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    return pdf


def _footer(pdf: FPDF, afz: Dict, extra: str = ""):
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    if extra:
        pdf.multi_cell(0, 5, extra)
        pdf.ln(2)
    pdf.cell(0, 5, "Met vriendelijke groet,", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, afz["groet"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 4, "Gegenereerd door Spark AI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)


def _regel(i: Dict) -> str:
    var = " · ".join(x for x in (i.get("kleur"), i.get("maat")) if x)
    return f"{i['name']}{' (' + var + ')' if var else ''}"


def factuur_pdf(order: Dict, nummer: str, afz: Dict, koper: Dict) -> bytes:
    pdf = _pdf(f"Factuur {nummer}", afz)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 5, f"Factuurdatum: {order['created_at'][:10]}")
    pdf.cell(0, 5, f"Bestelnummer: {order['id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Aan: {koper.get('naam') or order.get('shipping_name') or order.get('user_id')}", new_x="LMARGIN", new_y="NEXT")
    if order.get("shipping_address"):
        pdf.cell(0, 5, order["shipping_address"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    for w, t in ((90, "Omschrijving"), (20, "Aantal"), (35, "Prijs excl."), (35, "Totaal excl.")):
        pdf.cell(w, 7, t, border="B")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i in order["items"]:
        pdf.cell(90, 6, _regel(i)[:60])
        pdf.cell(20, 6, str(i["quantity"]), align="R")
        pdf.cell(35, 6, _eur(i["price"]), align="R")
        pdf.cell(35, 6, _eur(i["line_total"]), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    rows = [("Subtotaal excl. BTW", order.get("subtotaal_excl", order["total"])),
            (f"BTW {order.get('btw_pct', 21):g}%", order.get("btw", 0))]
    if order.get("verzendkosten"):
        rows.append(("Verzendkosten", order["verzendkosten"]))
    for lbl, val in rows:
        pdf.cell(145, 6, lbl, align="R"); pdf.cell(35, 6, _eur(val), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(145, 7, "Totaal", align="R"); pdf.cell(35, 7, _eur(order["total"]), align="R", new_x="LMARGIN", new_y="NEXT")
    _footer(pdf, afz, "Betaald via Spark-wallet. Bedankt voor je bestelling!"
            + (" Je bestelling ligt klaar om af te halen." if order.get("bezorging") == "afhalen" else " Je bestelling wordt verzonden."))
    return bytes(pdf.output())


def pakbon_pdf(order: Dict, afz: Dict, koper: Dict, verpakking: Optional[Dict]) -> bytes:
    pdf = _pdf(f"Pakbon bestelling {order['id']}", afz)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, f"Datum: {order['created_at'][:10]}   Bezorging: {order.get('bezorging', 'verzenden')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, f"Voor: {koper.get('naam') or order.get('shipping_name') or order.get('user_id')}", new_x="LMARGIN", new_y="NEXT")
    if order.get("shipping_address"):
        pdf.cell(0, 5, order["shipping_address"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 9)
    for w, t in ((20, "Aantal"), (110, "Artikel"), (50, "Ingepakt")):
        pdf.cell(w, 7, t, border="B")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i in order["items"]:
        pdf.cell(20, 7, str(i["quantity"]), align="R"); pdf.cell(110, 7, _regel(i)[:70]); pdf.cell(50, 7, "[   ]", new_x="LMARGIN", new_y="NEXT")
    if verpakking:
        pdf.ln(2); pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, f"Verpakking: {verpakking.get('naam')}", new_x="LMARGIN", new_y="NEXT")
    if order.get("notes"):
        pdf.ln(2); pdf.set_font("Helvetica", "", 9); pdf.multi_cell(0, 5, f"Opmerking koper: {order['notes']}")
    _footer(pdf, afz, "Geen prijzen op deze bon. Controleer de artikelen en vink af.")
    return bytes(pdf.output())


def leveranciersmail(order: Dict, products: List[Dict], inkoop: List[Dict], afz: Dict) -> List[Dict]:
    """Per leverancier één concept-mail: inkoop-regels uit de stuklijsten × bestelde aantallen, met kleur/maat."""
    idx = {a["id"]: a for a in inkoop}
    per_lev: Dict[str, Dict] = {}
    for i in order["items"]:
        prod = next((p for p in products if p["id"] == i["product_id"]), None)
        if not prod:
            continue
        for r in prod.get("stuklijst") or []:
            a = idx.get(r.get("inkoop_id"))
            if not a:
                continue
            lev = a.get("leverancier_naam") or "Eigen voorraad"
            key = (a["id"], i.get("kleur"), i.get("maat"))
            d = per_lev.setdefault(lev, {"leverancier": lev, "contact_id": a.get("leverancier_contact_id"), "regels": defaultdict(int), "namen": {}})
            d["regels"][key] += int(r.get("aantal") or 1) * int(i["quantity"])
            d["namen"][key] = a["naam"]
    mails = []
    for lev, d in per_lev.items():
        if lev == "Eigen voorraad":
            continue
        lines = [f"Beste {lev},", "", f"Graag bestel ik het volgende (ref. Spark-bestelling {order['id']}):", ""]
        for (aid, kleur, maat), aantal in sorted(d["regels"].items(), key=lambda x: (idx[x[0][0]].get("code") or "", x[0][0])):
            a = idx[aid]
            var = ", ".join(x for x in (kleur, maat) if x)
            lines.append(f"  {aantal}x  {a.get('code') or '-'}  {a['naam']}{'  —  ' + var if var else ''}")
        lines += ["", "Ik haal de bestelling zelf bij jullie op; de factuur graag per e-mail naar " + (afz["email"] or "mijn zakelijke e-mail") + ".",
                  "", "Met vriendelijke groet,", afz["groet"], afz["naam"], afz["telefoon"], "", "— Concept, gegenereerd door Spark AI. Nog niet verstuurd."]
        mails.append({"leverancier": lev, "contact_id": d["contact_id"], "onderwerp": f"Bestelling {afz['naam']} — ref. {order['id']}",
                      "tekst": "\n".join(lines), "status": "concept"})
    return mails


def archiveer(user_id: str, filename: str, content: bytes, description: str, tags: List[str]) -> Dict:
    """Schrijf een PDF in het Archief van een user (zelfde index als user_archive.upload_file)."""
    from modules.user_archive import routes as ua
    from modules.local_storage import persist_upload_bytes
    user_dir = ua._user_dir(user_id)
    category = ua._detect_category(filename)
    file_id = uuid.uuid4().hex[:12]
    dest = persist_upload_bytes(user_dir / category / f"{file_id}.pdf", content)
    entry = {"id": file_id, "filename": f"{file_id}.pdf", "original_name": filename, "category": category,
             "extension": ".pdf", "mime_type": "application/pdf", "size_bytes": len(content),
             "description": description, "tags": tags, "uploaded_at": datetime.now(timezone.utc).isoformat(),
             "uploaded_by": "spark", "path": str(dest)}
    files = ua._load_index(user_id)
    files.append(entry)
    ua._save_index(user_id, files)
    return {"file_id": file_id, "url": f"/api/archive/{user_id}/file/{file_id}", "naam": filename}


def volgend_factuurnummer(shop_path: Path, prefix: str) -> str:
    d = load_json(shop_path, default={})
    st = d.setdefault("settings", {})
    jaar = datetime.now(timezone.utc).year
    if st.get("factuur_jaar") != jaar:
        st["factuur_jaar"], st["factuur_teller"] = jaar, 0
    st["factuur_teller"] = int(st.get("factuur_teller", 0)) + 1
    save_json(shop_path, d)
    return f"{prefix}-{jaar}-{st['factuur_teller']:04d}"
