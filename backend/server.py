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
from modules.wallet import wallet_router
app.include_router(wallet_router, prefix="/api")

# Module 14: Trade
from modules.trade import trade_router
app.include_router(trade_router, prefix="/api")

# Module 15: Accounting
from modules.accounting import accounting_router
app.include_router(accounting_router, prefix="/api")

# Module 16: Shop
from modules.shop import shop_router
app.include_router(shop_router, prefix="/api")


# Module 17: Bots & Community
from modules.bots import bots_router
app.include_router(bots_router, prefix="/api")


# Module 18: Voice (STT/TTS)
from modules.voice import router as voice_router
app.include_router(voice_router, prefix="/api")

# Module 19: Profile, Roadmap, Notifications, Spark Profile
from modules.profile import router as profile_router
app.include_router(profile_router, prefix="/api")

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
    try:
        from modules.trade.monitor import get_monitor
        result = get_monitor().resume_if_was_running()
        if result.get("resumed"):
            print(f"   🔄 Trade monitor auto-resumed")
        else:
            print(f"   ⏸  Trade monitor: {result.get('reason', 'idle')}")
    except Exception as e:
        print(f"   ⚠️  Trade monitor resume failed: {e}")
    print("=" * 50)


@app.on_event("shutdown")
async def shutdown():
    print("⚡ Spark Core shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
