"""
v5_ijkpunt_001 — Schone start / ijkpunt voor Spark Core 2.0 (2026-05-23)

Doelen (uit Willem's verzoek):
1. Test-input opruimen (chat/logs/test-*, t.json, agenda-test-*)
2. Wallet ↔ ROAR balance synchroniseren (cijfers moeten kloppen)
3. Community test-spam opruimen (oude bot-test berichten met "test" content)
4. Schaduw-trader potjes verwijderen (Nick T / Gijs / Nick 4d81e2a4 / ghosts)
5. Winkelsysteem check: gift_requests opschonen (oude testgifts)
6. Potjes: terug naar werkelijk ingekochte balance (Bitvavo deposit €96.52 → 10 Spark + 10 Willem tokens @ €5.08)

Idempotent + maakt backup vóór wijzigen in /app/backend/data/_backups/ijkpunt_v5_1_<ts>/
"""
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("/app/backend/data")
BAK_DIR = DATA / "_backups" / f"ijkpunt_v5_1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Ankerwaarden
ECHTE_USERS_MET_TOKENS = {"user-000": 10, "user-001": 10}
TEST_USERS_TE_VERWIJDEREN_POTJES = {
    "user-574ac78e",  # Nick Teeuwen (schaduw)
    "user-a0ee2d7e",  # Gijs (schaduw)
    "user-4d81e2a4",  # Nick (dubbele)
    "user-1b492f19",  # ghost
    "user-bc76725e",  # ghost
}

stats = {"changes": []}


def backup(path: Path):
    if not path.exists():
        return
    rel = path.relative_to(DATA)
    dst = BAK_DIR / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dst)


def load(p: Path, default):
    if p.exists():
        return json.load(open(p))
    return default


def save(p: Path, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)


# ───────────────────────────────────────────────────────────────
# 1. Sync wallet/wallets.json met roar_balances.json
# ───────────────────────────────────────────────────────────────
roar_path = DATA / "roar/roar_balances.json"
wallets_path = DATA / "wallet/wallets.json"
user_wallets_path = DATA / "wallet/user_wallets.json"

backup(roar_path)
backup(wallets_path)
backup(user_wallets_path)

roar = load(roar_path, {})
balances = roar.get("balances", {})

# Forceer canonieke balances: Spark 10, Willem 10, rest weg uit balances
new_balances = dict(ECHTE_USERS_MET_TOKENS)
roar["balances"] = new_balances
save(roar_path, roar)
stats["changes"].append(f"roar_balances: gefilterd naar {new_balances}")

# Sync wallets.json
wallets = load(wallets_path, {"wallets": {}})
for uid in list(wallets.get("wallets", {}).keys()):
    w = wallets["wallets"][uid]
    w["tokens"] = new_balances.get(uid, 0)
    w["eur_balance"] = 0  # leeg per ijkpunt
save(wallets_path, wallets)
stats["changes"].append(f"wallets.json: token-velden gesynchroniseerd met roar_balances")

# Sync user_wallets.json (de andere wallet store)
uw = load(user_wallets_path, {"user_wallets": {}})
for uid, info in uw.get("user_wallets", {}).items():
    if isinstance(info, dict) and "wallet" in info:
        info["wallet"]["spark_tokens"] = new_balances.get(uid, 0)
        info["wallet"]["balance_eur"] = 0
        info["wallet"]["last_sync"] = datetime.now(timezone.utc).isoformat()
save(user_wallets_path, uw)
stats["changes"].append("user_wallets.json: spark_tokens + balance_eur gesynchroniseerd")

# ───────────────────────────────────────────────────────────────
# 2. Schaduw-trader potjes verwijderen
# ───────────────────────────────────────────────────────────────
pots_path = DATA / "financial/user_potjes.json"
backup(pots_path)
pots = load(pots_path, {"users": {}})
removed_users = []
for uid in list(pots.get("users", {}).keys()):
    if uid in TEST_USERS_TE_VERWIJDEREN_POTJES:
        del pots["users"][uid]
        removed_users.append(uid)
save(pots_path, pots)
stats["changes"].append(f"potjes verwijderd voor: {removed_users}")

# Ook bots_registry_state cleanup
reg_path = DATA / "trade/bots_registry_state.json"
backup(reg_path)
reg = load(reg_path, {"bots": []})
if isinstance(reg, dict) and "bots" in reg:
    before = len(reg["bots"])
    reg["bots"] = [b for b in reg["bots"] if b.get("user_id") not in TEST_USERS_TE_VERWIJDEREN_POTJES]
    save(reg_path, reg)
    stats["changes"].append(f"bots_registry: {before} → {len(reg['bots'])} (schaduw verwijderd)")

