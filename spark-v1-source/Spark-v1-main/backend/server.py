from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from utils.logger import SparkLogger
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
import asyncio
from starlette.middleware.base import BaseHTTPMiddleware

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure CORS origins
def get_cors_origins():
    """
    Get CORS origins from environment with smart defaults
    
    Priority:
    1. CORS_ORIGINS env variable (comma-separated)
    2. Fallback: ["*"] (allow all - for development)
    """
    cors_env = os.environ.get('CORS_ORIGINS', '*')
    
    if cors_env == '*':
        # Development: allow all
        return ["*"]
    
    # Production: parse comma-separated origins
    origins = [origin.strip() for origin in cors_env.split(',') if origin.strip()]
    
    # Always include localhost for development
    localhost_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Combine origins (deduplicate)
    all_origins = list(set(origins + localhost_origins))
    
    return all_origins

# Get CORS origins
CORS_ORIGINS = get_cors_origins()

# Log system startup
SparkLogger.log_system_event("⚡ Spark opgestart")
SparkLogger.log_system_event(f"🌍 CORS Origins: {CORS_ORIGINS}")

# Create FastAPI app
app = FastAPI(title="Spark AI", version="0.1")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache Control Middleware for Static Assets
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Never cache index.html (SPA entry point)
        if request.url.path == "/" or request.url.path.endswith("index.html"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Cache hashed static assets forever (JS/CSS with content hashes)
        elif request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        
        return response

app.add_middleware(CacheControlMiddleware)

# Create API router
api_router = APIRouter(prefix="/api")

# Import routes
from routes.spark_routes import router as spark_router
from routes.spark_profile_routes import router as spark_profile_router
from routes.roadmap_routes import router as roadmap_router
from routes.personal_routes import router as personal_router
from routes.notes_routes import router as notes_router
from routes.profile_routes import router as profile_router
from routes.profile_routes_new import router as profile_new_router
from routes.profile_routes_extended import router as profile_extended_router
from routes.graph_routes import router as graph_router
from routes.emotion_routes import router as emotion_router
from routes.knowledge_routes import router as knowledge_router
from routes.system_routes import router as system_router
from routes.voice_routes import router as voice_router
from routes.person_routes import router as person_router
from routes.leaderboard_routes import router as leaderboard_router
from routes.folder_routes import router as folder_router
from routes.learning_routes import router as learning_router
from routes.source_routes import router as source_router
from routes.scripting_routes import router as scripting_router
from routes.wallet_routes import router as wallet_router
from routes.accounting_routes import router as accounting_router
from routes.bot_routes import router as bot_router
from routes.community_routes import router as community_router
from routes.game_routes import router as game_router
from routes.factions_routes import router as factions_router
from routes.actors_routes import router as actors_router
from routes.knowledge_game_routes import router as knowledge_game_router
from routes.buildings_routes import router as buildings_router
from routes.blueprint_routes import router as blueprint_router  # NIEUW
from routes.context_routes import router as context_router  # Personal Context
from routes.expenses_routes import router as expenses_router  # Privé Uitgaven
from routes.income_routes import router as income_router  # Privé Inkomsten
from routes.bitvavo_routes import router as bitvavo_router  # Bitvavo Crypto Wallet
from routes.user_management_routes import router as user_mgmt_router  # User Management (Admin)
from routes.file_manager_routes import router as file_mgr_router  # File Manager (Admin)
from routes.module_routes import router as module_router  # Module Sandbox (Admin)
from routes.verbanden_routes import router as verbanden_router  # 5W+H Verbanden (Light)
from routes.audit_routes import router as audit_router  # Self-check / Audit tooling
from routes.task_routes import router as task_router  # Task Module (Core)
from routes.monitoring_routes import router as monitoring_router  # Monitoring Service (Core)
from routes.backtest_routes import router as backtest_router  # Backtesting Service (Core)
from routes.notification_routes import router as notification_router  # Notification Service (Core)
from routes.settings_routes import router as settings_router  # Settings Management (Core)
from routes.user_files_routes import router as user_files_router  # User File Storage (Personal Media)
from routes.roar_routes import router as roar_router  # ROAR Token System (Financial) - DEPRECATED
from routes.central_wallet_routes import router as central_wallet_router  # Central Wallet System (NEW)
from routes.bank_config_routes import router as bank_config_router  # Bank Configuration (Admin)
from routes.spark_core_sync_routes import router as spark_core_sync_router  # Spark Core Balance Sync
from routes.potjes_routes import router as potjes_router  # Potjes System (Bookkeeping Layer)

# Include routers
api_router.include_router(spark_router, tags=["spark"])
api_router.include_router(spark_profile_router, prefix="/spark/profile", tags=["spark_profile"])
api_router.include_router(roadmap_router, prefix="/roadmap", tags=["roadmap"])
api_router.include_router(personal_router, prefix="/personal", tags=["personal"])
api_router.include_router(notes_router, prefix="/notes", tags=["notes"])
api_router.include_router(profile_router, prefix="/profiles", tags=["profiles"])
api_router.include_router(profile_new_router, prefix="/profile", tags=["profile"])
api_router.include_router(profile_extended_router, prefix="/profile", tags=["profile"])
api_router.include_router(graph_router, prefix="/graph", tags=["graph"])
api_router.include_router(emotion_router, tags=["emotions"])
api_router.include_router(knowledge_router, tags=["knowledge"])
api_router.include_router(system_router, tags=["system"])
api_router.include_router(voice_router, prefix="/voice", tags=["voice"])
api_router.include_router(person_router, tags=["persons"])
api_router.include_router(leaderboard_router, tags=["leaderboard"])
api_router.include_router(folder_router, prefix="/folders", tags=["folders"])
api_router.include_router(learning_router, prefix="/learning", tags=["learning"])
api_router.include_router(source_router, prefix="/sources", tags=["sources"])
api_router.include_router(scripting_router, prefix="/scripting", tags=["scripting"])
api_router.include_router(wallet_router, prefix="/wallet", tags=["wallet"])
api_router.include_router(accounting_router, prefix="/accounting", tags=["accounting"])
api_router.include_router(bot_router, prefix="/bots", tags=["bots"])
api_router.include_router(community_router, prefix="/community", tags=["community"])
api_router.include_router(game_router, tags=["game"])
api_router.include_router(factions_router, tags=["factions"])
api_router.include_router(actors_router, tags=["actors"])
api_router.include_router(knowledge_game_router, tags=["knowledge-game"])
api_router.include_router(buildings_router, tags=["buildings"])
api_router.include_router(expenses_router, prefix="/expenses", tags=["expenses"])  # Privé Uitgaven
api_router.include_router(income_router, prefix="/income", tags=["income"])  # Privé Inkomsten
api_router.include_router(bitvavo_router, prefix="/bitvavo", tags=["bitvavo"])  # Crypto Wallet
api_router.include_router(user_mgmt_router, prefix="/admin/users", tags=["user-management"])  # Admin User Mgmt
api_router.include_router(file_mgr_router, prefix="/files", tags=["file-manager"])  # Admin File Manager
api_router.include_router(module_router, prefix="/modules", tags=["modules"])  # Module Sandbox
api_router.include_router(verbanden_router, tags=["verbanden"])  # 5W+H Verbanden (prefix al in router)
api_router.include_router(audit_router, tags=["audit"])  # Self-check / Audit (prefix al in router)
api_router.include_router(task_router, tags=["tasks"])  # Task Module (Core - prefix al in router)
api_router.include_router(monitoring_router, tags=["monitoring"])  # Monitoring Service (Core - prefix al in router)
api_router.include_router(backtest_router, tags=["backtest"])  # Backtesting Service (Core - prefix al in router)
api_router.include_router(notification_router, tags=["notifications"])  # Notification Service (Core - prefix al in router)
api_router.include_router(settings_router, tags=["settings"])  # Settings Management (Core - prefix al in router)
api_router.include_router(user_files_router, prefix="/user", tags=["user_files"])  # User File Storage (Personal Media)
api_router.include_router(roar_router, tags=["roar"])  # DEPRECATED - use central_wallet
api_router.include_router(central_wallet_router, prefix="/central", tags=["central_wallet"])  # NEW: Single source of truth
api_router.include_router(bank_config_router, tags=["bank_config"])  # Bank Config (prefix al in router)
api_router.include_router(spark_core_sync_router, prefix="/spark_core", tags=["spark_core_sync"])  # Balance Sync
api_router.include_router(potjes_router, prefix="/potjes", tags=["potjes"])  # Potjes System
app.include_router(blueprint_router)  # NIEUW: Heeft eigen prefix /api/blueprints
app.include_router(context_router)  # Personal Context API

# Import admin routes
from routes.admin_routes import router as admin_router
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])

