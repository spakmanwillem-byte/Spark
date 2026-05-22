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
      { title: 'Naam-display swap voor user-000/user-001 (Willem=00, Spark=01) — alleen in admin/bots, niet in data', status: 'done', anchor: 'name-swap', note: 'Data ongemoeid (Bitvavo creds, history blijven op user-001). Display-laag synct met user mental model' },
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
      { title: '📊 Leaderboard top 3 met letters bovenin', status: 'planned', anchor: 'leaderboard-top3' },
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
