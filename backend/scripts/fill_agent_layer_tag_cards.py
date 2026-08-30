"""Seed + fill 8 ontbrekende KB-kaarten uit de agent-layer tags.

Elke tag die ik in fill_agent_layer_cards.py gebruikte maar geen KB-kaart had,
krijgt een draft-kaart. Uitgangspunt Principe #8: elke losse string die
betekenis draagt hoort een agent en/of KB-kaart te hebben.

Idempotent via kb_service.add_to_inbox (dedupe over alle lades).
Draft = vertrouwen 0.5, needs_gpt_review=True.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402
from modules.kb_v2 import service as kb_service  # noqa: E402

INBOX = Path(__file__).parent.parent / "data" / "knowledge" / "v2" / "knowledge_inbox.json"

CARDS = {
    "principe-8": {
        "topic": "systeem",
        "tags": ["principe-8", "architectuur-principe", "subject-agent", "spark-architectuur", "roadmap", "meta"],
        "lagen": {
            "laag1": "Principe #8 (Subject-Agent Pattern) stelt: elke losse string, commando of module in Spark's codebase krijgt uiteindelijk een Agent-wrapper én een corresponderende KB-kaart.",
            "laag2": "Zonder dit principe blijven losse strings verspreid door de code (hardcoded intents, magic tags, modulenamen zonder uitleg) en kan Spark er niet zelf over praten. Met dit principe wordt elke betekenis-dragende bouwsteen introspectief.",
            "laag3": "Twee helften: (a) een dunne Agent-wrapper (bijv. task_agent, personal_agent, spark_pulse_agent) die de logica isoleert van de plek waar hij aangeroepen wordt, en (b) een KB-kaart met dezelfde naam die uitleg, herkomst, verbanden en footnote-metadata bevat. Zo kan Spark zowel doen ('voer task_agent.execute uit') als uitleggen ('een task_agent is…'). Loose strings die vandaag alleen als tag of magic-value bestaan, komen in de KB-inbox terecht via snap_agent.",
            "laag4": "Principe #8 is de brug tussen executie en zelfbewustzijn. Waar snap_agent al onbekende woorden vangt uit LLM-output, zorgt Principe #8 dat óók de eigen infrastructuur (modules, tags, concepten) op dezelfde manier gedocumenteerd wordt. Consequentie voor nieuwe code: introduceer nooit een tag zonder te checken of het begrip een kaart heeft, en introduceer geen nieuwe module zonder skeleton in /app/backend/modules/agents/ en corresponderende KB-kaart. Op termijn verdwijnt het onderscheid 'code' vs 'kennis' — beide worden dezelfde graaf.",
        },
        "ws5": {
            "wie": "Iedereen die aan Spark's codebase of KB werkt — E1, GPT en Willem zelf.",
            "wat": "Architectuur-principe: elke losse string krijgt een Agent-wrapper + KB-kaart.",
            "wanneer": "Bij elke nieuwe module, tag, magic-value of hardcoded intent.",
            "waar": "ROADMAP_CORE.md sectie Principe #8; concreet zichtbaar in /app/backend/modules/agents/ en /app/backend/data/knowledge/v2/.",
            "waarom": "Om Spark introspectief te maken over zijn eigen bouwstenen en om drift tussen code en documentatie te elimineren.",
            "hoe": "Nieuwe module → skeleton in modules/agents/ + KB-kaart via snap_agent.seed_agent_layer_cards. Nieuwe tag → check bestaan kaart, seed anders draft-kaart.",
        },
    },
    "spark-architectuur": {
        "topic": "systeem",
        "tags": ["spark-architectuur", "meta", "principe-8", "roadmap"],
        "lagen": {
            "laag1": "Spark-architectuur is de verzameling ontwerpkeuzes die Spark Core 2.0 tot een privacy-first, JSON-only, eco-container-gebaseerd systeem maken.",
            "laag2": "Kernpijlers: pure JSON-datastore (geen MongoDB/Postgres), eco-containers voor per-user data-isolatie, LLM-router met fallback, Knowledge Base v2 als geheugen, en de Subject-Agent-laag als executiebrug.",
            "laag3": "Elke laag heeft één taak: chat/ voor intent-matching, agents/ voor uitvoering, kb_v2/ voor geheugen, trade/ voor financiën, snap_agent voor auto-learning. Data blijft strikt lokaal in /app/backend/data/, gestructureerd per subsysteem. Frontend praat alleen via /api-prefix met FastAPI. Deze scheiding maakt Spark leesbaar, testbaar én volledig eigenaar-controleerbaar.",
            "laag4": "Spark-architectuur is bewust niet 'schaal-eerst' maar 'autonomie-eerst': de gebruiker moet zijn eigen data volledig kunnen inzien, exporteren en verhuizen zonder cloudafhankelijkheid. Principe #8 zorgt dat de architectuur zichzelf documenteert. Op termijn wordt elke architectuur-beslissing een KB-kaart, waardoor nieuwe agents (E1, GPT, Emmy) altijd de meest recente context zien zonder Willem's herhaling.",
        },
        "ws5": {
            "wie": "Willem als eigenaar; Spark Core 2.0 als systeem; alle contribuerende agents.",
            "wat": "Ontwerpkeuzes: JSON-only datastore, eco-containers, LLM-router, KB v2, Subject-Agent-laag.",
            "wanneer": "Continu — elke code-wijziging valt onder deze pijlers.",
            "waar": "/app/backend/ als geheel; gedocumenteerd in ROADMAP_CORE.md en per-module KB-kaarten.",
            "waarom": "Om privacy, autonomie, transparantie en zelfuitleg tegelijk te garanderen.",
            "hoe": "Elke nieuwe feature toetsen aan de vijf kernpijlers vóór implementatie.",
        },
    },
    "command_registry": {
        "topic": "systeem",
        "tags": ["command_registry", "capability", "registry", "spark-architectuur", "data-artefact"],
        "lagen": {
            "laag1": "command_registry.json is de master-lijst die intent-tags koppelt aan API-endpoints in Spark Core.",
            "laag2": "Elke entry beschrijft één capability: id, path, method, intent_tags, required_params, gradatie_min, behavior_class_hint en de source-functie die de call afhandelt.",
            "laag3": "Vandaag leest capability_handler_service deze registry direct; morgen delegeert task_agent naar dezelfde registry via resolve() + execute(). Zo krijgt Spark één plek om te leren welke acties bestaan, welke gradatie ze vereisen en waar de handler-code staat.",
            "laag4": "command_registry is een data-artefact volgens Principe #8: geen module maar een JSON-configbestand dat gelijkwaardig deel uitmaakt van de Spark-architectuur. Uitbreidingen (admin_only-flag, i18n-labels, i/o-schemas) volgen zonder codewijzigingen omdat consumers de registry per veld interpreteren.",
        },
        "ws5": {
            "wie": "capability_handler_service, task_agent, admin_command_agent — alle consumers van geregistreerde acties.",
            "wat": "JSON-registry met capability-metadata (path, tags, gradatie, source).",
            "wanneer": "Geladen bij elke resolve/execute-call; onderhouden bij het toevoegen van nieuwe capabilities.",
            "waar": "/app/backend/data/system/command_registry.json.",
            "waarom": "Om intent → endpoint mapping ontkoppeld te houden van handler-code, en om Spark één introspectiebron te geven.",
            "hoe": "Elke nieuwe capability krijgt één entry met alle verplichte velden en een corresponderende handler-functie.",
        },
    },
    "intent-uitvoering": {
        "topic": "systeem",
        "tags": ["intent-uitvoering", "workflow", "chat", "capability", "spark-architectuur"],
        "lagen": {
            "laag1": "Intent-uitvoering is de stap waarin een herkende gebruikers-intent daadwerkelijk een actie triggert (endpoint-call, data-mutatie, respons).",
            "laag2": "Onderscheiden van intent-matching (welke intent zit in dit bericht?) en compose (hoe formuleer ik het antwoord?). Uitvoering staat er tussenin en heeft haar eigen validatie, gradatie-check en audit.",
            "laag3": "In Spark Core wordt intent-uitvoering geleidelijk verhuisd van capability_handler_service naar task_agent, zodat matching en uitvoering ontkoppeld worden. Elke uitvoering doorloopt: (1) resolve → cmd_id, (2) gradatie-check, (3) params-validatie, (4) dispatch naar source-functie, (5) audit-log.",
            "laag4": "Intent-uitvoering is één van de drie chat-fasen (match → uitvoer → compose). Door dit als aparte laag te benoemen kan Spark straks per fase logs en metrics leveren, en kan het pulse-agent detecteren waar in de pipeline vertraging of fouten ontstaan.",
        },
        "ws5": {
            "wie": "task_agent (nieuwe route) en capability_handler_service (bestaande route) voeren intents uit.",
            "wat": "De middelste fase van chat-flow: van herkende intent naar concreet resultaat.",
            "wanneer": "Direct na intent-matching, vóór compose.",
            "waar": "/app/backend/modules/agents/task_agent.py en /app/backend/modules/chat/capability_handler_service.py.",
            "waarom": "Om matching, uitvoering en formulering apart testbaar en observeerbaar te maken.",
            "hoe": "Via resolve() → execute() met gradatie- en params-check en audit-log-entry.",
        },
    },
    "compose": {
        "topic": "systeem",
        "tags": ["compose", "chat", "antwoord-formulering", "spark-architectuur"],
        "lagen": {
            "laag1": "Compose is de fase waarin Spark uit ruwe data (uitvoerresultaat, persoonlijke context, KB-kaarten) een Nederlands antwoord vormt.",
            "laag2": "Compose gebruikt personal_agent voor context, LLM-router voor generatie en fallback-service voor deterministische zinnen wanneer geen LLM nodig of beschikbaar is.",
            "laag3": "In /app/backend/modules/chat/compose_routes.py + composer_helpers.py leeft de logica. Compose weet niets van intent-matching of uitvoering — hij krijgt een 'answer_intent' + payload en produceert de tekst. Zo blijft de laag agnostisch voor bron (chat, morning-brief, recap).",
            "laag4": "Compose is de laatste stap in de drie-fasen-pipeline (match → uitvoer → compose). Door persoonlijke context centraal via personal_agent te trekken, blijven antwoorden consistent qua toon en aanspreek-vorm. Toekomstige uitbreiding: compose-templates die de KB-cards zelf leesbaar reflecteren ('ik weet dat je gisteren met potje X bezig was').",
        },
        "ws5": {
            "wie": "compose_routes en composer_helpers als producers; personal_agent en LLM-router als toeleveranciers.",
            "wat": "De antwoord-formuleringsfase van elke chat-turn.",
            "wanneer": "Na uitvoering, vlak vóór het antwoord de user bereikt.",
            "waar": "/app/backend/modules/chat/compose_routes.py en composer_helpers.py.",
            "waarom": "Om antwoord-formulering ontkoppeld te houden van datalogica en per bron herbruikbaar te maken.",
            "hoe": "Door een 'answer_intent' + payload in te nemen en via templates + optionele LLM-call tekst te produceren.",
        },
    },
    "privacy_matrix": {
        "topic": "systeem",
        "tags": ["privacy_matrix", "privacy", "attente_spark", "data-artefact", "spark-architectuur"],
        "lagen": {
            "laag1": "privacy_matrix is een geplande JSON-config die per gebruikersveld (financiën, gezondheid, dagboek) een privacy-niveau vastlegt.",
            "laag2": "Onderdeel van Attente Spark Fase 2. Bepaalt of Spark een veld ongevraagd mag noemen, alleen op vraag, of nooit — per eco-container en per relatietype.",
            "laag3": "Nog niet gebouwd. Beoogde ligging: /app/backend/data/config/privacy_matrix.json. Consumers zijn personal_agent.get_privacy_flag(), compose-templates en het Ochtend-vraag-portaal. Structuur: { veld: { niveau: 'open|op_vraag|nooit', gedeeld_met: [rol] } }.",
            "laag4": "privacy_matrix is de expliciete uitdrukking van Spark's belofte: 'ik onthoud alles, maar ik zeg alleen wat jij toestaat'. Zonder deze matrix moet elke consumer zelf een defensieve default kiezen; met de matrix is er één bron-van-waarheid die de user zelf kan editen.",
        },
        "ws5": {
            "wie": "personal_agent, compose-templates, Ochtend-vraag-portaal als consumers; Willem als editor.",
            "wat": "JSON-matrix veld → privacy-niveau + gedeeld-met-rol.",
            "wanneer": "Consulted bij elke compose-call die persoonlijke velden aanraakt.",
            "waar": "/app/backend/data/config/privacy_matrix.json (nog te bouwen).",
            "waarom": "Om Spark's privacy-belofte expliciet, auditeerbaar en user-editbaar te maken.",
            "hoe": "Per veld een niveau kiezen; personal_agent leest en filtert velden vóór ze in compose belanden.",
        },
    },
    "self_awareness": {
        "topic": "systeem",
        "tags": ["self_awareness", "introspectie", "spark-architectuur", "principe-8", "meta"],
        "lagen": {
            "laag1": "Self-awareness in Spark betekent: het systeem kan feitelijk over de eigen infrastructuur praten (modules, KB-cards, health, drift) in plaats van alleen over de user.",
            "laag2": "Concreet mechanisme: elke module krijgt via Principe #8 een KB-kaart, en spark_pulse_agent verzamelt periodiek metrics zodat Spark 'weet hoe hij eraan toe is'.",
            "laag3": "Voorbeelden: Spark kan vertellen hoeveel kaarten in de inbox liggen, welke bots draaien, welke LLM-provider actief is, welke intents recent gemist zijn. Deze kennis komt niet uit een LLM-hallucinatie maar uit de KB en uit spark_pulse_agent.pulse().",
            "laag4": "Self-awareness is de tegenhanger van user-awareness (personal_agent). Beide zijn dunne wrappers volgens Principe #8. Zonder self-awareness blijft Spark blind voor eigen drift en achterstanden; mét self-awareness wordt hij een systeem dat onderhoudsbehoefte zelf kan signaleren en verwoorden.",
        },
        "ws5": {
            "wie": "Spark zelf; consumers zijn de Ochtend-portaal en admin-console.",
            "wat": "Het vermogen om over eigen modules, KB, bots en health te praten op feitelijke basis.",
            "wanneer": "Continu beschikbaar via pulse(); actief opgeroepen bij zelf-status-vragen en morning-brief.",
            "waar": "/app/backend/modules/agents/spark_pulse_agent.py + KB-cards van elke module.",
            "waarom": "Om drift vroeg te detecteren, om Sparks eigen uitleg-kwaliteit te verhogen en om Willem alleen te storen als nodig.",
            "hoe": "pulse() verzamelt metrics; narrate() maakt er een NL-zin van; snap_agent registreert nieuwe zelf-feiten in KB.",
        },
    },
    "observability": {
        "topic": "systeem",
        "tags": ["observability", "monitoring", "traced", "spark-architectuur", "roadmap"],
        "lagen": {
            "laag1": "Observability in Spark is het vermogen om achteraf te reconstrueren wat er gebeurde: welke intent, welke uitvoering, welke compose-templates, welke LLM-call.",
            "laag2": "Gepland via een @traced decorator (ROADMAP P2) die per functie start/end/duration/errors logt naar /app/backend/data/system/trace_log.jsonl.",
            "laag3": "Verschil met loggen: observability is gestructureerd (JSONL met correlation-id) zodat spark_pulse_agent en admin-dashboards er metrics uit kunnen aggregeren. Kan later gekoppeld worden aan health_score in pulse().",
            "laag4": "Observability is de meet-tak van self_awareness: waar self_awareness zegt 'ik weet dat ik draai', zegt observability 'ik weet hóé ik draaide'. Zonder deze laag blijft debuggen gokwerk; mét deze laag wordt elke chat-turn achteraf reconstrueerbaar zonder logfiles uit te pluizen.",
        },
        "ws5": {
            "wie": "Alle backend-modules worden geïnstrumenteerd; consumers zijn spark_pulse_agent en admin-dashboard.",
            "wat": "Gestructureerde trace-log per functie-aanroep (start/end/duration/errors, correlation-id).",
            "wanneer": "Actief bij elke geïnstrumenteerde call; zichtbaar in dashboard on-demand.",
            "waar": "@traced decorator (nog te bouwen); output naar /app/backend/data/system/trace_log.jsonl.",
            "waarom": "Om chat-turns achteraf reconstrueerbaar en Spark's health meetbaar te maken.",
            "hoe": "Decorator toevoegen aan kritieke functies; pulse aggregeert metrics per venster.",
        },
    },
}


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    # Stap 1: seed via kb_service (idempotent)
    seed_results = []
    for begrip in CARDS.keys():
        r = kb_service.add_to_inbox(begrip=begrip, source="spark_agent_layer_tag_seed", user_id="user-000")
        seed_results.append((begrip, r.get("existing"), (r.get("kaart") or {}).get("id"), r.get("lade")))

    # Stap 2: fill in-place
    data = load_json(INBOX, default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    updated = 0
    for k in kaarten:
        begrip = (k.get("begrip") or "").lower().strip()
        payload = CARDS.get(begrip)
        if not payload:
            continue
        lagen = k.setdefault("lagen", {"laag1": "", "laag2": "", "laag3": "", "laag4": ""})
        for lk, lv in payload["lagen"].items():
            if not lagen.get(lk):
                lagen[lk] = lv
        ws5 = k.setdefault("ws5", {})
        for wk, wv in payload["ws5"].items():
            if not ws5.get(wk):
                ws5[wk] = wv
        if not k.get("topic"):
            k["topic"] = payload["topic"]
        existing_tags = set(k.get("tags") or [])
        k["tags"] = list(existing_tags | set(payload["tags"]))
        fn = k.setdefault("footnote", {})
        fn["draft_filled_by"] = "e1_agent_layer_tag_fill"
        fn["draft_filled_at"] = now
        fn["needs_gpt_review"] = True
        fn["vertrouwen"] = 0.5
        if k.get("_inbox_reason") == "missing_laag1":
            k["_inbox_reason"] = "awaiting_gpt_review"
        updated += 1
    save_json(INBOX, data)

    print("=== SEED-resultaten ===")
    for begrip, existing, kid, lade in seed_results:
        status = "already-in-" + (lade or "inbox") if existing else "NEW"
        print(f"  {begrip:24s} → {kid}  ({status})")
    print(f"\nGevuld: {updated}/{len(CARDS)}")


if __name__ == "__main__":
    main()