# Root endpoints
@api_router.get("/")
async def root():
    return {
        "message": "Spark AI v0.1",
        "status": "operational",
        "description": "Lerende AI assistent door Willem Spakman",
        "build_timestamp": "2026-03-31T12:00:00Z",
        "frontend_hash": "e2f96fc9"
    }

@api_router.get("/debug/build-status")
async def debug_build_status():
    """Debug endpoint to check frontend build status"""
    from pathlib import Path
    import os
    
    backend_dir = Path(__file__).parent
    frontend_build = backend_dir.parent / "frontend" / "build"
    frontend_static = frontend_build / "static"
    index_file = frontend_build / "index.html"
    
    js_files = []
    if frontend_static.exists():
        js_dir = frontend_static / "js"
        if js_dir.exists():
            js_files = [f.name for f in js_dir.glob("main.*.js")]
    
    return {
        "backend_location": str(backend_dir),
        "frontend_build_path": str(frontend_build),
        "frontend_build_exists": frontend_build.exists(),
        "frontend_static_exists": frontend_static.exists(),
        "index_html_exists": index_file.exists(),
        "main_js_files": js_files,
        "cwd": os.getcwd()
    }

# Include API router in app

# Mount static files for media (audio, images, etc.)
media_dir = Path(__file__).parent / "data" / "media"
if media_dir.exists():
    app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")
    SparkLogger.log_system_event(f"📁 Media directory mounted: {media_dir}")
