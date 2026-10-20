#!/usr/bin/env bash
# ============================================================
# Spark Core 2.0 — run.sh
# Start backend + frontend in dev-modus (geen supervisor/systemd)
# ============================================================
#
# Gebruik:
#   ./run.sh             # Start beide, log naar stdout
#   ./run.sh backend     # Alleen backend
#   ./run.sh frontend    # Alleen frontend
#   ./run.sh prod        # Frontend bouwen (yarn build) + backend serveert alles op :8001 (aanrader op Odroid)
#   ./run.sh stop        # Stop alle Spark-processen
#   ./run.sh check       # Zelfscan: wat is er, wat ontbreekt (= ./doctor.sh)
#
# Voor autostart na reboot (Odroid): systemd via install.sh (deploy/spark-backend.service)
# ============================================================
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
TARGET="${1:-all}"
if [ "$TARGET" != "stop" ] && [ "$TARGET" != "check" ]; then
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/deploy/logging.sh" run "$@"
fi

BACKEND_PORT="${BACKEND_PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
PID_DIR="${SCRIPT_DIR}/.run"
mkdir -p "$PID_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log() { echo -e "${GREEN}[RUN]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

# ---------- Check ----------
if [ "$TARGET" = "check" ]; then exec "$SCRIPT_DIR/doctor.sh"; fi

# ---------- Stop ----------
if [ "$TARGET" = "stop" ]; then
  for f in "$PID_DIR"/*.pid; do
    [ -f "$f" ] || continue
    pid=$(cat "$f")
    if kill -0 "$pid" 2>/dev/null; then
      log "Killing PID $pid ($f)"
      kill "$pid" || true
    fi
    rm -f "$f"
  done
  exit 0
fi

# ---------- Backend ----------
start_backend() {
  cd "$SCRIPT_DIR/backend"
  # Portable data-pad via env-var
  export SPARK_ROOT="${SPARK_ROOT:-$SCRIPT_DIR}"
  export SPARK_DATA_DIR="${SPARK_DATA_DIR:-$SCRIPT_DIR/backend/data}"
  # shellcheck disable=SC1091
  source .venv/bin/activate 2>/dev/null || { warn "venv niet gevonden — draai eerst ./install.sh"; exit 1; }
  log "Backend start op :$BACKEND_PORT (SPARK_DATA_DIR=$SPARK_DATA_DIR)"
  uvicorn server:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload &
  echo $! > "$PID_DIR/backend.pid"
}

# ---------- Prod: build + één poort ----------
build_frontend() {
  cd "$SCRIPT_DIR/frontend"
  [ -f .env ] || cp .env.example .env
  # Zelfde host als de backend → relatieve API-calls, werkt vanaf elk apparaat in je netwerk
  log "Frontend bouwen (REACT_APP_BACKEND_URL leeg = zelfde host)… op een Odroid duurt dit 5-15 min"
  # Odroid: beperk node-geheugen zodat de build niet OOM'd op 2-4 GB
  REACT_APP_BACKEND_URL="" GENERATE_SOURCEMAP=false NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=1536}" yarn build
  cd "$SCRIPT_DIR"
}

# ---------- Frontend ----------
start_frontend() {
  cd "$SCRIPT_DIR/frontend"
  log "Frontend start op :$FRONTEND_PORT"
  PORT="$FRONTEND_PORT" yarn start &
  echo $! > "$PID_DIR/frontend.pid"
}

# ---------- Dispatch ----------
case "$TARGET" in
  backend)  start_backend ;;
  frontend) start_frontend ;;
  all)
    start_backend
    sleep 3
    start_frontend
    ;;
  prod)
    build_frontend
    start_backend
    log "Open http://<dit-ip>:$BACKEND_PORT in je browser (frontend wordt door de backend geserveerd)"
    ;;
  *) echo "Onbekende target: $TARGET (all|backend|frontend|prod|stop|check)"; exit 1 ;;
esac

# ---------- Wacht ----------
log "Spark draait. Ctrl+C om te stoppen, of './run.sh stop' vanuit andere shell."
trap 'log "Signal received, killing…"; ./run.sh stop; exit 0' INT TERM
wait
