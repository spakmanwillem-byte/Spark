import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  Map, CheckCircle, Clock, Circle, ChevronRight, ChevronDown,
  Rocket, Target, Flag, Star, Zap, Brain, Shield, Globe,
  Package, MessageSquare, Coins, Users, BarChart3, Layers,
  BookOpen, StickyNote, BookHeart, Award, Wallet, Trophy,
  Settings, Puzzle, Calendar, Home, TrendingUp, Link2, Sparkles,
  Lightbulb,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const phases = [
  {
    id: 'phase-spark-brain',
    title: '🧠 Spark\'s brein — wat er al draait (inventarisatie)',
    status: 'active',
    color: '#8b5cf6',
    icon: BookOpen,
    period: 'productie v0.6.6',
    items: [
      // ==== NLP & taal-laag (chat services) ====
      { title: '📝 NLP Snap-service — woord-similarity + auto-snap-kaarten (geen spaCy)', status: 'done', anchor: 'svc-snap', note: 'chat/snap_service.py — analyseert onbekende woorden, maakt snap-suggestions, grant XP bij auto-snap' },
      { title: '🎭 Emotion-service hybride — laag 1/2/3 detectie + anti-misbruik (max 3× woord)', status: 'done', anchor: 'svc-emotion', note: 'chat/emotion_service.py — detecteert emotie uit tekst, persistent in /data/emotions/ (7 records prod)' },
      { title: '🔍 Shadow Observer — stille gedragsanalyse (63 observaties in prod)', status: 'done', anchor: 'svc-shadow', note: 'chat/shadow_observer.py — Spark monitort zichzelf, leerresultaten in /data/shadow/' },
      { title: '🌐 Compositional reasoning — samengestelde concepten uit bestaande kaarten', status: 'done', anchor: 'svc-composit', note: 'chat/compositional_service.py — leidt nieuwe begrippen af door bestaande te combineren' },
      { title: '🧭 Wedervraag service (5W+H multi-turn verrijking)', status: 'done', anchor: 'svc-weder', note: 'chat/wedervraag_service.py — start in Conversatie 2.0 sessie afgekapt tot max 1× per 4 interacties' },
      { title: '🎯 Smart intents — high-value chat-routes (geen blind keyword match)', status: 'done', anchor: 'svc-intents', note: 'chat/smart_intents_service.py — herkent o.a. financiële/relatie/tijd vragen' },
      { title: '🗣️ Action intents — Spark voert app-commando\'s uit vanuit chat', status: 'done', anchor: 'svc-actions', note: 'chat/action_intents_service.py — "open trader", "ga naar agenda" etc.' },
      { title: '📚 Bijbel-lookup — Spark\'s eigen waarden/normen referentie', status: 'done', anchor: 'svc-bijbel', note: 'chat/bijbel_lookup_service.py + spark_bijbel.json — Spark consulteert eigen ethische bron' },
      { title: '🎨 Scan service — KB doorlopen en nieuwe onderwerpen flaggen', status: 'done', anchor: 'svc-scan' },
      { title: '🪞 Identity intent — Spark beantwoordt vragen over zichzelf', status: 'done', anchor: 'svc-identity', note: 'chat/identity_intent_service.py — "wie ben jij?", "wat kun je?"' },
      { title: '💚 Self-state service — Spark heeft eigen "hoe gaat het" gevoel', status: 'done', anchor: 'svc-self-state', note: 'chat/self_state_service.py — bewustzijn-laag voor reflectievragen' },
      { title: '👤 Relation extraction — auto-detect relaties uit gewoon gesprek', status: 'done', anchor: 'svc-relation', note: 'chat/relation_extraction_service.py + /data/persons/ (15 in prod)' },
      { title: '⏰ Time intent + user-timezone awareness', status: 'done', anchor: 'svc-time', note: 'chat/time_intent_service.py + user_time_service.py' },
      { title: '🎲 Chat recap — "wat hebben we gisteren besproken?"', status: 'done', anchor: 'svc-recap', note: 'chat/chat_recap_service.py + chat archief per dag' },
      { title: '🃏 Card-fill session — admin modus om door onbeantwoorde KB-kaarten te lopen', status: 'done', anchor: 'svc-cards' },
      { title: '🔥 XP-service — gamification grants bij snap-creatie / KB-actie', status: 'done', anchor: 'svc-xp' },
      { title: '📜 Spontaneous W-field extraction — Spark merkt antwoorden op WS5 in vrije zinnen op', status: 'done', anchor: 'svc-spontaneous-w' },
      { title: '🛡️ Legal intent — privacy / cookies / voorwaarden auto-route', status: 'done', anchor: 'svc-legal' },
      { title: '📄 Personal docs — testament / survivalgids generiek slot', status: 'done', anchor: 'svc-personal-docs' },
      // ==== Productie-data systemen ====
      { title: '🕸️ Knowledge Graph — 36.355 edges live in productie (9MB)', status: 'done', anchor: 'data-graph' },
      { title: '📖 Knowledge Base — 5.402 kaarten (86MB) waarvan ~58% ingevuld', status: 'done', anchor: 'data-kb' },
      { title: '💬 Community chat — 340 berichten live archief', status: 'done', anchor: 'data-community' },
      { title: '🎩 Personality data per bot (17 records — triggers + responses)', status: 'done', anchor: 'data-personality' },
      { title: '🪙 ROAR token state + 19 tokens uitgegeven, 999.980 in treasury', status: 'done', anchor: 'data-roar' },
      { title: '📒 Wallet history (1.1MB — alle transacties + reset-logs)', status: 'done', anchor: 'data-wallet' },
      // ==== Half-af / inactief ====
      { title: '🔔 Notifications systeem (datafolder bestaat, UI-laag in opbouw)', status: 'planned', anchor: 'mod-notif', note: '/data/notifications/ is leeg, code-pad ontbreekt nog' },
      { title: '🧾 Accounting (Moneybird bridge concept — 2 records, niet actief)', status: 'planned', anchor: 'mod-accounting', note: 'Stub aanwezig, geen sync naar Moneybird' },
      { title: '🚨 Urgent module (leeg, gedefinieerd maar niet gebruikt)', status: 'planned', anchor: 'mod-urgent' },
      { title: '🗣️ Voice module (folder bestaat, STT/TTS pending integration_playbook)', status: 'done', anchor: 'mod-voice', note: '✅ Whisper STT live via Emergent LLM Key in kb_v2/media_routes.py — voice→tekst werkt in kennis-kaarten. TTS-stem-keuze per bot opgeslagen in bot.settings.tts_voice (audio-uitspeel volgt later).' },
      { title: '🎤 Triggers — 12 keyword triggers actief, uitbreidbaar via NLP-tags', status: 'done', anchor: 'mod-triggers' },
      // v6_brainfart_001 — Notities van De Willem 25-mei
      // ==== v6 — gedaan in sessies 25 mei 2026 ====
      { title: '✅ KB v2 — 5 hooks landed (vocab/depth-router/verbanden/dnd-link/voice-snippet) + backfill 5318 kaarten', status: 'done', anchor: 'v6-kbv2-hooks', note: 'v6_kbv2_hooks_landing_001 — alle 5 P1-hooks live. Footnote.hooks_fired[] trail in elke kaart. 2244 kaarten met verbanden (96-99% coverage).' },
      { title: '✅ KB v2 unify CardDetail ↔ NewCardInline + topic-duplicate-check', status: 'done', anchor: 'v6-kbv2-unify', note: 'v6_kbv2_unify_001 — Gedeelde CardFormFields. Dup-check via knowledge_index met "Open bestaande →" knop. Compleetheid-badge over 8 velden.' },
      { title: '✅ Spark Identity v0.1 → v2.0 + Disclaimer-laag (4 kaders)', status: 'done', anchor: 'v6-identity-disclaimer', note: 'v6_identity_001 — Doel/Persoonlijkheid/Spark-over-zichzelf herschreven. Empathisch/Positief/Nieuwsgierig WEG. GET /api/spark/disclaimer + DisclaimerCard UI.' },
      { title: '✅ 7-laags Emotie Pipeline (Detectie → Weging → Contextfilter → Identiteit → Norm → Actie → Expressie)', status: 'done', anchor: 'v6-emotion-pipeline', note: 'v6_emotion_pipeline_001 — Module met 7 lagen + dry-run endpoint + Spark Brain UI tab. v6_emotion_pipeline_shadow_001: nu LIVE-shadow in chat-flow (parallel naast smart_intents, naar /data/emotions/pipeline_shadow/).' },
      { title: '✅ Capabilities 3 placeholders → live handlers (gesprek_lezen / toon_afbeelding / speel_geluid)', status: 'done', anchor: 'v6-cap-handlers', note: 'v6_capabilities_handlers_001 — 12/12 capabilities nu LIVE in capability_handler_service. Spark "handen" beide kanten gelinked.' },
      { title: '✅ Spark Brain delete-bug fix (window.confirm faalt in iframe)', status: 'done', anchor: 'v6-brain-delete', note: 'v6_brain_delete_001 — Custom React confirm-modal + sonner toast feedback. Geen stille fails meer.' },
      { title: '✅ KB v2 DELETE endpoint + UI knop (onbruikbare kaarten)', status: 'done', anchor: 'v6-kbv2-delete', note: 'v6_kbv2_delete_001 — POST /api/kb/v2/delete + Trash-knop in CardDetail + reden-veld voor traceability + log naar spark_logger.' },
      { title: '✅ A/B Diff-view: huidige route vs pipeline-advies', status: 'done', anchor: 'v6-ab-diff', note: 'v6_emotion_pipeline_ab_001 — Per chat-call vergelijking. Stats: match/mismatch/potential + match-ratio. UI in Spark Brain → Emotie Pipeline. Eerste data toont 60% match — boos/verdrietig vallen nu in knowledge-route ipv pipeline begrenzen/vertragen. Fundering vóór live route-override.' },
      { title: '✅ Bidirectionele Command-Registry MVP — fundering donderdag', status: 'done', anchor: 'v6-cmd-registry', note: 'v6_command_registry_001 — 27 commands met intent_tags + gradatie_min + behavior_class_hint. Extract → match → top-N. Skill-discovery embryo (intent_log.jsonl + /candidates endpoint detecteert 3+ keer voorkomende patterns). Hooks in chat-flow. 6 endpoints. Donderdag UI + LLM-upgrade.' },
      { title: '✅ Kernwaarden cleanup (11 → 9): Groeien + Emoties weg, sync productie', status: 'done', anchor: 'v6-kw-cleanup' },
      { title: '✅ Shadow widget — pipeline draait mee in chat (zichtbaar in Spark Brain)', status: 'done', anchor: 'v6-shadow-widget', note: 'v6_shadow_widget_001 — Live activity-blok met stats + laatste 15 chat-runs.' },
      // ==== Sessie 14 — 28 mei 2026 (P1-P4 batch) ====
      { title: '✅ Winkelstraat frontend + container-isolatie (multi-tenant shop architecture)', status: 'done', anchor: 'v6-winkelstraat-ui', note: 'v6_winkelstraat_frontend_001 — 3e hoofd-tab in WinkelPage.js (WinkelstraatTab.js). Voorwaarden-modal (v1, 2% commissie), create/edit/close-flow. Admin (gradatie ≤ 2) bypass van min-gradatie 4. Auto shop-container in /data/shops/{shop_id}/ met _meta.json bij elke nieuwe winkel. Founder-shop Roadkillshop krijgt FOUNDER-badge.' },
      { title: '✅ Boekhouding reconciliatie — €71.60 in balans', status: 'done', anchor: 'v6-kasboek-reconcile', note: 'v6_kasboek_reconcile_001 — GET /api/spark/kasboek/reconcile vergelijkt ROAR-tx ↔ kasboek ↔ wallet. POST /reconcile/fix boekt unbooked retroactief. Bevestigd: Willem anchor_mint €50.80 ontbrak → na fix gift_in=€71.60 (matcht Willem €50.80 + Gijs €20.80), in_balance=true.' },
      { title: '✅ Potje 1:1 regel — 1 token = 1 potje (alleen Spark heeft base 10 potjes)', status: 'done', anchor: 'v6-potje-per-token', note: 'v6_potje_per_token_001 — sync_potjes_to_tokens() + trim_potjes_to_tokens() + hooks in buy_tokens + gift accept. Admin bulk POST /api/trade/potjes/sync-all-to-tokens. Resultaat: Gijs 10→2 potjes, Marieke 0=0, Spark blijft op 10 base.' },
      { title: '✅ Spark hands intent-router 5/5 capability-routes actief in chat', status: 'done', anchor: 'v6-cap-handlers-002', note: 'v6_capabilities_handlers_003 — 4 nieuwe entries in spark_capabilities.json (kennis_inbox_status, bots_status, audit_health, agenda_vandaag) + 1 al bestaande (spark_saldo_check). Chat-router 5/5 actief: "welke bots draaien" / "audit gezondheid" / "hoeveel kaarten wachten" / "wat staat morgen op agenda" / "wat is spark saldo" allemaal routen naar capability_response.' },

      // ==== Communicatie-systeem (expliciet, was impliciet) ====
      { title: '💬 COMMUNICATIE — chat-flow (chat/routes.py)', status: 'done', anchor: 'comm-chat-flow', note: 'Hoofdorchestrator. Voor elke user-message: emotie-detectie → emotie-pipeline (shadow) → smart_intents → kbv2-commands → capability-handler → recap/identity/self-state → fallback. Streaming response.' },
      { title: '💬 COMMUNICATIE — action_intents (open module / ga naar X)', status: 'done', anchor: 'comm-action', note: 'chat/action_intents_service.py — Spark voert app-commando\'s uit ("open trader", "ga naar wallet") binnen chat.' },
      { title: '💬 COMMUNICATIE — capability_handler_service (12 commands van 2 kanten)', status: 'done', anchor: 'comm-cap-handler', note: 'chat/capability_handler_service.py — 12/12 LIVE. Tellen, lijsten, status-check, archief-lezen, gesprek-recap, etc. Match via spark_capabilities.json triggers.' },
      { title: '💬 COMMUNICATIE — community group chat (340 berichten productie)', status: 'done', anchor: 'comm-community', note: 'community/messages.json. Multi-user kanaal, online-tracking via /heartbeat polling.' },
      { title: '💬 COMMUNICATIE — private 1-op-1 chats', status: 'done', anchor: 'comm-private', note: 'modules/contacts/ + chat-thread per user-pair. Met scroll-fix (min-h-0).' },
      { title: '💬 COMMUNICATIE — TTS friendly text-fix (voorlees-vriendelijk)', status: 'done', anchor: 'comm-tts', note: 'chat/tts_friendly_service.py — strip markdown/codeblocks voor voorlezen.' },
      { title: '💬 COMMUNICATIE — Whisper STT (voice → tekst)', status: 'done', anchor: 'comm-stt', note: 'modules/voice/ Whisper integratie via emergent LLM key.' },
      { title: '🛣️ COMMUNICATIE — Spark hands intent-router uitbreiden (5 nieuwe semantic intent-tags)', status: 'done', anchor: 'comm-intent-expand', note: '✅ v6_capabilities_handlers_003 (28 mei) — 5/5 nieuwe capabilities live in chat-router: spark_saldo_check, agenda_vandaag, kennis_inbox_status, bots_status, audit_health. spark_capabilities.json uitgebreid met NL-trigger-patterns + entries in command_registry.json.' },
      { title: '🛣️ COMMUNICATIE — externe kanalen (WhatsApp/Signal/Telegram)', status: 'planned', anchor: 'comm-external', note: 'Toekomst: Spark via WhatsApp/Signal bereikbaar maken. Vereist 3rd-party integratie + auth-bridge.' },

      { title: '🆘 Help-JSON per gradatie (g1 t/m g7) — gerichte command/help-tracking', status: 'done', anchor: 'help-per-gradatie', note: '✅ v6_help_per_gradatie_001 — modules/help_per_gradatie/ live met GET /api/help/index (counts per gradatie) + /help/g{n} per gradatie. Help-tekst per gradatie geseed.' },
      { title: '📐 Blueprint-systeem — 1 JSON ↔ 1 module.py mapping', status: 'done', anchor: 'blueprint-system', note: '✅ v6_synapse_002 — Synapse-enricher genereert 59 markdown blueprints in /app/memory/blueprints/{naam}.md met Doel/Wat werkt/TODO/Splitting-trigger/Encryption/Relaties-checklist. Auto-update bij rescan.' },
      { title: '📚 Spark eigen index-mapstructuur + meta-index bestand', status: 'done', anchor: 'spark-index', note: '✅ v6_synapse_001 (F1+F5) — 57+ _meta.json containers + aggregator op /app/memory/SYNAPSE.json. Auto-scanner detecteert 418 endpoints uit @router-decorators. Touch-hook updatet activity_count + last_touched bij elke save_json(). UI-tab "Synapslaag" in Beheer.' },
      { title: '🔎 Integraties → tab 1 = "Spark Search" (Google-equivalent)', status: 'planned', anchor: 'spark-search', note: 'Eerste tab in Integraties = Sparks zoekfunctie binnen KB v2 + graph + later web. Latere fase: lees-functie (RSS/Drive), schrijf-functie (post).' },
      { title: '📅 Maand-reset 31 mei / 1 juni — kasboek-anker', status: 'planned', anchor: 'maand-reset', note: 'Snapshot 31 mei 23:59 van Spark-balans, alle wallets, trade-history. 1 juni 00:00 = alles nul, snapshot wordt open-saldo nieuw boekjaar. + Disclaimer privacy en tokenomics-doc updaten.' },
      { title: '🏷️ Token-waarde systeem / Winkel / Token / Digitaal bezit — formaliseren', status: 'planned', anchor: 'token-value-system', note: 'Vastleggen hoe token-waarde wordt bepaald, hoe winkel-prijzen erop reageren, wat digitaal bezit betekent voor user.' },
      { title: '🤖 Trade bot — Pot 1 als €10 staking-anker (locked, nooit traden)', status: 'done', anchor: 'trader-pot1-anchor', note: '✅ v6_pot1_staking_lock_001 — LOCKED_POT_INDEX=0 met pot_locked=True, lock_reason="staking_anchor". find_available_potje skipt gelockte potjes. Backfill voor legacy data + toggle-endpoint POST /api/trade/potjes/{user_id}/toggle-lock.' },
      { title: '⚠️ Trader: min-buy check (SOL min €7 → bot crasht nu)', status: 'done', anchor: 'trader-min-buy', note: '✅ v6_trade_minorder_001 (28 mei) — get_market_min_quote(market) met 1u-cache van Bitvavo /v2/markets minimums + fallbacks (BTC/ETH/SOL/ADA=€5). Pre-check op buy + sell. Error-codes: MIN_QUOTE, NO_BALANCE, ZERO_AFTER_CLAMP.' },
      { title: '➕ Watchlist + knop — coins toevoegen/verwijderen + 5 extra coins', status: 'planned', anchor: 'watchlist-plus', note: 'Plusje bij watchlist → coin toevoegen met monitor/bot + €10 pot voor onderzoek (incl. staking-tests).' },
      { title: '✏️ BUG: Notitie kan niet aangepast worden', status: 'done', anchor: 'bug-note-edit', note: '✅ v6_note_edit_001 — pencil-knop op notitie/taak-kaart opent inline edit (titel + inhoud). Backend PUT /api/notes/update/{id} + tasks/update.' },
      { title: '🎁 BUG: Wallet melding "gift 2x verwerkt" terwijl niet gedaan', status: 'done', anchor: 'bug-gift-double', note: '✅ v6_gift_idempotent_001 — threading.Lock + status:processing claim. Idempotent: 2e accept returnt already_accepted:true zonder dubbele transfer.' },
      { title: '🖼️ BUG: Avatar in Beheer→Archief→Bestanden upload werkt, aanpassen niet (wel in Users-pagina)', status: 'done', anchor: 'bug-archive-avatar-edit', note: '✅ v6_avatar_edit_001 — Bewerk-knop op user + system avatar tiles in AvatarGallerySection. Modal met titel + tags + bot_owner. Backend PATCH /api/avatar/gallery/{id} admin-guarded.' },
      // v6_brainfart_002 — KB v2 verbanden/normalisatie leermodules (25-mei)
      { title: '🔗 KB v2 → fase: verbanden leggen, koppelen, hernoemen (na core klaar)', status: 'done', anchor: 'kb-relations-phase', note: '✅ Fase 1 done: compute_verbanden hook gefired bij classify+edit. 644/659 kaarten in lade "doen" hebben verbanden. UI rendert "Gerelateerd"-sectie in CardDetail. Fase 2 (hernoemen + handmatig koppelen) volgt later.' },
      { title: '🧪 Leermodules: synoniem-detectie & auto-normalisatie van tags', status: 'done', anchor: 'kb-learn-synonyms', note: '✅ v6_command_registry_001 — intent_registry/extractor.py heeft ~150 synoniem→canonical-tag mappings. Multi-word phrases worden vóór tokenisatie gematched. Skill-discovery via intent_log.jsonl voor auto-leren van nieuwe patterns.' },
      { title: '🌳 Hoofd-node vs sub-tag hierarchie (bv. "emotie" = hoofd-node, "blij/boos" = sub-tags)', status: 'planned', anchor: 'kb-node-hierarchy', note: 'Stelregel: een paar concepten zijn hoofd-nodes (emotie, werkwoord, voorwerp, plaats…). Daaronder hangen sub-tags. Tag-system wordt boom i.p.v. platte lijst.' },
      { title: '🔤 Plural→Singular normalisatie van tags ("emoties" → "emotie")', status: 'planned', anchor: 'kb-tag-singular', note: 'Auto-rewrite alle tag-instanties naar enkelvoud. Pas toe over hele KB v2 + werkwoorden. Voorkomt dat "emotie" en "emoties" als 2 aparte nodes leven.' },
      { title: '⚙️ Werkwoord-stamherkenning (bakt / bakken / bakker → stam "bak")', status: 'planned', anchor: 'kb-verb-stem', note: 'Bakker = persoon die bakt, "wij gaan bakken" = werkwoord-vorm. Beide delen stam "bak". Stam wordt node, vormen worden edges met label (persoon / werkwoord / bezigheid).' },
      { title: '🪞 Gelijkheid-engine: stam-herkenning over werkwoorden + zelfstandige naamwoorden', status: 'planned', anchor: 'kb-similarity', note: 'Soms valt "bak kaas" (voorwerp) onder zelfde stam maar andere relatie. Engine moet onderscheid maken via context-tag (voorwerp/handeling/persoon).' },
      { title: '📊 Curatie-dashboard: zie afwijkingen, los enkelvoud/synoniem-conflict op met 1 klik', status: 'planned', anchor: 'kb-curation-dash', note: 'Admin-pagina: lijst van potentiële duplicaten/synoniemen/plural-issues. Per regel: "Voeg samen" / "Negeer" / "Markeer als apart concept".' },
      // v6_brainfart_003 — Hooks/commands + KB consistency + topic-uniqueness (25-mei)
      { title: '🔌 Hook-systeem voor triggers/commands (gebruiker-uitbreidbaar)', status: 'planned', anchor: 'trigger-hooks', note: 'Statische trigger.json → dynamisch hook-systeem. User kan via UI trigger toevoegen ("als ik X zeg → doe Y"). Elke trigger = hook met action-plugin.' },
      { title: '👥 Triggers community-extensible (g2+ stelt voor, g1 keurt goed)', status: 'planned', anchor: 'trigger-community', note: 'Curatie-flow voorkomt dat verkeerde triggers KB vervuilen. Of: triggers per gradatie-scope (eigen vs globaal).' },
      { title: '🟰 KB-invul UI volledig consistent maken (één layout overal)', status: 'planned', anchor: 'kb-ui-unified', note: 'Voorwaarde voor topic-uniqueness check. CardDetail/NewCardInline/Herzien-flow moeten exact dezelfde velden + validatie hebben. Anders werkt geen enkele trigger betrouwbaar.' },
      { title: '🚫 Snap-creatie: topic-uniqueness check tegen knowledge_index.json', status: 'planned', anchor: 'snap-topic-unique', note: 'Bij nieuwe snap: als topic al bestaat → 2 opties: "Toevoegen aan bestaande kaart" / "Nieuwe variant maken". Voorkomt 5300 lege variant-kaarten.' },
      { title: '❌ Negatie-trigger: "nee niet [onderwerp]" → exclude voor sessie', status: 'planned', anchor: 'negate-trigger', note: 'User zegt "nee niet emotie" → Spark slaat in user-preferences excluded_topics op voor huidige sessie/snap-flow.' },
      // v6_brainfart_004 — Bidirectionele intent-capability matcher (25-mei)
      { title: '🎯 Command-registry: elke /api-endpoint krijgt intent-tags', status: 'planned', anchor: 'cmd-registry', note: 'JSON: {path, intent_tags[], required_params[], gradatie_min}. /agenda/list → [tijd,planning,bekijken]. /wallet/topup → [geld,toevoegen,wallet]. Geen 1-op-1 trigger→command meer.' },
      { title: '🧭 Intent-extractor: user-zin → tag-vector', status: 'planned', anchor: 'intent-extractor', note: 'User zegt "Wat staat morgen op mijn agenda?" → extractor tagt [tijd,planning,bekijken]. Triggers worden primitieve versie hiervan. Later: emergent LLM voor robustere extractie.' },
      { title: '🤝 Capability-matcher: tag-overlap score → top-3 kandidaat-commands', status: 'planned', anchor: 'cap-matcher', note: 'Bidirectioneel: user-intent ↔ command-capability ontmoeten elkaar in tag-ruimte. Spark kan nieuwe combinaties bedenken zonder hardcoded trigger.' },
      { title: '❓ Disambiguation: bij meerdere matches → "Bedoelde je X of Y?"', status: 'planned', anchor: 'cmd-disambiguation', note: 'Voorkomt verkeerde uitvoer. Spark leert van gebruikers-keuze welke combinatie de juiste was → tags fine-tunen.' },
      // v6_brainfart_005 — Emergente capability via command-compositie (25-mei)
      { title: '🧬 Sequential composition: command-keten bouwen voor onbekende intent', status: 'planned', anchor: 'cmd-compose-seq', note: 'Geen 1-op-1 match? Spark componeert keten: cmdA → output → cmdB → output → cmdC. Bv. "lijstje gekocht gisteren voor boekhouding" = /wallet/transactions → /accounting/category-summary → /notes/create.' },
      { title: '🪂 Fallback chains: dichtstbijzijnde match + user-bevestiging', status: 'planned', anchor: 'cmd-fallback', note: 'Geen exacte match? Toon top-3 closest met overlap-score. User kiest → Spark leert die mapping.' },
      { title: '🌱 Skill discovery: Spark biedt aan herkende compositie als snelkoppeling op te slaan', status: 'planned', anchor: 'cmd-skill-discovery', note: 'Spark merkt patroon (zelfde keten 3x gebruikt) → "Zal ik hier 1 command van maken?" → user keurt goed → nieuwe samengestelde capability live. Spark groeit organisch zonder dat dev iets bouwt.' },
      // v6_brainfart_006 — Gradatie-locks op command-niveau (25-mei)
      { title: '🔒 Per-gradatie command-JSON (commands_g1.json t/m commands_g7.json)', status: 'planned', anchor: 'cmd-gradatie-files', note: 'Net als help_gN.json. Auto-afgeleid van master command_registry.json o.b.v. gradatie_min van elk command. g3 ziet alleen wat g3 mag uitvoeren.' },
      { title: '🛡️ Gradatie-lock check IN command-registry, niet alleen in UI', status: 'planned', anchor: 'cmd-grad-lock', note: 'Elke command in registry: gradatie_min veld. Matcher honoreert deze. UI-locks zijn slechts decoratief — echte security zit op API-laag + registry.' },
      { title: '🪜 Privilege-fallback: blocked command → bied request-flow aan', status: 'planned', anchor: 'cmd-priv-fallback', note: 'g3 vraagt iets dat g1-only is → Spark biedt aan: "Wil ik er een aanvraag-taak van maken voor admin?" → routes naar /notes/tasks/create (g3-allowed) met juiste context.' },
      { title: '🌐 Skill-discovery gradatie-aware', status: 'planned', anchor: 'cmd-skill-grad', note: 'Compositie waarin g1-command zit kan g3 niet als eigen snelkoppeling opslaan. Of: g3 stelt voor → g1 keurt goed → wordt globaal beschikbaar voor iedereen vanaf passende gradatie.' },
    ],
  },
  {
    id: 'phase-werkwijze',
    title: '📐 Werkwijze & Conventies (lees bij elke sessie)',
    status: 'active',
    color: '#06b6d4',
    icon: BookOpen,
    period: 'permanent / levend',
    items: [
      { title: 'DSP-001 · Bot-data dual-source: bot_users.json + system/users.json — beide updaten bij nieuwe bot', status: 'done', anchor: 'dsp-bot-data', note: 'bot_users.json = triggers/responses. users.json = unified identity. Cross-ref in beide files via _arch_ref' },
      { title: '📚 ARCHITECTURE.md bijhouden in /app/memory/ — elke nieuwe dual-source → DSP-NNN entry + cross-ref', status: 'active', anchor: 'arch-notebook', note: 'Voorkomt dat dual-source kennis verzandt tussen sessies. Volgende agent leest dit altijd mee bij handoff' },
      { title: 'Geen MongoDB ooit — alleen lokale JSON via load_json/save_json (modules.core.storage)', status: 'done', anchor: 'no-mongo', note: 'Privacy/autonomy fundament. Nieuwe agent: niet importeren PyMongo' },
      { title: 'Naam-display fix (v5_display_fix_001): user-000=Spark, user-001=De Willem — aligneert admin/bots met rest van app (data was altijd correct)', status: 'done', anchor: 'name-fix', note: 'Eerdere "swap" was juist de bug; canonical mapping nu overal hetzelfde' },
      { title: 'Bij ELKE nieuwe download/zip-upload: diffen vóór mergen, geen blind kopiëren', status: 'done', anchor: 'diff-first', note: 'Voorkomt dat productie-state preview pollueert of andersom' },
      { title: 'Dutch communicatie — agent altijd in Nederlands met user', status: 'done', anchor: 'lang-nl' },
      { title: '🎤 STT/TTS toggles per bot in Bot-instellingen → koppeling Whisper+TTS via integration_playbook (niet zelf SDK installeren)', status: 'planned', anchor: 'voice-integration' },
      { title: 'Bij avatar-bug type checks: user_id matters! Verteller-berichten NIET user-001 geven', status: 'done', anchor: 'avatar-userid', note: 'DSP-002 in spe — leerpunt uit Base Line intro' },
    ],
  },
  {
    id: 'phase-0',
    title: 'Phase 0: Core Setup',
    status: 'done',
    color: '#22c55e',
    icon: Shield,
    period: 'Maart 2026',
    items: [
      { title: 'FastAPI backend met JSON storage (geen MongoDB)', status: 'done' },
      { title: 'React frontend met dark theme', status: 'done' },
      { title: 'Auth module (login, users, gradaties)', status: 'done' },
      { title: 'Sidebar navigatie (4 secties)', status: 'done' },
    ],
  },
  {
    id: 'phase-1',
    title: 'Phase 1: Workspace',
    status: 'done',
    color: '#22c55e',
    icon: Home,
    period: 'Maart 2026',
    items: [
      { title: 'Dashboard met live data kaarten', status: 'done' },
      { title: 'Gesprekken (Spark AI / Community / Privé tabs)', status: 'done' },
      { title: 'Kennisbank zoekengine (2400+ kaarten, CRUD)', status: 'done' },
      { title: 'Agenda module', status: 'done' },
      { title: 'Dagboek met mood tracking', status: 'done' },
      { title: 'Notities & Taken (hybrid)', status: 'done' },
      { title: 'Roadmap overzicht', status: 'done' },
    ],
  },
  {
    id: 'phase-2',
    title: 'Phase 2: Spark AI',
    status: 'done',
    color: '#22c55e',
    icon: Brain,
    period: 'Maart 2026',
    items: [
      { title: 'Triggers beheer (toevoegen/verwijderen)', status: 'done' },
      { title: 'Emotie analyse systeem', status: 'done' },
      { title: 'Verbanden / Knowledge Graph', status: 'done' },
      { title: 'Spark Brain (identiteit & persoonlijkheid)', status: 'done' },
      { title: 'Spark Profiel (23 categorieën)', status: 'done' },
    ],
  },
  {
    id: 'phase-3',
    title: 'Phase 3: Modules',
    status: 'done',
    color: '#22c55e',
    icon: Package,
    period: 'Maart 2026',
    items: [
      { title: 'Trader interface', status: 'done' },
      { title: 'Live Bitvavo candles + Watchlist (5 coins)', status: 'done' },
      { title: 'Monitor systeem (Bollinger Band engine)', status: 'done' },
      { title: 'Snel Handelen (mock/live trades)', status: 'done' },
      { title: 'Achievements (13 milestones, XP, rarity)', status: 'done' },
      { title: 'Leaderboard (ranglijst + podium)', status: 'done' },
      { title: 'Wallet overzicht + opname systeem', status: 'done' },
      { title: 'ROAR Token Winkel (kopen/verkopen)', status: 'done' },
      { title: 'Boekhouding (4 kasboeken)', status: 'done' },
      { title: 'Persoonskaarten (6 personen)', status: 'done' },
      { title: 'Community Chat (3 bots)', status: 'done' },
      { title: 'Integraties (bestandsbrowser + module sandbox)', status: 'done' },
    ],
  },
  {
    id: 'phase-4',
    title: 'Phase 4: Beheer',
    status: 'done',
    color: '#22c55e',
    icon: Settings,
    period: 'Maart 2026',
    items: [
      { title: 'Mijn Profiel pagina', status: 'done' },
      { title: '🎨 Mijn Profiel → Instellingen-tab (Beeld/Geluid/Connecties, per-user glow base color)', status: 'done', anchor: 'profile-settings-tab', note: 'v5_ui_prefs_001 — color picker 8 preset + custom hex, live CSS variable --glow-base. Toekomst: gradatie op humeur, auto-bark' },
      { title: 'Gebruikers admin', status: 'done' },
      { title: 'Analytics (Systeem / Network / Layer)', status: 'done' },
      { title: 'Instellingen (6 tabs: Algemeen, Beeld, Geluid, Integraties, Features, Tips)', status: 'done' },
    ],
  },
  {
    id: 'phase-5',
    title: 'Phase 5: Backend Koppeling',
    status: 'active',
    color: '#f59e0b',
    icon: Zap,
    period: 'Q2 2026',
    items: [
      { title: 'Dagboek API (opslaan/laden entries)', status: 'done' },
      { title: 'Notities & Taken API (CRUD + sync)', status: 'done' },
      { title: 'Wallet koppelen aan oude wallet data', status: 'done' },
      { title: 'Trader API met live data', status: 'done' },
      { title: 'Agenda persistent opslaan', status: 'done' },
      { title: 'Gesprekken opslaan in JSON', status: 'done' },
      { title: 'Instellingen API (settings.json)', status: 'planned' },
      { title: 'Leaderboard berekenen uit echte user data', status: 'planned' },
      { title: 'Analytics met echte metrics', status: 'planned' },
    ],
  },
  {
    id: 'phase-6',
    title: 'Phase 6: Spark Brain & AI',
    status: 'planned',
    color: '#3b82f6',
    icon: Brain,
    period: 'Q2-Q3 2026',
    items: [
      { title: 'Spark Brain identiteit beheer', status: 'done' },
      { title: 'TTS / STT integratie', status: 'done' },
      { title: 'Notificatie systeem', status: 'done' },
      { title: 'Spark Profiel (biografie, filosofie, ethiek)', status: 'done' },
      { title: 'Willem Personality profiel', status: 'done' },
      { title: 'Uitgebreid profiel (adres, noodcontact)', status: 'done' },
      { title: 'Roadmap API backend', status: 'done' },
      { title: 'AI conversatie engine', status: 'planned' },
      { title: 'Externe integraties (Bitvavo live, Telegram)', status: 'planned' },
    ],
  },
  {
    id: 'phase-7',
    title: 'Phase 7: Deployment & Polish',
    status: 'planned',
    color: '#a855f7',
    icon: Rocket,
    period: 'Q3 2026',
    items: [
      { title: 'Standalone deployment setup', status: 'planned' },
      { title: 'Data backup & restore', status: 'planned' },
      { title: 'Performance optimalisatie', status: 'planned' },
      { title: 'Documentatie & handleiding', status: 'planned' },
      { title: 'Beveiligingsaudit', status: 'planned' },
    ],
  },
  {
    id: 'phase-dnd',
    title: 'Phase D&D: Levende Spark World',
    status: 'active',
    color: '#a855f7',
    icon: Sparkles,
    period: 'Q2-Q3 2026',
    items: [
      { title: '🌟 Lore index (Base Line, fracties, elementen)', status: 'done', anchor: 'lore-index' },
      { title: '🎒 Persoonskaart + inventory + slots/gewicht', status: 'done', anchor: 'persoonskaart' },
      { title: '👁️ Spark observatie systeem (avatar/KB events)', status: 'done', anchor: 'spark-observe' },
      { title: '🎨 Aura/glow per gedragspatroon (kleur uit counters)', status: 'active', anchor: 'aura' },
      { title: '⚖️ Avatars als wereld-functies (Reaper/Boekhouder/etc.)', status: 'active', anchor: 'avatar-functions' },
      { title: '📊 World state — top entiteiten dominantie', status: 'active', anchor: 'world-state' },
      { title: '🎯 Hyperlinked stats — gedrag → identiteit (geen cijfers)', status: 'planned', anchor: 'hyperlink-stats' },
      { title: '🐶 Auto-bark als community reward', status: 'planned', anchor: 'auto-bark' },
      { title: '🧥 Body-slots (helm/cape/schoenen) na Rugzak', status: 'planned', anchor: 'body-slots' },
      { title: '🔮 Particles op aura (klok-deeltjes/runen/mist)', status: 'planned', anchor: 'particles' },
      { title: '⚡ Aspect-bark bij dominantie (>60% van events)', status: 'planned', anchor: 'aspect-bark' },
      { title: '🗺️ Quest-systeem ontstaat uit gedragspatronen', status: 'planned', anchor: 'emergent-quests' },
      { title: '📜 Lore-currency (zeldzame KB-kaarten = waarde)', status: 'planned', anchor: 'lore-currency' },
      { title: '🌫️ Vervormde verhalen (canon herschrijven via consensus)', status: 'planned', anchor: 'dynamic-canon' },
      { title: '🌦️ Weerstation (weer.nl koppeling → cloud/humeur per user)', status: 'planned', anchor: 'weather-mood', note: 'Naast emotie krijgt elke user een "wolk" gevoed door echt weer op zijn locatie. Komt later in Phase Emotie samen' },
      { title: '🪙 Token-tier: Community → Community Plus bij token-bezit', status: 'planned', anchor: 'community-plus', note: '1+ token = community member, bot-toegang gekoppeld aan wallet-saldo. Spark zelf spaart eigen potjes uit handelswinst → kan ze weggeven of behouden' },
      { title: '🎤 STT/TTS per bot — admin spreekt namens bot, bot spreekt terug', status: 'planned', anchor: 'bot-voice', note: 'Toggles in Bot-instellingen zitten al — OpenAI Whisper + TTS koppeling volgt' },
      { title: '🎙️ D&D-kaart als spreekkanaal — bot leest tekst voor uit kaart', status: 'planned', anchor: 'dnd-voice-cards' },
      // v6_spark_world_concept_001 — Volledig wereldopbouw concept (P1, ná deploy)
      { title: '🇳🇱 Nederland-als-fantasy-continent (basiswereld)', status: 'planned', anchor: 'sw-nl-base', note: 'Echte NL-kaart vertaald naar D&D-stijl. Kustlijnen, provincies, waterstructuren blijven herkenbaar. Visueel fantasy.' },
      { title: '🏰 12 provincies als facties', status: 'planned', anchor: 'sw-facties', note: 'Groningen=Noord begin, Friesland=water/zee, Drenthe=bossen, Overijssel=handel, Gelderland=militair, Utrecht=orde, NH=haven, ZH=politiek, Zeeland=mystiek, Brabant=ambacht, Limburg=heuvels, Flevoland=experimenteel' },
      { title: '❄️ Startgebied "The North" — Groningen', status: 'planned', anchor: 'sw-the-north', note: 'Bekend terrein, lokaal fotografeerbaar, logisch uitbreidbaar' },
      { title: '📸 Foto→Fantasy workflow (asset creator)', status: 'planned', anchor: 'sw-foto-flow', note: 'Echte foto → metadata (locatie, richting, functie) → D&D-vertaling met behoud perspectief/compositie → 512×512 asset' },
      { title: '🗺️ Asset-types: wereldkaart, stad top-down, scene view, NPC avatars', status: 'planned', anchor: 'sw-asset-types' },
      { title: '🌧️ Realtime weer-koppeling per regio', status: 'planned', anchor: 'sw-realtime-weer', note: 'Weer.nl Groningen → game-regen/mist/zon. Quest-triggers op weersomstandigheden.' },
      { title: '🌅 24-uurs realtime dag/nacht sync', status: 'planned', anchor: 'sw-realtime-tijd', note: 'Dag = dag, nacht = nacht. Nacht-quests, dag-events.' },
      { title: '🛡️ D&D character sheet UI (Stormhaven-stijl)', status: 'planned', anchor: 'sw-char-sheet', note: 'Persoonskaart met level/XP/HP/SP, equipment slots (helm/cape/wapen/schoenen), inventory grid (4×6), avatar art, dorp-portretje. Zie ontwerp-mockup test ui D&D.png' },
      { title: '🛒 Multi-tenant shop (per user eigen tab)', status: 'planned', anchor: 'sw-multi-shop', note: 'Beheer kan extra winkel-tabs aanmaken gekoppeld aan andere gebruikers. Bv. zus → edelstenenwinkel. Alle binnen 1 ecosysteem.' },
      { title: '👕 Avatar-T-shirts (on-demand print)', status: 'planned', anchor: 'sw-avatar-tshirts', note: 'User kiest eigen avatar of Roadkill design → laat het op T-shirt drukken. Print-on-demand integratie.' },
      { title: '💾 Per-user GB opslagsysteem (1GB standaard, bij te kopen)', status: 'planned', anchor: 'sw-storage-tier', note: 'Logica niet marketing. Gebruikte capaciteit telt. Extra GB via Spark shop.' },
    ],
  },
  {
    id: 'phase-v065',
    title: 'Deploy v0.6.5: Levende Wallet & Trader',
    status: 'done',
    color: '#22c55e',
    icon: Rocket,
    period: '23 mei 2026',
    items: [
      { title: '✨ Welkom-bark eerste login (praat gewoon + type "help")', status: 'done', anchor: 'welcome-bark' },
      { title: '🔄 Trader & Wallet admin switch (Mijn / Spark)', status: 'done', anchor: 'admin-switch' },
      { title: '🤖 Spark trader hourly auto-start (server-persistent)', status: 'done', anchor: 'spark-autostart' },
      { title: '💰 €96.52 bijstorting → 10/10 ROAR tokens verdeeld', status: 'done', anchor: 'tokens-10-10' },
      { title: '💸 Saldo €0 = vrij cash, vermogen zit in 10 potjes', status: 'done', anchor: 'saldo-potjes-split' },
      { title: '🪙 Lazy bot-slot per user (auto zichtbaar in Analytics)', status: 'done', anchor: 'lazy-slots' },
      { title: '🌙 Checkbox "Draaien als ik offline ben" (persistentie)', status: 'done', anchor: 'offline-persist' },
      { title: '🛑 Admin force-sell per potje (audit + warning modal)', status: 'done', anchor: 'force-sell' },
      { title: '📊 Analytics bot-kaart redesign (uitklap + history)', status: 'done', anchor: 'bot-cards' },
    ],
  },
  {
    id: 'phase-v066',
    title: 'Deploy v0.6.6: D&D Base Line & Slim KB-overdracht',
    status: 'done',
    color: '#a855f7',
    icon: Sparkles,
    period: '23 mei 2026',
    items: [
      { title: '🎭 [start verhaal] in community chat — Base Line intro', status: 'done', anchor: 'baseline-intro', note: '4 berichten: opening → AD in tijd, donker → bundel licht slaat als water → altaar x0,y0,z0 → 3 keuzestenen' },
      { title: '👂 Drie zintuig-keuzes: Horen / Zien / Zwijgen', status: 'done', anchor: 'baseline-choices', note: 'Werkt end-to-end. behavior_tracker logt elke keuze als groei-input. Ruiken/Proeven komen later' },
      { title: '🆘 Help-knop community chat (typ "help")', status: 'done', anchor: 'community-help', note: 'Productie-bug fix: typ help, /help, ? of hulp → command-overzicht' },
      { title: '📦 KB-diff export endpoint (slim — paar KB ipv 11MB)', status: 'done', anchor: 'kb-diff-export', note: '/api/backup/kb-changed-since-deploy — alleen kaarten die na deploy zijn aangepast' },
      { title: '📥 KB-diff import endpoint (merge tussen omgevingen)', status: 'done', anchor: 'kb-diff-import', note: '/api/knowledge/import-diff — upload-mergen met automatische backup, match by id of begrip' },
      { title: '🗂️ 3 download-opties op Backup-pagina', status: 'done', anchor: 'backup-3-cards', note: 'Wijzigingen / KB-diff slim / Volledig — keuze afhankelijk van wat je nodig hebt' },
      { title: '🎭 5e bot toegevoegd: De Dood', status: 'done', anchor: 'bot-dood', note: 'Reflectieve acteur bij memento-momenten, eindes, transities. Gallery-avatar gekoppeld' },
      { title: '⚙️ Bot-instellingen tab in UsersAdminPage', status: 'done', anchor: 'bot-settings-tab', note: 'Alleen voor is_bot users. Velden: rol, persoonlijkheid, channels, bark-template, avatar-lock, STT/TTS toggles' },
      { title: '🔥 Trader hot coin-swap (productie-bug fix)', status: 'done', anchor: 'trader-hotswap', note: 'Coin-picker klikbaar tijdens running monitor. Potjes verdelen automatisch 5×2 over actieve coins' },
      { title: '⚰️ De Dood als Verteller bij verhalen (intro v0.6.6 fix)', status: 'done', anchor: 'verteller-dood', note: 'Niet Spark — De Dood vertelt het ontstaansverhaal. Past bij zijn rol "transities/eindes/beginpunten". Geboorte = ook een transitie. user_id verteller berichten = bot-dood (eigen avatar, geen user-overlap meer)' },
    ],
  },
  {
    id: 'phase-conversatie-2',
    title: '💬 Conversatie 2.0: Spark voelt als gesprek, niet formulier',
    status: 'planned',
    color: '#ec4899',
    icon: BookHeart,
    period: 'na v0.6.6 deploy',
    items: [
      { title: '🤐 W-vraag systeem dempen — pas vragen ná afgesloten gesprek + max 1× per 4 interacties', status: 'planned', anchor: 'ws5-quiet', note: 'Geen formulier-push meer. Spark voelt minder als kennisbank-trechter, meer als iemand die af en toe nieuwsgierig is' },
      { title: '✋ "stop" als universeel safe-word', status: 'planned', anchor: 'stop-safeword', note: 'Werkt in chat, D&D, wedervraag, overal. Direct pauze of breek. Net als in echt leven' },
      { title: '🔍 Profiel-lookup via gewone vraag', status: 'planned', anchor: 'profile-nlp', note: '"wat is je achternaam?" → Spark leest uit context (over wie) + profiel. Geen /commando nodig' },
      { title: '🕸️ Relatie-graph name resolution (alleen vrienden)', status: 'planned', anchor: 'relation-graph', note: 'Spark resolved namen via persons-tabel + user-graph. Privacy-gate: alleen tussen vrienden, geen vreemden taggen' },
      { title: '📨 Spark als bode — relay-berichten met attributie', status: 'planned', anchor: 'spark-relay', note: '"Hé Spark, zeg tegen Heidi dat ik wacht" → Heidi krijgt prive: "Willem wilde dat ik dit zou zeggen: [...]" + 4-staps confirm flow (zien → lezen → reageren → reply terug)' },
      { title: '📞 Antwoordapparaat-modus: agenda-aware auto-replies (WhatsApp/Signal/web)', status: 'planned', anchor: 'voicemail-agenda', note: 'Bij gekoppelde messaging-integratie: Spark gebruikt agenda voor "Willem is bij de tandarts". Excuus-lijst aanvinkbaar. Optioneel TTS oplezen van bot-berichten op verzoek user' },
    ],
  },
  {
    id: 'phase-tokenshop-trader-v2',
    title: '🏪 Token-shop & Trader v2',
    status: 'planned',
    color: '#fbbf24',
    icon: Wallet,
    period: 'na Conversatie 2.0',
    items: [
      { title: '📈 Lijngrafiek token-prijs in winkel (zoals coin-chart)', status: 'planned', anchor: 'token-chart', note: 'Verwerkt prijsverloop ROAR token over tijd, naast huidige fixed-price kaart' },
      { title: '💼 Dashboard: saldo (cash) + vermogen (Bitvavo+potjes) zichtbaar', status: 'planned', anchor: 'dashboard-fin', note: 'Eerst alleen gradatie 4 → 1 (oplopend privé)' },
      { title: '🎰 Wallet potjes = #tokens (niet vast 10)', status: 'planned', anchor: 'potjes-per-token', note: 'Willem met 1 token = 1 potje; Spark met 10 tokens = 10 potjes. Geen vaste 10' },
      { title: '🎙️ Storting → spraakcommando "ik stortte X€" + Spark vraagt welke user te crediten', status: 'planned', anchor: 'verbal-deposit' },
      { title: '🤖 Bottrader: elk potje = aparte bot-instance (niet 1 bot/n potjes)', status: 'planned', anchor: 'one-bot-per-pot', note: 'Bug 18:46 fix-richting: per-potje state ipv shared bot' },
      { title: '📊 Leaderboard top 3 met letters bovenin', status: 'done', anchor: 'leaderboard-top3', note: 'v5_leaderboard_avatars_001 — UserAvatar component met echte gallery-image + roadkill fallback ipv letter' },
    ],
  },
  {
    id: 'phase-achievements-milestones',
    title: '🏆 Achievements: Mijlpalen (avatar, tokens, eerstes)',
    status: 'done',
    color: '#fbbf24',
    icon: Award,
    period: 'voltooid mei 2026',
    items: [
      { title: '🖼️ "Ik koos een Avatar" — 50 XP wanneer user avatar wijzigt naar non-default', status: 'done', anchor: 'ach-avatar-chose' },
      { title: '🤳 "Eigen Avatar" — 50 XP wanneer user eigen foto upload (Mijn Profiel)', status: 'done', anchor: 'ach-avatar-uploaded' },
      { title: '🪙 "I got a ROAR Token" — 50 XP bij eerste token op wallet', status: 'done', anchor: 'ach-first-roar' },
      { title: '📢 Notification-bark met monitor-uitleg bij eerste ROAR token', status: 'done', anchor: 'first-roar-bark' },
      { title: 'Cross-module hook `unlock_milestone(user_id, achievement_id)` voor toekomstige mijlpalen', status: 'done', anchor: 'unlock-milestone-hook' },
    ],
  },
  {
    id: 'phase-instellingen-tabs',
    title: '⚙️ Instellingen: User + Admin scheiding',
    status: 'done',
    color: '#06b6d4',
    icon: Wallet,
    period: 'voltooid mei 2026',
    items: [
      { title: '👤 Mijn Profiel → Instellingen-tab (Account/Beeld/Geluid/Connecties)', status: 'done', anchor: 'profile-settings-tab' },
      { title: '🔑 Sleutelwoord wijzigen + reset-naar-Welkom01 in Mijn Profiel', status: 'done', anchor: 'self-password' },
      { title: '🎨 Per-user glow basiskleur (`--glow-base` CSS var)', status: 'done', anchor: 'per-user-glow' },
      { title: '🎨 Admin App Kleurenschema (`--app-primary/secondary/bg-tint`)', status: 'done', anchor: 'admin-color-scheme' },
      { title: '📦 Avatar Galerij verplaatst → Beheer/Instellingen/Archief/Foto sub-tab', status: 'done', anchor: 'avatar-gallery-archive' },
      { title: '🗑️ Avatar Galerij gesplitst in Gebruikers / Systeem (locked) tabs + modal-confirm delete', status: 'done', anchor: 'avatar-split-delete' },
    ],
  },
  {
    id: 'phase-color-refactor',
    title: '🎨 App-brede kleur-refactor naar CSS-vars',
    status: 'planned',
    color: '#a855f7',
    icon: Wallet,
    period: 'P2',
    items: [
      { title: 'Hard-coded amber → `var(--app-primary)` (sidebar/login/buttons)', status: 'planned', anchor: 'color-var-refactor', note: 'Zodat admin-kleurschema écht doorklinkt in heel de app' },
      { title: 'Glow-gradatie op basis van humeur (consumeert --glow-base + emotion mood)', status: 'planned', anchor: 'mood-glow-gradient' },
      { title: 'Auto-bark functionaliteit (toggle staat al klaar in Mijn Profiel)', status: 'planned', anchor: 'auto-bark' },
    ],
  },
  {
    id: 'phase-spark-hands',
    title: '🤲 Spark\'s handen — Capability registry (natural language)',
    status: 'active',
    color: '#06b6d4',
    icon: Brain,
    period: 'lopend',
    items: [
      { title: '📋 Capability registry JSON met triggers/module/status (live/placeholder/idea)', status: 'done', anchor: 'cap-registry', note: '/app/backend/data/personality/spark_capabilities.json — 11 starter-capabilities' },
      { title: '🗣️ Vocab uitgebreid: vraag/denken/actie per emotie + commando_acties top-level', status: 'done', anchor: 'cap-vocab', note: 'spark_vocab.json v1.1 — verschilt nu per emotie i.p.v. same words' },
      { title: '🎯 Intent matcher: user-zin "kan jij X?" → capability_id', status: 'planned', anchor: 'cap-matcher', note: 'Bouwt voort op chat/smart_intents_service.py' },
      { title: '⚡ Execution router: capability_id → echte module-call', status: 'planned', anchor: 'cap-executor' },
      { title: '🪞 Placeholder-eerlijkheid: "ik kan dat (nog) niet" voor idea/placeholder-status', status: 'planned', anchor: 'cap-placeholder' },
      { title: '🖼️ Capability "Spark\'s handen — beeld" (toon afbeelding)', status: 'planned', anchor: 'cap-image' },
      { title: '🔊 Capability "Spark\'s handen — oren/stem" (speel geluid)', status: 'planned', anchor: 'cap-sound' },
      { title: '🔎 Capability "Spark zoekt in kennisbank"', status: 'planned', anchor: 'cap-search', note: 'Integratie + bestanden tabs als Spark\'s tools' },
    ],
  },
  {
    id: 'phase-roar-economy-v2',
    title: '🪙 ROAR economy v2 — gift UI + auto-sync',
    status: 'active',
    color: '#f59e0b',
    icon: Wallet,
    period: 'lopend',
    items: [
      { title: '🎁 ROAR-gift modal in Winkel → ROAR Tokens (sender kiest user + bedrag + notitie)', status: 'done', anchor: 'roar-gift-modal', note: 'v5_roar_gift_001 — pending → accept/reject/cancel, 24h expiry, inbox-banner. Paper-trail in roar.transactions + admin_log' },
      { title: '📥 Gift-inbox met accept/reject knoppen per gift', status: 'done', anchor: 'gift-inbox' },
      { title: '⏰ Auto-expire pending gifts na 24u (lazy-check bij list calls)', status: 'done', anchor: 'gift-expiry' },
      { title: '🔒 Privacy-implicatie: gift_requests.json bevat sender/recipient pairs — alleen zichtbaar voor betrokken users + admin. Encryptie at-rest later overwegen', status: 'planned', anchor: 'gift-privacy-note' },
      { title: '👁️ Outbox-view in Mijn Profiel of Wallet om historie te zien (status: pending/accepted/rejected/expired/cancelled)', status: 'planned', anchor: 'gift-outbox-view' },
      { title: '📊 Admin-overzicht gift-paper-trail (Beheer → Analytics)', status: 'planned', anchor: 'gift-admin-overview' },
      { title: '📣 De Trader-meldingen (boekhouder DM) PER-USER ipv altijd naar Willem', status: 'done', anchor: 'per-user-trade-dm', note: 'v5_per_user_trade_dm_001 — Spark-trades blijven naar admin, user-trades gaan naar de user zelf' },
      { title: '🔄 `user_wallets.json` ↔ `roar_balances.json` auto-sync hook (gift accept syncs auto)', status: 'done', anchor: 'wallet-roar-sync' },
      { title: 'Storting via SEPA-flow met automatische ROAR-mint optie', status: 'planned', anchor: 'sepa-roar-mint' },
    ],
  },
  {
    id: 'phase-zip-mindgraph',
    title: '🗂️ Zip + Mindgraph notities',
    status: 'planned',
    color: '#94a3b8',
    icon: BookHeart,
    period: 'na Trader v2',
    items: [
      { title: '📝 Zip-bestand bevat ook aantekeningen (mindgraph + andere afgeleide data)', status: 'planned', anchor: 'zip-mindgraph', note: 'Of mindgraph altijd-opnieuw genereren bij merge? Onderzoek' },
      { title: '💡 Spark stelt vraag elke 4e interactie: "Wat denk jij dat ik zou moeten kunnen?"', status: 'planned', anchor: 'spark-feedback-q', note: 'Sluit aan bij Conversatie 2.0 dempen-systeem' },
    ],
  },
];