else:
    SparkLogger.log_system_event(f"⚠️ Media directory not found: {media_dir}")

app.include_router(api_router)

# Mount frontend production build FIRST (higher priority)
frontend_build = Path(__file__).parent.parent / "frontend" / "build"
print(f"[MOUNT DEBUG] Checking frontend build: {frontend_build}, exists: {frontend_build.exists()}")
if frontend_build.exists():
    # Serve frontend static files (JS, CSS, images)
    frontend_static = frontend_build / "static"
    print(f"[MOUNT DEBUG] Checking frontend static: {frontend_static}, exists: {frontend_static.exists()}")
    if frontend_static.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_static)), name="frontend_static")
        print(f"[MOUNT DEBUG] ✅ Frontend static MOUNTED: {frontend_static}")
        SparkLogger.log_system_event(f"📁 Frontend static mounted: {frontend_static}")
    else:
        print(f"[MOUNT DEBUG] ❌ Frontend static NOT FOUND: {frontend_static}")
        SparkLogger.log_system_event(f"⚠️ Frontend static directory not found: {frontend_static}")
else:
    print(f"[MOUNT DEBUG] ❌ Frontend build NOT FOUND: {frontend_build}")
    SparkLogger.log_system_event(f"⚠️ Frontend build not found: {frontend_build}")

