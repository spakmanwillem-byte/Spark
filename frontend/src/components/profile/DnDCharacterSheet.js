/**
 * DnDCharacterSheet (v6_dnd_character_sheet_001)
 *
 * Stormhaven-stijl D&D character sheet voor de Avatar-tab.
 *
 * Layout (3 kolommen op desktop, gestapeld op mobiel):
 *   - Top bar:      Titel | Rang-shields | Currency
 *   - Links:        14-slot body silhouet (equipment)
 *   - Midden:       KARAKTER portret + Statistieken + Aanval & Verdediging + Overig
 *   - Rechts:       INVENTORY grid + Huis & Opslag + DORP preview
 *   - Onderaan:     Event feed (ringbuffer) + CHAR INFO panel
 *   - Footer nav:   OVERZICHT | STATISTIEKEN | TALENTEN | VAARDIGHEDEN | QUESTS | RELATIES | PRESTATIES | INSTELLINGEN
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  User, Sword, Shield, Sparkles, Coins, Gem, Heart, Footprints, Crown,
  Save, Edit3, Map, Home, MessageSquare, Scroll, BookOpen, Award,
  Activity, FileText, Settings, Upload, ChevronDown, ChevronUp, Send,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// ----- Slot grid: 9 links (3x3) + 9 rechts (3x3) rond een center silhouet ----
const SLOT_LAYOUT_LEFT = [
  { key: 'linkerhand',  label: 'LINKERHAND',  fallback: 'Schild' },
  { key: 'offhand',     label: 'OFFHAND',     fallback: 'Lantaarn' },
  { key: 'pijl_boog',   label: 'PIJL & BOOG', fallback: 'Pijl en Boog' },
  { key: 'rugzak',      label: 'RUGZAK',      fallback: 'Rugzak' },
  { key: 'ring_l',      label: 'RING (L)',    fallback: 'Ring' },
  { key: 'riem',        label: 'RIEM',        fallback: 'Riem' },
];

const SLOT_LAYOUT_CENTER_TOP = [
  { key: 'hoofd',       label: 'HOOFD',       fallback: 'Hoofdband' },
];
const SLOT_LAYOUT_CENTER = [
  { key: 'rechterhand', label: 'RECHTERHAND', fallback: 'Klein Zwaard' },
  { key: 'handen',      label: 'HANDEN',      fallback: 'Handschoenen' },
  { key: 'ring_r',      label: 'RING (R)',    fallback: 'Ring' },
];
const SLOT_LAYOUT_CENTER_BOTTOM = [
  { key: 'broek',       label: 'BROEK',       fallback: 'Broek' },
  { key: 'torso',       label: 'TORSO',       fallback: 'T-shirt' },
  { key: 'voeten',      label: 'VOETEN',      fallback: 'Schoenen' },
];

const SLOT_LAYOUT_RIGHT = [
  { key: 'nek',         label: 'NEK',         fallback: 'Ketting' },
  { key: 'schouders',   label: 'SCHOUDERS',   fallback: 'Schouderbeschermer' },
  { key: 'armen',       label: 'ARMEN',       fallback: 'Armband' },
  { key: 'trinket',     label: 'TRINKET',     fallback: 'Medaillon' },
  { key: 'sjaal',       label: 'SJAAL',       fallback: 'Sjaal' },
];

const RANK_SHIELDS = [
  { color: '#b45309', label: 'Brons' },
  { color: '#06b6d4', label: 'Lucht' },
  { color: '#dc2626', label: 'Bloed' },
  { color: '#a855f7', label: 'Mystiek' },
  { color: '#3b82f6', label: 'Diep' },
  { color: '#eab308', label: 'Goud' },
];

const FOOTER_TABS = [
  { id: 'overzicht',    label: 'OVERZICHT',    icon: Activity },
  { id: 'statistieken', label: 'STATISTIEKEN', icon: BookOpen },
  { id: 'talenten',     label: 'TALENTEN',     icon: Sparkles },
  { id: 'vaardigheden', label: 'VAARDIGHEDEN', icon: Sword },
  { id: 'quests',       label: 'QUESTS',       icon: Scroll },
  { id: 'relaties',     label: 'RELATIES',     icon: User },
  { id: 'prestaties',   label: 'PRESTATIES',   icon: Award },
  { id: 'instellingen', label: 'INSTELLINGEN', icon: Settings },
];

const FEED_COLORS = {
  SYSTEEM: '#f59e0b',
  WERELD:  '#06b6d4',
  GUILD:   '#3b82f6',
  VERHAAL: '#a855f7',
  HANDEL:  '#22c55e',
};

// ============================================================
// HOOFD-COMPONENT
// ============================================================
export function DnDCharacterSheet({ userId, isAdmin, onOpenAvatarSettings }) {
  const [char, setChar] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [activeFooter, setActiveFooter] = useState('overzicht');
  const [infoTab, setInfoTab] = useState('char_info');
  const [editingMeta, setEditingMeta] = useState(false);
  const [eventDraft, setEventDraft] = useState('');

  const reload = useCallback(() => {
    fetch(`${API}/api/dnd/character/${userId}`)
      .then(r => r.json())
      .then(setChar)
      .catch(() => {});
  }, [userId]);

  useEffect(() => { reload(); }, [reload]);

  useEffect(() => {
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setAvatarUrl(d.url ? `${API}${d.url}?t=${Date.now()}` : null))
      .catch(() => {});
  }, [userId]);

  if (!char) {
    return (
      <div data-testid="dnd-sheet-loading" className="flex items-center justify-center py-20 text-amber-500/60 text-sm">
        Character sheet laden…
      </div>
    );
  }

  const sendEvent = async (kind, text) => {
    if (!text.trim()) return;
    await fetch(`${API}/api/dnd/character/${userId}/event`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ kind, text }),
    });
    setEventDraft('');
    reload();
  };

  const xpInLvl = char.derived?.xp_in_level ?? 0;
  const xpPerLvl = char.derived?.xp_per_level ?? 100;
  const xpPct = Math.min(100, Math.round((xpInLvl / xpPerLvl) * 100));

  return (
    <div data-testid="dnd-character-sheet" className="relative">
      {/* ===== HEADER BAR — Titel | Rang | Shields | Currency ===== */}
      <CharacterHeaderBar
        char={char}
        isAdmin={isAdmin}
        onEdit={() => setEditingMeta(true)}
      />

      {/* ===== HOOFD 3-KOLOMS LAYOUT ===== */}
      <div className="mt-3 grid grid-cols-12 gap-3">
        {/* === KOLOM LINKS: Body silhouet met slots === */}
        <div className="col-span-12 lg:col-span-5">
          <PaperPanel>
            <PaperHeader>BODY · EQUIPMENT</PaperHeader>
            <BodySilhouettePanel
              equipment={char.equipment || {}}
              userId={userId}
              isAdmin={isAdmin}
              onChange={reload}
            />
          </PaperPanel>
        </div>

        {/* === KOLOM MIDDEN: Karakter + Stats === */}
        <div className="col-span-12 md:col-span-6 lg:col-span-3 space-y-3">
          <KarakterPortretPanel
            avatarUrl={avatarUrl}
            level={char.derived?.level ?? 0}
            xpPct={xpPct}
            xpInLvl={xpInLvl}
            xpPerLvl={xpPerLvl}
            onOpenAvatarSettings={onOpenAvatarSettings}
          />
          <StatsPanel title="STATISTIEKEN" stats={char.statistieken || {}} accent="#f59e0b" />
          <StatsPanel title="AANVAL & VERDEDIGING" stats={char.aanval_verdediging || {}} accent="#dc2626" />
          <OverigPanel char={char} />
        </div>

        {/* === KOLOM RECHTS: Inventory + Huis & Opslag === */}
        <div className="col-span-12 md:col-span-6 lg:col-span-4 space-y-3">
          <InventoryGridPanel userId={userId} />
          <HuisOpslagPanel />
          <DorpPreviewPanel char={char} onNavigateMap={() => onOpenAvatarSettings?.('map')} />
        </div>
      </div>

      {/* ===== EVENT FEED + CHAR INFO ===== */}
      <div className="mt-3 grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-5">
          <EventFeedPanel
            feed={char.event_feed || []}
            draft={eventDraft}
            setDraft={setEventDraft}
            onSend={(t) => sendEvent('SYSTEEM', t)}
          />
        </div>
        <div className="col-span-12 md:col-span-4">
          <CharInfoPanel char={char} activeTab={infoTab} setActiveTab={setInfoTab} />
        </div>
        <div className="col-span-12 md:col-span-3">
          {/* Compacte map preview als rechter kolom hieronder ontbreekt */}
          <MiniMapPanel char={char} />
        </div>
      </div>

      {/* ===== FOOTER NAV ===== */}
      <FooterNav active={activeFooter} setActive={setActiveFooter} />

      {/* ===== EDIT MODAL ===== */}
      {editingMeta && (
        <EditMetaModal
          char={char}
          userId={userId}
          onClose={() => setEditingMeta(false)}
          onSaved={() => { setEditingMeta(false); reload(); }}
        />
      )}
    </div>
  );
}

