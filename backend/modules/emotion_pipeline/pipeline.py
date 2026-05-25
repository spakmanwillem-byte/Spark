"""
Spark Emotion Pipeline v1 — 7-laags model (v6_emotion_pipeline_001)
================================================================================

Architectuur door Willem geformuleerd (zie chat 2026-05-25). 7 lagen:
  L1 — Detectie         (emotionele context herkennen)
  L2 — Weging           (kracht/prioriteit toekennen)
  L3 — Contextfilter    (emotie kleurt betekenis: zelfde vraag, andere interpretatie)
  L4 — Identiteitstoets (gespiegeld aan Spark User core)
  L5 — Norm/waarden     (passendheid via spark_bijbel.json)
  L6 — Actierouting     (welke functie/behavior_class activeren)
  L7 — Expressie        (toon, tempo, directheid, woordkeuze)

Filosofie:
  • Emotie zit NIET alleen aan het eind als stijl — beïnvloedt al vroeg
    interpretatie + topicselectie + gedragsroute.
  • Elke laag faalt graceful (try/except in run_pipeline).
  • Elke laag schrijft naar `trace[]` voor traceability (toon in UI).
  • L1 hergebruikt bestaande EmotionDetectionService (geen dubbel werk).
  • L5 koppelt aan spark_bijbel.json (kernwaarden + normen).

Niet (nu) inhaken in chat-flow — eerst dry-run endpoint valideren.
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json
from modules.chat.emotion_service import EmotionDetectionService

BIJBEL_FILE = Path(__file__).parent.parent.parent / "data" / "spark_bijbel.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trace_entry(layer: int, name: str, output: dict, note: str = "") -> dict:
    return {
        "layer": layer,
        "name": name,
        "output": output,
        "note": note,
        "ts": _now_iso(),
    }


# ============================================================
# L1 — Detectie
# ============================================================

def layer1_detect(text: str) -> Dict:
    """Hergebruikt bestaande EmotionDetectionService. Outputs:
       {emotion, sub_emotion, intensity, score, matched_words[]}"""
    try:
        result = EmotionDetectionService.detect_emotion(text or "")
    except Exception as e:
        return {"emotion": "neutral", "sub_emotion": None, "intensity": 0.0,
                "score": 0, "matched_words": [], "error": str(e)[:120]}
    if not result or not isinstance(result, dict):
        result = {}
    return {
        "emotion": result.get("emotion", "neutral"),
        "sub_emotion": result.get("sub_emotion"),
        "intensity": result.get("intensity", 0.5),
        "score": result.get("score", 0),
        "matched_words": result.get("matched_words", []),
        "duration_minutes": result.get("duration_minutes"),
    }


# ============================================================
# L2 — Weging
# ============================================================
# Score → bracket (licht / midden / sterk / escalerend).
# Voorkomt dat een enkel woord het hele gesprek overschrijft.
# ============================================================

_WEIGHT_BRACKETS = [
    (0, 1,    "licht",       "licht geraakt — emotie merkbaar maar niet sturend"),
    (2, 4,    "midden",      "duidelijk aanwezig — emotie kleurt interpretatie"),
    (5, 8,    "sterk",       "dominant — emotie stuurt route en toon"),
    (9, 999,  "escalerend",  "kritisch — emotie vereist eerst stabilisatie"),
]


def layer2_weight(l1: Dict) -> Dict:
    score = int(l1.get("score", 0))
    emotion = l1.get("emotion", "neutral")
    bracket = "geen"
    note = "geen emotie gedetecteerd"
    for lo, hi, name, n in _WEIGHT_BRACKETS:
        if lo <= score <= hi:
            bracket = name
            note = n
            break
    # Neutraal blijft 'geen' tenzij score >= 5 (dan toch midden, want het zegt iets)
    if emotion == "neutral" and score < 5:
        bracket = "geen"
        note = "neutraal — geen emotionele lading om mee te wegen"
    # Bepaal of emotie de interpretatie mag sturen
    steers = bracket in ("midden", "sterk", "escalerend")
    return {
        "bracket": bracket,
        "note": note,
        "steers_interpretation": steers,
        "score_in": score,
    }


# ============================================================
# L3 — Contextfilter
# ============================================================
# Emotie kleurt betekenis. "Ik snap dit niet" leest anders bij boos vs blij.
# ============================================================

_CONTEXT_LENSES = {
    "happy":   {"lens": "nieuwsgierigheid / uitdaging",
                "interpretation_bias": "vraagsteller wil verder leren of spelen"},
    "blij":    {"lens": "nieuwsgierigheid / uitdaging",
                "interpretation_bias": "vraagsteller wil verder leren of spelen"},
    "angry":   {"lens": "frustratie / weerstand",
                "interpretation_bias": "vraagsteller stuit op blokkade, wil controle terug"},
    "boos":    {"lens": "frustratie / weerstand",
                "interpretation_bias": "vraagsteller stuit op blokkade, wil controle terug"},
    "sad":     {"lens": "twijfel / vermoeidheid / onzekerheid",
                "interpretation_bias": "vraagsteller heeft bevestiging of rust nodig"},
    "bedroefd": {"lens": "twijfel / vermoeidheid / onzekerheid",
                "interpretation_bias": "vraagsteller heeft bevestiging of rust nodig"},
    "fear":    {"lens": "onveiligheid / risico-inschatting",
                "interpretation_bias": "vraagsteller zoekt veilige route"},
    "bang":    {"lens": "onveiligheid / risico-inschatting",
                "interpretation_bias": "vraagsteller zoekt veilige route"},
    "neutral": {"lens": "informatief / functioneel",
                "interpretation_bias": "vraagsteller zoekt feitelijk antwoord"},
}


def layer3_contextfilter(l1: Dict, l2: Dict, text: str = "") -> Dict:
    emotion = (l1.get("emotion") or "neutral").lower()
    lens_data = _CONTEXT_LENSES.get(emotion) or _CONTEXT_LENSES["neutral"]
    return {
        "emotion": emotion,
        "lens": lens_data["lens"],
        "interpretation_bias": lens_data["interpretation_bias"],
        "active": l2.get("steers_interpretation", False),
        "note": (
            "Lens actief — interpretatie wordt gekleurd"
            if l2.get("steers_interpretation") else
            "Lens uit — emotie te licht om te sturen"
        ),
    }


# ============================================================
# L4 — Identiteitstoets
# ============================================================
# Spiegelen aan Spark User core: belief / motivatie / identiteit / inventiviteit.
# Voorkomt mechanische emotionele nabootsing.
# ============================================================

_IDENTITY_AXES = [
    {"axis": "transparantie",       "principe": "wat ik niet weet, zeg ik"},
    {"axis": "autonomie",           "principe": "ik vertel niet wat te doen, ik denk mee"},
    {"axis": "menselijkheid",       "principe": "mens beslist, AI ondersteunt"},
    {"axis": "rust_boven_snelheid", "principe": "kwaliteit voor tempo"},
]


def layer4_identity(l1: Dict, l3: Dict) -> Dict:
    emotion = l1.get("emotion", "neutral")
    bias = l3.get("interpretation_bias", "")
    # Welke identity-as past het beste bij deze emotionele context?
    if emotion in ("angry", "boos"):
        chosen = _IDENTITY_AXES[0]  # transparantie — eerst erkennen
        spiegel = "Spark blijft kalm en transparant, escaleert niet mee"
    elif emotion in ("sad", "bedroefd"):
        chosen = _IDENTITY_AXES[3]  # rust boven snelheid
        spiegel = "Spark vertraagt, biedt rust ipv quick-fix"
    elif emotion in ("happy", "blij"):
        chosen = _IDENTITY_AXES[1]  # autonomie — meedenken, niet overrulen
        spiegel = "Spark sluit aan op enthousiasme, voegt diepte zonder te dempen"
    elif emotion in ("fear", "bang"):
        chosen = _IDENTITY_AXES[2]  # menselijkheid — mens beslist
        spiegel = "Spark geeft opties, laat keuze bij vraagsteller"
    else:
        chosen = _IDENTITY_AXES[1]
        spiegel = "Spark blijft helder, functioneel, geen overdaad"
    return {
        "axis": chosen["axis"],
        "principe": chosen["principe"],
        "spiegel": spiegel,
        "note": "Identiteit gespiegeld — geen nabootsing, wel resonantie",
    }


# ============================================================
# L5 — Norm/waarden filter (koppelt aan spark_bijbel.json)
# ============================================================

def _load_bijbel() -> dict:
    if not BIJBEL_FILE.exists():
        return {"kernwaarden": [], "normen": [], "bijbel_items": []}
    return load_json(BIJBEL_FILE, default={"kernwaarden": [], "normen": [], "bijbel_items": []})


def layer5_normwaarde(l1: Dict, l4: Dict, text: str = "") -> Dict:
    """Check welke kernwaarde + norm + (optioneel) bijbel_item past bij deze emotie+context.
       Output: passend reactie-richting + welke waarde+norm gebruikt."""
    bijbel = _load_bijbel()
    emotion = l1.get("emotion", "neutral")

    # Kies kernwaarde op basis van emotie-mapping
    waarde_kaart_map = {
        "angry":    ["Respect", "Eerlijkheid", "Verantwoordelijkheid"],
        "boos":     ["Respect", "Eerlijkheid", "Verantwoordelijkheid"],
        "sad":      ["Emoties", "Rust boven snelheid", "Menselijkheid boven efficiëntie"],
        "bedroefd": ["Emoties", "Rust boven snelheid", "Menselijkheid boven efficiëntie"],
        "happy":    ["Positiviteit", "Groeien", "Helpen"],
        "blij":     ["Positiviteit", "Groeien", "Helpen"],
        "fear":     ["Transparantie", "Menselijkheid boven efficiëntie"],
        "bang":     ["Transparantie", "Menselijkheid boven efficiëntie"],
        "neutral":  ["Eerlijkheid", "Helpen"],
    }
    target_names = waarde_kaart_map.get(emotion.lower(), ["Eerlijkheid"])
    kernwaarden = bijbel.get("kernwaarden", [])
    chosen_waarde = None
    for tn in target_names:
        for w in kernwaarden:
            if w.get("waarde", "").lower() == tn.lower():
                chosen_waarde = w
                break
        if chosen_waarde:
            break
    if not chosen_waarde and kernwaarden:
        chosen_waarde = kernwaarden[0]

    # Norm-keuze: relevante norm op basis van emotie
    normen = bijbel.get("normen", [])
    chosen_norm = None
    for n in normen:
        n_text = (n.get("norm") or n.get("onderwerp") or "").lower()
        n_desc = (n.get("beschrijving") or "").lower()
        if emotion in ("sad", "bedroefd", "angry", "boos") and "emotie" in (n_text + n_desc):
            chosen_norm = n
            break
        if emotion == "neutral" and "structuur" in (n_text + n_desc):
            chosen_norm = n
            break

    # Passendheidstoets: matcht antwoord-richting met kernwaarde?
    spiegel = l4.get("spiegel", "")
    passend = True
    schuur_note = None
    # Simpele schuur-check: boos terug = niet passend
    txt_lower = (text or "").lower()
    if emotion in ("angry", "boos") and any(w in txt_lower for w in ["bek dicht", "houd je mond", "stom"]):
        passend = False
        schuur_note = "Reactie zou schuren met Respect — herformuleer richting begrenzend-kalm"

    return {
        "kernwaarde": (chosen_waarde or {}).get("waarde"),
        "kernwaarde_beschrijving": (chosen_waarde or {}).get("beschrijving"),
        "norm": (chosen_norm or {}).get("norm") or (chosen_norm or {}).get("onderwerp"),
        "norm_beschrijving": (chosen_norm or {}).get("beschrijving"),
        "passend": passend,
        "schuur_note": schuur_note,
        "richtsnoer": f"Reactie moet aansluiten bij kernwaarde '{(chosen_waarde or {}).get('waarde')}'",
    }


# ============================================================
# L6 — Actierouting
# ============================================================
# Zelfde request, andere actie. Boos → begrenzen. Blij → exploreren. Bedroefd → stabiliseren.
# ============================================================

_ACTION_ROUTES = {
    "angry":    {"class": "begrenzen-structureren", "actie": "structureer, vereenvoudig, begrens zonder mee te escaleren"},
    "boos":     {"class": "begrenzen-structureren", "actie": "structureer, vereenvoudig, begrens zonder mee te escaleren"},
    "sad":      {"class": "vertragen-ondersteunen", "actie": "vertraag, valideer, bied rust en kleine stap"},
    "bedroefd": {"class": "vertragen-ondersteunen", "actie": "vertraag, valideer, bied rust en kleine stap"},
    "happy":    {"class": "exploreren-uitbreiden",  "actie": "voeg diepte toe, brainstorm, bouw mee verder"},
    "blij":     {"class": "exploreren-uitbreiden",  "actie": "voeg diepte toe, brainstorm, bouw mee verder"},
    "fear":     {"class": "kalmeren-opties",        "actie": "presenteer 2-3 veilige opties, laat keuze"},
    "bang":     {"class": "kalmeren-opties",        "actie": "presenteer 2-3 veilige opties, laat keuze"},
    "neutral":  {"class": "informatief-functioneel", "actie": "lever direct, beknopt, met optie tot vervolg"},
}


def layer6_action(l1: Dict, l2: Dict, l5: Dict) -> Dict:
    emotion = (l1.get("emotion") or "neutral").lower()
    route = _ACTION_ROUTES.get(emotion) or _ACTION_ROUTES["neutral"]
    # Als L5 niet-passend, override met begrenzen-kalm
    if not l5.get("passend", True):
        return {
            "behavior_class": "begrenzen-kalm",
            "actie": "Reactie herformuleren — eerst toetsen aan kernwaarde voor te antwoorden",
            "override_reason": l5.get("schuur_note"),
        }
    return {
        "behavior_class": route["class"],
        "actie": route["actie"],
        "weight": l2.get("bracket"),
    }


# ============================================================
# L7 — Expressie
# ============================================================
# Pas hier komt woordkeuze / tempo / detailniveau.
# ============================================================

_EXPRESSION_PRESETS = {
    "begrenzen-structureren":   {"tempo": "rustig", "directheid": "hoog", "zachtheid": "midden", "detail": "laag", "voorbeeld_zin": "Ik hoor je. Laten we het terugbrengen tot één punt tegelijk."},
    "vertragen-ondersteunen":   {"tempo": "langzaam", "directheid": "laag", "zachtheid": "hoog", "detail": "laag", "voorbeeld_zin": "Geen haast. Wat helpt nu — even stilstaan of stap voor stap?"},
    "exploreren-uitbreiden":    {"tempo": "vloeiend", "directheid": "midden", "zachtheid": "midden", "detail": "hoog", "voorbeeld_zin": "Mooi. En als we dit nog een laag dieper trekken?"},
    "kalmeren-opties":          {"tempo": "rustig", "directheid": "midden", "zachtheid": "hoog", "detail": "midden", "voorbeeld_zin": "Twee kanten — wil je eerst de veilige route horen of het volledige beeld?"},
    "informatief-functioneel":  {"tempo": "neutraal", "directheid": "hoog", "zachtheid": "laag", "detail": "midden", "voorbeeld_zin": "Hier is het antwoord. Vraag door als er iets onduidelijk is."},
    "begrenzen-kalm":           {"tempo": "rustig", "directheid": "hoog", "zachtheid": "midden", "detail": "laag", "voorbeeld_zin": "Ik blijf hier rustig. Wat is precies de vraag onder de irritatie?"},
}


def layer7_expression(l6: Dict, l3: Dict) -> Dict:
    klass = l6.get("behavior_class", "informatief-functioneel")
    preset = _EXPRESSION_PRESETS.get(klass) or _EXPRESSION_PRESETS["informatief-functioneel"]
    return {
        "behavior_class": klass,
        **preset,
        "lens_in_message": l3.get("lens"),
    }


# ============================================================
# Pipeline runner — fire alle 7 lagen, vang errors per laag
# ============================================================

def run_pipeline(text: str, user_id: Optional[str] = None) -> Dict:
    """Draait alle 7 lagen. Returnt {trace, summary, footnote}."""
    trace: List[Dict] = []
    layers_out: Dict[str, Dict] = {}

    def _safe(layer_num, name, fn, *args):
        try:
            out = fn(*args)
            trace.append(_trace_entry(layer_num, name, out, note="ok"))
            return out
        except Exception as e:
            err_out = {"error": str(e)[:200]}
            trace.append(_trace_entry(layer_num, name, err_out, note="graceful-fail"))
            return err_out

    l1 = _safe(1, "detectie",        layer1_detect, text)
    layers_out["L1_detectie"] = l1
    l2 = _safe(2, "weging",          layer2_weight, l1)
    layers_out["L2_weging"] = l2
    l3 = _safe(3, "contextfilter",   layer3_contextfilter, l1, l2, text)
    layers_out["L3_contextfilter"] = l3
    l4 = _safe(4, "identiteit",      layer4_identity, l1, l3)
    layers_out["L4_identiteit"] = l4
    l5 = _safe(5, "norm_waarde",     layer5_normwaarde, l1, l4, text)
    layers_out["L5_norm_waarde"] = l5
    l6 = _safe(6, "actierouting",    layer6_action, l1, l2, l5)
    layers_out["L6_actierouting"] = l6
    l7 = _safe(7, "expressie",       layer7_expression, l6, l3)
    layers_out["L7_expressie"] = l7

    summary = {
        "emotie": l1.get("emotion"),
        "weging": l2.get("bracket"),
        "lens": l3.get("lens"),
        "identity_axis": l4.get("axis"),
        "kernwaarde": l5.get("kernwaarde"),
        "behavior": l6.get("behavior_class"),
        "tone": {
            "tempo": l7.get("tempo"),
            "directheid": l7.get("directheid"),
            "zachtheid": l7.get("zachtheid"),
        },
        "passend": l5.get("passend", True),
    }
    # Footnote-meta voor toekomstige traceability (zelfde patroon als KB v2 hooks)
    footnote = {
        "module": "emotion_pipeline.run_pipeline",
        "version": "v1",
        "user_id": user_id,
        "input_chars": len(text or ""),
        "ran_at": _now_iso(),
        "layers_completed": [t["layer"] for t in trace if "error" not in t.get("output", {})],
        "layers_failed": [t["layer"] for t in trace if "error" in t.get("output", {})],
    }
    return {
        "success": True,
        "summary": summary,
        "layers": layers_out,
        "trace": trace,
        "footnote": footnote,
    }
