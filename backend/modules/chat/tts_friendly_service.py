"""
TTS-friendly service — voegt natuurlijke conversational tail toe aan korte
chat-antwoorden zodat Text-to-Speech soepeler klinkt.

v5_tts_pad_001 — Spark's korte antwoorden ('Ja.', 'Klaar.', 'Genoteerd!') voelen
abrupt in spraak. Deze laag voegt een rustige afsluiter toe zodat de stem
natuurlijk uitloopt zonder de betekenis te veranderen.

Heuristiek:
- Alleen padden als raw text < 40 chars EN geen vraagteken aan het eind EN
  geen markdown-blokken (geen **bold**, geen newlines, geen lijsten).
- Skip voor types die expliciet een knop/vraag tonen (wedervraag, w_question, helpetc.)
- Random milde afsluiter, varieert zodat het niet robotisch klinkt.
"""
import random
import re

# Conversational tails — kort, vriendelijk, niet inhoudelijk
_TAILS = [
    "Laat maar weten als je verder wilt.",
    "Vraag gerust door als er meer is.",
    "Ik blijf in de buurt.",
    "Zeg het maar als je iets wilt veranderen.",
    "Klaar voor je volgende vraag.",
    "Vertel het me als ik iets moet aanvullen.",
    "Geef een seintje als je verder gaat.",
]

# Response types die NOOIT padding krijgen (eigen UX-flow)
_SKIP_TYPES = {
    "wedervraag",
    "w_question",
    "homonym_disambiguation",
    "help_overview",
    "dnd_help",
    "kbv2_neighbor",
    "kbv2_classify_prompt",
    "agenda_proposal",
    "decomposition_question",
    "snap_question",
    "compositional",
    "card_factory_draft",
    "community_recap",
    "time",
    "identity",
    "credits_thanks",
}

# Markdown-tekens die op rich content wijzen
_MD_RE = re.compile(r"(\*\*|__|^[-•]\s|\n)", re.MULTILINE)


def maybe_pad_for_tts(response: dict) -> dict:
    """Wijzig response in-place: voeg TTS-tail toe als bericht kort & plat is.

    Mutates and returns the same dict for chain-style use.
    """
    if not isinstance(response, dict):
        return response
    msg = (response.get("message") or "").strip()
    if not msg:
        return response

    rtype = response.get("type") or ""
    if rtype in _SKIP_TYPES:
        return response

    # Skip als bericht eindigt op een vraag of meerdere zinnen heeft
    if msg.endswith("?"):
        return response

    # Skip als markdown of multi-line content
    if _MD_RE.search(msg):
        return response

    # Skip als bericht al lang genoeg is voor natuurlijke TTS-flow
    if len(msg) >= 40:
        return response

    # Pad met een natuurlijke tail (één spatie, geen extra newlines)
    tail = random.choice(_TAILS)
    response["message"] = f"{msg} {tail}"
    response["tts_padded"] = True
    return response