export function RoadmapPage({ onNavigate }) {
  const { user } = useAuth();
  const [expandedPhase, setExpandedPhase] = useState(
    phases.find(p => p.status === 'active')?.id || phases[0].id
  );
  // v4_roadmap_user_ideas_001 — toon bug-tickets / ideeën van user op roadmap
  const [myBugs, setMyBugs] = useState([]);
  const isAdmin = (user?.gradatie ?? 7) <= 2;
  useEffect(() => {
    if (!user?.id) return;
    // Alleen admins krijgen /bugs/list (403 anders) — voor non-admin probeer mijn-bugs endpoint
    const url = isAdmin
      ? `${API}/api/bugs/list?viewer_id=${user.id}`
      : `${API}/api/bugs/mine?user_id=${user.id}`;
    fetch(url)
      .then(r => r.ok ? r.json() : { bugs: [] })
      .then(d => {
        const all = d.bugs || [];
        // Voor admin filter op eigen tickets, voor non-admin returnt API al alleen eigen
        const mine = isAdmin ? all.filter(b => b.created_by_id === user.id) : all;
        setMyBugs(mine);
      })
      .catch(() => {});
  }, [user?.id, isAdmin]);

  const totalItems = phases.reduce((a, p) => a + p.items.length, 0);
  const doneItems = phases.reduce((a, p) => a + p.items.filter(i => i.status === 'done').length, 0);
  const overallPct = Math.round((doneItems / totalItems) * 100);
  const activePhase = phases.find(p => p.status === 'active');

  return (
    <MainLayout activePage="roadmap" onNavigate={onNavigate}>
      <div data-testid="roadmap-page" className="p-4 md:p-6 space-y-5 max-w-4xl mx-auto">

        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
            <Map className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Roadmap</h1>
            <p className="text-xs text-slate-500">Spark Core 2.0 ontwikkelplan</p>
          </div>
        </div>

        {/* Overall progress */}
        <div className="p-5 rounded-xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(234,88,12,0.03))' }}>
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-lg font-bold text-white">Totale Voortgang</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {doneItems} van {totalItems} taken afgerond
                {activePhase && <span className="text-amber-400 ml-2">Nu: {activePhase.title}</span>}
              </p>
            </div>
            <div className="text-right">
              <span className="text-3xl font-bold text-amber-400">{overallPct}%</span>
            </div>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${overallPct}%`, background: 'linear-gradient(90deg, #22c55e, #f59e0b, #a855f7)' }} />
          </div>
          <div className="flex gap-1.5 mt-3">
            {phases.map(p => {
              const pDone = p.items.filter(i => i.status === 'done').length;
              const pPct = p.items.length > 0 ? (pDone / p.items.length) * 100 : 0;
              return (
                <div key={p.id} className="flex-1 h-1.5 rounded-full overflow-hidden bg-slate-800">
                  <div className="h-full rounded-full" style={{ width: `${pPct}%`, background: p.color }} />
                </div>
              );
            })}
          </div>
        </div>

        {/* v4_roadmap_user_ideas_001 — Jouw Ideeën */}
        {myBugs.length > 0 && (
          <div data-testid="roadmap-user-ideas" className="p-5 rounded-xl border border-amber-500/20 bg-slate-900/30">
            <div className="flex items-center gap-2 mb-3">
              <Lightbulb className="w-5 h-5 text-amber-400" />
              <h2 className="text-base font-bold text-white">Jouw Ideeën & Tickets</h2>
              <span className="text-[10px] px-2 py-0.5 bg-amber-500/15 text-amber-300 rounded-full">{myBugs.length}</span>
            </div>
            <div className="space-y-1.5">
              {myBugs.slice(0, 8).map(b => {
                const status = b.status || 'open';
                const sBg =
                  status === 'opgelost' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' :
                  status === 'in_behandeling' ? 'bg-blue-500/10 text-blue-300 border-blue-500/30' :
                  status === 'afgewezen' ? 'bg-slate-700/40 text-slate-500 border-slate-700' :
                  'bg-amber-500/10 text-amber-300 border-amber-500/30';
                return (
                  <div key={b.id} data-testid={`my-bug-${b.id}`}
                    className="flex items-start gap-3 p-3 bg-slate-800/30 hover:bg-slate-800/50 border border-slate-800/60 rounded-lg transition-colors">
                    <span className={`text-[9px] px-1.5 py-0.5 rounded border uppercase font-medium ${sBg} flex-shrink-0 mt-0.5`}>
                      {status === 'in_behandeling' ? 'in behandeling' : status}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-white">{b.description || b.titel || b.summary || '(geen omschrijving)'}</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {b.created_at ? new Date(b.created_at).toLocaleString('nl-NL', {day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'}) : ''}
                        {b.page && <span className="ml-2 text-slate-400">· {b.page}</span>}
                      </p>
                    </div>
                  </div>
                );
              })}
              {myBugs.length > 8 && (
                <p className="text-[10px] text-slate-500 text-center pt-1">+ {myBugs.length - 8} meer</p>
              )}
            </div>
          </div>
        )}

        {/* Timeline */}
        <div className="space-y-3">
          {phases.map((phase, idx) => {
            const isExpanded = expandedPhase === phase.id;
            const PhaseIcon = phase.icon;
            const doneCount = phase.items.filter(i => i.status === 'done').length;
            const phasePct = phase.items.length > 0 ? Math.round((doneCount / phase.items.length) * 100) : 0;

            return (
              <div key={phase.id} className="relative">
                {idx < phases.length - 1 && (
                  <div className="absolute left-[19px] top-[56px] w-0.5 h-[calc(100%-32px)] z-0" style={{
                    background: phase.status === 'done' ? '#22c55e40' : '#1e293b'
                  }} />
                )}

                <button
                  data-testid={`phase-${phase.id}`}
                  onClick={() => setExpandedPhase(isExpanded ? null : phase.id)}
                  className={`relative z-10 w-full text-left p-4 rounded-xl border transition-all ${
                    phase.status === 'active'
                      ? 'border-amber-500/30 bg-amber-500/5 hover:bg-amber-500/8'
                      : 'border-slate-800 bg-slate-900/50 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{
                      background: phase.status === 'done' ? `${phase.color}15` : phase.status === 'active' ? `${phase.color}20` : '#1e293b',
                      border: phase.status === 'active' ? `2px solid ${phase.color}40` : 'none',
                    }}>
                      {phase.status === 'done'
                        ? <CheckCircle className="w-5 h-5" style={{ color: phase.color }} />
                        : phase.status === 'active'
                          ? <PhaseIcon className="w-5 h-5" style={{ color: phase.color }} />
                          : <Circle className="w-5 h-5 text-slate-600" />
                      }
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="text-sm font-bold text-white">{phase.title}</h3>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                          phase.status === 'done' ? 'bg-green-500/10 text-green-400' :
                          phase.status === 'active' ? 'bg-amber-500/10 text-amber-400' :
                          'bg-slate-700/50 text-slate-500'
                        }`}>
                          {phase.status === 'done' ? 'Voltooid' : phase.status === 'active' ? 'Actief' : 'Gepland'}
                        </span>
                        <span className="text-[10px] text-slate-600">{phase.period}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden max-w-[200px]">
                          <div className="h-full rounded-full transition-all" style={{ width: `${phasePct}%`, background: phase.color }} />
                        </div>
                        <span className="text-[10px] text-slate-500">{doneCount}/{phase.items.length}</span>
                      </div>
                    </div>

                    {isExpanded
                      ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0" />
                      : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    }
                  </div>
                </button>

                {isExpanded && (
                  <div className="ml-5 pl-5 border-l-2 mt-1 space-y-1 py-2" style={{ borderColor: `${phase.color}30` }}>
                    {phase.items.map((item, i) => {
                      const itemId = item.anchor ? `${phase.id}-${item.anchor}` : `${phase.id}-i${i}`;
                      return (
                        <div key={i} id={itemId}
                          className="group flex items-center gap-2.5 py-1.5 px-3 rounded-lg hover:bg-slate-800/30 transition-colors target:bg-amber-500/10 target:ring-1 target:ring-amber-500/40">
                          {item.status === 'done'
                            ? <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                            : item.status === 'active'
                              ? <Clock className="w-4 h-4 text-amber-400 flex-shrink-0 animate-pulse" />
                              : <Circle className="w-4 h-4 text-slate-600 flex-shrink-0" />
                          }
                          <span className={`text-sm flex-1 ${item.status === 'done' ? 'text-slate-300' : item.status === 'active' ? 'text-white' : 'text-slate-500'}`}>
                            {item.title}
                          </span>
                          {item.anchor && (
                            <a href={`#${itemId}`}
                              className="text-[10px] text-slate-600 hover:text-amber-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity"
                              title="Permalink — gebruik in update-bark als roadmap_ref">
                              {`#${item.anchor}`}
                            </a>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </MainLayout>
  );
}

export default RoadmapPage;
