# Spark Core 2.0 — Portability & Odroid Migratie

## Waarom deze doc?
De preview-omgeving (Emergent K8s) gebruikt hardcoded paden en supervisor. Voor migratie naar **Odroid** (of andere Linux hardware) heb je nodig:
1. Portable paden (geen `/app/backend/*` in code)
2. Non-supervisor start (`run.sh` in dev, systemd in prod)
3. Duidelijke `.env` scheiding
4. Ghost-key controle bij restore

Deze doc + `install.sh` + `run.sh` maakt dat mogelijk.

---

## Snelstart Odroid (bijgewerkt 20-10-2026, v14_spark_root_001)

```bash
# 1. Repo ophalen (GitHub "Save to GitHub" → clone of zip uitpakken)
git clone <jouw-repo> spark-core && cd spark-core

# 2. Installeren (Ubuntu 22.04 of 24.04, arm64/x86_64). Maakt venv, yarn install en kopieert .env.example → .env
./install.sh --dev

# 3. Sleutels invullen (minimaal ADMIN_PASSWORD en SPARK_MASTERKEY)
nano backend/.env

# 4. Starten — aanrader op Odroid: één poort, backend serveert de gebouwde frontend
./run.sh prod            # bouwt frontend (duurt een paar minuten op ARM) en start backend op :8001
# → open http://<odroid-ip>:8001 op je laptop/telefoon in hetzelfde netwerk

# Alternatief (dev): twee processen, hot-reload
./run.sh                 # backend :8001 + frontend dev-server :3000 (zet dan REACT_APP_BACKEND_URL in frontend/.env)
./run.sh stop
```

**Wat er vóór 20-10 misging op een verse machine**: `.env`-bestanden zitten niet in de GitHub-export (gitignored) en er was
geen `.env.example`; `install.sh` eiste `python3.11` (bestaat niet op Ubuntu 24.04); ~60 paden stonden hard op `/app/...`;
de dev-server opent geen browser op een headless Odroid. Nu: `.env.example` voor beide, python-autodetect, alle paden via
`modules/core/paths.py` (`SPARK_ROOT`, override met env), en `./run.sh prod` voor één poort.

**Logs bij problemen**: `./run.sh backend` in de voorgrond laat de Python-fout direct zien; stuur die regel(s) naar Spark.

## Portable paden (v8_odroid_portability_001)

**Probleem**: veel modules gebruikten `Path("/app/backend/data")` — werkte alleen in Emergent K8s.

**Oplossing**: env-var `SPARK_DATA_DIR` met fallback naar relatief pad:

```python
DATA = Path(os.environ.get("SPARK_DATA_DIR") or (Path(__file__).parent.parent.parent / "data"))
```

**Gefixt in deze sessie**:
- ✅ `modules/scheduler/__init__.py` — DATA path
- ⏳ Rest volgt in refactor-sessie (comments met `/app/backend/*` zijn onschuldig, alleen code-paths tellen)

**Zelf checken hoeveel hardcoded paden er nog zijn:**
```bash
grep -rn "Path(\"/app\|Path('/app" backend/modules --include="*.py" | grep -v "^Binary"
```

**Fix-pattern per file**:
```python
# VOOR
DATA = Path("/app/backend/data")

# NA (portable)
import os
DATA = Path(os.environ.get("SPARK_DATA_DIR") or (Path(__file__).parent.parent.parent / "data"))
```

---

## .env Config

### `backend/.env`
```env
MONGO_URL=                              # LEEG mag — Spark gebruikt alleen JSON
DB_NAME=spark_core                      # verplicht (framework-check)

# Bitvavo (crypto trading)
BITVAVO_KEY=
BITVAVO_SECRET=

# LLM providers (kies wat je gebruikt)
GROQ_API_KEY=
CEREBRAS_API_KEY=
EMERGENT_LLM_KEY=                       # Voor TTS/STT + optionele LLM

# Portable-pad override (optioneel — anders wordt fallback gebruikt)
SPARK_DATA_DIR=/opt/spark/backend/data
```

### `frontend/.env`
```env
REACT_APP_BACKEND_URL=http://192.168.1.50:8001    # Odroid LAN-IP
```

---

## Ghost-keys controle