// ============================================================
// SUB-COMPONENTS
// ============================================================

function CharacterHeaderBar({ char, isAdmin, onEdit }) {
  return (
    <div
      data-testid="char-header-bar"
      className="rounded-xl border-2 border-amber-900/50 bg-gradient-to-r from-slate-950 via-stone-950 to-slate-950 px-3 py-2 flex items-center gap-3 flex-wrap"
      style={{
        boxShadow: 'inset 0 0 24px rgba(245,158,11,0.05), 0 0 0 1px rgba(245,158,11,0.15)',
      }}
    >
      {/* Banner-emblem */}
      <div className="w-14 h-16 flex-shrink-0 rounded-md border border-amber-700/60 bg-gradient-to-b from-amber-900/40 to-purple-900/30 flex items-center justify-center">
        <Crown className="w-7 h-7 text-amber-400" />
      </div>

      {/* Titel + Ondertitel */}
      <div className="flex-1 min-w-[160px]">
        <p className="text-[9px] uppercase tracking-[0.2em] text-amber-500/70">Titel</p>
        <h2 data-testid="char-titel" className="text-xl font-serif font-bold text-amber-100 leading-tight">
          {char.titel || 'Naamloos'}
        </h2>
        <p className="text-[11px] italic text-amber-300/60">{char.ondertitel || ''}</p>
      </div>

      {/* Rang */}
      <div className="border-l border-r border-amber-900/40 px-3 py-1">
        <p className="text-[9px] uppercase tracking-[0.2em] text-amber-500/70">Rang / Status</p>
        <p data-testid="char-rang" className="text-sm font-bold text-amber-100">{char.rang_titel || 'Burger'}</p>
        <p className="text-[10px] text-amber-400/60">Community Level {char.derived?.level ?? 0}+</p>
        {/* Progress bar */}
        <div className="mt-1 w-32 h-1.5 bg-stone-900 rounded-full overflow-hidden border border-amber-900/40">
          <div className="h-full bg-gradient-to-r from-amber-700 to-yellow-400"
            style={{ width: `${char.rang_progress_pct ?? 0}%` }} />
        </div>
        <p className="text-[9px] text-amber-400/60 mt-0.5">{char.rang_progress_pct ?? 0}%</p>
      </div>

      {/* Rank shields */}
      <div className="flex items-center gap-1">
        {RANK_SHIELDS.map((s, i) => (
          <div key={i} data-testid={`rank-shield-${i}`}
            title={s.label}
            className="w-7 h-9 rounded-sm border border-amber-900/40 flex items-center justify-center"
            style={{ background: `linear-gradient(180deg, ${s.color}40, ${s.color}10)`, opacity: i < 4 ? 1 : 0.4 }}>
            <Shield className="w-3.5 h-3.5" style={{ color: s.color }} />
          </div>
        ))}
      </div>

      {/* Currency */}
      <div className="flex items-center gap-2">
        <CurrencyPill icon={Coins} color="#eab308" value={char.currency?.goud ?? 0} testid="cur-goud" />
        <CurrencyPill icon={Gem}   color="#06b6d4" value={char.currency?.gems ?? 0} testid="cur-gems" />
        <CurrencyPill icon={Heart} color="#a855f7" value={char.currency?.ziel ?? 0} testid="cur-ziel" />
      </div>

      {/* Edit-knop */}
      <button
        data-testid="char-edit-meta-btn"
        onClick={onEdit}
        title="Bewerk titel / klasse / fractie"
        className="w-8 h-8 rounded border border-amber-900/40 bg-stone-900/40 hover:bg-amber-900/30 text-amber-400 flex items-center justify-center">
        <Edit3 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

function CurrencyPill({ icon: Icon, color, value, testid }) {
  return (
    <div data-testid={testid} className="flex items-center gap-1.5 px-2 py-1 rounded-md border border-amber-900/40 bg-stone-900/60">
      <Icon className="w-4 h-4" style={{ color }} />
      <span className="text-sm font-mono font-bold text-amber-100">{Number(value || 0).toLocaleString('nl-NL')}</span>
    </div>
  );
}

// ----- BODY SILHOUETTE -----
function BodySilhouettePanel({ equipment, userId, isAdmin, onChange }) {
  const [editingSlot, setEditingSlot] = useState(null);

  return (
    <div className="relative p-3 min-h-[440px]">
      <div className="grid grid-cols-[1fr_minmax(110px,140px)_1fr] gap-3">
        {/* LINKS kolom */}
        <div className="flex flex-col gap-2">
          {SLOT_LAYOUT_LEFT.map(s => (
            <SlotCell key={s.key} slot={s} item={equipment[s.key]} align="right"
              onClick={() => setEditingSlot(s)} />
          ))}
        </div>

        {/* CENTRUM: silhouet + center slots */}
        <div className="flex flex-col items-center gap-2">
          {SLOT_LAYOUT_CENTER_TOP.map(s => (
            <SlotCell key={s.key} slot={s} item={equipment[s.key]} align="center"
              onClick={() => setEditingSlot(s)} />
          ))}
          <div className="relative w-[120px] h-[180px]">
            {/* SVG silhouet */}
            <svg viewBox="0 0 120 200" className="absolute inset-0 w-full h-full"
              fill="none" stroke="#fde68a" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" style={{ opacity: 0.35 }}>
              <circle cx="60" cy="22" r="14" />
              <path d="M40 38 Q60 30 80 38 L86 80 L72 90 L72 130 L80 180 L66 180 L60 130 L54 180 L40 180 L48 130 L48 90 L34 80 Z" fill="rgba(245,158,11,0.08)" />
              <line x1="34" y1="48" x2="14" y2="100" /><line x1="14" y1="100" x2="20" y2="140" />
              <line x1="86" y1="48" x2="106" y2="100" /><line x1="106" y1="100" x2="100" y2="140" />
            </svg>
          </div>
          {SLOT_LAYOUT_CENTER.map(s => (
            <SlotCell key={s.key} slot={s} item={equipment[s.key]} align="center"
              onClick={() => setEditingSlot(s)} />
          ))}
          {SLOT_LAYOUT_CENTER_BOTTOM.map(s => (
            <SlotCell key={s.key} slot={s} item={equipment[s.key]} align="center"
              onClick={() => setEditingSlot(s)} />
          ))}
        </div>

        {/* RECHTS kolom */}
        <div className="flex flex-col gap-2">
          {SLOT_LAYOUT_RIGHT.map(s => (
            <SlotCell key={s.key} slot={s} item={equipment[s.key]} align="left"
              onClick={() => setEditingSlot(s)} />
          ))}
        </div>
      </div>

      {editingSlot && (
        <EquipSlotModal
          slot={editingSlot}
          item={equipment[editingSlot.key]}
          userId={userId}
          onClose={() => setEditingSlot(null)}
          onSaved={() => { setEditingSlot(null); onChange?.(); }}
        />
      )}
    </div>
  );
}

function SlotCell({ slot, item, align = 'right', onClick }) {
  const filled = !!item;
  const naam = item?.naam || slot.fallback;
  return (
    <button
      data-testid={`slot-${slot.key}`}
      onClick={onClick}
      className={`group flex items-center gap-2 px-1 py-1 rounded ${align === 'right' ? 'flex-row-reverse text-right' : align === 'center' ? 'flex-col text-center' : 'flex-row text-left'} hover:bg-amber-900/10 transition-colors w-full`}
      style={{ minHeight: 50 }}
    >
      <div
        className={`w-10 h-10 rounded border-2 flex-shrink-0 flex items-center justify-center text-lg ${filled ? 'border-amber-500/60 bg-amber-950/40 text-amber-200' : 'border-amber-900/40 bg-stone-950/70 text-stone-700'}`}
        style={{ boxShadow: filled ? '0 0 12px rgba(245,158,11,0.3)' : 'none' }}>
        {item?.icon || (filled ? '✦' : '·')}
      </div>
      <div className={`flex-1 min-w-0 ${align === 'center' ? 'text-[8px]' : ''}`}>
        <p className="text-[8px] uppercase tracking-[0.15em] text-amber-500/70 truncate">{slot.label}</p>
        <p className={`text-[10px] truncate ${filled ? 'text-amber-100' : 'text-stone-500'}`}>{naam}</p>
      </div>
    </button>
  );
}

function EquipSlotModal({ slot, item, userId, onClose, onSaved }) {
  const [naam, setNaam] = useState(item?.naam || '');
  const [icon, setIcon] = useState(item?.icon || '');
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await fetch(`${API}/api/dnd/character/${userId}/equip`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_key: slot.key, item_id: naam ? `custom-${slot.key}` : null, naam: naam.trim(), icon }),
      });
      onSaved();
    } finally { setBusy(false); }
  };

  const unequip = async () => {
    setBusy(true);
    try {
      await fetch(`${API}/api/dnd/character/${userId}/equip`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_key: slot.key, item_id: null }),
      });
      onSaved();
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="equip-modal" className="bg-stone-950 border-2 border-amber-700/60 rounded-xl p-5 w-full max-w-md" onClick={e => e.stopPropagation()}>
        <h3 className="text-amber-100 font-serif text-lg mb-1">{slot.label}</h3>
        <p className="text-amber-400/60 text-xs mb-4">Equip een item in dit slot</p>
        <label className="block text-[10px] uppercase tracking-wider text-amber-400 mb-1">Item naam</label>
        <input data-testid="equip-input-naam" value={naam} onChange={e => setNaam(e.target.value)}
          placeholder={slot.fallback}
          className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100 mb-3" />
        <label className="block text-[10px] uppercase tracking-wider text-amber-400 mb-1">Icoon (emoji)</label>
        <input data-testid="equip-input-icon" value={icon} onChange={e => setIcon(e.target.value)}
          placeholder="🛡️ ⚔️ 💍 …" maxLength={4}
          className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100 mb-4" />
        <div className="flex gap-2 justify-between">
          <button data-testid="equip-unequip" onClick={unequip} disabled={busy || !item}
            className="px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded border border-red-900/40 disabled:opacity-30">
            Uitrusten
          </button>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-3 py-1.5 text-xs text-stone-300 hover:bg-stone-800 rounded">Annuleer</button>
            <button data-testid="equip-save" onClick={save} disabled={busy}
              className="px-4 py-1.5 text-xs bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold rounded">
              Opslaan
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ----- KARAKTER PORTRET -----
function KarakterPortretPanel({ avatarUrl, level, xpPct, xpInLvl, xpPerLvl, onOpenAvatarSettings }) {
  return (
    <PaperPanel>
      <PaperHeader>KARAKTER</PaperHeader>
      <div className="p-3 flex flex-col items-center">
        <button
          data-testid="char-portret"
          onClick={() => onOpenAvatarSettings?.('portrait')}
          className="relative w-full aspect-square max-w-[180px] rounded-lg overflow-hidden border-2 border-amber-700/60 group"
          style={{ boxShadow: '0 0 24px rgba(245,158,11,0.2), inset 0 0 24px rgba(0,0,0,0.6)' }}>
          {avatarUrl ? (
            <img src={avatarUrl} alt="" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-amber-900/40 to-stone-900 flex items-center justify-center">
              <User className="w-16 h-16 text-amber-700/60" />
            </div>
          )}
          <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-black/60 flex items-center justify-center transition-opacity">
            <Upload className="w-6 h-6 text-amber-300" />
          </div>
        </button>
        <p className="mt-2 text-amber-100 font-serif text-base">Niveau {level}</p>
        <div className="mt-1 w-full h-2 bg-stone-900 rounded-full overflow-hidden border border-amber-900/40">
          <div className="h-full bg-gradient-to-r from-amber-700 to-yellow-300" style={{ width: `${xpPct}%` }} />
        </div>
        <p className="text-[10px] text-amber-400/60 mt-0.5 font-mono">{xpInLvl} / {xpPerLvl}</p>
      </div>
    </PaperPanel>
  );
}

