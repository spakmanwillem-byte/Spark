#!/usr/bin/env bash
# ============================================================
# Spark Core 2.0 — install.sh
# Voor lokale Odroid / Linux migratie
# ============================================================
#
# Gebruik:
#   ./install.sh                # Volledige install
#   ./install.sh --skip-deps    # Skip apt/system-level deps
#   ./install.sh --dev          # Dev-modus (geen systemd, alleen dependencies)
#
# Testet op: Ubuntu 22.04 (x86_64 + arm64 = Odroid N2+/M1)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ---------- Config ----------
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
NODE_VERSION="${NODE_VERSION:-20}"
SPARK_USER="${SPARK_USER:-$USER}"
INSTALL_DEPS=true
DEV_MODE=false

for arg in "$@"; do
  case $arg in
    --skip-deps) INSTALL_DEPS=false ;;
    --dev)       DEV_MODE=true ;;
    *) echo "Onbekend arg: $arg"; exit 1 ;;
  esac
done

# ---------- Kleuren ----------
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { echo -e "${GREEN}[INSTALL]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------- Detect platform ----------
ARCH=$(uname -m)
OS=$(uname -s)
log "Platform: $OS $ARCH"

# ---------- System deps ----------
if [ "$INSTALL_DEPS" = true ]; then
  log "APT dependencies installeren..."
  sudo apt-get update -qq
  sudo apt-get install -y \
    python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python3-pip \
    curl git build-essential ca-certificates \
    ffmpeg libsndfile1 \
    || { err "APT install mislukt"; exit 1; }

  # Node.js via NodeSource
  if ! command -v node &> /dev/null; then
    log "Node.js ${NODE_VERSION} installeren..."
    curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
    sudo apt-get install -y nodejs
  fi

  # Yarn
  if ! command -v yarn &> /dev/null; then
    log "Yarn installeren..."
    sudo npm install -g yarn
  fi
else
  log "System deps overgeslagen (--skip-deps)"
fi

# ---------- Backend ----------
log "Backend Python-venv opzetten..."
cd backend
python${PYTHON_VERSION} -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Emergent integrations (optioneel — key nodig)
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ || warn "emergentintegrations install faalde — Emergent LLM key features werken niet."
deactivate
cd ..

# ---------- Frontend ----------
log "Frontend dependencies installeren..."
cd frontend
yarn install --frozen-lockfile
cd ..

# ---------- Data-mappen ----------
log "Data-mappen initialiseren..."
mkdir -p backend/data/{system/logs,trade/backtests,trade/logs,chat/logs,chat/prive,knowledge/v2,wallet,roar,kb_v2,dnd,scheduler,triggers,personality}
mkdir -p memory
mkdir -p backend/data/_backups

# ---------- .env checks ----------
log ".env bestanden checken..."
if [ ! -f backend/.env ]; then
  warn "backend/.env ontbreekt! Kopieer .env.example → .env en vul in:"
  echo "  MONGO_URL=  (leeg mag, JSON-only)"
  echo "  DB_NAME=spark_core"
  echo "  BITVAVO_KEY=..."
  echo "  BITVAVO_SECRET=..."
  echo "  GROQ_API_KEY=..."
  echo "  CEREBRAS_API_KEY=..."
  echo "  EMERGENT_LLM_KEY=... (voor TTS/STT + optionele LLM)"
  echo "  SPARK_DATA_DIR=$(pwd)/backend/data  # portable path override"
fi
if [ ! -f frontend/.env ]; then
  warn "frontend/.env ontbreekt! Vereist:"
  echo "  REACT_APP_BACKEND_URL=http://<odroid-ip>:8001  (of localhost:8001)"
fi

# ---------- Systemd (optioneel, alleen bij prod-install) ----------
if [ "$DEV_MODE" = false ] && [ "$INSTALL_DEPS" = true ]; then
  log "Systemd services aanmaken..."
  sudo cp deploy/spark-backend.service /etc/systemd/system/ 2>/dev/null || warn "deploy/spark-backend.service niet gevonden — sla over"
  sudo cp deploy/spark-frontend.service /etc/systemd/system/ 2>/dev/null || warn "deploy/spark-frontend.service niet gevonden — sla over"
  if [ -f /etc/systemd/system/spark-backend.service ]; then
    sudo systemctl daemon-reload
    sudo systemctl enable spark-backend spark-frontend
    log "Systemd services enabled. Start met: sudo systemctl start spark-backend spark-frontend"
  fi
fi

# ---------- Klaar ----------
log "✓ Install compleet!"
log ""
log "Volgende stap:"
if [ "$DEV_MODE" = true ]; then
  log "  ./run.sh    # start backend + frontend in foreground"
else
  log "  sudo systemctl start spark-backend spark-frontend"
  log "  sudo journalctl -u spark-backend -f    # logs volgen"
fi
