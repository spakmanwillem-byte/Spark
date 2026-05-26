"""
Spark Core - Main Application Entry Point

Modulaire architectuur:
- /modules/auth   -> Authenticatie, sessies, users
- /modules/core   -> Storage layer, utilities
- /config         -> Configuratie

Elke module is zelfstandig en heeft eigen routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import config
from config.settings import CORS_ORIGINS

# Create FastAPI app
app = FastAPI(
    title="Spark Core",
    version="2.0",
    description="Modulaire Spark AI - Stap voor stap opgebouwd"
)

# CORS middleware
cors_origins = ["*"] if CORS_ORIGINS == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware (voor analytics > network tab)
import time as _time
from fastapi import Request as _Request

@app.middleware("http")
async def track_requests(request: _Request, call_next):
    start = _time.time()
    response = await call_next(request)
    duration_ms = (_time.time() - start) * 1000
    # Skip de tracking-endpoint zelf om recursie/spam te voorkomen
    path = request.url.path
    if path.startswith("/api/analytics/network-info"):
        return response
    try:
        from modules.analytics.routes import track_request
        client_ip = request.client.host if request.client else "?"
        track_request(client_ip, request.method, path, response.status_code, duration_ms)
    except Exception:
        pass
    return response

# ============== MODULE IMPORTS ==============
# Modules worden hier 1 voor 1 toegevoegd als ze klaar zijn

# Module 1: Auth (users, sessions, gradaties)
from modules.auth import auth_router
app.include_router(auth_router, prefix="/api")

# Module 2: Knowledge (kennisbank)
from modules.knowledge import knowledge_router
app.include_router(knowledge_router, prefix="/api")

# Module 3: Files & Module Sandbox
from modules.files import files_router
app.include_router(files_router, prefix="/api")

from modules.user_archive import user_archive_router
app.include_router(user_archive_router, prefix="/api")

from modules.analytics import analytics_router
app.include_router(analytics_router, prefix="/api")

from modules.system_archive import system_archive_router
app.include_router(system_archive_router, prefix="/api")

# Module 4: Achievements
from modules.achievements import achievements_router
app.include_router(achievements_router, prefix="/api")

# Module 5: Chat (Snap + NLP + Knowledge Lookup)
from modules.chat import chat_router
app.include_router(chat_router, prefix="/api")

from modules.contributions.routes import router as contributions_router
app.include_router(contributions_router)

# Module 6: Agenda
from modules.agenda import agenda_router
app.include_router(agenda_router, prefix="/api")

# Module 7: Notes & Tasks
from modules.notes import notes_router
app.include_router(notes_router, prefix="/api")

# Module 8: Triggers (consolidated)
from modules.triggers import triggers_router
app.include_router(triggers_router, prefix="/api")

# Module 9: Persons (persoonskaarten)
from modules.persons import persons_router
app.include_router(persons_router, prefix="/api")

# Module 10: Dagboek
from modules.dagboek import dagboek_router
app.include_router(dagboek_router, prefix="/api")

# Module 11: Spark Core (identity, bijbel)
from modules.spark import router as spark_router
app.include_router(spark_router, prefix="/api")

# Module 12: Knowledge Graph
from modules.graph import router as graph_router
app.include_router(graph_router, prefix="/api")

# Module 13: Wallet
from modules.wallet import wallet_router, tikkie_router
app.include_router(wallet_router, prefix="/api")
app.include_router(tikkie_router, prefix="/api")

# Module 14: Trade
from modules.trade import trade_router
app.include_router(trade_router, prefix="/api")

# Module 15: Accounting
from modules.accounting import accounting_router
app.include_router(accounting_router, prefix="/api")

# v5_closing_flow_001 — De Boekhouder closing-flow (terlens-terug-boek)
from modules.boekhouder.routes import router as boekhouder_router
app.include_router(boekhouder_router, prefix="/api")

# v5_spark_kasboek_001 — Spark's eigen kasboek (BTW-afroming)
from modules.spark_kasboek import router as spark_kasboek_router
app.include_router(spark_kasboek_router, prefix="/api")

# v6_mint_from_wallet_001 — Spark "Maak Token" flow
from modules.spark_mint import router as spark_mint_router
app.include_router(spark_mint_router, prefix="/api")

# v6_bonnetje_001 — Bonnetjes voor klant-aankopen
from modules.bonnetjes import router as bonnetjes_router
app.include_router(bonnetjes_router, prefix="/api")

# v6_tijdelijke_lening_001 — Tijdelijke uithaal-leningen + auto-resolve
from modules.spark_leningen import router as spark_leningen_router
app.include_router(spark_leningen_router, prefix="/api")

# v5_event_overlay_001
from modules.events.routes import router as events_router
app.include_router(events_router, prefix="/api")

# Module 16: Shop
from modules.shop import shop_router, shop_gift_router
app.include_router(shop_router, prefix="/api")
app.include_router(shop_gift_router, prefix="/api")


# Module 17: Bots & Community
from modules.bots import bots_router
app.include_router(bots_router, prefix="/api")


# Module 18: Voice (STT/TTS)
from modules.voice import router as voice_router
app.include_router(voice_router, prefix="/api")

# Module 19: Profile, Roadmap, Notifications, Spark Profile
from modules.profile import router as profile_router
app.include_router(profile_router, prefix="/api")

# Module 19b: Avatar (galerij + user portretten)
from modules.profile.avatar import router as avatar_router
app.include_router(avatar_router, prefix="/api")

# v4_inventory_001 — Stats + Inventory (D&D laag)
from modules.inventory.routes import router as inventory_router
app.include_router(inventory_router, prefix="/api")

# v4_update_bark_001 — Deploy ankers + privacy/update barks
from modules.deploy.routes import router as deploy_router
app.include_router(deploy_router, prefix="/api")

# v4_dnd_001 — D&D Lore + Behavior + Aura + Observations
from modules.dnd.routes import router as dnd_router
app.include_router(dnd_router, prefix="/api")

# v6_dnd_bark_001 — Spark World bark-flow (zintuig-keuze + D&D kaarten)
from modules.dnd.spark_world import router as spark_world_router
app.include_router(spark_world_router, prefix="/api")

# Module 20: Backup (export/import van alle Spark data)
from modules.backup import backup_router
app.include_router(backup_router, prefix="/api")

# Module 21: Urgent notifications (glow op sidebar tabs)
from modules.urgent import urgent_router
app.include_router(urgent_router, prefix="/api")

# Module 22: Contacts (privé-berichten + gradatie-zichtbaarheid)
from modules.contacts import contacts_router
app.include_router(contacts_router, prefix="/api")


# Module 23: Bugs (bug-meldingen door iedereen, beheer door admins gradatie ≤ 2)
from modules.bugs import bugs_router
app.include_router(bugs_router, prefix="/api")


# Module 24: Insights (v4_016 — Analyser voor Shadow Observer data, read-only)
from modules.insights import insights_router
app.include_router(insights_router, prefix="/api")


# Module 25: Settings (v4_settings_001 — System + user settings met gradatie-gating)
from modules.settings import settings_router
app.include_router(settings_router, prefix="/api")

# Module 26: Admin Logs (v5_spark_logger_001 — per-module trace logs voor observability)
from modules.admin import logs_router as admin_logs_router
app.include_router(admin_logs_router, prefix="/api")

# v6_capabilities_admin_001 — Spark's capabilities overzicht voor Analytics → CAPABILITIES tab
from modules.admin import capabilities_router as admin_capabilities_router
app.include_router(admin_capabilities_router, prefix="/api")

# Module 27: Knowledge Base v2 (v5_kbv2_001 — 4 lades + inbox + index)
from modules.kb_v2 import kbv2_router, kbv2_media_router
app.include_router(kbv2_router, prefix="/api")
app.include_router(kbv2_media_router, prefix="/api")

# v6_emotion_pipeline_001 — 7-laags emotie-pipeline (dry-run)
from modules.emotion_pipeline.routes import router as emotion_pipeline_router
app.include_router(emotion_pipeline_router, prefix="/api")

# v6_command_registry_001 — Bidirectionele intent ↔ capability matcher (fundering donderdag)
from modules.intent_registry.routes import router as intent_registry_router
app.include_router(intent_registry_router, prefix="/api")

# v6_winkelstraat_001 — Multi-tenant winkelstraat
from modules.winkelstraat.routes import router as winkelstraat_router
app.include_router(winkelstraat_router, prefix="/api")

# v6_help_per_gradatie_001 — Help/commands per gradatie auto-afgeleid uit command_registry
from modules.help_per_gradatie.routes import router as help_router
app.include_router(help_router, prefix="/api")

# v6_glow_nav_001 — Spark wijst UI-tabs aan via chat ("waar is winkelstraat?")
from modules.glow_nav.routes import router as glow_router
app.include_router(glow_router, prefix="/api")

# v6_synapse_001 — Spark's synapslaag (zelf-lezende meta op alle mappen)
from modules.synapse.routes import router as synapse_router
app.include_router(synapse_router, prefix="/api")

# v6_container_001 — Universeel container-patroon (user/shop/asset/...)
from modules.container.routes import router as container_router
app.include_router(container_router, prefix="/api")

# Module 28: Card Factory (v5_card_factory_001 — DnD/Event/Bark generieke kaarten)
from modules.cards import cards_router
app.include_router(cards_router, prefix="/api")



# ============== HEALTH & ROOT ==============

@app.get("/health")
async def health_check():
    """Health check for deployment"""
    return {"status": "healthy", "service": "spark-core"}


@app.get("/api")
async def api_root():
    """API root - shows available modules"""
    return {
        "name": "Spark Core",
        "version": "2.0",
        "modules": {
            "auth": {
                "status": "active",
                "endpoints": [
                    "/api/auth/login",
                    "/api/auth/logout",
                    "/api/auth/session/heartbeat",
                    "/api/auth/session/validate",
                    "/api/auth/users",
                    "/api/auth/gradaties"
                ]
            },
            "knowledge": {"status": "planned"},
            "chat": {"status": "planned"}
        }
    }


@app.get("/api/system/health")
async def system_health():
    """Detailed system health"""
    from datetime import datetime, timezone
    return {
        "status": "healthy",
        "service": "spark-core",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Ambient sound serving (v4_actions_001)
from fastapi.responses import FileResponse
from pathlib import Path as _Path
import json as _json

@app.get("/api/system/ambient/list")
async def list_ambient_loops():
    """List ambient loops + their triggers (for settings UI)."""
    reg_path = _Path(__file__).parent / "data" / "system" / "ambient" / "registry.json"
    if not reg_path.exists():
        return {"loops": []}
    return _json.loads(reg_path.read_text())


@app.get("/api/system/ambient/{filename}")
async def serve_ambient(filename: str):
    """Serve een ambient audio bestand (wav/mp3/ogg)."""
    safe = _Path(filename).name  # voorkom path traversal
    fp = _Path(__file__).parent / "data" / "system" / "ambient" / safe
    if not fp.exists() or not fp.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Ambient file niet gevonden")
    return FileResponse(fp, media_type="audio/wav" if safe.endswith(".wav") else "audio/mpeg")


# ============== STARTUP ==============

@app.on_event("startup")
async def startup():
    print("=" * 50)
    print("🚀 Spark Core 2.0 Starting...")
    print("=" * 50)
    print("📦 Modules loaded:")
    print("   ✅ Auth (users, sessions, gradaties)")
    print("   ⏳ Knowledge (pending)")
    print("   ⏳ Chat (pending)")
    print("=" * 50)
    # Auto-resume trade monitor als die draaide voor crash/restart
    # v4_startup_safe_001: in een thread zodat traag Bitvavo de boot niet blokkeert
    def _resume_in_background():
        try:
            from modules.trade.monitor import get_monitor, resume_registry_bots, resume_registered_users
            # 1. Legacy single monitor
            result = get_monitor().resume_if_was_running()
            if result.get("resumed"):
                print("   🔄 Trade monitor auto-resumed (legacy)")
            # 2. Per-user registry bots (Spark + anderen)
            reg_result = resume_registry_bots()
            n = reg_result.get("resumed", 0)
            if n > 0:
                print(f"   🤖 {n} registry-bot(s) auto-resumed")
            # 3. Proactief geregistreerde users (zichtbaar in Analytics, niet running)
            resume_registered_users()
        except Exception as e:
            print(f"   ⚠️  Trade monitor resume failed: {e}")
    try:
        import threading
        threading.Thread(target=_resume_in_background, daemon=True).start()
        print("   🚀 Trade monitor resume scheduled (non-blocking)")
    except Exception as e:
        print(f"   ⚠️  Could not schedule monitor resume: {e}")
    print("=" * 50)
    # v5_spark_logger_001 — opschonen oude logs (> 28 dagen)
    try:
        from modules.core.spark_logger import purge_old_logs, log_event
        p = purge_old_logs()
        print(f"   🧹 Logs purge: {p['deleted_dirs']} day-folders verwijderd (cutoff {p['cutoff']})")
        log_event("system", "startup", intent="backend startup gereed", detail={
            "purged_dirs": p["deleted_dirs"], "cutoff": p["cutoff"],
        })
    except Exception as e:
        print(f"   ⚠️  Log purge failed: {e}")
    print("=" * 50)
    # Voorkomt cold-start latency op de eerste user request (chat, verbanden, KB-zoek).
    try:
        import time as _t
        from pathlib import Path as _P
        from modules.core.storage import load_json
        warmup_files = [
            _P("/app/backend/data/knowledge/learned_knowledge/knowledge_base.json"),
            _P("/app/backend/data/graph/nodes.json"),
            _P("/app/backend/data/graph/edges.json"),
            _P("/app/backend/data/personality/spark_vocab.json"),
            _P("/app/backend/data/system/users.json"),
        ]
        t0 = _t.perf_counter()
        loaded = 0
        for fp in warmup_files:
            if fp.exists():
                load_json(fp, default={})
                loaded += 1
        dur_ms = round((_t.perf_counter() - t0) * 1000)
        print(f"   🔥 Cache warmup: {loaded}/{len(warmup_files)} files in {dur_ms}ms (cold-start eliminated)")
    except Exception as e:
        print(f"   ⚠️  Cache warmup failed: {e}")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown():
    print("⚡ Spark Core shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