# registered_users.json
reg_u_path = DATA / "trade/registered_users.json"
backup(reg_u_path)
ru = load(reg_u_path, {})
if isinstance(ru, dict):
    for uid in TEST_USERS_TE_VERWIJDEREN_POTJES:
        if uid in ru:
            del ru[uid]
    save(reg_u_path, ru)

# ───────────────────────────────────────────────────────────────
# 3. Chat logs opruimen — test-prefix bestanden
# ───────────────────────────────────────────────────────────────
chat_logs = DATA / "chat/logs"
removed_logs = []
if chat_logs.is_dir():
    for f in chat_logs.iterdir():
        name = f.name
        if (
            name.startswith("test-")
            or name == "t.json"
            or name.startswith("agenda-test-")
            or name.startswith("user-testedge")
            or name.startswith("user-ca4d31b1")  # ghost
            or name.startswith("user-78f2b0d7")  # ghost
            or name.startswith("user-1b492f19")  # ghost
            or name.startswith("user-bc76725e")  # ghost
        ):
            backup(f)
            f.unlink()
            removed_logs.append(name)
stats["changes"].append(f"chat/logs/: {len(removed_logs)} test-bestanden verwijderd")

# ───────────────────────────────────────────────────────────────
# 4. Community messages opschonen — verwijder berichten met "test" inhoud
# ───────────────────────────────────────────────────────────────
comm_path = DATA / "community/messages.json"
backup(comm_path)
comm = load(comm_path, {"messages": []})
msgs = comm.get("messages", [])
before = len(msgs)
def is_test(m):
    txt = (m.get("text") or m.get("message") or "").lower()
    if "test" in txt and len(txt) < 40:
        return True
    # 'help' command echoes uit user-001 zelf-tests
    if txt.strip() in ("test", "test bericht", "testje", "test123"):
        return True
    return False

msgs = [m for m in msgs if not is_test(m)]
comm["messages"] = msgs
save(comm_path, comm)
stats["changes"].append(f"community/messages.json: {before} → {len(msgs)} berichten")

# ───────────────────────────────────────────────────────────────
# 5. Gift requests opschonen — verwijder oude testgifts (expired/rejected)
# ───────────────────────────────────────────────────────────────
gifts_path = DATA / "roar/gift_requests.json"
backup(gifts_path)
gifts = load(gifts_path, {"gifts": []})
before_g = len(gifts.get("gifts", []))
# Houd alleen pending of accepted-binnen-laatste-30-dagen
from datetime import timedelta
cutoff = datetime.now(timezone.utc) - timedelta(days=30)
def keep_gift(g):
    if g.get("status") == "pending":
        return True
    ts = g.get("accepted_at") or g.get("rejected_at") or g.get("created_at") or ""
    try:
        dt = datetime.fromisoformat(ts)
        return dt > cutoff
    except Exception:
        return False
gifts["gifts"] = [g for g in gifts.get("gifts", []) if keep_gift(g)]
save(gifts_path, gifts)
stats["changes"].append(f"gift_requests: {before_g} → {len(gifts['gifts'])}")

# ───────────────────────────────────────────────────────────────
# 6. Trade-feed opruimen
# ───────────────────────────────────────────────────────────────
tf_path = DATA / "chat/community/trade-feed.json"
backup(tf_path)
tf = load(tf_path, {"messages": []})
before_tf = len(tf.get("messages", []))
# Houd laatste 50
if "messages" in tf and len(tf["messages"]) > 50:
    tf["messages"] = tf["messages"][-50:]
save(tf_path, tf)
stats["changes"].append(f"trade-feed: {before_tf} → {len(tf.get('messages', []))}")

# ───────────────────────────────────────────────────────────────
# 7. Snapshot ijkpunt
# ───────────────────────────────────────────────────────────────
snapshot = {
    "ijkpunt_version": "v5.1",
    "ts": datetime.now(timezone.utc).isoformat(),
    "anchor": {
        "deposit_eur_total": 96.52,
        "tokens_issued": 20,
        "token_price_initial_eur": 5.08,
        "spark_user-000": {"tokens": 10, "potjes": 10, "capital_per_pot": 5.08, "totaal_eur": 50.80},
        "willem_user-001": {"tokens": 10, "potjes": 10, "capital_per_pot": 5.08, "totaal_eur": 50.80},
        "bron": "Bitvavo SEPA deposit dep-0001 + 10/10 mint",
    },
    "schaduw_users_potjes_verwijderd": list(TEST_USERS_TE_VERWIJDEREN_POTJES),
    "changes": stats["changes"],
    "backup_dir": str(BAK_DIR),
}
save(DATA / "system/ijkpunt_v5_1.json", snapshot)
print(json.dumps(snapshot, indent=2, ensure_ascii=False))
