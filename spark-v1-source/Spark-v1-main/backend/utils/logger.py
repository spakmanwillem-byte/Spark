import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

LOGS_DIR = Path(__file__).parent.parent / "data" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

class SparkLogger:
    @staticmethod
    def _write_log(filename: str, message: str):
        """Write to log file"""
        log_file = LOGS_DIR / filename
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    @staticmethod
    def log_new_user(naam: str, sleutelwoord: str, gradatie: int):
        """Log nieuwe gebruiker"""
        message = f"✅ {naam} ({sleutelwoord}) → Gradatie {gradatie}"
        SparkLogger._write_log("nieuwe_mensen.log", message)
    
    @staticmethod
    def log_deleted_user(naam: str, sleutelwoord: str, backup_file: str, stats: dict):
        """Log verwijderde gebruiker"""
        message = f"❌ {naam} ({sleutelwoord}) verwijderd\n"
        message += f"   └─ Backup: {backup_file}\n"
        message += f"   └─ Data: {stats.get('gesprekken', 0)} gesprekken, {stats.get('dagboek', 0)} dagboek entries"
        SparkLogger._write_log("verwijderde_mensen.log", message)
    
    @staticmethod
    def log_new_word(woord: str, betekenis: str, bron: Optional[str] = None):
        """Log nieuw geleerd woord"""
        message = f"📚 '{woord}' = {betekenis}"
        if bron:
            message += f"\n   Bron: {bron}"
        SparkLogger._write_log("nieuwe_woorden.log", message)
    
    @staticmethod
    def log_unknown_word(woord: str, context: str, user: str):
        """Log onbekend woord"""
        message = f"❓ '{woord}'\n"
        message += f"   Context: '{context}'\n"
        message += f"   User: {user}\n"
        message += f"   → Vraag Willem om uitleg"
        SparkLogger._write_log("onbekende_woorden.log", message)
    
    @staticmethod
    def log_gradatie_change(naam: str, sleutelwoord: str, old_gradatie: int, new_gradatie: int, reden: str, handmatig: bool = False):
        """Log gradatie wijziging"""
        icon = "📈" if new_gradatie < old_gradatie else "📉"
        type_str = "Handmatig door Willem" if handmatig else "Automatisch"
        message = f"{icon} {naam} ({sleutelwoord}): {old_gradatie} → {new_gradatie}\n"
        message += f"   Reden: {type_str} ({reden})"
        SparkLogger._write_log("gradatie_wijzigingen.log", message)
    
    @staticmethod
    def log_masterkey_attempt(naam: Optional[str], sleutelwoord: Optional[str], success: bool, ip: str = "localhost"):
        """Log masterkey toegang poging"""
        if success:
            message = f"✅ {naam} ({sleutelwoord}) - Masterkey 'SAMEN'\n"
            message += f"   IP: {ip}\n"
            message += f"   Admin functies actief"
        else:
            message = f"❌ {'Onbekend' if not naam else naam} - Masterkey poging gefaald\n"
            message += f"   IP: {ip}\n"
            message += f"   → Security alert!"
        SparkLogger._write_log("masterkey_toegang.log", message)
    
    @staticmethod
    def log_system_event(event: str):
        """Log systeem gebeurtenis"""
        SparkLogger._write_log("systeem_events.log", event)

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
