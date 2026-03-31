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

# Module 3: Chat/Spark Brain (later)
# from modules.chat import chat_router
# app.include_router(chat_router, prefix="/api")


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


@app.on_event("shutdown")
async def shutdown():
    print("⚡ Spark Core shutting down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
