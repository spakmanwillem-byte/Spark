"""
Glow-Nav service (v6_glow_nav_001) — Spark wijst via chat de juiste UI-tab aan
================================================================================
Werking:
  1. /tabs/registry → master mapping van app-routes/tabs naar NLP-aliases
  2. /tabs/navigate?q=... → match query → returnt {route, glow_target, label}
  3. Chat-hook: bij intent_tags 'navigate' + tab/winkel/pagina → response.navigate_to + response.glow_target

Frontend luistert op deze velden en triggert scroll-into-view + pulse-animatie.
"""
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/tabs", tags=["glow-nav"])

TABS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "tabs_registry.json"


def _default_tabs() -> dict:
    return {
        "_arch_ref": "v6_glow_nav_001 — UI tab → route + aliases voor NLP-navigatie. IDs matchen MainLayout.navigationConfig zodat glow_target = `nav-{id}` overeenkomt met data-testid in sidebar. v13c_glow_admin_gate_001 (sessie 54): adminOnly-flag toegevoegd om admin-routes voor gewone users te weren.",
        "version": "v6",
        "tabs": [
            # WORKSPACE
            {"id": "dashboard", "label": "Dashboard", "route": "/", "aliases": ["dashboard", "home", "start", "overzicht"], "icon": "Home"},
            {"id": "chat", "label": "Gesprekken", "route": "/chat", "aliases": ["chat", "gesprekken", "praten", "spark chat", "gesprek"], "icon": "MessageSquare"},
            {"id": "archief", "label": "Archief", "route": "/archief", "aliases": ["archief", "media", "foto's", "geluiden", "filmpjes", "winkel foto", "product foto", "product afbeelding", "privé foto"], "icon": "Archive"},
            {"id": "calendar", "label": "Agenda", "route": "/calendar", "aliases": ["agenda", "kalender", "planning", "afspraak", "afspraken"], "icon": "Calendar"},
            {"id": "dagboek", "label": "Dagboek", "route": "/dagboek", "aliases": ["dagboek", "reflectie", "mood", "stemming"], "icon": "BookHeart"},
            {"id": "notities", "label": "Notities & Taken", "route": "/notities", "aliases": ["notities", "noteer", "memo", "todo", "taken", "taak", "notitie"], "icon": "StickyNote"},
            # Roadmap admin-only (v13c_roadmap_admin_only_001) — te veel jargon voor oudere users tot core af is
            {"id": "roadmap", "label": "Roadmap", "route": "/roadmap", "aliases": ["roadmap", "planning roadmap"], "icon": "Map", "adminOnly": True},
            # SPARK AI (allemaal admin-only)
            {"id": "spark-brain", "label": "Spark Brain", "route": "/spark/brain", "aliases": ["spark brain", "brein", "identiteit", "normen", "waarden", "bijbel", "emotie pipeline"], "icon": "Brain", "adminOnly": True},
            {"id": "knowledge-v2", "label": "Kennisbank", "route": "/knowledge", "aliases": ["kennis", "kb", "kennisbank", "begrip", "weten", "kaarten"], "icon": "BookOpen", "adminOnly": True},
            {"id": "triggers", "label": "Triggers", "route": "/spark/triggers", "aliases": ["triggers", "trigger lijst"], "icon": "Zap", "adminOnly": True},
            {"id": "emotions", "label": "Emoties", "route": "/spark/emotions", "aliases": ["emoties", "emotie"], "icon": "Sparkles", "adminOnly": True},
            {"id": "connections", "label": "Verbanden", "route": "/spark/connections", "aliases": ["verbanden", "graph", "connecties", "relaties"], "icon": "Link", "adminOnly": True},
            # MODULES
            {"id": "trade", "label": "Trade", "route": "/modules/trade", "aliases": ["trade", "trader", "crypto", "buy", "sell", "kopen", "verkopen", "bitvavo"], "icon": "TrendingUp"},
            {"id": "wallet", "label": "Wallet", "route": "/modules/wallet", "aliases": ["wallet", "geld", "saldo", "tikkie", "portemonnee", "balans"], "icon": "Wallet"},
            {"id": "winkel", "label": "Winkel", "route": "/modules/winkel", "aliases": ["winkel", "winkelstraat", "shop", "roadkillshop", "merch"], "icon": "ShoppingBag"},
            {"id": "boekhouding", "label": "Boekhouding", "route": "/modules/boekhouding", "aliases": ["boekhouding", "kasboek", "boeken", "accounting"], "icon": "BookMarked"},
            {"id": "achievements", "label": "Achievements", "route": "/modules/achievements", "aliases": ["achievement", "achievements", "milestone", "punten", "xp"], "icon": "Trophy", "adminOnly": True},
            {"id": "leaderboard", "label": "Leaderboard", "route": "/modules/leaderboard", "aliases": ["leaderboard", "ranglijst", "podium", "top"], "icon": "Award", "adminOnly": True},
            {"id": "integrations", "label": "Integraties", "route": "/modules/integrations", "aliases": ["integraties", "integrations", "koppelingen", "api keys"], "icon": "Puzzle", "adminOnly": True},
            # BEHEER
            # v13c_shop_tab_moved_to_profile_001 — shop-onderhoud zit nu in Mijn Profiel als sub-tab
            {"id": "profiel", "label": "Mijn Profiel", "route": "/profiel", "aliases": ["profiel", "mijn profiel", "instellingen profiel", "avatar instellen", "mijn winkel", "winkel beheren", "shop beheren"], "icon": "User"},
            {"id": "users", "label": "Gebruikers", "route": "/admin/users", "aliases": ["gebruikers", "users beheer", "leden"], "icon": "Users", "adminOnly": True},
            {"id": "analytics", "label": "Analytics", "route": "/admin/analytics", "aliases": ["analytics", "statistieken", "stats"], "icon": "BarChart", "adminOnly": True},
            {"id": "settings", "label": "Instellingen", "route": "/admin/settings", "aliases": ["beheer instellingen", "systeem archief", "beheer archief", "spark archief", "admin archief", "system archive", "system archief", "instellingen", "settings"], "icon": "Settings", "adminOnly": True},
        ],
    }


