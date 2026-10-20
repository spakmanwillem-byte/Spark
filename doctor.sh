#!/usr/bin/env bash
# ============================================================
# Spark Core 2.0 — doctor.sh  (Odroid zelfscan vanuit de terminal)
# ============================================================
#
#   ./doctor.sh          # scan: wat is er, wat ontbreekt, wat staat verkeerd
#   ./doctor.sh --fix    # zelfde scan, maar installeert/repareert wat ontbreekt (vraagt sudo)
#   ./doctor.sh --net    # extra: netwerk/poort/HTTPS-check voor toegang van buiten
#
# Werkt zonder venv/node — puur bash, dus ook als install.sh half mislukt is.
# ============================================================
set -uo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

FIX=false; NET=false
for a in "$@"; do case $a in --fix) FIX=true ;; --net) NET=true ;; *) echo "Onbekend arg: $a"; exit 1 ;; esac; done

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
OK=0; WARN=0; FAIL=0
ok()   { echo -e "  ${GREEN}✓${NC} $*"; OK=$((OK+1)); }
warn() { echo -e "  ${YELLOW}!${NC} $*"; WARN=$((WARN+1)); }
fail() { echo -e "  ${RED}✗${NC} $*"; FAIL=$((FAIL+1)); }
head_() { echo -e "\n${BLUE}── $* ──${NC}"; }
fixing() { echo -e "  ${BLUE}→ fix:${NC} $*"; }

PORT="${BACKEND_PORT:-8001}"
APT_MISSING=()

install_caddy() {
  fixing "Caddy installeren via apt-repo"
  sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl >/dev/null
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update -qq && sudo apt-get install -y caddy && ok "caddy geïnstalleerd" || fail "caddy install mislukt"
}

# ---------- 1. Platform ----------
head_ "Platform"
ARCH=$(uname -m); OS_NAME=$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-$(uname -s)}")
ok "$OS_NAME ($ARCH)"
case "$ARCH" in aarch64|arm64|x86_64) ;; *) warn "Architectuur $ARCH niet getest — wheels voor numpy/pandas kunnen ontbreken" ;; esac

