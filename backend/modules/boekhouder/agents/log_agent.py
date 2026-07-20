"""LogAgent — paper trail voor ALLE financiële events.

Elke mutatie krijgt: uuid + timestamp + hash_prev (immutable chain).
Storage: `data/boekhouder/logs/{topic}/{YYYY-MM}.jsonl` (append-only).

Topics: mint, gift, deposit, trade_close, reserve, drift_fix
Elke topic in eigen subfolder = "geagent per onderwerp" zoals Willem wilde.
"""
from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from .base_agent import BaseFinanceAgent, DATA

LOGS_DIR = DATA / "boekhouder" / "logs"


class LogAgent(BaseFinanceAgent):
    topic = "log_agent"

    def _month_file(self, topic: str) -> Path:
        now = datetime.now(timezone.utc)
        d = LOGS_DIR / topic
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{now.year}-{now.month:02d}.jsonl"

    def _last_hash(self, topic: str) -> str:
        fp = self._month_file(topic)
        if not fp.exists() or fp.stat().st_size == 0:
            return "GENESIS"
        with fp.open("rb") as f:
            f.seek(0, 2); size = f.tell()
            f.seek(max(0, size - 2048))
            tail = f.read().decode("utf-8", "ignore")
        last = tail.strip().split("\n")[-1] if tail.strip() else ""
        try:
            return json.loads(last).get("event_hash", "GENESIS")
        except Exception:
            return "GENESIS"

    def record(self, topic: str, event_type: str, actor: str,
               data: Dict[str, Any]) -> Dict[str, Any]:
        """Schrijf event weg met hash-chain naar `logs/{topic}/YYYY-MM.jsonl`."""
        event_id = str(uuid.uuid4())
        ts = datetime.now(timezone.utc).isoformat()
        prev = self._last_hash(topic)
        payload = {
            "event_id": event_id, "timestamp": ts, "topic": topic,
            "type": event_type, "actor": actor, "data": data, "hash_prev": prev,
        }
        chain_input = f"{prev}|{event_id}|{event_type}|{ts}|{json.dumps(data, sort_keys=True)}"
        payload["event_hash"] = hashlib.sha256(chain_input.encode()).hexdigest()[:16]
        fp = self._month_file(topic)
        with fp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload

    def lookup(self, topic: str = None, target_id: str = None,
               actor: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Zoek events. Loopt alle maand-bestanden af (nieuwste eerst)."""
        results: List[Dict[str, Any]] = []
        topics = [topic] if topic else [p.name for p in LOGS_DIR.iterdir() if p.is_dir()] if LOGS_DIR.exists() else []
        for t in topics:
            tdir = LOGS_DIR / t
            if not tdir.exists(): continue
            files = sorted(tdir.glob("*.jsonl"), reverse=True)
            for fp in files:
                for line in fp.read_text(encoding="utf-8").strip().split("\n")[::-1]:
                    if not line.strip(): continue
                    try:
                        ev = json.loads(line)
                    except Exception: continue
                    if target_id and target_id not in json.dumps(ev.get("data", {})): continue
                    if actor and ev.get("actor") != actor: continue
                    results.append(ev)
                    if len(results) >= limit: return results
        return results

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        """Overview van beschikbare log-topics + counts."""
        topics = {}
        if LOGS_DIR.exists():
            for tdir in LOGS_DIR.iterdir():
                if not tdir.is_dir(): continue
                count = 0
                for fp in tdir.glob("*.jsonl"):
                    with fp.open() as f: count += sum(1 for _ in f)
                topics[tdir.name] = count
        return {"topics": topics, "total_events": sum(topics.values())}