# Mount backend static files for uploaded icons
backend_static_dir = Path(__file__).parent / "static"
backend_static_dir.mkdir(exist_ok=True)
(backend_static_dir / "uploaded_icons").mkdir(exist_ok=True)
app.mount("/backend-static", StaticFiles(directory=str(backend_static_dir)), name="backend_static")
SparkLogger.log_system_event(f"📁 Backend static directory mounted: {backend_static_dir}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Health check endpoints for deployment and monitoring
@app.get("/health")
async def root_health_check():
    """Root health check for Kubernetes/deployment probes (no /api prefix)"""
    return {
        "status": "healthy",
        "service": "spark-foundation-backend"
    }

@app.get("/api/system/health")
async def health_check():
    """Detailed health check endpoint with timestamp"""
    return {
        "status": "healthy",
        "service": "spark-foundation-backend",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Run on server startup"""
    logger.info("🚀 Spark AI starting up...")
    
    # Auto-sync knowledge_base.json → nodes.json
    from utils.auto_sync import sync_on_startup
    sync_on_startup()
    
    # Start Harry's hourly announcements
    start_bot_scheduler()
    
    logger.info("✅ Spark AI startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    SparkLogger.log_system_event("⚡ Spark afgesloten")
    logger.info("Spark AI shutting down")
    
    # Stop scheduler
    if hasattr(app.state, 'scheduler'):
        app.state.scheduler.shutdown()
        logger.info("⏰ Bot scheduler stopped")

# Bot Scheduler Functions
def post_harry_announcement():
    """Harry posts hourly time announcement to community chat"""
    import json
    import uuid
    from pathlib import Path
    
    COMMUNITY_CHAT_FILE = Path("/app/backend/data/community/messages.json")
    
    try:
        # Load messages
        if COMMUNITY_CHAT_FILE.exists():
            with open(COMMUNITY_CHAT_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {"messages": [], "active_users": []}
        
        # Create Harry's announcement
        hour = datetime.now().hour
        announcement = {
            "id": str(uuid.uuid4()),
            "user_id": "bot-harry",
            "user_name": "Harry Klokkenmaker",
            "message": f"🕐 Het is nu {hour}:00 uur!",
            "is_bot": True,
            "timestamp": datetime.now().isoformat()
        }
        
        data["messages"].append(announcement)
        
        # Save
        with open(COMMUNITY_CHAT_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"⏰ Harry announced: {hour}:00")
        
    except Exception as e:
        logger.error(f"❌ Harry announcement failed: {e}")

def update_game_loop():
    """DISABLED - Game system removed for clean backend"""
    # Game loop disabled - will be rebuilt as separate module
    pass

def sync_spark_core_balance():
    """Sync Spark Core Bitvavo balance periodically"""
    from services.spark_core_sync_service import SparkCoreSyncService
    
    try:
        result = SparkCoreSyncService.sync_bitvavo_balance()
        if result.get('success'):
            logger.info(f"💰 [SYNC] Balance updated: €{result.get('balance_eur', 0):.2f}")
        else:
            logger.warning(f"⚠️ [SYNC] Failed: {result.get('message')}")
    except Exception as e:
        logger.error(f"❌ [SYNC] Error: {e}")

def start_bot_scheduler():
    """Start background scheduler - Game loop DISABLED"""
    scheduler = BackgroundScheduler()
    
    # Harry's hourly announcement (every hour at :00)
    scheduler.add_job(
        post_harry_announcement,
        'cron',
        minute=0,
        id='harry_hourly',
        replace_existing=True
    )
    
    # GAME LOOP DISABLED
    # Game system removed for clean, stable backend
    # Will be rebuilt as separate module later
    
    # Spark Core Balance Sync - read interval from config
    from services.spark_core_sync_service import SparkCoreSyncService
    sync_status = SparkCoreSyncService.get_sync_status()
    
    if sync_status.get('auto_sync'):
        interval_minutes = sync_status.get('interval_minutes', 30)
        scheduler.add_job(
            sync_spark_core_balance,
            'interval',
            minutes=interval_minutes,
            id='spark_core_sync',
            replace_existing=True
        )
        logger.info(f"💰 Spark Core balance sync started - every {interval_minutes} minutes")
    else:
        logger.info("💰 Spark Core balance sync disabled (enable via API)")
    
    scheduler.start()
    app.state.scheduler = scheduler
    
    logger.info("⏰ Bot scheduler started - Harry will announce every hour")
    logger.info("🎮 Game loop DISABLED - removed for stable backend")

# SPA Catch-All Route (MUST BE LAST - after all API routes)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve React SPA index.html for all non-API, non-health routes"""
    # Don't intercept API, health, or media routes
    if (full_path.startswith("api/") or 
        full_path.startswith("media/") or 
        full_path.startswith("backend-static/") or
        full_path == "health"):
        raise HTTPException(status_code=404, detail="Not found")
    
    frontend_build = Path(__file__).parent.parent / "frontend" / "build"
    index_file = frontend_build / "index.html"
    
    if index_file.exists():
        # Serve index.html with strict no-cache headers
        response = FileResponse(index_file)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    else:
        raise HTTPException(status_code=404, detail="Frontend not built")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