// ----- STATS PANEEL -----
function StatsPanel({ title, stats, accent }) {
  const STAT_ICONS = {
    'Kracht': '✦', 'Behendigheid': '✕', 'Intelligentie': '☉',
    'Conditie': '♥', 'Wilskracht': '⚑', 'Geluk': '✧',
    'Aanvalskracht': '⚔', 'Verdediging': '🛡', 'Magie Kracht': '✺',
    'Crit. Kans': '✷', 'Beweging': '➤', 'Initiatief': '⟳',
  };
  return (
    <PaperPanel>
      <PaperHeader>{title}</PaperHeader>
      <div className="p-2.5 space-y-1.5">
        {Object.entries(stats).map(([k, v]) => (
          <div key={k} data-testid={`stat-${k.replace(/[^a-z0-9]/gi, '-').toLowerCase()}`}
            className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-amber-200/90">
              <span style={{ color: accent }}>{STAT_ICONS[k] || '•'}</span>
              {k}
            </span>
            <span className="font-mono font-bold text-amber-100">
              {typeof v === 'number' && k.includes('Kans') ? `${v}%` : v}
            </span>
          </div>
        ))}
      </div>
    </PaperPanel>
  );
}

function OverigPanel({ char }) {
  const items = [
    { label: 'Klasse',  value: char.klasse  || '—', icon: '◉' },
    { label: 'Beroep',  value: char.beroep  || '—', icon: '◆' },
    { label: 'Fractie', value: char.fractie || '—', icon: '✦' },
    { label: 'Locatie', value: char.locatie_naam || '—', icon: '◎' },
  ];
  return (
    <PaperPanel>
      <PaperHeader>OVERIG</PaperHeader>
      <div className="p-2.5 space-y-1.5">
        {items.map(it => (
          <div key={it.label} className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-1.5 text-amber-200/90">
              <span className="text-amber-500/70">{it.icon}</span>{it.label}
            </span>
            <span className="font-mono text-amber-100 truncate ml-2 max-w-[60%] text-right">{it.value}</span>
          </div>
        ))}
      </div>
    </PaperPanel>
  );
}

