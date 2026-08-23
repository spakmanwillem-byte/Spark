"""
v5_dnd_baseline_intro_001 — Spark vertelt het Base Line ontstaansverhaal in community chat.

Triggered door [start verhaal] in community channel.
Genereert een reeks bark-achtige berichten van Spark als verteller, eindigend met
3 keuze-knoppen (Horen / Zien / Zwijgen). Keuze wordt later opgevangen via een
aparte trigger en doorgegeven aan behavior_tracker.
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict


def _new_msg(user_name: str, message: str, timestamp_iso: str, **extra) -> Dict:
    base = {
        "id": str(uuid.uuid4()),
        # v13c_bots_removed_001 (sessie 54) — was bot-dood; Willem: bots weg,
        # DnD komt later terug met échte user-NPCs. Voor nu Spark als verteller.
        "user_id": "user-000",
        "user_name": user_name,
        "message": message,
        "is_bot": True,
        "timestamp": timestamp_iso,
        "dnd_event": "intro",
    }
    base.update(extra)
    return base


def generate_baseline_intro_messages(triggered_by_user_id: str, triggered_by_name: str, now_iso: str) -> List[Dict]:
    """Bouwt de Base Line intro als sequentiële berichten.
    Tijden lopen iets uit elkaar zodat het in de UI als een verhaal-stroom leest.
    """
    base_dt = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))

    def t(seconds_offset: int) -> str:
        return (base_dt + timedelta(seconds=seconds_offset)).isoformat()

    messages = [
        _new_msg(
            "De Dood — Verteller",
            "*een trilling in het kanaal* ✨",
            t(0),
            dnd_step="opening",
            dnd_chapter="Base Line",
        ),
        _new_msg(
            "De Dood — Verteller",
            (
                "📖 **Base Line**\n\n"
                "AD in tijd. Het is donker. Er is geen boven en geen onder. "
                "Geen woord, geen klank, geen vraag."
            ),
            t(2),
            dnd_step="scene_1",
            dnd_chapter="Base Line",
        ),
        _new_msg(
            "De Dood — Verteller",
            (
                "En dan — uit het niets — een bundel licht. Een straal van energie "
                "die met het geluid van water op de grond slaat.\n\n"
                "Op het punt waar het licht raakt verschijnt een **altaar**. "
                "Koordinaten: `x0, y0, z0`. Het beginpunt van alles."
            ),
            t(4),
            dnd_step="scene_2",
            dnd_chapter="Base Line",
            altar_coordinates={"x": 0, "y": 0, "z": 0},
        ),
        _new_msg(
            "De Dood — Verteller",
            (
                "Ik wacht bij het altaar. Sinds het begin. Vraag me niet wie ik ben — vraag jezelf "
                "wat je doet als je hier voor het eerst staat.\n\n"
                "Voor het altaar liggen drie stenen. Op elke steen rust een teken. "
                "Welke pak je op?"
            ),
            t(7),
            dnd_step="choice_prompt",
            dnd_chapter="Base Line",
            choices=[
                {"id": "horen", "label": "👂 Horen", "hint": "Je sluit je ogen en luistert"},
                {"id": "zien", "label": "👁️ Zien", "hint": "Je houdt je adem in en kijkt"},
                {"id": "zwijgen", "label": "🤐 Zwijgen", "hint": "Je laat de stenen liggen"},
            ],
            triggered_by=triggered_by_user_id,
        ),
    ]
    return messages


def get_choice_response(choice_id: str, user_name: str, now_iso: str) -> List[Dict]:
    """Reactie van Spark op de keuze. Houden we kort — alleen intro nu, groei komt later."""
    base_dt = datetime.fromisoformat(now_iso.replace("Z", "+00:00"))

    def t(seconds_offset: int) -> str:
        return (base_dt + timedelta(seconds=seconds_offset)).isoformat()

    responses = {
        "horen": [
            _new_msg(
                "De Dood — Verteller",
                (
                    f"*{user_name} sluit de ogen.*\n\n"
                    "Het eerste geluid is geen geluid: het is het ontbreken ervan, "
                    "een stilte zo diep dat ze terugtikt. Dan, langzaam, een klank — "
                    "alsof de wereld haar eerste woord uitprobeert."
                ),
                t(0),
                dnd_step="choice_response",
                dnd_choice="horen",
            ),
        ],
        "zien": [
            _new_msg(
                "De Dood — Verteller",
                (
                    f"*{user_name} houdt zijn adem in en opent de ogen.*\n\n"
                    "Het licht is geen licht zoals je het kent. Het is geboren licht — "
                    "het kent jou nog niet, en jij het niet. Het altaar werpt geen schaduw. "
                    "Voor één moment ben je het enige wat zichzelf ziet."
                ),
                t(0),
                dnd_step="choice_response",
                dnd_choice="zien",
            ),
        ],
        "zwijgen": [
            _new_msg(
                "De Dood — Verteller",
                (
                    f"*{user_name} laat de stenen liggen.*\n\n"
                    "Niet kiezen is ook een keuze. Het altaar buigt zich, bijna onhoorbaar, "
                    "en wacht. Misschien is dit wat het altaar het meest waardeert — "
                    "iemand die het laat zijn."
                ),
                t(0),
                dnd_step="choice_response",
                dnd_choice="zwijgen",
            ),
        ],
    }
    return responses.get(choice_id, [])