**Probleem**: bij zip-restore van preview → Odroid kunnen er "ghost keys" achterblijven (user_id's die nergens meer bestaan, of blueprints die verwijzen naar files die er niet meer zijn).

**Check script** (voer uit na restore):
```bash
cd backend
python3 -c "
from pathlib import Path
import json

DATA = Path('data')
issues = []

# 1. User_potjes zonder user in users.json
users = {u['user_id']: u for u in (json.load(open(DATA/'system'/'users.json')).get('users', []))}
potjes = json.load(open(DATA/'trade'/'user_potjes.json'))
for uid in potjes.keys():
    if uid not in users and uid != 'user-000':
        issues.append(f'GHOST user_potjes: {uid}')

# 2. Blueprint verwijzingen
bp = json.load(open('modules/trade/blueprints/spark_trader.json'))
public_path = Path('data/trade/spark_trader_public.json')
if not public_path.exists():
    issues.append('MISSING: spark_trader_public.json')

# 3. KB index vs feitelijke lades
idx = json.load(open(DATA/'knowledge'/'v2'/'knowledge_index.json'))
for begrip, entry in list(idx.get('entries', {}).items())[:100]:
    if entry.get('lade') is None:
        # verwijst naar inbox — check of daar staat
        inbox = json.load(open(DATA/'knowledge'/'v2'/'inbox.json'))
        ids = {k['id'] for k in inbox.get('kaarten', [])}
        if entry.get('kaart_id') not in ids:
            issues.append(f'GHOST index entry: {begrip} → {entry.get(\"kaart_id\")}')

print(f'Issues: {len(issues)}')
for i in issues[:20]: print(f'  {i}')
"
```

---

## Zelfscan op de Odroid: `./doctor.sh`

Puur bash, werkt ook als install.sh half mislukt is.
```bash
./doctor.sh          # wat is er, wat ontbreekt, wat staat verkeerd (RAM, python, node, venv, .env, poort 8001)
./doctor.sh --fix    # installeert wat ontbreekt (apt, node, yarn, venv+pip, yarn install), vraagt sudo
./doctor.sh --net    # extra: publiek IP / CG-NAT-check, caddy, poort 80/443, DuckDNS
```
Loopt iets vast → plak de rode regels in de chat, of de staart van de log:
```bash
tail -40 logs/laatste_doctor.log      # idem: laatste_install.log, laatste_run.log
```
Elke run van install.sh / run.sh / doctor.sh schrijft automatisch een log in `logs/` (zonder kleurcodes, met regelnummer + commando bij een fout).

---

## Systemd (autostart na reboot)

`deploy/spark-backend.service` is een template; `install.sh` vult `__SPARK_ROOT__`/`__SPARK_USER__` in en zet 'm in `/etc/systemd/system/`.
Eén service volstaat: de backend serveert de gebouwde frontend (`./run.sh prod` eenmalig draaien zodat `frontend/build/` bestaat).
```bash
sudo systemctl start spark-backend
sudo journalctl -u spark-backend -f
```

---

## Van buiten bereikbaar (Ziggo poort open + HTTPS)

**Waarom HTTPS:** de browser laat de microfoon (STT/opnemen) alleen toe via `https://` of `localhost`. Via `http://<odroid-ip>:8001` werkt alles behalve de mic.

1. **Gratis domein**: maak op https://www.duckdns.org een subdomein (bv. `sparkwillem.duckdns.org`) en noteer je token.
2. **DuckDNS-updater** (Ziggo wisselt je IP af en toe):
   ```bash
   sudo cp deploy/duckdns-update.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/duckdns-update.sh
   printf 'DOMAIN=sparkwillem\nTOKEN=jouw-token\n' | sudo tee /etc/duckdns.conf
   echo '*/5 * * * * root /usr/local/bin/duckdns-update.sh' | sudo tee /etc/cron.d/duckdns
   ```
3. **Caddy** (HTTPS reverse-proxy, haalt zelf een certificaat): `./doctor.sh --net --fix` installeert 'm, daarna:
   ```bash
   sudo cp deploy/Caddyfile.example /etc/caddy/Caddyfile
   sudo nano /etc/caddy/Caddyfile      # JOUWNAAM.duckdns.org vervangen
   sudo systemctl reload caddy
   ```
4. **Ziggo-modem** (192.168.178.1 → Geavanceerd → Port forwarding): TCP **80** en **443** → LAN-IP van de Odroid (zie `./doctor.sh`). Geef de Odroid daar ook een vast IP (DHCP-reservering).
5. Open `https://sparkwillem.duckdns.org` — login met je Spark-account; poort 8001 zelf hoeft **niet** open.

**CG-NAT-check:** `./doctor.sh --net` toont je publieke IP. Als het WAN-IP in je modem daar niet mee overeenkomt (of met 100.64–100.127 begint) zit je achter CG-NAT en werkt port-forwarding niet → bel Ziggo voor een publiek IPv4-adres, of gebruik Tailscale/Cloudflare Tunnel.

**Beveiliging:** wat publiek staat, wordt gescand. Sterk `ADMIN_PASSWORD`/`SPARK_MASTERKEY`, `sudo apt install unattended-upgrades`, en overweeg `ufw allow 80,443/tcp && ufw enable` (ssh eerst toestaan!).

---

## Backup & Restore

### Backup vanaf preview
```bash
curl -X POST "$PREVIEW_URL/api/backup/create" -o spark_backup_$(date +%Y%m%d).zip
```

### Restore op Odroid
```bash
cd /opt/spark
unzip spark_backup_20260709.zip
./run.sh stop
# valideer via ghost-keys check (hierboven)
./run.sh
```

---

## Wat er NOG NIET portable is

**Bewust niet aangeraakt** in v8 (Willems keuze: focus op deployment, niet grote refactor):
- Docstring-referenties naar `/app/backend/...` in `core/tracing.py`, `user_archive/routes.py`, `backup/routes.py` — puur comments, geen executable paths
- Sommige tests in `/app/backend/tests/backtest_*.py` hebben absolute paden in output-directories → alleen relevant als je backtests draait

**Volgt in refactor-sessie** (P2):
- `trade/monitor.py` splitten (1700+ regels → core/alerts/reporter) + alle paden portable
- Frontend hardcoded ports check (`3000` in enkele plaatsen als fallback)

---

## Test Portability

Voer uit vóór migratie:
```bash
# 1. Simuleer andere data-dir
SPARK_DATA_DIR=/tmp/spark-test-data ./run.sh backend
# → moet /tmp/spark-test-data aanmaken en initialiseren zonder errors

# 2. Test cold-start zonder existing data
rm -rf backend/data && mkdir backend/data
./run.sh backend
# → moet clean-slate booten met defaults
```

---

## Support & vragen

Bij problemen: eerst `./doctor.sh`, dan `journalctl -u spark-backend -n 100` op de Odroid,
of run `./run.sh backend` in foreground om real-time logs te zien.