// ----- INVENTORY GRID -----
function InventoryGridPanel({ userId }) {
  const [inv, setInv] = useState(null);
  useEffect(() => {
    fetch(`${API}/api/inventory/${userId}`).then(r => r.json()).then(setInv).catch(() => {});
  }, [userId]);

  const slots = inv?.slots || [];
  const total = 48; // 8 cols x 6 rows
  const filled = slots.length;

  return (
    <PaperPanel>
      <PaperHeader right={
        <div className="flex items-center gap-1 text-[10px] font-bold">
          {['Alle', '⚔', '🛡', '🧪', '🌿', '◆', '🗝', '📜'].map((t, i) => (
            <button key={i} data-testid={`inv-filter-${i}`}
              className="px-1.5 py-0.5 rounded hover:bg-amber-900/30 text-amber-300">
              {t}
            </button>
          ))}
        </div>
      }>INVENTORY</PaperHeader>
      <div className="p-2">
        <div data-testid="inv-grid" className="grid grid-cols-8 gap-1">
          {Array.from({ length: total }).map((_, i) => {
            const slot = slots[i];
            return (
              <div key={i}
                className={`aspect-square rounded border ${slot ? 'border-amber-700/60 bg-amber-950/30 flex items-center justify-center text-sm' : 'border-amber-900/30 bg-stone-950/50'}`}
                title={slot?.naam || ''}>
                {slot ? (slot.icon || '◆') : ''}
              </div>
            );
          })}
        </div>
        <div className="mt-2 flex items-center justify-between text-[10px] text-amber-400/80">
          <span data-testid="inv-weight-display">Gewicht: <span className="font-mono text-amber-200">{inv?.capacity?.weight_used ?? 0} / {inv?.capacity?.weight_max ?? 0}</span></span>
          <button className="px-2 py-0.5 rounded border border-amber-900/40 hover:bg-amber-900/30 text-amber-300">Sorteren</button>
        </div>
        <p className="text-[9px] text-amber-400/50 mt-1">Slots gebruikt: {filled} · capaciteit-cap (via rugzak/items) niet meegerekend op grid</p>
      </div>
    </PaperPanel>
  );
}