RAM_MB=$(awk '/MemTotal/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
SWAP_MB=$(awk '/SwapTotal/ {printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo 0)
if [ "$RAM_MB" -ge 3500 ]; then ok "RAM: ${RAM_MB} MB (swap ${SWAP_MB} MB)"
elif [ "$RAM_MB" -ge 1800 ]; then warn "RAM: ${RAM_MB} MB — 'yarn build' kan krap zijn; swap ${SWAP_MB} MB. Tip: NODE_OPTIONS=--max-old-space-size=1536 ./run.sh prod"
else fail "RAM: ${RAM_MB} MB — te weinig voor yarn build; bouw de frontend op een laptop en kopieer frontend/build/"; fi
if [ "$RAM_MB" -lt 3500 ] && [ "$SWAP_MB" -lt 1000 ]; then
  warn "Weinig swap. Aanrader: sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile"
fi

DISK_FREE=$(df -Pm "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
if [ "${DISK_FREE:-0}" -ge 3000 ]; then ok "Schijf vrij: ${DISK_FREE} MB"; else fail "Schijf vrij: ${DISK_FREE} MB — minimaal ~3 GB nodig (node_modules + venv)"; fi

# ---------- 2. Systeemtools ----------
head_ "Systeemtools"
check_cmd() { # naam  apt-pakket  [min-versie-cmd]
  local name=$1 pkg=$2
  if command -v "$name" >/dev/null 2>&1; then ok "$name: $(command -v "$name") $("$name" --version 2>/dev/null | head -1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -1)"
  else fail "$name ontbreekt (apt: $pkg)"; APT_MISSING+=("$pkg"); fi
}
check_cmd python3 python3
check_cmd git git
check_cmd curl curl
check_cmd ffmpeg ffmpeg
check_cmd gcc build-essential

if command -v python3 >/dev/null; then
  PYV=$(python3 -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
  if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)'; then ok "Python $PYV (≥3.10)"; else fail "Python $PYV is te oud, 3.10+ nodig"; fi
  if python3 -c 'import venv, ensurepip' 2>/dev/null; then ok "python3-venv aanwezig"; else fail "python3-venv ontbreekt"; APT_MISSING+=("python${PYV}-venv" "python3-venv"); fi
  if dpkg -s "python3-dev" >/dev/null 2>&1 || dpkg -s "python${PYV}-dev" >/dev/null 2>&1; then ok "python3-dev aanwezig"; else warn "python3-dev ontbreekt (nodig als een wheel gecompileerd moet worden)"; APT_MISSING+=("python3-dev"); fi
fi

NODE_OK=false
if command -v node >/dev/null; then
  NV=$(node -v | tr -d v | cut -d. -f1)
  if [ "$NV" -ge 18 ]; then ok "node $(node -v)"; NODE_OK=true; else fail "node $(node -v) te oud, 18+ nodig"; fi
else fail "node ontbreekt"; fi
if command -v yarn >/dev/null; then ok "yarn $(yarn -v)"; else fail "yarn ontbreekt"; fi

# ---------- 3. Spark-installatie ----------
head_ "Spark-installatie ($SCRIPT_DIR)"
[ -x install.sh ] && ok "install.sh uitvoerbaar" || { warn "install.sh niet uitvoerbaar"; $FIX && { fixing "chmod +x *.sh"; chmod +x install.sh run.sh doctor.sh; }; }

if [ -x backend/.venv/bin/python ]; then
  if backend/.venv/bin/python -c 'import fastapi, uvicorn' 2>/dev/null; then ok "backend/.venv met fastapi+uvicorn"
  else fail "backend/.venv bestaat maar pip-packages ontbreken/incompleet"; VENV_BROKEN=true; fi
  for m in numpy pandas; do backend/.venv/bin/python -c "import $m" 2>/dev/null && ok "python: $m importeert" || warn "python: $m importeert niet (ARM-wheel?) — check 'pip install $m' in de venv"; done
else fail "backend/.venv ontbreekt → ./install.sh (of --fix)"; VENV_MISSING=true; fi

[ -d frontend/node_modules ] && ok "frontend/node_modules aanwezig" || { fail "frontend/node_modules ontbreekt → yarn install"; NM_MISSING=true; }
if [ -f frontend/build/index.html ]; then
  ok "frontend/build aanwezig ($(date -r frontend/build/index.html '+%d-%m %H:%M')) — backend serveert dit op :$PORT"
else warn "frontend/build ontbreekt → './run.sh prod' bouwt hem (eenmalig, duurt op Odroid 5-15 min)"; fi

[ -d backend/data ] && ok "backend/data aanwezig ($(du -sm backend/data 2>/dev/null | cut -f1) MB)" || warn "backend/data ontbreekt — wordt bij eerste start aangemaakt (leeg)"

# ---------- 4. .env ----------
head_ "Configuratie (.env)"
if [ -f backend/.env ]; then
  ok "backend/.env aanwezig"
  envval() { grep -E "^$1=" backend/.env | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'" ; }
  for k in ADMIN_PASSWORD SPARK_MASTERKEY; do
    v=$(envval $k)
    if [ -z "$v" ] || [[ "$v" == kies-een-* ]]; then fail "$k niet ingevuld (nano backend/.env)"; else ok "$k ingevuld"; fi
  done
  [ -n "$(envval EMERGENT_LLM_KEY)" ] && ok "EMERGENT_LLM_KEY ingevuld (LLM/TTS/STT cloud actief)" || warn "EMERGENT_LLM_KEY leeg → Spark draait basis (KB, relaties, feiten, commands, TTSS). Geen LLM-verdieping/Whisper. Mag."
  [ -n "$(envval LLM_PRIMARY_BASE_URL)" ] && ok "LLM_PRIMARY_BASE_URL gezet: $(envval LLM_PRIMARY_BASE_URL)" || warn "Geen lokale LLM (LLM_PRIMARY_BASE_URL leeg) — later Ollama: http://localhost:11434/v1"
else
  fail "backend/.env ontbreekt"
  $FIX && [ -f backend/.env.example ] && { fixing "cp backend/.env.example backend/.env"; cp backend/.env.example backend/.env; warn "Vul nu ADMIN_PASSWORD en SPARK_MASTERKEY in: nano backend/.env"; }
fi
if [ -f frontend/.env ]; then ok "frontend/.env aanwezig"; else
  warn "frontend/.env ontbreekt (prod-modus heeft 'm niet nodig)"
  $FIX && [ -f frontend/.env.example ] && { fixing "cp frontend/.env.example frontend/.env"; cp frontend/.env.example frontend/.env; }
fi

# ---------- 5. Draait het? ----------
head_ "Processen & poorten"
LAN_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
if ss -ltn 2>/dev/null | grep -q ":$PORT "; then
  ok "Poort $PORT is in gebruik (Spark draait?)"
  if curl -fs --max-time 3 "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1 || curl -fs --max-time 3 "http://127.0.0.1:$PORT/api/" >/dev/null 2>&1; then
    ok "Backend antwoordt op http://127.0.0.1:$PORT/api"
  else warn "Poort $PORT bezet maar /api antwoordt niet — ander proces? (ss -ltnp | grep $PORT)"; fi
  if curl -fs --max-time 3 "http://127.0.0.1:$PORT/" | grep -qi "<html"; then ok "Frontend wordt geserveerd op http://$LAN_IP:$PORT"; else warn "Frontend niet op / — draai './run.sh prod' zodat frontend/build bestaat"; fi
else
  warn "Niets luistert op :$PORT → start met ./run.sh prod"
fi
[ -n "$LAN_IP" ] && ok "LAN-adres: $LAN_IP → open http://$LAN_IP:$PORT op laptop/telefoon in huis"
if systemctl list-unit-files 2>/dev/null | grep -q '^spark-backend.service'; then
  ok "systemd spark-backend: $(systemctl is-enabled spark-backend 2>/dev/null) / $(systemctl is-active spark-backend 2>/dev/null)"
else warn "Geen systemd-service — Spark start niet vanzelf na reboot (install.sh zonder --dev zet 'm)"; fi

# ---------- 6. Netwerk / van buiten ----------
if $NET; then
  head_ "Toegang van buiten (Ziggo poort open + HTTPS)"
  PUB_IP=$(curl -fs --max-time 5 https://api.ipify.org 2>/dev/null || echo "")
  if [ -n "$PUB_IP" ]; then
    ok "Publiek IP: $PUB_IP"
    echo "    → Kijk in je Ziggo-modem (192.168.178.1 → Geavanceerd → Status) wat het WAN-IP is."
    echo "      Is dat NIET $PUB_IP of begint het met 100.64–100.127 → CG-NAT: poort openzetten werkt dan niet (bel Ziggo voor 'publiek IPv4')."
  else fail "Geen internet vanaf de Odroid (curl api.ipify.org mislukt)"; fi
  if command -v caddy >/dev/null; then ok "caddy $(caddy version 2>/dev/null | cut -d' ' -f1) geïnstalleerd (HTTPS reverse-proxy)"; else
    warn "caddy ontbreekt — nodig voor HTTPS (microfoon werkt in de browser alleen via https)"
    $FIX && install_caddy
  fi
  if [ -f /etc/caddy/Caddyfile ] && grep -q "reverse_proxy" /etc/caddy/Caddyfile 2>/dev/null; then
    ok "/etc/caddy/Caddyfile verwijst naar: $(grep -oE '[a-z0-9.-]+\.(duckdns\.org|nl|com|net|org|dev)' /etc/caddy/Caddyfile | head -1)"
  else warn "Caddyfile nog niet ingesteld → zie deploy/Caddyfile.example + PORTABILITY.md 'Van buiten bereikbaar'"; fi
  for p in 80 443; do ss -ltn 2>/dev/null | grep -q ":$p " && ok "Poort $p luistert lokaal (caddy)" || warn "Poort $p luistert niet — caddy nog niet actief"; done
  if [ -f /etc/cron.d/duckdns ] || crontab -l 2>/dev/null | grep -q duckdns; then ok "DuckDNS-updater staat in cron"; else warn "Geen DuckDNS-updater → deploy/duckdns-update.sh (zodat je domein je wisselende Ziggo-IP volgt)"; fi
fi

# ---------- 7. Fix ----------
if $FIX; then
  head_ "Repareren"
  if [ ${#APT_MISSING[@]} -gt 0 ]; then
    fixing "apt install ${APT_MISSING[*]}"
    sudo apt-get update -qq && sudo apt-get install -y "${APT_MISSING[@]}" || fail "apt install mislukt"
  fi
  if ! $NODE_OK; then
    fixing "Node.js 20 via NodeSource"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs || fail "node install mislukt"
  fi
  command -v yarn >/dev/null || { fixing "yarn"; sudo npm install -g yarn || fail "yarn install mislukt"; }
  if [ "${VENV_MISSING:-false}" = true ] || [ "${VENV_BROKEN:-false}" = true ]; then
    fixing "backend venv + pip install -r requirements.txt (kan 10+ min duren op ARM)"
    ( cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt ) || fail "pip install mislukt — plak de laatste regels van de fout in de chat"
    ( cd backend && . .venv/bin/activate && pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ -q ) || warn "emergentintegrations niet geïnstalleerd (alleen nodig met EMERGENT_LLM_KEY)"
  fi
  if [ "${NM_MISSING:-false}" = true ]; then
    fixing "yarn install (frontend)"
    ( cd frontend && yarn install --frozen-lockfile ) || fail "yarn install mislukt"
  fi
  echo; echo "Fix klaar — draai ./doctor.sh nog eens om te controleren."
fi

# ---------- Samenvatting ----------
echo
echo -e "${BLUE}══ Samenvatting ══${NC}  ${GREEN}$OK ok${NC}  ${YELLOW}$WARN let op${NC}  ${RED}$FAIL fout${NC}"
if [ "$FAIL" -gt 0 ] && ! $FIX; then echo "Probeer: ./doctor.sh --fix   (installeert wat ontbreekt)"; fi
[ "$FAIL" -eq 0 ] && echo "Klaar om te starten: ./run.sh prod"
exit 0
