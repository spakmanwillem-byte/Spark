"""
Spark Core - Configuration Settings
Centrale configuratie voor het hele systeem
"""
from pathlib import Path
import os

# Paths
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"

# Data subdirectories
SYSTEM_DATA_DIR = DATA_DIR / "system"
USERS_DATA_DIR = DATA_DIR / "users"
KNOWLEDGE_DATA_DIR = DATA_DIR / "knowledge"
TRIGGERS_DATA_DIR = DATA_DIR / "triggers"

# Core files
USERS_FILE = SYSTEM_DATA_DIR / "users.json"
GRADATIES_FILE = SYSTEM_DATA_DIR / "gradaties.json"
ACHIEVEMENTS_FILE = SYSTEM_DATA_DIR / "achievements.json"

# Session settings
SESSION_TIMEOUT_MINUTES = 30
HEARTBEAT_INTERVAL_SECONDS = 30

# CORS
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

# Ensure directories exist
for directory in [DATA_DIR, SYSTEM_DATA_DIR, USERS_DATA_DIR, KNOWLEDGE_DATA_DIR, TRIGGERS_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
