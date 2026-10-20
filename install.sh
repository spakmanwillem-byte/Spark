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
# Doel: Ubuntu 22.04 / 24.04 (x86_64 + arm64 = Odroid N2+/M1/H-serie)
# Eerst kijken wat er al is / ontbreekt?  ./doctor.sh   (of ./doctor.sh --fix)
# ============================================================
set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/deploy/logging.sh" install "$@"

# ---------- Config ----------
# Python: neem wat er is (3.10+); Ubuntu 22.04 = 3.10, 24.04 = 3.12. Override met PYTHON_BIN=python3.11
PYTHON_BIN="${PYTHON_BIN:-python3}"
PYTHON_VERSION="$($PYTHON_BIN -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")' 2>/dev/null || echo 3)"
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
    python3 python3-venv python3-pip python3-dev \
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
$PYTHON_BIN -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
# emergentintegrations staat op een eigen index; zonder internet daarheen → zonder (alleen nodig met EMERGENT_LLM_KEY)
pip install -r requirements.txt --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ \
  || { warn "emergentintegrations niet beschikbaar — installeer de rest"; grep -v '^emergentintegrations' requirements.txt > /tmp/spark_req.txt && pip install -r /tmp/spark_req.txt; }
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
if [ ! -f backend/.env ] && [ -f backend/.env.example ]; then
  cp backend/.env.example backend/.env
  warn "backend/.env aangemaakt uit .env.example — vul ADMIN_PASSWORD en SPARK_MASTERKEY in (nano backend/.env)"
fi
if [ ! -f frontend/.env ] && [ -f frontend/.env.example ]; then
  cp frontend/.env.example frontend/.env
  warn "frontend/.env aangemaakt — zet REACT_APP_BACKEND_URL op http://<odroid-ip>:8001 als je vanaf een ander apparaat kijkt"
fi

# ---------- Systemd (optioneel, alleen bij prod-install) ----------
# Eén service: backend serveert ook de gebouwde frontend (./run.sh prod) op :8001
if [ "$DEV_MODE" = false ] && [ "$INSTALL_DEPS" = true ]; then
  log "Systemd service aanmaken (spark-backend, autostart na reboot)..."
  if [ -f deploy/spark-backend.service ]; then
    sed -e "s#__SPARK_ROOT__#${SCRIPT_DIR}#g" -e "s#__SPARK_USER__#${SPARK_USER}#g" deploy/spark-backend.service | sudo tee /etc/systemd/system/spark-backend.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable spark-backend
    log "spark-backend enabled. Eerst frontend bouwen: ./run.sh prod (eenmalig), daarna: sudo systemctl start spark-backend"
  else
    warn "deploy/spark-backend.service niet gevonden — sla systemd over"
  fi
fi

# ---------- Klaar ----------
log "✓ Install compleet!"
log ""
log "Volgende stap:"
log "  nano backend/.env     # ADMIN_PASSWORD + SPARK_MASTERKEY invullen"
log "  ./doctor.sh           # controleer of alles klopt"
log "  ./run.sh prod         # frontend bouwen + alles op http://<odroid-ip>:8001"
if [ "$DEV_MODE" = false ]; then
  log "  sudo systemctl start spark-backend     # daarna: start vanzelf na reboot"
  log "  sudo journalctl -u spark-backend -f    # logs volgen"
fi
log "  ./doctor.sh --net     # als je Spark ook van buiten wilt bereiken (Ziggo poort open + HTTPS)"