def _load_tabs() -> dict:
    """v13c_glow_admin_gate_001 — force-refresh naar v3 als disk-versie ouder is,
    zodat adminOnly-flags aankomen zonder handmatig JSON te bewerken."""
    defaults = _default_tabs()
    if not TABS_FILE.exists():
        TABS_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_json(TABS_FILE, defaults)
        return defaults
    d = load_json(TABS_FILE, default=defaults)
    if d.get("version") != defaults.get("version"):
        save_json(TABS_FILE, defaults)
        return defaults
    return d


@router.get("/registry")
async def get_registry(is_admin: bool = False):
    """v13c_glow_admin_gate_001 — filter admin-tabs voor niet-admins."""
    d = _load_tabs()
    if is_admin:
        return d
    filtered = {**d, "tabs": [t for t in d.get("tabs", []) if not t.get("adminOnly")]}
    return filtered


class NavigateBody(BaseModel):
    q: str
    user_gradatie: Optional[int] = None
    is_admin: Optional[bool] = None  # v13c_glow_admin_gate_001 — nodig om admin-tabs af te schermen


@router.post("/navigate")
async def navigate(body: NavigateBody):
    """Match user-query naar tab. Returnt navigate_to + glow_target voor frontend.

    v13c_glow_admin_gate_001 (sessie 54) — Als is_admin=False (of None) worden
    tabs met adminOnly=True overgeslagen. Voorkomt dat een gewone user via
    'toon kennisbank' naar /knowledge geleid wordt en 403 krijgt.
    """
    q = (body.q or "").lower().strip()
    if not q:
        return {"success": False, "match": None, "message": "Geen vraag opgegeven"}

    is_admin = bool(body.is_admin)
    d = _load_tabs()
    # v13c_glow_alias_priority_001 (sessie 54) — Match langste alias eerst,
    # anders wint "archief" van "systeem archief" (substring-hit).
    # Bouw candidate-lijst: (alias, tab) gesorteerd op alias-lengte desc.
    candidates = []
    for tab in d.get("tabs", []):
        if tab.get("adminOnly") and not is_admin:
            continue
        # Label + id ook als kandidaten (label wint als hij letterlijk in q staat)
        candidates.append((tab["label"].lower(), tab, 1.0))
        candidates.append((tab["id"].lower(), tab, 1.0))
        for alias in tab.get("aliases", []):
            candidates.append((alias.lower(), tab, 0.8))
    # Sorteer op lengte (langste eerst), stabiel op score
    candidates.sort(key=lambda c: (-len(c[0]), -c[2]))

    best = None
    best_score = 0
    for alias, tab, score in candidates:
        if alias and alias in q:
            best = tab
            best_score = score
            break

    if not best:
        return {
            "success": False,
            "match": None,
            "message": f"Geen tab gevonden voor '{body.q}'. Probeer: kennis, agenda, wallet, winkelstraat, etc.",
        }

    return {
        "success": True,
        "match": best,
        "navigate_to": best["route"],
        "glow_target": f"nav-{best['id']}",
        "score": best_score,
        "spoken_response": f"De **{best['label']}**-tab vind je hier: {best['route']}. Ik laat 'm even oplichten voor je.",
    }


@router.get("/tabs")
async def list_tabs(is_admin: bool = False):
    """Simpel: alleen labels + ids voor UI selector.
    v13c_glow_admin_gate_001 — admin-tabs afschermen voor niet-admins."""
    d = _load_tabs()
    return {
        "success": True,
        "tabs": [
            {"id": t["id"], "label": t["label"], "route": t["route"], "icon": t.get("icon")}
            for t in d.get("tabs", [])
            if is_admin or not t.get("adminOnly")
        ],
    }
