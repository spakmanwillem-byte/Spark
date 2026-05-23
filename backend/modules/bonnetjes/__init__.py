"""
v6_bonnetje_001 — Bonnetje-generator voor klant-token-aankopen.

Bij elke buy_roar door een klant (niet-anker) maakt deze module:
- Een markdown/JSON bonnetje met alle tarieven (totaal, netto, BTW, coin-fee, etc.)
- Opslag in /app/backend/data/users/{user_id}/archief/bonnetjes/{tx_id}.md
- Index in user's archief register

Endpoints:
  GET /api/bonnetjes/user/{user_id}         — lijst bonnetjes
  GET /api/bonnetjes/{tx_id}                — full content (markdown)
  GET /api/bonnetjes/{tx_id}/download       — download als .md
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from pathlib import Path
from datetime import datetime, timezone
import json

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/bonnetjes", tags=["bonnetjes"])

DATA = Path(__file__).parent.parent.parent / "data"
USERS_DIR = DATA / "users"


def _bonnetje_dir(user_id: str) -> Path:
    return USERS_DIR / user_id / "archief" / "bonnetjes"


def _index_file(user_id: str) -> Path:
    return USERS_DIR / user_id / "archief" / "bonnetjes_index.json"


def maak_bonnetje(tx: dict, user_naam: str = "Klant") -> dict:
    """Genereer + opslaan bonnetje voor klant-aankoop.

    tx velden: id, ts, user_id, token_amount, amount_eur, price_per_token,
               btw_afgeroomd_eur, netto_eur (optioneel — anders berekend)
    """
    user_id = tx.get("user_id")
    if not user_id:
        return {"error": "no user_id"}
    bdir = _bonnetje_dir(user_id)
    bdir.mkdir(parents=True, exist_ok=True)

    btw = tx.get("btw_afgeroomd_eur", 0)
    incl = tx.get("amount_eur", 0)
    netto = tx.get("netto_eur", round(incl - btw, 4))
    n = tx.get("token_amount", 1)
    price = tx.get("price_per_token", incl / max(1, n))
    ts = tx.get("timestamp") or tx.get("ts") or datetime.now(timezone.utc).isoformat()
    tx_id = tx.get("id", "no-id")

    md = f"""# 🧾 Bonnetje #{tx_id[:8]}

**Datum**: {ts[:19].replace('T', ' ')} UTC
**Klant**: {user_naam} (`{user_id}`)
**Verkoper**: Roadkill / Spark Core 2.0
**Product**: ROAR Token (digitale concept-token, geen officiële cryptomunt)

---

## Aankoop

| Item | Aantal | Prijs/stuk | Bedrag |
|---|---|---|---|
| ROAR Token | {n} | €{price:.4f} | €{incl:.2f} |

## Tarief-opbouw (incl-BTW model)

| Onderdeel | % | Bedrag |
|---|---|---|
| Netto verkoop (Spark omzet) | — | €{netto:.4f} |
| 21% BTW (uit incl-prijs, 21/121) | 21% | €{btw:.4f} |
| **Totaal betaald** | — | **€{incl:.2f}** |

> _BTW-grondslag: €{incl:.2f} × 21/121 = €{btw:.4f}. BTW is gereserveerd in Spark's kasboek
> en wordt later afgedragen aan de Belastingdienst. Spark heeft geen bankrekening, alle
> mutaties zijn alleen administratief (papertrail-model)._

## Voorwaarden

- ROAR is een **intern concept-token**, geen officieel betaalmiddel of cryptomunt.
- Token-prijs kan stijgen of dalen op basis van circulating supply.
- Spark Core behoudt altijd ≥ 51% governance (510.000 tokens in treasury).
- Aankoop is **symbolische ondersteuning** van het Spark Core concept.
- Token kan later worden gegift, gebruikt voor merch, of geconverteerd bij eventuele
  toekomstige coin-uitrol (1:1 papertrail-conversie).

---

_Bonnetje gegenereerd door Spark Core 2.0 — `v6_bonnetje_001`_
_Transaction ID: `{tx_id}`_
"""
    out_path = bdir / f"{tx_id}.md"
    out_path.write_text(md, encoding="utf-8")

    # Update index
    idx_path = _index_file(user_id)
    idx = load_json(idx_path, default={"bonnetjes": []})
    idx["bonnetjes"].insert(0, {
        "tx_id": tx_id,
        "ts": ts,
        "bedrag_eur": incl,
        "btw_eur": btw,
        "netto_eur": netto,
        "n_tokens": n,
        "file": f"{tx_id}.md",
    })
    save_json(idx_path, idx)
    return {"success": True, "path": str(out_path), "tx_id": tx_id}


@router.get("/user/{user_id}")
async def list_bonnetjes(user_id: str):
    idx = load_json(_index_file(user_id), default={"bonnetjes": []})
    return idx


@router.get("/{tx_id}/{filename}")
async def get_bonnetje_md(tx_id: str, filename: str):
    """Fetch bonnetje content by searching across all users (admin-only access pattern)."""
    for user_dir in USERS_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        p = user_dir / "archief" / "bonnetjes" / f"{tx_id}.md"
        if p.exists():
            return PlainTextResponse(p.read_text(encoding="utf-8"))
    raise HTTPException(404, "Bonnetje niet gevonden")


@router.get("/{tx_id}")
async def get_bonnetje(tx_id: str):
    for user_dir in USERS_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        p = user_dir / "archief" / "bonnetjes" / f"{tx_id}.md"
        if p.exists():
            return PlainTextResponse(p.read_text(encoding="utf-8"))
    raise HTTPException(404, "Bonnetje niet gevonden")


@router.get("/{tx_id}/download/file")
async def download_bonnetje(tx_id: str):
    for user_dir in USERS_DIR.iterdir():
        if not user_dir.is_dir():
            continue
        p = user_dir / "archief" / "bonnetjes" / f"{tx_id}.md"
        if p.exists():
            return FileResponse(str(p), media_type="text/markdown", filename=f"bonnetje-{tx_id[:8]}.md")
    raise HTTPException(404, "Bonnetje niet gevonden")