function HuisOpslagPanel() {
  return (
    <PaperPanel>
      <PaperHeader>HUIS &amp; OPSLAG</PaperHeader>
      <div className="grid grid-cols-2 gap-2 p-2">
        <div>
          <p className="text-[9px] uppercase tracking-wider text-amber-500/70 mb-1 text-center">Huis sloten</p>
          <div className="grid grid-cols-5 gap-1">
            {['🏠', '📦', '🗃', '⛪', '+'].map((c, i) => (
              <div key={i} className="aspect-square rounded border border-amber-900/40 bg-stone-950/60 flex items-center justify-center text-sm text-amber-300/70">{c}</div>
            ))}
          </div>
        </div>
        <div>
          <p className="text-[9px] uppercase tracking-wider text-amber-500/70 mb-1 text-center">Meubel sloten</p>
          <div className="grid grid-cols-5 gap-1">
            {['🪑', '🛏', '🗄', '🪟', '+'].map((c, i) => (
              <div key={i} className="aspect-square rounded border border-amber-900/40 bg-stone-950/60 flex items-center justify-center text-sm text-amber-300/70">{c}</div>
            ))}
          </div>
        </div>
      </div>
    </PaperPanel>
  );
}

function DorpPreviewPanel({ char, onNavigateMap }) {
  return (
    <PaperPanel>
      <PaperHeader>DORP</PaperHeader>
      <div className="relative h-32 overflow-hidden">
        {/* Placeholder dorps-illustratie */}
        <div className="absolute inset-0 bg-gradient-to-b from-stone-800 via-amber-950/40 to-stone-950">
          <svg viewBox="0 0 200 80" className="absolute bottom-0 w-full h-full" preserveAspectRatio="xMidYMax slice">
            <path d="M0 80 L0 60 L20 50 L20 40 L30 30 L40 40 L60 35 L70 25 L85 30 L100 18 L115 30 L130 25 L150 35 L170 30 L185 40 L200 50 L200 80 Z" fill="#451a03" />
            <path d="M30 50 L30 35 L40 30 L50 35 L50 50 Z" fill="#78350f" />
            <path d="M70 50 L70 30 L85 25 L100 30 L100 50 Z" fill="#78350f" />
            <path d="M120 50 L120 32 L135 28 L150 32 L150 50 Z" fill="#78350f" />
          </svg>
        </div>
        <div className="absolute top-2 right-2 text-right">
          <p className="text-[9px] uppercase tracking-wider text-amber-500/70">Dorp</p>
          <p data-testid="dorp-naam" className="text-sm font-serif font-bold text-amber-100">{char.dorp || 'Stormhaven'}</p>
          <p className="text-[10px] text-amber-300/70">Layout: Level {char.dorp_level ?? 1}</p>
          <p className="text-[10px] text-amber-300/70">Fog of War: {char.fog_of_war_pct ?? 0}%</p>
        </div>
        <button
          data-testid="dorp-kaart-btn"
          onClick={onNavigateMap}
          className="absolute bottom-2 right-2 text-[10px] px-2 py-1 rounded border border-amber-700/60 bg-stone-950/80 hover:bg-amber-900/40 text-amber-200">
          Kaart Bekijken
        </button>
      </div>
    </PaperPanel>
  );
}

