#!/usr/bin/env bash
# Maakt backend/.venv met een Python die bij de pins past (3.12) en installeert requirements.txt
# zonder het Emergent-only pakket `emergentintegrations` (dat wordt apart, optioneel, geprobeerd).
# Gebruikt `uv` als dat er is (of installeert het): die haalt zelf Python 3.12 op voor arm64/x86_64,
# dus het maakt niet uit welke Python op het systeem staat (3.14 op Ubuntu 26.04 breekt de pins).
# Gebruik: bash deploy/setup_venv.sh <spark_root>
set -uo pipefail
ROOT="${1:?spark_root}"
cd "$ROOT/backend" || exit 1
EXTRA_IDX="https://d33sy5i8bnduwe.cloudfront.net/simple/"
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
REQ_LOCAL="$(mktemp /tmp/spark_req.XXXXXX)"
grep -v '^emergentintegrations' requirements.txt > "$REQ_LOCAL"

say() { echo -e "  \033[0;34m→\033[0m $*"; }

if ! command -v uv >/dev/null 2>&1; then
  say "uv installeren (snelle pip + beheerde Python)…"
  curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || true
fi

if command -v uv >/dev/null 2>&1; then
  say "uv $(uv --version | cut -d' ' -f2): venv met Python 3.12 (wordt gedownload als die er niet is)"
  rm -rf .venv
  uv venv --python 3.12 .venv || { echo "uv venv mislukt"; exit 1; }
  say "pakketten installeren (uv, 2-10 min)…"
  uv pip install --python .venv/bin/python -r "$REQ_LOCAL" || { echo "uv pip install mislukt"; exit 1; }
  uv pip install --python .venv/bin/python emergentintegrations --extra-index-url "$EXTRA_IDX" >/dev/null 2>&1 \
    && say "emergentintegrations geïnstalleerd (Universal Key bruikbaar als EMERGENT_LLM_KEY gezet is)" \
    || say "emergentintegrations niet beschikbaar → Spark draait in basis-modus (geen cloud-LLM/TTS/STT via Universal Key)"
else
  PY=""
  for c in python3.12 python3.11 python3.10 python3; do command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }; done
  [ -n "$PY" ] || { echo "Geen python3 gevonden"; exit 1; }
  PYV=$("$PY" -c 'import sys;print(f"{sys.version_info[0]}.{sys.version_info[1]}")')
  case "$PYV" in 3.1[0-2]) ;; *) echo "  ! Python $PYV: pins zijn getest op 3.10-3.12 — installeer python3.12 of laat uv toe (internet nodig)";; esac
  say "venv met $PY ($PYV)"
  [ -x .venv/bin/python ] || "$PY" -m venv .venv || { echo "venv mislukt"; exit 1; }
  . .venv/bin/activate
  pip install --upgrade pip -q
  pip install -r "$REQ_LOCAL" || { echo "pip install mislukt"; exit 1; }
  pip install emergentintegrations --extra-index-url "$EXTRA_IDX" -q 2>/dev/null \
    && say "emergentintegrations geïnstalleerd" \
    || say "emergentintegrations niet beschikbaar → basis-modus"
  deactivate
fi
rm -f "$REQ_LOCAL"
.venv/bin/python -c 'import fastapi, uvicorn, numpy, pandas; print("  ✓ venv ok:", __import__("sys").version.split()[0])'
