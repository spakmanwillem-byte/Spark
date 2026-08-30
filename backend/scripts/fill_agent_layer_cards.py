"""Vul de 4 subject-agent KB-kaarten met initiële inhoud (draft).

Wijzigt in-place kaarten in knowledge_inbox.json op basis van ID.
Idempotent: laat velden staan als ze al gevuld zijn.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402

INBOX = Path(__file__).parent.parent / "data" / "knowledge" / "v2" / "knowledge_inbox.json"

CARDS = {
    "kbv2-04a9994f": {  # task_agent
        "begrip": "task_agent",
        "topic": "systeem",
        "tags": [
            "agent", "task_agent", "command_registry",
            "intent-uitvoering", "spark-architectuur", "principe-8",
        ],
        "lagen": {
            "laag1": "task_agent is de dunne brug tussen een herkende chat-intent en het bijbehorende endpoint in command_registry.json.",
            "laag2": "Waar vandaag intent-matching én uitvoering samen zaten in capability_handler_service, splitst task_agent die twee stappen: eerst resolve() (welk commando past bij deze intent-tags?), daarna execute() (met gradatie-check en audit-log).",
            "laag3": "task_agent leest command_registry.json als single-source-of-truth. resolve(intent_tags) scoort registry-entries op tag-overlap en geeft de beste match terug. execute(cmd_id, params, user_id) controleert de gradatie van de user, valideert required_params, dispatcht naar de aangewezen source-functie en schrijft een audit-regel. Zo kan elk kanaal (chat, dashboard-widget, admin-console) hetzelfde commando aanroepen zonder de matching-logica te dupliceren.",
            "laag4": "task_agent is de eerste concrete uitwerking van Principe #8 (Subject-Agent Pattern): elke losse capaciteit krijgt een agent-wrapper én een KB-kaart, zodat Spark introspectief kan uitleggen wélk commando bij welk intent hoort. Op langere termijn hangt hier ook een snap_agent-hook aan: onbekende cmd_id → skeleton in KB-inbox. Registry hot-reload volgt via mtime-check. Zonder task_agent blijft intent-uitvoering versplinterd; mét deze laag wordt het één plek voor scoring, gradatie-gate en audit — cruciaal voor Sparks zelfuitleg-vermogen.",
        },
        "ws5": {
            "wie": "Spark's chat-router, admin-console, dashboard-widgets — elk kanaal dat een geregistreerd commando wil uitvoeren.",
            "wat": "Een dunne wrapper met resolve() en execute() bovenop command_registry.json.",
            "wanneer": "Bij elke chat-turn waar een capability-intent gedetecteerd wordt, of bij UI-calls die een registered command triggeren.",
            "waar": "/app/backend/modules/agents/task_agent.py — leest /app/backend/data/system/command_registry.json.",
            "waarom": "Om intent-matching en uitvoering te scheiden zodat meerdere kanalen dezelfde logica hergebruiken, en zodat Spark één plek heeft om over 'welke acties ken ik?' te praten.",
            "hoe": "resolve(): tag-overlap-score met tie-break op laagste gradatie_min. execute(): gradatie-check + params-check + dispatch via entry.source + audit-log-entry.",
        },
    },
    "kbv2-3e8865f1": {  # admin_command_agent
        "begrip": "admin_command_agent",
        "topic": "systeem",
        "tags": [
            "agent", "admin_command_agent", "admin", "capability",
            "audit", "spark-architectuur", "principe-8",
        ],
        "lagen": {
            "laag1": "admin_command_agent is de wrapper die admin-only capability-commando's centraal gate-keeps en uitvoert.",
            "laag2": "Vandaag zit de admin-check verspreid: soms een require_admin-decorator op de route, soms een handmatige controle binnen de handler. Deze agent bundelt de check op één plek en biedt één entrypoint 'voer admin-commando X uit als user Y'.",
            "laag3": "admin_command_agent onderhoudt een whitelist van cmd_ids die admin-only zijn (subset van command_registry.json). execute_as_admin(cmd_id, user_id, params) voert twee checks uit — is de user admin-capable én staat het cmd_id op de whitelist — en delegeert dan naar task_agent.execute() met een audit-flag. Zware acties (reconcile-all, seed-full-KB, capable-toggle) krijgen later een dubbele bevestigingsstap.",
            "laag4": "Deze agent is de admin-tak van Principe #8 en respecteert de eco-container-grens: een admin in container A mag geen data in container B raken. Toekomstige uitbreidingen: 'admin_only=True'-veld direct op registry-entries (whitelist verdwijnt dan), gestructureerde audit-events ('admin_action'), en integratie met de UsersAdminPage-toggle. Zonder deze laag blijft admin-check gedupliceerd; met deze laag krijgt Spark één plek om aan Willem uit te leggen 'wat kan alleen een admin?'.",
        },
        "ws5": {
            "wie": "Alleen users met admin-capable-flag; consumer is de UsersAdminPage of interne maintenance-scripts.",
            "wat": "Wrapper met whitelist, admin-check en gecentraliseerde audit-log voor admin-only capabilities.",
            "wanneer": "Bij elke aanroep die een admin-only commando triggert (reconciles, seeds, toggles).",
            "waar": "/app/backend/modules/agents/admin_command_agent.py — samenwerkend met modules.auth.deps en task_agent.",
            "waarom": "Om admin-toegang consistent te gate-keepen, audit-trails te centraliseren en eco-container-integriteit te bewaken.",
            "hoe": "is_admin_command(cmd_id) checkt whitelist; execute_as_admin() valideert user + cmd, delegeert naar task_agent.execute() en schrijft een 'admin_action'-audit-entry.",
        },
    },
    "kbv2-18adeb37": {  # personal_agent
        "begrip": "personal_agent",
        "topic": "systeem",
        "tags": [
            "agent", "personal_agent", "context", "compose",
            "privacy_matrix", "spark-architectuur", "principe-8",
        ],
        "lagen": {
            "laag1": "personal_agent is de reader-agent die persoonlijke context (naam, gradatie, recente tags, actieve potjes) op één plek bundelt voor Spark's compose-laag.",
            "laag2": "Vandaag halen compose_routes, capability-handler en recap-service ieder afzonderlijk persoonlijke feiten op — met copy-paste als gevolg en per-route verschillende antwoorden op 'wat weet Spark van mij?'. personal_agent geeft één snapshot() terug die alle consumers hergebruiken.",
            "laag3": "snapshot(user_id, depth) kent drie diepte-niveaus: 'minimal' (alleen naam + gradatie), 'standard' (+ recente dagboek-tags), 'deep' (+ actieve potjes + laatste vragen + gemoeds-samenvatting). recent_topics() dedupliceert onderwerpen fuzzy (≥92) via snap_service, get_privacy_flag() honoreert straks de nog te bouwen privacy_matrix.json (Attente Spark Fase 2). Belangrijk: personal_agent is READ-only — schrijven gebeurt in personalia_extraction_service en dagboek-routes.",
            "laag4": "personal_agent is de tegenhanger van spark_pulse_agent: 'wat weet ik van Willem' versus 'wat weet ik van mezelf'. Beide zijn dunne wrappers conform Principe #8. Een cache met TTL 30s voorkomt dat één chat-turn met meerdere compose-aanroepen dezelfde dagboek-index tientallen keren leest. Zonder deze laag blijven persoonlijke antwoorden per route verschillen; mét deze laag bouwt Spark één samenhangend beeld van de gebruiker.",
        },
        "ws5": {
            "wie": "Spark's compose-laag, capability-handler en recap-service — alles wat persoonlijke context nodig heeft om een antwoord af te stemmen.",
            "wat": "Gestructureerde snapshot-dict met naam, gradatie, tags, potjes en gemoed — op verschillende diepte-niveaus.",
            "wanneer": "Bij elke compose-call waar de user personaliseerbare content krijgt (chat-antwoord, morning-brief, recap).",
            "waar": "/app/backend/modules/agents/personal_agent.py — leest personalia, dagboek-tags, user_potjes.json en chat-log.",
            "waarom": "Om persoonlijke context consistent, cachebaar en privacy-bewust op één plek te ontsluiten.",
            "hoe": "snapshot() laagsgewijs data laden per depth-niveau, met 30s TTL-cache per user_id en later privacy-matrix-check per veld.",
        },
    },
    "kbv2-45d1d661": {  # spark_pulse_agent
        "begrip": "spark_pulse_agent",
        "topic": "systeem",
        "tags": [
            "agent", "spark_pulse_agent", "self_awareness", "heartbeat",
            "observability", "spark-architectuur", "principe-8",
        ],
        "lagen": {
            "laag1": "spark_pulse_agent is Spark's zelfbewustzijn-agent: hij verzamelt periodiek een health-snapshot van de eigen infrastructuur en vertelt daarover in Sparks eigen stem.",
            "laag2": "Zonder deze laag weet Spark niet in real-time hoe het met hemzelf gaat (KB-inbox achterstand, bots-status, LLM-router-fallback, intent-miss-rate). pulse_agent bundelt die signalen en levert er een korte NL-samenvatting bij, bruikbaar voor het Ochtend-vraag-portaal en voor zelf-onderhoud.",
            "laag3": "pulse() verzamelt vier blokken: KB (inbox_count, cards_total, deprecated_hits_24h), trade (bots_running, last_reconcile, drift_detected), llm_router (active_provider, fallback_active), en chat (intent_miss_rate_1h, avg_response_ms). Uit die metrics komt een health_score (0-100). narrate() vertaalt de dict naar een Nederlandse zin zonder LLM-call (puur templating per health-bucket). should_alert() geeft True bij health_score < 60, drift, actieve fallback of inbox > 50. Een scheduler-hook draait pulse() elke 30 minuten.",
            "laag4": "spark_pulse_agent is de zelf-reflectie-tak van Principe #8 en het spiegelbeeld van personal_agent ('wat weet ik van mezelf' versus 'wat weet ik van Willem'). Bij drift plaatst hij automatisch een skeleton met tag 'self-repair' in de KB-inbox via snap_agent. Op termijn wordt de ochtendbriefing hierop gebouwd: elke ochtend één zin over hoe Spark er zelf voor staat — kort, feitelijk, in zijn eigen woordkeuze. Zonder deze laag blijft Spark blind voor eigen achterstanden; mét deze laag wordt hij een systeem dat naar zichzelf luistert.",
        },
        "ws5": {
            "wie": "Spark zelf, gescheduled door modules.scheduler; consumers zijn het ochtend-portaal en de admin-dashboard-widget.",
            "wat": "Health-snapshot-dict + Nederlandse narrator-zin + alert-signaal.",
            "wanneer": "Elke 30 minuten scheduled, of on-demand via het ochtend-portaal en admin-console.",
            "waar": "/app/backend/modules/agents/spark_pulse_agent.py — leest KB-index, trade/monitor, llm_router-state en chat_log.",
            "waarom": "Om Spark real-time zelf-inzicht te geven, drift vroeg te detecteren en Willem alleen te storen wanneer nodig.",
            "hoe": "pulse() verzamelt metrics, narrate() templatet een zin per health-bucket, should_alert() bepaalt of er een melding aan Willem hoort te gaan.",
        },
    },
}


def main() -> None:
    data = load_json(INBOX, default={"kaarten": []})
    kaarten = data.get("kaarten", [])
    now = datetime.now(timezone.utc).isoformat()
    updated = 0
    for k in kaarten:
        payload = CARDS.get(k.get("id"))
        if not payload:
            continue
        # Vul lagen alleen als leeg
        lagen = k.setdefault("lagen", {"laag1": "", "laag2": "", "laag3": "", "laag4": ""})
        for lk, lv in payload["lagen"].items():
            if not lagen.get(lk):
                lagen[lk] = lv
        # ws5
        ws5 = k.setdefault("ws5", {})
        for wk, wv in payload["ws5"].items():
            if not ws5.get(wk):
                ws5[wk] = wv
        # topic
        if not k.get("topic"):
            k["topic"] = payload["topic"]
        # tags: merge uniek
        existing_tags = set(k.get("tags") or [])
        merged_tags = list(existing_tags | set(payload["tags"]))
        k["tags"] = merged_tags
        # footnote: markeer als draft-fill door e1, GPT-review nodig
        fn = k.setdefault("footnote", {})
        fn["draft_filled_by"] = "e1_agent_layer_fill"
        fn["draft_filled_at"] = now
        fn["needs_gpt_review"] = True
        fn["vertrouwen"] = 0.5  # halfway — draft, wacht op GPT-verrijking
        # remove missing_laag1 reason (nu gevuld)
        if k.get("_inbox_reason") == "missing_laag1":
            k["_inbox_reason"] = "awaiting_gpt_review"
        updated += 1
    save_json(INBOX, data)
    print(f"updated {updated}/4 cards")


if __name__ == "__main__":
    main()