function MiniMapPanel({ char }) {
  return (
    <PaperPanel>
      <PaperHeader>SPARK WORLD</PaperHeader>
      <div className="p-3 text-center">
        <Map className="w-10 h-10 mx-auto text-amber-500/70" />
        <p className="text-[11px] text-amber-200 mt-2 font-serif">{char.locatie_naam || 'Stormhaven'}</p>
        <p className="text-[9px] text-amber-400/60 mt-1">Interactieve map<br />komt in fase 2</p>
      </div>
    </PaperPanel>
  );
}

// ----- EVENT FEED -----
function EventFeedPanel({ feed, draft, setDraft, onSend }) {
  return (
    <PaperPanel>
      <PaperHeader>INFORMATIE · LAATSTE MELDINGEN</PaperHeader>
      <div className="p-2.5">
        <div data-testid="event-feed" className="space-y-1 max-h-44 overflow-y-auto pr-1">
          {(feed || []).slice(0, 10).map((ev, i) => (
            <div key={i} className="text-[11px] leading-snug">
              <span className="font-bold" style={{ color: FEED_COLORS[ev.kind] || '#f59e0b' }}>
                [{ev.kind}]
              </span>{' '}
              <span className="text-amber-100/90">{ev.text}</span>
            </div>
          ))}
          {(!feed || feed.length === 0) && (
            <p className="text-[11px] text-amber-400/50 italic">Nog geen meldingen.</p>
          )}
        </div>
        <div className="mt-2 flex gap-1">
          <input
            data-testid="event-input"
            value={draft}
            onChange={e => setDraft(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && onSend(draft)}
            placeholder="Typ hier je bericht…"
            className="flex-1 px-2 py-1.5 bg-stone-950 border border-amber-900/40 rounded text-xs text-amber-100 placeholder-amber-500/40"
          />
          <button
            data-testid="event-send"
            onClick={() => onSend(draft)}
            className="px-2.5 py-1.5 bg-amber-700 hover:bg-amber-600 rounded text-xs text-stone-950 font-bold flex items-center gap-1">
            <Send className="w-3 h-3" /> Verstuur
          </button>
        </div>
      </div>
    </PaperPanel>
  );
}

function CharInfoPanel({ char, activeTab, setActiveTab }) {
  const tabs = [
    { id: 'char_info', label: 'CHAR INFO' },
    { id: 'lore',      label: 'LORE' },
    { id: 'quest_log', label: 'QUEST LOG' },
    { id: 'notas',     label: 'Notas' },
  ];
  return (
    <PaperPanel>
      <div className="flex border-b border-amber-900/40">
        {tabs.map(t => {
          const a = activeTab === t.id;
          return (
            <button key={t.id} data-testid={`info-tab-${t.id}`}
              onClick={() => setActiveTab(t.id)}
              className={`flex-1 px-2 py-1.5 text-[10px] uppercase tracking-wider transition-colors ${a ? 'text-amber-200 bg-amber-900/20 border-b-2 border-amber-400' : 'text-amber-500/60 hover:text-amber-300'}`}>
              {t.label}
            </button>
          );
        })}
      </div>
      <div className="p-3 text-[11px] text-amber-100/90 leading-relaxed min-h-[140px]">
        {activeTab === 'char_info' && (
          <div className="space-y-1">
            <Row k="Naam"    v={char.titel} />
            <Row k="Titel"   v={char.ondertitel} />
            <Row k="Rang"    v={`${char.rang_titel} (Community Level ${char.derived?.level ?? 0}+)`} />
            <Row k="Klasse"  v={char.klasse  || '—'} />
            <Row k="Beroep"  v={char.beroep  || '—'} />
            <Row k="Fractie" v={char.fractie || '—'} />
            <Row k="Locatie" v={char.locatie_naam || '—'} />
            {char.bio && (
              <>
                <p className="text-amber-400/70 mt-2 mb-0.5">Bio:</p>
                <p className="text-amber-100/85 italic">{char.bio}</p>
              </>
            )}
          </div>
        )}
        {activeTab === 'lore' && (
          <p className="italic text-amber-400/60">Lore-fragmenten verschijnen hier zodra je ze ontdekt in Spark World.</p>
        )}
        {activeTab === 'quest_log' && (
          <p className="italic text-amber-400/60">Geen actieve quests. Spark zal er een aanbieden bij gedragspatronen.</p>
        )}
        {activeTab === 'notas' && (
          <p className="italic text-amber-400/60">Persoonlijke aantekeningen — komt binnenkort.</p>
        )}
      </div>
    </PaperPanel>
  );
}

function Row({ k, v }) {
  return (
    <div className="flex">
      <span className="text-amber-400/70 w-16">{k}:</span>
      <span className="flex-1 text-amber-100/90 truncate">{v}</span>
    </div>
  );
}

function FooterNav({ active, setActive }) {
  return (
    <div className="mt-4 flex border-t-2 border-amber-900/50 overflow-x-auto">
      {FOOTER_TABS.map(t => {
        const a = active === t.id;
        const Icon = t.icon;
        return (
          <button key={t.id} data-testid={`char-footer-${t.id}`}
            onClick={() => setActive(t.id)}
            className={`flex-shrink-0 flex items-center gap-1.5 px-3 py-2 text-[10px] uppercase tracking-wider transition-colors ${a ? 'text-amber-200 bg-amber-900/20' : 'text-amber-500/60 hover:text-amber-300 hover:bg-amber-900/10'}`}>
            <Icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

// ----- META EDIT MODAL -----
function EditMetaModal({ char, userId, onClose, onSaved }) {
  const [form, setForm] = useState({
    titel: char.titel || '',
    ondertitel: char.ondertitel || '',
    klasse: char.klasse || '',
    beroep: char.beroep || '',
    fractie: char.fractie || '',
    locatie_naam: char.locatie_naam || '',
    bio: char.bio || '',
    currency: { ...(char.currency || { goud: 0, gems: 0, ziel: 0 }) },
  });
  const [busy, setBusy] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await fetch(`${API}/api/dnd/character/${userId}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      onSaved();
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="edit-meta-modal" onClick={e => e.stopPropagation()}
        className="bg-stone-950 border-2 border-amber-700/60 rounded-xl p-5 w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <h3 className="text-amber-100 font-serif text-xl mb-3">Character bewerken</h3>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Titel"        v={form.titel}        onChange={v => setForm({ ...form, titel: v })} />
          <Field label="Ondertitel"   v={form.ondertitel}   onChange={v => setForm({ ...form, ondertitel: v })} />
          <Field label="Klasse"       v={form.klasse}       onChange={v => setForm({ ...form, klasse: v })} />
          <Field label="Beroep"       v={form.beroep}       onChange={v => setForm({ ...form, beroep: v })} />
          <Field label="Fractie"      v={form.fractie}      onChange={v => setForm({ ...form, fractie: v })} />
          <Field label="Locatie"      v={form.locatie_naam} onChange={v => setForm({ ...form, locatie_naam: v })} />
        </div>
        <Field label="Bio (langer)" v={form.bio} onChange={v => setForm({ ...form, bio: v })} textarea />

        <h4 className="text-amber-300 text-xs uppercase tracking-wider mt-4 mb-2">Currency</h4>
        <div className="grid grid-cols-3 gap-3">
          <NumField label="Goud" v={form.currency.goud} onChange={v => setForm({ ...form, currency: { ...form.currency, goud: v } })} />
          <NumField label="Gems" v={form.currency.gems} onChange={v => setForm({ ...form, currency: { ...form.currency, gems: v } })} />
          <NumField label="Ziel" v={form.currency.ziel} onChange={v => setForm({ ...form, currency: { ...form.currency, ziel: v } })} />
        </div>

        <div className="flex justify-end gap-2 mt-5">
          <button onClick={onClose} className="px-3 py-1.5 text-xs text-stone-300 hover:bg-stone-800 rounded">Annuleer</button>
          <button data-testid="meta-save-btn" onClick={save} disabled={busy}
            className="px-4 py-1.5 text-xs bg-amber-600 hover:bg-amber-500 text-stone-950 font-bold rounded flex items-center gap-1.5">
            <Save className="w-3 h-3" /> Opslaan
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, v, onChange, textarea }) {
  const id = `field-${label.toLowerCase().replace(/\s+/g, '-')}`;
  return (
    <div className={textarea ? 'col-span-2 mt-3' : ''}>
      <label className="block text-[10px] uppercase tracking-wider text-amber-400 mb-1">{label}</label>
      {textarea ? (
        <textarea data-testid={id} value={v} onChange={e => onChange(e.target.value)} rows={3}
          className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100" />
      ) : (
        <input data-testid={id} value={v} onChange={e => onChange(e.target.value)}
          className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100" />
      )}
    </div>
  );
}

function NumField({ label, v, onChange }) {
  return (
    <div>
      <label className="block text-[10px] uppercase tracking-wider text-amber-400 mb-1">{label}</label>
      <input
        data-testid={`cur-input-${label.toLowerCase()}`}
        type="number" value={v} onChange={e => onChange(parseInt(e.target.value || '0', 10))}
        className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100 font-mono" />
    </div>
  );
}

// ----- HUIS-STIJL FRAME COMPONENTS -----
function PaperPanel({ children }) {
  return (
    <div
      className="rounded-lg border-2 border-amber-900/40 bg-gradient-to-b from-stone-950 to-stone-900 overflow-hidden"
      style={{ boxShadow: 'inset 0 0 24px rgba(0,0,0,0.5), 0 0 0 1px rgba(245,158,11,0.1)' }}>
      {children}
    </div>
  );
}

function PaperHeader({ children, right }) {
  return (
    <div className="px-3 py-1.5 border-b border-amber-900/40 bg-gradient-to-r from-amber-950/40 to-stone-950 flex items-center justify-between">
      <h3 className="text-[10px] uppercase tracking-[0.25em] text-amber-300 font-serif font-bold">{children}</h3>
      {right}
    </div>
  );
}

export default DnDCharacterSheet;
