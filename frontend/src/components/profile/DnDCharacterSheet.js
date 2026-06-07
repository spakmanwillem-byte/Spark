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
import { StormhavenMapView } from './StormhavenMapView';
import { FractiesKaderPanel, LandkaartBark, StadDetailBark } from './FractiesTab';

const API = process.env.REACT_APP_BACKEND_URL;

// v6_item_image_match_001 — Koppel ITEM_CATALOG items aan D&D game-cards via tags/naam → 512x512 image
function findCardForItem(item, gameCards) {
  if (!item || !gameCards?.length) return null;
  const itemNaam = String(item.naam || '').toLowerCase().trim();
  const itemTags = (item.tags || []).map(t => String(t).toLowerCase());
  // Specifieke item_id → kaart-naam mapping (forceer match voor de basis-set)
  const ID_MAP = {
    'brood':         ['basis brood', 'brood'],
    'vlees':         ['basis vlees', 'vlees'],
    'water':         ['waterput', 'water'],
    'kaas':          ['kaas'],
    'appel':         ['appel'],
    'ei':            ['ei'],
    'fakkel':        ['fakkel', 'toorts', 'lantaarn'],
    'munt-goud':     ['goud', 'munt'],
    'zwaard-klein':  ['1 hand wapen rechts', 'zwaard', 'wapen rechts'],
    'schild-basis':  ['basis schild', 'schild'],
    'linnen-shirt':  ['t-shirt', 'shirt'],
    'linnen-broek':  ['broek basis', 'broek'],
    'lederen-helm':  ['hoofd', 'helm'],
    'leren-laarzen': ['schoenen', 'laarzen', 'voeten'],
    'backpack-basic':['basis rugzak', 'rugzak'],
    'backpack-large':['rugzak'],
  };
  const itemId = item.item_id || item.id || '';
  const wanted = ID_MAP[itemId] || [itemNaam, ...itemTags].filter(Boolean);

  for (const w of wanted) {
    const lw = String(w).toLowerCase().trim();
    // 1. exact begrip match
    const m1 = gameCards.find(c => String(c.begrip || '').toLowerCase().trim() === lw);
    if (m1) return m1;
  }
  for (const w of wanted) {
    const lw = String(w).toLowerCase().trim();
    // 2. begrip contains
    const m2 = gameCards.find(c => String(c.begrip || '').toLowerCase().includes(lw));
    if (m2) return m2;
    // 3. tag exact
    const m3 = gameCards.find(c => (c.tags || []).some(t => String(t).toLowerCase().trim() === lw));
    if (m3) return m3;
  }
  return null;
}

function itemImage(item, gameCards) {
  // v6_unified_001 — catalog-items uit /api/inventory/catalog/all hebben image_url direct
  if (item?.image_url) return `${API}${item.image_url}`;
  // Inventory.slots → item_id kan ook een card_id zijn (game-xxx)
  const itemId = item?.item_id || item?.id || '';
  if (typeof itemId === 'string' && itemId.startsWith('game-') && gameCards) {
    const c = gameCards.find(x => x.id === itemId);
    if (c) return cardFirstImage(c);
  }
  // Anders: fallback op findCardForItem (legacy hardcoded items)
  const card = findCardForItem(item, gameCards);
  return cardFirstImage(card);
}

// v6_dnd_card_visuals_001 — Helpers om D&D game-cards te koppelen aan plekken in de sheet
// Match-strategieën (in volgorde):
//   1. tag exact (case-insensitief): bv. tag "dorp" / "lijf" / "torso"
//   2. begrip exact: bv. begrip "dorp" / "t-shirt"
//   3. begrip bevat: bv. begrip "Basis Dorp" → match voor "dorp"
function findCardByKeywords(cards, keywords) {
  if (!cards || !cards.length) return null;
  const kws = keywords.map(k => String(k).toLowerCase().trim()).filter(Boolean);
  // 1. exact tag match (loop op kw eerst → eerste keyword wint)
  for (const kw of kws) {
    const m = cards.find(c => (c.tags || []).some(t => String(t).toLowerCase().trim() === kw));
    if (m) return m;
  }
  // 2. exact begrip match
  for (const kw of kws) {
    const m = cards.find(c => String(c.begrip || '').toLowerCase().trim() === kw);
    if (m) return m;
  }
  // 3. begrip-contains match
  for (const kw of kws) {
    const m = cards.find(c => String(c.begrip || '').toLowerCase().includes(kw));
    if (m) return m;
  }
  return null;
}

function cardFirstImage(card, apiUrl = API) {
  const u = card?.media?.image_urls?.[0];
  return u ? `${apiUrl}${u}` : null;
}

// v6_dnd_card_visuals_002 — uitgebreide synoniemen-lijst per slot (sluit aan op user's 31 D&D-kaarten)
const SLOT_SYNONYMS = {
  hoofd:       ['hoofd', 'helm', 'hoed', 'hoofdband', 'kroon', 'kap'],
  nek:         ['nek', 'ketting', 'sieraad', 'medaillon'],
  schouders:   ['schouders', 'schouder', 'schouderbeschermer', 'mantel'],
  armen:       ['armen', 'arm', 'pols', 'armband', 'polsband'],
  trinket:     ['trinket', 'medaillon', 'amulet'],
  torso:       ['torso', 't-shirt', 'shirt', 'hemd', 'borst', 'borstplaat', 'wambuis'],
  broek:       ['broek', 'benen', 'broeken', 'leggings'],
  voeten:      ['voeten', 'schoen', 'schoenen', 'laarzen', 'laars'],
  sjaal:       ['sjaal', 'doek'],
  riem:        ['riem', 'heuptas', 'gordel', 'gesp'],
  handen:      ['handen', 'hand', 'handschoenen', 'handschoen'],
  ring_l:      ['ring_l', 'ring (l)', 'ring'],
  ring_r:      ['ring_r', 'ring (r)', 'ring'],
  rugzak:      ['rugzak', 'tas', 'reistas'],
  linkerhand:  ['linkerhand', 'links', 'schild', 'buckler'],
  rechterhand: ['rechterhand', 'rechts', 'wapen', 'zwaard', 'staf', 'bijl', 'dolk'],
  offhand:     ['offhand', 'lantaarn', 'fakkel', 'toorts'],
  pijl_boog:   ['pijl_boog', 'pijl & boog', 'pijl en boog', 'boog', 'kruisboog'],
};

function getSlotKeywords(slot) {
  return SLOT_SYNONYMS[slot.key] || [slot.key, slot.label.toLowerCase(), slot.fallback.toLowerCase()];
}

function findCardForSlot(slot, cards) {
  return findCardByKeywords(cards, getSlotKeywords(slot));
}

// v6_dnd_body_layout_001 — Slot-layout komt nu uit backend `/api/dnd/body-layout` (admin-bewerkbaar)
// (oude constanten SLOT_LAYOUT_* en oude SlotCell component verwijderd in deze refactor)

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
  const [gameCards, setGameCards] = useState([]);
  const [inventory, setInventory] = useState(null);
  const [achievements, setAchievements] = useState([]);
  const [activeFooter, setActiveFooter] = useState('overzicht');
  const [infoTab, setInfoTab] = useState('char_info');
  const [editingMeta, setEditingMeta] = useState(false);
  const [eventDraft, setEventDraft] = useState('');
  const [showMapView, setShowMapView] = useState(false);
  // v6_bewoner_001 — bewoners + thuis-status + actieve bewoner (handel)
  const [bewoners, setBewoners] = useState([]);
  const [isHome, setIsHome] = useState(true);
  const [activeBewonerId, setActiveBewonerId] = useState(null);
  const [activeBewoner, setActiveBewoner] = useState(null);

  const reload = useCallback(() => {
    fetch(`${API}/api/dnd/character/${userId}`)
      .then(r => r.json())
      .then(setChar)
      .catch(() => {});
    // v6_dnd_rugzak_sync_001 — laad inventory zodat RUGZAK slot er mee kan syncen
    fetch(`${API}/api/inventory/${userId}`)
      .then(r => {
        if (!r.ok) return null;
        return r.json();
      })
      .then(d => {
        if (!d) return;
        setInventory(d);
        setAchievements(d.stats?.achievements || []);
      })
      .catch(() => {});
  }, [userId]);

  useEffect(() => { reload(); }, [reload]);

  useEffect(() => {
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setAvatarUrl(d.url ? `${API}${d.url}?t=${Date.now()}` : null))
      .catch(() => {});
  }, [userId]);

  // v6_dnd_card_visuals_001 — Laad D&D game-cards zodat we ze als visuele bouwstenen kunnen gebruiken
  useEffect(() => {
    fetch(`${API}/api/dnd/spark-world/game-cards?limit=500`)
      .then(r => r.json())
      .then(d => setGameCards(d.cards || []))
      .catch(() => setGameCards([]));
  }, []);

  // v6_bewoner_001 — bewoners van de huidige stad laden + is_home check
  useEffect(() => {
    if (!char?.dorp) return;
    fetch(`${API}/api/dnd/bewoners/?hoofdstad=${encodeURIComponent(char.dorp)}`)
      .then(r => r.json())
      .then(d => setBewoners(d.bewoners || []))
      .catch(() => setBewoners([]));
  }, [char?.dorp]);

  useEffect(() => {
    fetch(`${API}/api/inventory/${userId}/is-home`)
      .then(r => r.json())
      .then(d => setIsHome(!!d.is_home))
      .catch(() => {});
  }, [userId, char?.locatie_naam]);

  useEffect(() => {
    if (!activeBewonerId) { setActiveBewoner(null); return; }
    fetch(`${API}/api/dnd/bewoners/${activeBewonerId}`)
      .then(r => r.json())
      .then(setActiveBewoner)
      .catch(() => setActiveBewoner(null));
  }, [activeBewonerId, inventory]);

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

  // v6_transfer_001 — verplaats item tussen containers met thuis-check
  const transferItem = async (from_container, to_container, payload) => {
    try {
      const r = await fetch(`${API}/api/inventory/${userId}/transfer`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_container, to_container, ...payload }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        window.alert(e.detail || `Kon item niet verplaatsen (${r.status})`);
        return false;
      }
      reload();
      return true;
    } catch (err) {
      window.alert('Fout bij verplaatsen');
      return false;
    }
  };

  // v6_bewoner_001 — koop item uit bewoner-slot
  const buyFromBewoner = async (bewonerId, slotIdx) => {
    const r = await fetch(`${API}/api/dnd/bewoners/${bewonerId}/buy`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, bewoner_slot_index: slotIdx }),
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      window.alert(e.detail || 'Aankoop mislukt');
      return;
    }
    setActiveBewonerId(bewonerId);  // herlaad bewoner
    reload();
  };

  const sellToBewoner = async (bewonerId, slotId) => {
    const r = await fetch(`${API}/api/dnd/bewoners/${bewonerId}/sell`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, user_slot_id: slotId }),
    });
    if (!r.ok) {
      const e = await r.json().catch(() => ({}));
      window.alert(e.detail || 'Verkoop mislukt');
      return;
    }
    setActiveBewonerId(bewonerId);
    reload();
  };

  const xpInLvl = char.derived?.xp_in_level ?? 0;
  const xpPerLvl = char.derived?.xp_per_level ?? 100;
  const xpPct = Math.min(100, Math.round((xpInLvl / xpPerLvl) * 100));

  // v6_dnd_rugzak_sync_001 — RUGZAK slot toont automatisch de carry-item uit inventory.
  // Als geen rugzak ge-equipt is, maar inventory heeft een 'carry'-item, gebruik die als virtual equipment.
  const equipment = { ...(char.equipment || {}) };
  if (!equipment.rugzak && inventory?.slots) {
    const carry = inventory.slots.find(s => s.kind === 'carry');
    if (carry) {
      equipment.rugzak = {
        item_id: carry.item_id,
        naam: carry.naam,
        icon: carry.icon || '🎒',
        from_inventory: true,
        capacity_bonus: carry.capacity_bonus || 0,
        weight_bonus: carry.weight_bonus || 0,
      };
    }
  }

  // Vind dorpCard hier ook (zelfde logica als DorpPreviewPanel) zodat we hem aan map view kunnen geven
  const dorpCard = findCardByKeywords(gameCards, ['dorp', 'basis dorp', 'stad', char.dorp || '']);

  return (
    <div data-testid="dnd-character-sheet" className="relative">
      {/* ===== HEADER BAR — Titel | Rang | Shields | Currency ===== */}
      <CharacterHeaderBar
        char={char}
        isAdmin={isAdmin}
        achievements={achievements}
        onEdit={() => setEditingMeta(true)}
      />

      {/* ===== EVENT FEED — bovenaan, breed (Willem: info omhoog & breder) ===== */}
      <div className="mt-3">
        <EventFeedPanel
          feed={char.event_feed || []}
          draft={eventDraft}
          setDraft={setEventDraft}
          onSend={(t) => sendEvent('SYSTEEM', t)}
        />
      </div>

      {/* ===== HOOFD 3-KOLOMS LAYOUT ===== */}
      <div className="mt-3 grid grid-cols-12 gap-3">
        {/* === KOLOM LINKS: Body silhouet met slots + CharInfo === */}
        <div className="col-span-12 lg:col-span-5 space-y-3">
          <PaperPanel>
            <PaperHeader>BODY · EQUIPMENT</PaperHeader>
            <BodySilhouettePanel
              equipment={equipment}
              userId={userId}
              isAdmin={isAdmin}
              onChange={reload}
              gameCards={gameCards}
              capacity={inventory?.capacity || null}
            />
          </PaperPanel>
          {/* v6_dnd_layout_v2 — CharInfo verplaatst onder Body+Equipment (Willem 31 mei) */}
          <CharInfoPanel char={char} userId={userId} activeTab={infoTab} setActiveTab={setInfoTab} />
        </div>

        {/* === KOLOM MIDDEN: Karakter + Stats + Overig + Bewoners (2x3) === */}
        <div className="col-span-12 md:col-span-6 lg:col-span-3 space-y-3">
          <KarakterPortretPanel
            avatarUrl={avatarUrl}
            level={char.derived?.level ?? 0}
            xpPct={xpPct}
            xpInLvl={xpInLvl}
            xpPerLvl={xpPerLvl}
            onOpenAvatarSettings={onOpenAvatarSettings}
          />
          {/* v6_charinfo_consolidate_001 — Stats/Aanval/Overig samengevoegd in CharInfoPanel-tabs */}
          {/* v6_dice_001 — Dobbelsteen-paneel met jouw 2 D&D-kaart-avatars */}
          <DiceRollerPanel userId={userId} stats={char.statistieken || {}} onRolled={reload} />
          {/* v6_bewoners_layout_002 — Bewoners-strip compact 2x3=6 in MID-kolom onder Overig */}
          <BewonersStripPanel
            bewoners={bewoners}
            activeBewonerId={activeBewonerId}
            onSelect={setActiveBewonerId}
            char={char}
            compact={true}
          />
        </div>

        {/* === KOLOM RECHTS: Rugzak + Huis & Opslag + Dorp + Handel === */}
        <div className="col-span-12 md:col-span-6 lg:col-span-4 space-y-3">
          {/* v6_rugzak_kader_001 — Rugzak als eigen kader naast Huis & Opslag (mobile carry, met kg) */}
          <RugzakKaderPanel inventory={inventory} userId={userId} gameCards={gameCards} onChange={reload} onTransfer={transferItem} isHome={isHome} />
          {/* v6_dnd_layout_v2 — Huis & Opslag is stilstaand (500 slots, geen kg) */}
          <HuisOpslagPanel gameCards={gameCards} inventory={inventory} onTransfer={transferItem} isHome={isHome} />
          <DorpPreviewPanel char={char} gameCards={gameCards} onNavigateMap={() => setShowMapView(true)} />
          {/* v6_dnd_fracties_fullwidth_001 — MiniMapPanel verwijderd uit avatar-tab;
              FractiesKaderPanel is verplaatst naar volle breedte onder de grid (zie hieronder).
              Landkaart-bark blijft bereikbaar via de "Landkaart"-knop in FractiesKaderPanel. */}
          {/* v6_bewoners_layout_002 — Handel-kader onder Spark World map (geopend bij selectie) */}
          {activeBewoner && (
            <BewonerHandelPanel
              bewoner={activeBewoner}
              playerInventory={inventory}
              playerGoud={char.currency?.goud || 0}
              onBuy={(idx) => buyFromBewoner(activeBewoner.id, idx)}
              onSell={(slotId) => sellToBewoner(activeBewoner.id, slotId)}
              onClose={() => setActiveBewonerId(null)}
              gameCards={gameCards}
              compact={true}
            />
          )}
        </div>
      </div>

      {/* v6_dnd_fracties_fullwidth_001 — Fracties + Landkaart op volle beeldbreedte */}
      <div className="mt-3">
        <FractiesKaderPanel userId={userId} isAdmin={isAdmin} />
      </div>

      {/* (Bewoners-strip + Handel zijn verplaatst naar MID resp. RIGHT kolom hierboven) */}

      {/* ===== HANDEL-KADER VOORBEREIDING (rest van flow nog te bouwen) ===== */}
      <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3" data-testid="dnd-trade-prep">
        <div className="p-3 border border-dashed border-amber-900/40 rounded-lg bg-stone-950/50">
          <p className="text-[10px] uppercase tracking-wider text-amber-400/80 mb-1">🏪 Warehouse</p>
          <p className="text-[10px] text-amber-200/60 italic">Per stad/fractie · opslag voor handelaren · binnenkort</p>
        </div>
        <div className="p-3 border border-dashed border-amber-900/40 rounded-lg bg-stone-950/50">
          <p className="text-[10px] uppercase tracking-wider text-amber-400/80 mb-1">⚖️ Auction House</p>
          <p className="text-[10px] text-amber-200/60 italic">Loot kopen / verkopen · prijs per fractie · binnenkort</p>
        </div>
        <div className="p-3 border border-dashed border-amber-900/40 rounded-lg bg-stone-950/50">
          <p className="text-[10px] uppercase tracking-wider text-amber-400/80 mb-1">🍞 Werkbank</p>
          <p className="text-[10px] text-amber-200/60 italic">Thuis koken/maken · brood, vlees, drank · binnenkort</p>
        </div>
      </div>

      {/* (EventFeed + CharInfo zijn verplaatst — EventFeed bovenaan breed, CharInfo onder Body+Equipment) */}

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

      {/* ===== STORMHAVEN DORP-ZOOM ===== */}
      {showMapView && (
        <StormhavenMapView
          dorpCard={dorpCard}
          gameCards={gameCards}
          char={char}
          onClose={() => setShowMapView(false)}
        />
      )}
    </div>
  );
}

// ============================================================
// SUB-COMPONENTS
// ============================================================

function CharacterHeaderBar({ char, isAdmin, achievements = [], onEdit }) {
  // v6_dnd_military_stripes_001 — Leger-stijl: 1 streepje = 100 levels (chevron stripes)
  const level = char.derived?.level ?? 0;
  const fullStripes = Math.floor(level / 100);
  const partialPct = level % 100; // 0..99 → tweede chevron-fill
  const totalStripes = Math.max(fullStripes + 1, 3); // toon minimaal 3 chevrons als visueel kader
  const stripes = Array.from({ length: totalStripes }, (_, i) => ({
    full: i < fullStripes,
    partial: i === fullStripes ? partialPct : 0,
  }));

  return (
    <div
      data-testid="char-header-bar"
      className="rounded-xl border-2 border-amber-900/50 bg-gradient-to-r from-slate-950 via-stone-950 to-slate-950 px-3 py-2 flex items-center gap-3 flex-wrap"
      style={{
        boxShadow: 'inset 0 0 24px rgba(245,158,11,0.05), 0 0 0 1px rgba(245,158,11,0.15)',
      }}
    >
      {/* Banner-emblem + Achievement medals row */}
      <div className="relative">
        <div className="w-14 h-16 flex-shrink-0 rounded-md border border-amber-700/60 bg-gradient-to-b from-amber-900/40 to-purple-900/30 flex items-center justify-center">
          <Crown className="w-7 h-7 text-amber-400" />
        </div>
        {/* Medals stack onder de banner — max 4 zichtbaar */}
        {achievements.length > 0 && (
          <div data-testid="achievement-medals" className="absolute -bottom-2 left-1/2 -translate-x-1/2 flex -space-x-1.5">
            {achievements.slice(0, 4).map((a, i) => (
              <div key={a.code || i} title={a.naam || a.code}
                className="w-5 h-5 rounded-full bg-gradient-to-br from-amber-400 to-yellow-600 border-2 border-stone-950 flex items-center justify-center text-[10px] shadow-lg">
                🏅
              </div>
            ))}
            {achievements.length > 4 && (
              <div className="w-5 h-5 rounded-full bg-stone-800 border-2 border-stone-950 flex items-center justify-center text-[8px] text-amber-200 font-bold">
                +{achievements.length - 4}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Titel + Ondertitel */}
      <div className="flex-1 min-w-[160px]">
        <p className="text-[9px] uppercase tracking-[0.2em] text-amber-500/70">Titel</p>
        <h2 data-testid="char-titel" className="text-xl font-serif font-bold text-amber-100 leading-tight">
          {char.titel || 'Naamloos'}
        </h2>
        <p className="text-[11px] italic text-amber-300/60">{char.ondertitel || ''}</p>
      </div>

      {/* Rang + Militaire streepjes (100 levels = 1 streepje) */}
      <div className="border-l border-r border-amber-900/40 px-3 py-1">
        <p className="text-[9px] uppercase tracking-[0.2em] text-amber-500/70">Rang / Status</p>
        <p data-testid="char-rang" className="text-sm font-bold text-amber-100">{char.rang_titel || 'Burger'}</p>
        <p className="text-[10px] text-amber-400/60">Level {level} · {fullStripes} {fullStripes === 1 ? 'streep' : 'strepen'}</p>
        {/* Chevron stripes */}
        <div data-testid="rank-stripes" className="mt-1 flex items-center gap-0.5">
          {stripes.map((s, i) => (
            <RankStripe key={i} full={s.full} partial={s.partial} />
          ))}
        </div>
        <p className="text-[9px] text-amber-400/60 mt-0.5 font-mono">{partialPct}/100 tot volgende streep</p>
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

function RankStripe({ full, partial = 0 }) {
  // Chevron-stijl streepje (parallelogram met punt naar rechts)
  return (
    <div className="relative w-5 h-3.5 overflow-hidden"
      style={{ clipPath: 'polygon(0 0, 70% 0, 100% 50%, 70% 100%, 0 100%, 30% 50%)' }}>
      <div className="absolute inset-0 bg-stone-800/80" />
      <div
        className={`absolute inset-0 ${full ? 'bg-gradient-to-r from-amber-500 to-yellow-300' : 'bg-gradient-to-r from-amber-600 to-yellow-400'}`}
        style={{
          width: full ? '100%' : `${partial}%`,
          boxShadow: full ? 'inset 0 0 4px rgba(255,255,255,0.4)' : 'none',
        }} />
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

// v6_dnd_body_layout_001 — Body-avatar URL (goud-omlijnde silhouet, uploaded by user)
const BODY_AVATAR_URL = 'https://customer-assets.emergentagent.com/job_question-hub-160/artifacts/sb88yjie_WhatsApp%20Image%202026-05-29%20at%2023.58.26%20%281%29.jpeg';

// ----- BODY SILHOUETTE -----
function BodySilhouettePanel({ equipment, userId, isAdmin, onChange, gameCards = [], capacity = null }) {
  const [editingSlot, setEditingSlot] = useState(null);
  const [slotLayout, setSlotLayout] = useState([]);
  const [editMode, setEditMode] = useState(false);
  const [dragging, setDragging] = useState(null);
  const containerRef = useRef(null);

  // Laad sleepbare slot-posities (admin-bewerkbaar)
  const reloadLayout = useCallback(() => {
    fetch(`${API}/api/dnd/body-layout`)
      .then(r => r.json())
      .then(d => setSlotLayout(d.slots || []))
      .catch(() => {});
  }, []);
  useEffect(() => { reloadLayout(); }, [reloadLayout]);

  // Per slot: vind een matching kaart via gedeelde synoniemen
  const slotPreview = (slot) => cardFirstImage(findCardForSlot(slot, gameCards));

  const saveLayout = async (newSlots) => {
    setSlotLayout(newSlots);
    await fetch(`${API}/api/dnd/body-layout`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, slots: newSlots }),
    }).catch(() => {});
  };

  const resetLayout = async () => {
    if (!window.confirm('Reset alle slot-posities naar standaard?')) return;
    const r = await fetch(`${API}/api/dnd/body-layout/reset`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    }).then(x => x.json()).catch(() => null);
    if (r?.slots) setSlotLayout(r.slots);
  };

  const pointerToPct = (clientX, clientY) => {
    const el = containerRef.current;
    if (!el) return null;
    const rect = el.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * 100;
    const y = ((clientY - rect.top) / rect.height) * 100;
    return { x: Math.max(3, Math.min(97, x)), y: Math.max(3, Math.min(97, y)) };
  };

  const onPointerMove = (e) => {
    if (!dragging) return;
    const p = pointerToPct(e.clientX, e.clientY);
    if (!p) return;
    setSlotLayout(prev => prev.map(s => s.key === dragging ? { ...s, x: p.x, y: p.y } : s));
  };
  const onPointerUp = () => {
    if (!dragging) return;
    setDragging(null);
    saveLayout(slotLayout);
  };
  const onSlotPointerDown = (e, slot) => {
    if (editMode) {
      e.preventDefault();
      setDragging(slot.key);
      e.currentTarget.setPointerCapture?.(e.pointerId);
    } else {
      setEditingSlot(slot);
    }
  };

  return (
    <div className="relative">
      {isAdmin && (
        <div className="absolute top-1 right-1 z-20 flex gap-1">
          <button data-testid="body-edit-toggle" onClick={() => setEditMode(!editMode)}
            className={`text-[9px] px-1.5 py-0.5 rounded border ${editMode ? 'border-amber-400 bg-amber-500/30 text-amber-100' : 'border-amber-700/40 text-amber-300 hover:bg-amber-900/30 bg-stone-950/70'}`}>
            {editMode ? '✓ klaar' : '✏ sleep'}
          </button>
          {editMode && (
            <button data-testid="body-reset-btn" onClick={resetLayout}
              className="text-[9px] px-1.5 py-0.5 rounded border border-red-700/40 text-red-300 hover:bg-red-900/30 bg-stone-950/70">
              reset
            </button>
          )}
        </div>
      )}

      <div ref={containerRef}
        data-testid="body-silhouette"
        className="relative w-full overflow-hidden rounded select-none"
        style={{ paddingBottom: '125%', touchAction: 'none' }}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerLeave={onPointerUp}>

        {/* Body-avatar achtergrond (goud-silhouet upload) */}
        <img src={BODY_AVATAR_URL} alt="Body silhouet"
          className="absolute inset-0 w-full h-full object-cover"
          style={{ opacity: 0.95 }}
          draggable={false} />

        {/* Vignet voor leesbaarheid labels */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: 'radial-gradient(ellipse at center, transparent 30%, rgba(0,0,0,0.5) 100%)' }} />

        {/* Slot-frames absoluut gepositioneerd */}
        {slotLayout.map(slot => (
          <SlotFrame key={slot.key}
            slot={slot}
            item={equipment[slot.key]}
            preview={slotPreview(slot)}
            editMode={editMode}
            isDragging={dragging === slot.key}
            capacity={slot.key === 'rugzak' ? capacity : null}
            onPointerDown={(e) => onSlotPointerDown(e, slot)} />
        ))}
      </div>

      {editingSlot && (
        <EquipSlotModal
          slot={editingSlot}
          item={equipment[editingSlot.key]}
          previewCard={findCardForSlot(editingSlot, gameCards)}
          gameCards={gameCards}
          userId={userId}
          onClose={() => setEditingSlot(null)}
          onSaved={() => { setEditingSlot(null); onChange?.(); }}
        />
      )}

      {isAdmin && editMode && (
        <p className="text-[9px] text-amber-400/70 italic px-2 py-1 text-center">
          🖱 Sleep slot-frames over de avatar · ✓ klaar om vast te zetten
        </p>
      )}
    </div>
  );
}

function SlotFrame({ slot, item, preview, editMode, isDragging, onPointerDown, capacity = null }) {
  const filled = !!item;
  const naam = item?.naam || slot.fallback;
  // v6_rugzak_kg_001 — Rugzak slot toont kg-meter (gebruikt/max) onder de naam.
  const isRugzak = slot.key === 'rugzak';
  const kgUsed = capacity?.weight_used ?? 0;
  const kgMax = capacity?.weight_max ?? 0;
  const kgPct = kgMax > 0 ? Math.min(100, Math.round((kgUsed / kgMax) * 100)) : 0;
  const kgColor = kgPct >= 90 ? '#dc2626' : kgPct >= 70 ? '#eab308' : '#22c55e';
  return (
    <div
      data-testid={`slot-${slot.key}`}
      onPointerDown={onPointerDown}
      className={`absolute group ${editMode ? 'cursor-grab' : 'cursor-pointer'} ${isDragging ? 'z-30 scale-110' : 'z-10 hover:scale-105'}`}
      style={{
        left: `${slot.x}%`,
        top: `${slot.y}%`,
        transform: 'translate(-50%, -50%)',
        transition: isDragging ? 'none' : 'transform 0.15s',
      }}>
      {/* Frame box */}
      <div
        className={`relative w-10 h-10 rounded border-2 flex items-center justify-center text-base overflow-hidden ${filled ? 'border-amber-400 bg-amber-950/80' : preview ? 'border-amber-600/70 bg-stone-950/70' : 'border-amber-800/50 bg-stone-950/80'}`}
        style={{
          boxShadow: filled
            ? '0 0 14px rgba(245,158,11,0.6), inset 0 0 6px rgba(245,158,11,0.2)'
            : '0 0 6px rgba(0,0,0,0.7)',
        }}>
        {!filled && preview && (
          <img src={preview} alt="" className="absolute inset-0 w-full h-full object-cover"
            style={{ opacity: 0.55, filter: 'sepia(0.15)' }} draggable={false} />
        )}
        <span className="relative z-10 text-amber-100">
          {item?.icon || (filled ? '✦' : (preview ? '' : '·'))}
        </span>
        {item?.from_inventory && (
          <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border border-stone-950"
            title="Gesynced met inventory" />
        )}
      </div>

      {/* Label onder slot */}
      <div className="absolute left-1/2 top-full mt-0.5 -translate-x-1/2 text-center whitespace-nowrap pointer-events-none">
        <p className="text-[8px] uppercase tracking-[0.12em] text-amber-300/95 font-bold"
          style={{ paintOrder: 'stroke', WebkitTextStroke: '0.3px #000', textShadow: '0 1px 3px rgba(0,0,0,0.95)' }}>
          {slot.label}
        </p>
        <p className={`text-[8px] ${filled ? 'text-amber-100' : 'text-amber-200/60'}`}
          style={{ textShadow: '0 1px 3px rgba(0,0,0,0.95)' }}>
          {naam}
        </p>
        {isRugzak && kgMax > 0 && (
          <div data-testid="rugzak-kg-meter" className="mt-0.5 mx-auto" style={{ width: 56 }}>
            <p className="text-[8px] font-mono font-bold"
              style={{ color: kgColor, textShadow: '0 1px 3px rgba(0,0,0,0.95)' }}>
              {kgUsed.toFixed(1)}/{kgMax.toFixed(0)} kg
            </p>
            <div className="h-1 rounded-full bg-black/70 border border-amber-900/40 overflow-hidden">
              <div className="h-full transition-all" style={{ width: `${kgPct}%`, background: kgColor }} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EquipSlotModal({ slot, item, userId, onClose, onSaved, previewCard, gameCards = [] }) {
  const [naam, setNaam] = useState(item?.naam || '');
  const [icon, setIcon] = useState(item?.icon || '');
  const [busy, setBusy] = useState(false);
  // v6_item_stats_001 — catalog items voor dit slot (met stats_bonus preview)
  const [catalogItems, setCatalogItems] = useState([]);
  const [selectedCatalogItem, setSelectedCatalogItem] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/inventory/catalog/all`)
      .then(r => r.json())
      .then(d => {
        const all = d.items || [];
        const kw = getSlotKeywords(slot);
        const filtered = all.filter(it => {
          if (it.slot === slot.key) return true;
          const tags = (it.tags || []).map(t => String(t).toLowerCase());
          return kw.some(k => tags.includes(k));
        });
        setCatalogItems(filtered);
      })
      .catch(() => setCatalogItems([]));
  }, [slot.key]);

  // v6_dnd_card_visuals_002 — kandidaten uit D&D-galerij via gedeelde synoniemen
  const candidates = (() => {
    const kw = getSlotKeywords(slot);
    return (gameCards || []).filter(c => {
      const tags = (c.tags || []).map(t => String(t).toLowerCase());
      const begrip = String(c.begrip || '').toLowerCase();
      return kw.some(k => tags.includes(k) || begrip === k || begrip.includes(k));
    }).slice(0, 8);
  })();

  const pickCard = (c) => {
    setNaam(c.begrip || '');
    if (!icon) setIcon('🎴');
    setSelectedCatalogItem(null);
  };

  const pickCatalogItem = (it) => {
    setNaam(it.naam || '');
    setIcon(it.icon || '◆');
    setSelectedCatalogItem(it);
  };

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
      <div data-testid="equip-modal" className="bg-stone-950 border-2 border-amber-700/60 rounded-xl p-5 w-full max-w-md max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h3 className="text-amber-100 font-serif text-lg mb-1">{slot.label}</h3>
        <p className="text-amber-400/60 text-xs mb-4">Equip een item in dit slot</p>

        {/* Catalog items voor dit slot (met stats) */}
        {catalogItems.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] uppercase tracking-wider text-amber-400 mb-1.5">
              Item-catalogus ({catalogItems.length}) · stats inbegrepen
            </p>
            <div data-testid="equip-catalog-items" className="space-y-1.5">
              {catalogItems.map(it => {
                const sel = selectedCatalogItem?.id === it.id || (naam || '').toLowerCase() === (it.naam || '').toLowerCase();
                const statBonus = it.stats_bonus || {};
                const combatBonus = it.combat_bonus || {};
                const meta = it.meta || {};
                const itImg = itemImage({ ...it, item_id: it.id }, gameCards);
                return (
                  <button key={it.id} data-testid={`equip-catalog-${it.id}`}
                    onClick={() => pickCatalogItem(it)}
                    className={`w-full text-left p-2 rounded border transition-all ${sel ? 'border-amber-400 bg-amber-900/30 ring-1 ring-amber-400/40' : 'border-stone-700 hover:border-amber-600 bg-stone-900/40'}`}>
                    <div className="flex items-start gap-2">
                      <div className="w-12 h-12 rounded border border-amber-900/40 bg-stone-950/60 overflow-hidden flex items-center justify-center text-2xl shrink-0">
                        {itImg ? (
                          <img src={itImg} alt={it.naam} className="w-full h-full object-cover" />
                        ) : (
                          <span className="text-amber-200">{(it.naam || '?').charAt(0)}</span>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-bold text-amber-100 truncate">{it.naam}</p>
                          <span className="text-[10px] text-amber-400/70 font-mono shrink-0">{it.weight}kg</span>
                        </div>
                        {it.description && (
                          <p className="text-[10px] text-amber-300/60 italic mt-0.5 line-clamp-2">{it.description}</p>
                        )}
                        {/* Stats bonus pills */}
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {Object.entries(statBonus).map(([k, v]) => (
                            <span key={k} className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-900/40 border border-emerald-700/40 text-emerald-200 font-mono">
                              {v > 0 ? '+' : ''}{v} {k}
                            </span>
                          ))}
                          {Object.entries(combatBonus).map(([k, v]) => (
                            <span key={k} className={`text-[9px] px-1.5 py-0.5 rounded border font-mono ${v > 0 ? 'bg-red-900/40 border-red-700/40 text-red-200' : 'bg-amber-900/30 border-amber-700/40 text-amber-300/80'}`}>
                              {v > 0 ? '+' : ''}{v} {k}
                            </span>
                          ))}
                          {it.value_goud && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-yellow-900/40 border border-yellow-700/40 text-yellow-200 font-mono">
                              {it.value_goud}g
                            </span>
                          )}
                          {it.rarity && (
                            <span className="text-[9px] px-1.5 py-0.5 rounded bg-stone-800 border border-stone-600 text-stone-300 italic uppercase tracking-wider">
                              {it.rarity}
                            </span>
                          )}
                        </div>
                        {/* Meta (klasse/beroep/fractie/locatie) */}
                        {(meta.klasse || meta.beroep || meta.fractie || meta.locatie) && (
                          <p className="text-[9px] text-amber-400/50 mt-1">
                            {[meta.klasse && `Klasse: ${meta.klasse}`, meta.beroep && `Beroep: ${meta.beroep}`,
                              meta.fractie && `Fractie: ${meta.fractie}`, meta.locatie && `📍 ${meta.locatie}`]
                              .filter(Boolean).join(' · ')}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Kaart-suggesties uit D&D galerij */}
        {candidates.length > 0 && (
          <div className="mb-4">
            <p className="text-[10px] uppercase tracking-wider text-amber-400 mb-1.5">
              Snel kiezen uit D&amp;D-galerij ({candidates.length})
            </p>
            <div data-testid="equip-card-suggestions" className="grid grid-cols-4 gap-1.5">
              {candidates.map(c => {
                const img = cardFirstImage(c);
                const selected = (naam || '').toLowerCase() === (c.begrip || '').toLowerCase();
                return (
                  <button key={c.id} data-testid={`equip-pick-${c.id}`}
                    onClick={() => pickCard(c)} title={c.begrip}
                    className={`aspect-square rounded border-2 overflow-hidden transition-all ${selected ? 'border-amber-400 ring-2 ring-amber-400/40' : 'border-stone-700 hover:border-amber-600'}`}>
                    {img ? (
                      <img src={img} alt={c.begrip} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-amber-300 text-lg bg-stone-900">🎴</div>
                    )}
                  </button>
                );
              })}
            </div>
            <p className="text-[9px] text-stone-500 mt-1 italic">Tip: voeg tag <code className="text-amber-300">{slot.key}</code> aan een D&amp;D-kaart om hem hier te laten zien.</p>
          </div>
        )}

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

function OverigPanel({ char, userId }) {
  // v6_rps_battle_001 — battles + goud onder Locatie
  const [rps, setRps] = React.useState({ battles_won: 0, battles_lost: 0, gold: 1000 });
  React.useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/games/rps/stats?user_id=${userId}`)
      .then(r => r.json())
      .then(d => setRps({
        battles_won: d.stats?.battles_won || 0,
        battles_lost: d.stats?.battles_lost || 0,
        gold: d.stats?.gold ?? 1000,
      }))
      .catch(() => {});
  }, [userId]);

  const items = [
    { label: 'Klasse',  value: char.klasse  || '—', icon: '◉' },
    { label: 'Beroep',  value: char.beroep  || '—', icon: '◆' },
    { label: 'Fractie', value: char.fractie || '—', icon: '✦' },
    { label: 'Locatie', value: char.locatie_naam || '—', icon: '◎' },
    { label: 'Battles', value: `${rps.battles_won} W · ${rps.battles_lost} L`, icon: '⚔', testid: 'charinfo-battles' },
    { label: 'Goud',    value: `${rps.gold}`, icon: '🪙', testid: 'charinfo-gold' },
  ];
  return (
    <PaperPanel>
      <PaperHeader>OVERIG</PaperHeader>
      <div className="p-2.5 space-y-1.5">
        {items.map(it => (
          <div key={it.label} className="flex items-center justify-between text-xs" data-testid={it.testid}>
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
function InventoryGridPanel({ userId, inventory: invProp }) {
  const [inv, setInv] = useState(invProp || null);
  useEffect(() => {
    if (invProp) { setInv(invProp); return; }
    fetch(`${API}/api/inventory/${userId}`).then(r => r.json()).then(setInv).catch(() => {});
  }, [userId, invProp]);

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

// v6_rugzak_kader_002 — Eigen kader voor de Rugzak (mobile carry, met kg-limiet)
// 32-slot grid (8×4), items tonen jouw 512x512 D&D-kaart images (geen emojis), vullen via gameplay
function RugzakKaderPanel({ inventory = null, userId, gameCards = [], onChange, onTransfer, isHome = true }) {
  // Filter alleen rugzak-items (location !== 'huis')
  const allSlots = inventory?.slots || [];
  const slots = allSlots.filter(s => (s.location || 'rugzak') !== 'huis');
  const cap = inventory?.capacity || { weight_used: 0, weight_max: 0, slots_used: 0, slots_total: 0 };
  const VISIBLE_SLOTS = 32; // 8 cols × 4 rows
  const kgUsed = cap.weight_used || 0;
  const kgMax = cap.weight_max || 0;
  const kgPct = kgMax > 0 ? Math.min(100, Math.round((kgUsed / kgMax) * 100)) : 0;
  const kgColor = kgPct >= 90 ? '#dc2626' : kgPct >= 70 ? '#eab308' : '#22c55e';

  // Speed-modifier op basis van kg-vulling (kosmetisch indicator)
  const speedLabel =
    kgPct >= 90 ? 'Zwaar geladen — traag' :
    kgPct >= 70 ? 'Vol — iets trager' :
    kgPct >= 40 ? 'Goede balans' : 'Licht — snel';

  const removeItem = async (slot_id) => {
    if (!window.confirm('Item uit rugzak halen?')) return;
    await fetch(`${API}/api/inventory/${userId}/items/${slot_id}`, { method: 'DELETE' }).catch(() => {});
    onChange?.();
  };

  const moveToHuis = async (e, slot_id) => {
    e.stopPropagation();
    if (!isHome) { window.alert('Niet thuis: ga eerst terug naar je dorp.'); return; }
    await onTransfer?.('rugzak', 'huis', { slot_id });
  };

  return (
    <PaperPanel>
      <PaperHeader right={
        <span className="text-[10px] font-mono font-bold" data-testid="rugzak-kg-counter" style={{ color: kgColor }}>
          {kgUsed.toFixed(1)} / {kgMax.toFixed(0)} kg
        </span>
      }>RUGZAK · ONDERWEG</PaperHeader>
      <div className="p-3 space-y-2.5">
        <p className="text-[10px] text-amber-300/70 italic -mt-0.5">
          🎒 Wat je meeneemt op pad. Meer kg = langzamer. Items vullen de slots wanneer je ze vindt of koopt.
        </p>

        {/* Kg progress bar */}
        <div data-testid="rugzak-kg-bar" className="space-y-1">
          <div className="h-2 rounded-full bg-black/70 border border-amber-900/40 overflow-hidden">
            <div className="h-full transition-all" style={{ width: `${kgPct}%`, background: kgColor }} />
          </div>
          <div className="flex justify-between text-[9px]">
            <span className="text-amber-400/80">Slots: <span className="font-mono text-amber-200">{cap.slots_used || 0}/{cap.slots_total || 0}</span></span>
            <span style={{ color: kgColor }} className="italic font-medium">{speedLabel}</span>
          </div>
        </div>

        {/* 32-slot grid (8x4) — items tonen 512x512 D&D images */}
        <div data-testid="rugzak-grid" className="grid grid-cols-8 gap-1">
          {Array.from({ length: VISIBLE_SLOTS }).map((_, i) => {
            const item = slots[i];
            const img = item ? itemImage(item, gameCards) : null;
            return (
              <div key={i} data-testid={`rugzak-slot-${i}`}
                title={item ? `${item.naam} · ${item.weight || 0}kg${item.value_goud ? ` · ${item.value_goud}g` : ''}` : ''}
                className={`aspect-square rounded border overflow-hidden relative group ${item ? 'border-amber-700/60 bg-amber-950/40' : 'border-amber-900/30 bg-stone-950/50'}`}>
                {item && img && (
                  <img src={img} alt={item.naam} className="absolute inset-0 w-full h-full object-cover" />
                )}
                {item && !img && (
                  <span className="absolute inset-0 flex items-center justify-center text-sm text-amber-200">{item.naam?.charAt(0)}</span>
                )}
                {item && (
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-black/75 flex flex-col items-center justify-center gap-0.5 transition-opacity">
                    {isHome && (
                      <button data-testid={`rugzak-tohome-${i}`} onClick={(e) => moveToHuis(e, item.id)}
                        className="text-[8px] px-1 py-0.5 bg-amber-600 hover:bg-amber-500 text-stone-950 rounded font-bold">
                        → Huis
                      </button>
                    )}
                    <button data-testid={`rugzak-drop-${i}`} onClick={() => removeItem(item.id)}
                      className="text-[8px] px-1 py-0.5 bg-red-700 hover:bg-red-600 text-stone-100 rounded">
                      Drop
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </PaperPanel>
  );
}



function HuisOpslagPanel({ gameCards = [], inventory = null, onTransfer, isHome = true }) {
  const HUIS_TAGS = ['huis', 'gebouw', 'opslag', 'locatie'];
  const MEUBEL_TAGS = ['meubel'];
  const STORAGE_MAX = 500;
  const VISIBLE_STORAGE_SLOTS = 32; // 8 cols × 4 rows venster op de 500 totaal

  const isHuis = c => {
    const tags = (c.tags || []).map(t => String(t).toLowerCase());
    const begrip = String(c.begrip || '').toLowerCase();
    return HUIS_TAGS.some(t => tags.includes(t)) || begrip.includes('huis') || begrip.includes('gebouw') || begrip.includes('straat');
  };
  const isMeubel = c => {
    const tags = (c.tags || []).map(t => String(t).toLowerCase());
    const begrip = String(c.begrip || '').toLowerCase();
    return MEUBEL_TAGS.some(t => tags.includes(t))
      || ['stoel', 'bed', 'kast', 'kist', 'tafel', 'bank'].some(w => begrip.includes(w));
  };

  const huisCards = (gameCards || []).filter(isHuis).slice(0, 5);
  const huisIds = new Set(huisCards.map(c => c.id));
  const meubelCards = (gameCards || []).filter(c => isMeubel(c) && !huisIds.has(c.id)).slice(0, 5);

  const fallbackHuis = ['🏠', '📦', '🗃', '⛪', '+'];
  const fallbackMeubel = ['🪑', '🛏', '🗄', '🪟', '+'];

  // Opslag items (uit inventory.slots, alleen waar location=='huis')
  const allSlots = inventory?.slots || [];
  const storageItems = allSlots.filter(s => s.location === 'huis');
  const storageUsed = storageItems.length;

  const moveToRugzak = async (e, slot_id) => {
    e.stopPropagation();
    if (!isHome) { window.alert('Niet thuis: ga eerst terug naar je dorp.'); return; }
    await onTransfer?.('huis', 'rugzak', { slot_id });
  };

  return (
    <PaperPanel>
      <PaperHeader right={
        <span className="text-[10px] font-mono text-amber-300/80" data-testid="opslag-cap-counter">
          Opslag <span className="text-amber-200">{storageUsed}</span>/{STORAGE_MAX} · <span className="text-emerald-300/80 italic">geen kg-limiet</span>
        </span>
      }>HUIS &amp; OPSLAG · STILSTAAND</PaperHeader>
      <div className="space-y-3 p-3">
        <p className="text-[10px] text-emerald-300/70 italic -mt-1">
          🏠 Hier staat alles stil — bereid eten, sla loot op, geen gewicht-restrictie. Pak in je rugzak wat je meeneemt op pad.
        </p>
        {/* Rij 1: Huis + Meubel slots */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-wider text-amber-500/70 mb-1.5 text-center">Huis sloten</p>
            <div className="grid grid-cols-5 gap-1.5">
              {[0, 1, 2, 3, 4].map(i => {
                const card = huisCards[i];
                const img = cardFirstImage(card);
                return (
                  <div key={i} data-testid={`huis-slot-${i}`}
                    className="aspect-square min-h-[56px] rounded border border-amber-900/40 bg-stone-950/60 flex items-center justify-center text-2xl text-amber-300/70 overflow-hidden relative"
                    title={card?.begrip || ''}>
                    {img ? (
                      <img src={img} alt={card.begrip} className="absolute inset-0 w-full h-full object-cover" />
                    ) : (
                      <span>{fallbackHuis[i]}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider text-amber-500/70 mb-1.5 text-center">Meubel sloten</p>
            <div className="grid grid-cols-5 gap-1.5">
              {[0, 1, 2, 3, 4].map(i => {
                const card = meubelCards[i];
                const img = cardFirstImage(card);
                return (
                  <div key={i} data-testid={`meubel-slot-${i}`}
                    className="aspect-square min-h-[56px] rounded border border-amber-900/40 bg-stone-950/60 flex items-center justify-center text-2xl text-amber-300/70 overflow-hidden relative"
                    title={card?.begrip || ''}>
                    {img ? (
                      <img src={img} alt={card.begrip} className="absolute inset-0 w-full h-full object-cover" />
                    ) : (
                      <span>{fallbackMeubel[i]}</span>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Rij 2: Opslag grid (master inventory) */}
        <div>
          <p className="text-[10px] uppercase tracking-wider text-amber-500/70 mb-1.5 text-center">Opslag (eerste {VISIBLE_STORAGE_SLOTS} van {STORAGE_MAX})</p>
          <div data-testid="opslag-grid" className="grid grid-cols-8 gap-1">
            {Array.from({ length: VISIBLE_STORAGE_SLOTS }).map((_, i) => {
              const item = storageItems[i];
              const img = item ? itemImage(item, gameCards) : null;
              return (
                <div key={i} data-testid={`opslag-slot-${i}`}
                  className={`aspect-square rounded border overflow-hidden relative group ${item ? 'border-amber-700/60 bg-amber-950/30' : 'border-amber-900/30 bg-stone-950/50'}`}
                  title={item?.naam || ''}>
                  {item && img && (
                    <img src={img} alt={item.naam} className="absolute inset-0 w-full h-full object-cover" />
                  )}
                  {item && !img && (
                    <span className="absolute inset-0 flex items-center justify-center text-sm text-amber-200">{item.naam?.charAt(0)}</span>
                  )}
                  {item && isHome && (
                    <div className="absolute inset-0 opacity-0 group-hover:opacity-100 bg-black/75 flex items-center justify-center transition-opacity">
                      <button data-testid={`opslag-torug-${i}`} onClick={(e) => moveToRugzak(e, item.id)}
                        className="text-[8px] px-1 py-0.5 bg-amber-600 hover:bg-amber-500 text-stone-950 rounded font-bold">
                        → Rugzak
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </PaperPanel>
  );
}

function DorpPreviewPanel({ char, gameCards = [], onNavigateMap }) {
  // v6_dnd_card_visuals_001 — gebruik basis-dorp D&D-kaart als achtergrond
  const dorpCard = findCardByKeywords(gameCards, ['dorp', 'basis dorp', 'stad', char.dorp || '']);
  const dorpImg = cardFirstImage(dorpCard);
  const dorpNaam = dorpCard?.begrip || char.dorp || 'Stormhaven';

  return (
    <PaperPanel>
      <PaperHeader>DORP</PaperHeader>
      <div className="relative h-52 overflow-hidden rounded-md m-2 group">
        {dorpImg ? (
          <img src={dorpImg} alt={dorpNaam}
            className="absolute inset-0 w-full h-full object-cover" />
        ) : (
          /* Fallback: getekende dorp-illustratie */
          <div className="absolute inset-0 bg-gradient-to-b from-stone-800 via-amber-950/40 to-stone-950">
            <svg viewBox="0 0 200 80" className="absolute bottom-0 w-full h-full" preserveAspectRatio="xMidYMax slice">
              <path d="M0 80 L0 60 L20 50 L20 40 L30 30 L40 40 L60 35 L70 25 L85 30 L100 18 L115 30 L130 25 L150 35 L170 30 L185 40 L200 50 L200 80 Z" fill="#451a03" />
              <path d="M30 50 L30 35 L40 30 L50 35 L50 50 Z" fill="#78350f" />
              <path d="M70 50 L70 30 L85 25 L100 30 L100 50 Z" fill="#78350f" />
              <path d="M120 50 L120 32 L135 28 L150 32 L150 50 Z" fill="#78350f" />
            </svg>
          </div>
        )}
        {/* Vignet zodat tekst leesbaar blijft over willekeurige foto */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-black/40 pointer-events-none" />

        <div className="absolute top-2 right-2 text-right">
          <p className="text-[9px] uppercase tracking-wider text-amber-300/90">Dorp</p>
          <p data-testid="dorp-naam" className="text-sm font-serif font-bold text-amber-100">{dorpNaam}</p>
          <p className="text-[10px] text-amber-200/85">Layout: Level {char.dorp_level ?? 1}</p>
          <p className="text-[10px] text-amber-200/85">Fog of War: {char.fog_of_war_pct ?? 0}%</p>
        </div>
        <button
          data-testid="dorp-kaart-btn"
          onClick={onNavigateMap}
          className="absolute bottom-2 right-2 text-[10px] px-2 py-1 rounded border border-amber-700/60 bg-stone-950/80 hover:bg-amber-900/40 text-amber-200 font-bold uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-opacity">
          Kaart Bekijken
        </button>
      </div>
    </PaperPanel>
  );
}

function MiniMapPanel({ char, userId, isAdmin }) {
  // v6_dnd_world_001 — 12 provincies + fractie shields op de "Nederland map kaal" achtergrond
  // v6_map_avatars_001 — provincies tonen nu hoofdstad-avatar (eerste bewoner) i.p.v. lege stip
  const NL_MAP_URL = 'https://customer-assets.emergentagent.com/job_question-hub-160/artifacts/pkw3x971_Nederland%20map%20kaal.jpeg';
  const [provincies, setProvincies] = useState([]);
  const [fracties, setFracties] = useState([]);
  const [dorpAvatarUrl, setDorpAvatarUrl] = useState(null);
  const [stadAvatarUrl, setStadAvatarUrl] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [dragging, setDragging] = useState(null);
  const [selectedProv, setSelectedProv] = useState(null);
  // v6_spark_world_kaart_btn_001 — "Kaart Bekijken" knop opent zelfde NL-bark als Fracties
  const [showLandkaart, setShowLandkaart] = useState(false);
  const [steden, setSteden] = useState([]);
  const [openStad, setOpenStad] = useState(null);
  const svgRef = useRef(null);

  const reload = useCallback(() => {
    fetch(`${API}/api/dnd/world/provincies`)
      .then(r => r.json())
      .then(d => { setProvincies(d.provincies || []); setFracties(d.fracties || []); })
      .catch(() => {});
    // v6_spark_world_kaart_btn_001 — steden voor de Kaart Bekijken bark
    fetch(`${API}/api/dnd/world/steden`)
      .then(r => r.json())
      .then(d => setSteden(d.steden || []))
      .catch(() => {});
    // Basis dorp + Basis stad als avatars per provincie (groei-logica: spark hoofdstad = stad, rest = dorp)
    fetch(`${API}/api/dnd/spark-world/game-cards?limit=500`)
      .then(r => r.json())
      .then(d => {
        const cards = d.cards || [];
        const findFirst = (...begrippen) => {
          for (const b of begrippen) {
            const lb = b.toLowerCase().trim();
            const c = cards.find(x => (x.begrip || '').toLowerCase().trim() === lb);
            if (c) return c;
          }
          return null;
        };
        const dorp = findFirst('basis dorp', 'Basis dorp');
        const stad = findFirst('basis stad', 'Basis Stad');
        const dorpImg = dorp?.media?.image_urls?.[0];
        const stadImg = stad?.media?.image_urls?.[0];
        if (dorpImg) setDorpAvatarUrl(dorpImg);
        if (stadImg) setStadAvatarUrl(stadImg);
      })
      .catch(() => {});
  }, []);
  useEffect(() => { reload(); }, [reload]);

  const fractieOf = (fid) => fracties.find(f => f.id === fid) || fracties.find(f => f.id === 'neutraal') || {};

  const saveProvincie = async (id, patch) => {
    setProvincies(prev => prev.map(p => p.id === id ? { ...p, ...patch } : p));
    await fetch(`${API}/api/dnd/world/provincies`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, updates: [{ id, ...patch }] }),
    }).catch(() => {});
  };

  const resetAll = async () => {
    if (!window.confirm('Reset alle 12 provincies naar standaard mapping?')) return;
    const r = await fetch(`${API}/api/dnd/world/provincies/reset`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    }).then(x => x.json()).catch(() => null);
    if (r?.provincies) setProvincies(r.provincies);
  };

  const svgFromPointer = (clientX, clientY) => {
    const svg = svgRef.current;
    if (!svg) return null;
    const rect = svg.getBoundingClientRect();
    const x = ((clientX - rect.left) / rect.width) * 100;
    const y = ((clientY - rect.top) / rect.height) * 100;
    return { x_pct: Math.max(2, Math.min(98, x)), y_pct: Math.max(2, Math.min(98, y)) };
  };

  const onPointerDown = (e, id) => {
    if (!editMode) { setSelectedProv(id === selectedProv ? null : id); return; }
    e.preventDefault();
    setDragging(id);
    e.currentTarget.setPointerCapture?.(e.pointerId);
  };
  const onPointerMove = (e) => {
    if (!dragging) return;
    const p = svgFromPointer(e.clientX, e.clientY);
    if (!p) return;
    setProvincies(prev => prev.map(prov => prov.id === dragging ? { ...prov, ...p } : prov));
  };
  const onPointerUp = () => {
    if (!dragging) return;
    const prov = provincies.find(p => p.id === dragging);
    if (prov) saveProvincie(dragging, { x_pct: prov.x_pct, y_pct: prov.y_pct });
    setDragging(null);
  };

  const selProv = selectedProv ? provincies.find(p => p.id === selectedProv) : null;
  const selFrac = selProv ? fractieOf(selProv.fractie_id) : null;

  return (
    <PaperPanel>
      <PaperHeader>SPARK WORLD · 12 PROVINCIES</PaperHeader>

      <div className="relative p-2 select-none">
        <div className="relative rounded-md overflow-hidden group">
          <svg ref={svgRef} viewBox="0 0 100 100" className="w-full h-72 block"
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerLeave={onPointerUp}
            style={{ touchAction: 'none', cursor: dragging ? 'grabbing' : 'default' }}>
          <image href={NL_MAP_URL} x="0" y="0" width="100" height="100"
            preserveAspectRatio="xMidYMid slice" />

          {/* Provincie shields — v6_dnd_fractie_marker_001: fractie-avatar voorrang boven dorp/stad */}
          {provincies.map(p => {
            const f = fractieOf(p.fractie_id);
            // v6_map_markers_uniform_001 — alle markers zelfde grootte, geen glow
            const isMain = p.fractie_id === 'spark';
            const baseR = 4.0;
            const isSelected = selectedProv === p.id;
            const glowColor = f.kleur || '#94a3b8';
            // v6_dnd_fractie_marker_001 — Marker-avatar prioriteit:
            //   1. fractie icon/banner (uit fracties.json) als ingevuld
            //   2. fallback naar basis-stad/basis-dorp avatar
            //   3. anders fractie-shield (gevulde cirkel)
            const isStad = p.fractie_id === 'spark';
            const fallbackAvatar = isStad ? (stadAvatarUrl || dorpAvatarUrl) : dorpAvatarUrl;
            const avatarUrl = f.icon_image_url || f.banner_image_url || fallbackAvatar;
            const isPlayerHere = (char?.dorp || '').toLowerCase() === (p.hoofdstad || '').toLowerCase();
            return (
              <g key={p.id} data-testid={`prov-${p.id}`}
                onPointerDown={(e) => onPointerDown(e, p.id)}
                style={{ cursor: editMode ? 'grab' : 'pointer' }}>
                {/* Avatar-circle als beschikbaar, anders fractie-shield */}
                {avatarUrl ? (
                  <>
                    <defs>
                      <clipPath id={`clip-${p.id}`}>
                        <circle cx={p.x_pct} cy={p.y_pct} r={baseR} />
                      </clipPath>
                    </defs>
                    <image href={`${API}${avatarUrl}`}
                      x={p.x_pct - baseR} y={p.y_pct - baseR}
                      width={baseR * 2} height={baseR * 2}
                      clipPath={`url(#clip-${p.id})`}
                      preserveAspectRatio="xMidYMid slice" />
                    <circle cx={p.x_pct} cy={p.y_pct} r={baseR}
                      fill="none"
                      stroke={isSelected ? '#fde68a' : glowColor}
                      strokeWidth={isSelected ? 0.8 : 0.5}
                      opacity="0.85" />
                  </>
                ) : (
                  <>
                    <circle cx={p.x_pct} cy={p.y_pct} r={baseR}
                      fill={glowColor}
                      stroke={isSelected ? '#fde68a' : '#000'}
                      strokeWidth={isSelected ? 0.8 : 0.4}
                      opacity={p.fractie_id === 'neutraal' ? 0.55 : 0.85} />
                    <circle cx={p.x_pct} cy={p.y_pct} r={1.3}
                      fill="#fef3c7"
                      opacity="0.85" />
                  </>
                )}
                {/* Speler-glow-dot — pulse op huidige locatie */}
                {isPlayerHere && (
                  <>
                    <circle cx={p.x_pct} cy={p.y_pct + baseR + 0.5} r={1.2}
                      fill="#22c55e"
                      style={{ filter: 'drop-shadow(0 0 4px #22c55e)' }}>
                      <animate attributeName="r" values="1.2;2;1.2" dur="1.8s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="1;0.4;1" dur="1.8s" repeatCount="indefinite" />
                    </circle>
                    <title>Jij bent hier</title>
                  </>
                )}
                {/* Label */}
                <text x={p.x_pct} y={p.y_pct + baseR + 2.4} textAnchor="middle"
                  fill="#fde68a" fontSize={2.2}
                  fontFamily="serif" fontWeight={isMain ? 'bold' : 'normal'}
                  style={{ paintOrder: 'stroke', stroke: '#000', strokeWidth: 0.5, pointerEvents: 'none' }}>
                  {p.hoofdstad}
                </text>
              </g>
            );
          })}
        </svg>
          {/* v6_map_hover_btn_001 — Kaart Bekijken bij hover, net als Dorp */}
          <button
            data-testid="map-kaart-bekijken-btn"
            onClick={() => setShowLandkaart(true)}
            className="absolute bottom-2 right-2 text-[10px] px-2 py-1 rounded border border-amber-700/60 bg-stone-950/80 hover:bg-amber-900/40 text-amber-200 font-bold uppercase tracking-wider opacity-0 group-hover:opacity-100 transition-opacity"
          >
            Kaart Bekijken
          </button>
        </div>

        {/* Selected provincie detail */}
        {selProv && (
          <div data-testid="prov-detail" className="border-t border-amber-900/40 pt-2 mt-1 bg-stone-950/60 rounded p-2">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-[9px] uppercase tracking-wider text-amber-500/70">{selProv.naam}</p>
                <p className="text-[12px] text-amber-100 font-serif">{selProv.hoofdstad}</p>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full" style={{ background: selFrac?.kleur || '#94a3b8' }} />
                <span className="text-[11px] text-amber-200">{selFrac?.naam || '—'}</span>
              </div>
            </div>
            {isAdmin && (
              <div className="mt-1.5 flex flex-wrap gap-1">
                {fracties.map(f => (
                  <button key={f.id} data-testid={`prov-fractie-${f.id}`}
                    onClick={() => saveProvincie(selProv.id, { fractie_id: f.id })}
                    className={`text-[9px] px-1.5 py-0.5 rounded border ${selProv.fractie_id === f.id ? 'border-amber-400' : 'border-stone-700 hover:border-amber-700'}`}
                    style={{ color: f.kleur, background: `${f.kleur}15` }}>
                    {f.naam}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* v6_spark_world_kaart_btn_001 — Landkaart-bark (zelfde als in Fracties-kader) */}
      {showLandkaart && (
        <LandkaartBark
          provincies={provincies}
          steden={steden}
          fracties={fracties}
          userId={userId}
          isAdmin={isAdmin}
          onClose={() => setShowLandkaart(false)}
          onOpenStad={(s) => setOpenStad(s)}
        />
      )}
      {openStad && (
        <StadDetailBark stadId={openStad.id} onClose={() => setOpenStad(null)} />
      )}
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

function CharInfoPanel({ char, userId, activeTab, setActiveTab }) {
  // v6_charinfo_consolidate_001 — tabs hernoemd + Aanval/Stats samengevouwen
  const tabs = [
    { id: 'char_info', label: 'CHAR INFO' },
    { id: 'aanval',    label: 'AANVAL & VERDEDIGING' },
    { id: 'stats',     label: 'STATISTIEKEN' },
    { id: 'notas',     label: 'Notas' },
  ];

  // RPS-battles/goud (was OverigPanel-content, nu in CHAR INFO tab)
  const [rps, setRps] = React.useState({ battles_won: 0, battles_lost: 0, gold: 1000 });
  React.useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/games/rps/stats?user_id=${userId}`)
      .then(r => r.json())
      .then(d => setRps({
        battles_won: d.stats?.battles_won || 0,
        battles_lost: d.stats?.battles_lost || 0,
        gold: d.stats?.gold ?? 1000,
      }))
      .catch(() => {});
  }, [userId]);

  const STAT_ICONS = {
    'Kracht': '✦', 'Behendigheid': '✕', 'Intelligentie': '☉',
    'Conditie': '♥', 'Wilskracht': '⚑', 'Geluk': '✧',
    'Aanvalskracht': '⚔', 'Verdediging': '🛡', 'Magie Kracht': '✺',
    'Crit. Kans': '✷', 'Beweging': '➤', 'Initiatief': '⟳',
  };
  const renderStats = (stats, accent) => (
    <div className="space-y-1.5">
      {Object.entries(stats || {}).map(([k, v]) => (
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
  );

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
            <Row k="Battles" v={`${rps.battles_won} W · ${rps.battles_lost} L`} />
            <Row k="Goud"    v={`${rps.gold}`} />
            {char.bio && (
              <>
                <p className="text-amber-400/70 mt-2 mb-0.5">Bio:</p>
                <p className="text-amber-100/85 italic">{char.bio}</p>
              </>
            )}
          </div>
        )}
        {activeTab === 'aanval' && renderStats(char.aanval_verdediging, '#dc2626')}
        {activeTab === 'stats' && renderStats(char.statistieken, '#f59e0b')}
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
          <ClassField label="Klasse" v={form.klasse} onChange={v => setForm({ ...form, klasse: v })} />
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

// v6_rps_classes_001 — 3 basisklassen voor steen-papier-schaar zelf-uitvecht-systeem
const RPS_CLASSES = [
  { value: 'Handgevecht Soldaat', shape: 'steen',   icon: '🪨', desc: 'Steen — verplettert Schaar' },
  { value: 'Boog Soldaat',        shape: 'schaar',  icon: '✂', desc: 'Schaar — knipt Papier' },
  { value: 'Magie Soldaat',       shape: 'papier',  icon: '📜', desc: 'Papier — wikkelt Steen' },
];

function ClassField({ label, v, onChange }) {
  return (
    <div>
      <label className="block text-[10px] uppercase tracking-wider text-amber-400 mb-1">{label}</label>
      <select
        data-testid="field-klasse"
        value={v}
        onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-stone-900 border border-amber-900/40 rounded text-sm text-amber-100">
        <option value="">— kies een basisklasse —</option>
        {RPS_CLASSES.map(c => (
          <option key={c.value} value={c.value}>{c.icon} {c.value} ({c.desc})</option>
        ))}
      </select>
      <p className="text-[9px] text-amber-400/60 mt-1 italic">
        Bepaalt jouw vorm in Steen-Papier-Schaar zelfuitvecht-systeem (later: tree, XP, rang).
      </p>
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

// ============================================================
// v6_bewoner_001 — Bewoner-strip + Handel-paneel
// ============================================================
function BewonersStripPanel({ bewoners = [], activeBewonerId, onSelect, char, compact = false }) {
  if (!bewoners.length) return null;
  // Compact mode: 2x3 grid, kleinere avatars (max 6 zichtbaar)
  const visible = compact ? bewoners.slice(0, 6) : bewoners;
  const avatarSize = compact ? 'w-12 h-12' : 'w-16 h-16';
  const wrap = compact ? 'grid grid-cols-3 gap-2' : 'flex gap-3 overflow-x-auto';
  return (
    <PaperPanel>
      <PaperHeader right={
        <span className="text-[10px] text-amber-400/60">{visible.length}/{bewoners.length}</span>
      }>BEWONERS · {char?.dorp || ''}</PaperHeader>
      <div className={`p-2 ${wrap}`} data-testid="bewoners-strip">
        {visible.map(b => {
          const sel = activeBewonerId === b.id;
          return (
            <button key={b.id} data-testid={`bewoner-${b.id}`}
              onClick={() => onSelect(sel ? null : b.id)}
              className={`flex flex-col items-center gap-0.5 p-1.5 rounded-lg border-2 transition-all ${sel ? 'border-amber-400 bg-amber-900/30' : 'border-stone-700 hover:border-amber-600 bg-stone-950/60'}`}>
              <div className={`${avatarSize} rounded-full overflow-hidden border-2 border-amber-700/60`}
                style={{ boxShadow: '0 0 10px rgba(245,158,11,0.3)' }}>
                {b.avatar_url ? (
                  <img src={`${API}${b.avatar_url}`} alt={b.naam} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full bg-stone-800 flex items-center justify-center text-amber-200">{b.naam?.charAt(0)}</div>
                )}
              </div>
              <p className="text-[9px] font-bold text-amber-100 truncate w-full text-center leading-tight">{b.naam.split(' ')[0]}</p>
              <p className="text-[8px] text-amber-400/70 truncate w-full text-center leading-tight">{b.beroep}</p>
            </button>
          );
        })}
      </div>
    </PaperPanel>
  );
}

function BewonerHandelPanel({ bewoner, playerInventory, playerGoud, onBuy, onSell, onClose, gameCards = [], compact = false }) {
  if (!bewoner) return null;
  const bewonerSlots = bewoner.inventory_slots || [];
  const playerSlots = (playerInventory?.slots || []).filter(s => (s.location || 'rugzak') === 'rugzak');
  const BEWONER_SLOT_COUNT = 8;
  const PLAYER_SLOT_COUNT = 8;
  // Compact: stack vertikaal i.p.v. 3 kolommen (past in smalle RIGHT-col)
  const layoutCls = compact ? 'flex flex-col gap-3' : 'grid grid-cols-12 gap-3';
  const avatarSize = compact ? 'w-20 h-20' : 'w-32 h-32';
  const gridCols = compact ? 'grid-cols-4' : 'grid-cols-4';

  return (
    <PaperPanel>
      <PaperHeader right={
        <button data-testid="bewoner-handel-close" onClick={onClose}
          className="text-[10px] px-2 py-0.5 rounded border border-amber-700/40 text-amber-300 hover:bg-amber-900/30">
          sluit
        </button>
      }>HANDEL · {bewoner.naam}</PaperHeader>
      <div className={`p-3 ${layoutCls}`} data-testid="bewoner-handel">
        {/* Avatar + info */}
        <div className={`${compact ? 'flex gap-3 items-start' : 'col-span-12 md:col-span-3 flex flex-col items-center'}`}>
          <div className={`${avatarSize} rounded-lg overflow-hidden border-2 border-amber-700/60 shrink-0`}
            style={{ boxShadow: '0 0 16px rgba(245,158,11,0.4)' }}>
            {bewoner.avatar_url ? (
              <img src={`${API}${bewoner.avatar_url}`} alt={bewoner.naam} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full bg-stone-800 flex items-center justify-center text-amber-200 text-2xl">{bewoner.naam?.charAt(0)}</div>
            )}
          </div>
          <div className={compact ? 'flex-1 min-w-0' : 'mt-2 text-center'}>
            <p className="text-sm font-serif font-bold text-amber-100 leading-tight">{bewoner.naam}</p>
            <p className="text-[10px] text-amber-400/70">{bewoner.beroep} · {bewoner.rang || 'Burger'}</p>
            <p className="text-[10px] text-yellow-300 font-mono mt-1">💰 {bewoner.wallet?.goud || 0}g</p>
            {bewoner.beschrijving && (
              <p className="text-[10px] italic text-amber-200/70 mt-1 leading-snug line-clamp-3">&ldquo;{bewoner.beschrijving}&rdquo;</p>
            )}
          </div>
        </div>

        {/* Bewoner verkoopt */}
        <div className={compact ? '' : 'col-span-12 md:col-span-4'}>
          <p className="text-[10px] uppercase tracking-wider text-amber-400 mb-1.5">Te koop · klik om te kopen</p>
          <div data-testid="bewoner-shop-grid" className={`grid ${gridCols} gap-1.5`}>
            {Array.from({ length: BEWONER_SLOT_COUNT }).map((_, i) => {
              const item = bewonerSlots[i];
              const img = item ? itemImage(item, gameCards) : null;
              const canAfford = item && playerGoud >= (item.value_goud || 0);
              return (
                <button key={i} data-testid={`bewoner-buy-slot-${i}`}
                  disabled={!item || !canAfford}
                  onClick={() => item && canAfford && onBuy(i)}
                  title={item ? `${item.naam} · ${item.value_goud}g${!canAfford ? ' (te duur)' : ''}` : ''}
                  className={`aspect-square rounded border-2 overflow-hidden relative transition-all ${item ? (canAfford ? 'border-emerald-700/60 bg-emerald-950/30 hover:border-emerald-400 cursor-pointer' : 'border-red-900/40 bg-stone-950/60 opacity-60 cursor-not-allowed') : 'border-stone-800 bg-stone-950/50'}`}>
                  {item && img && (
                    <img src={img} alt={item.naam} className="absolute inset-0 w-full h-full object-cover" />
                  )}
                  {item && !img && (
                    <span className="absolute inset-0 flex items-center justify-center text-amber-200">{item.naam?.charAt(0)}</span>
                  )}
                  {item && (
                    <div className="absolute bottom-0 inset-x-0 bg-black/80 text-yellow-300 text-[9px] font-mono font-bold py-0.5 text-center">
                      {item.value_goud}g
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Speler verkoopt */}
        <div className={compact ? '' : 'col-span-12 md:col-span-5'}>
          <p className="text-[10px] uppercase tracking-wider text-amber-400 mb-1.5">Jouw rugzak · klik = verkoop (50%)</p>
          <div data-testid="bewoner-sell-grid" className={`grid ${gridCols} gap-1.5`}>
            {Array.from({ length: PLAYER_SLOT_COUNT }).map((_, i) => {
              const item = playerSlots[i];
              const img = item ? itemImage(item, gameCards) : null;
              const sellPrice = item ? Math.max(1, Math.floor((item.value_goud || 0) / 2)) : 0;
              return (
                <button key={i} data-testid={`bewoner-sell-slot-${i}`}
                  disabled={!item}
                  onClick={() => item && onSell(item.id)}
                  title={item ? `${item.naam} verkopen voor ${sellPrice}g` : ''}
                  className={`aspect-square rounded border-2 overflow-hidden relative transition-all ${item ? 'border-amber-700/60 bg-amber-950/30 hover:border-amber-400 cursor-pointer' : 'border-stone-800 bg-stone-950/50'}`}>
                  {item && img && (
                    <img src={img} alt={item.naam} className="absolute inset-0 w-full h-full object-cover" />
                  )}
                  {item && !img && (
                    <span className="absolute inset-0 flex items-center justify-center text-amber-200">{item.naam?.charAt(0)}</span>
                  )}
                  {item && (
                    <div className="absolute bottom-0 inset-x-0 bg-black/80 text-yellow-300 text-[9px] font-mono font-bold py-0.5 text-center">
                      +{sellPrice}g
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </PaperPanel>
  );
}

// ============================================================
// v6_dice_001 — Dobbelsteen-paneel: basis + super, met jouw D&D-kaart-avatars
// ============================================================
function DiceRollerPanel({ userId, stats = {}, onRolled }) {
  const [cards, setCards] = useState(null);
  const [rolling, setRolling] = useState(false);
  const [result, setResult] = useState(null);
  const [statKey, setStatKey] = useState('geluk');
  const [actie, setActie] = useState('');

  useEffect(() => {
    fetch(`${API}/api/dnd/dice/cards`)
      .then(r => r.json())
      .then(setCards)
      .catch(() => setCards(null));
  }, []);

  const roll = async (dice) => {
    setRolling(true);
    setResult(null);
    // Korte visuele "rol"-pauze
    await new Promise(res => setTimeout(res, 700));
    try {
      const r = await fetch(`${API}/api/dnd/dice/roll`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, dice, stat_key: statKey, actie }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Worp mislukt');
      setResult(data);
      onRolled?.();
    } catch (e) {
      window.alert(e.message);
    } finally {
      setRolling(false);
    }
  };

  const levelColor = {
    kritiek_faal: '#dc2626',
    faal: '#f97316',
    succes: '#22c55e',
    groot_succes: '#a78bfa',
    kritiek_succes: '#fbbf24',
  };

  return (
    <PaperPanel>
      <PaperHeader>DOBBELSTENEN · 1d20</PaperHeader>
      <div className="p-3 space-y-2.5">
        {/* Stat-keuze + actie */}
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5">
            <label className="text-[10px] text-amber-400/80 w-12">Stat:</label>
            <select data-testid="dice-stat-select"
              value={statKey} onChange={e => setStatKey(e.target.value)}
              className="flex-1 bg-stone-950 border border-amber-900/50 rounded px-1.5 py-0.5 text-[11px] text-amber-100">
              {Object.keys(stats).length === 0 && <option value="">geen stats</option>}
              {Object.entries(stats).map(([k, v]) => (
                <option key={k} value={k}>{k} (+{v})</option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1.5">
            <label className="text-[10px] text-amber-400/80 w-12">Actie:</label>
            <input data-testid="dice-action-input"
              value={actie} onChange={e => setActie(e.target.value)}
              placeholder="bv. verken bos…"
              className="flex-1 bg-stone-950 border border-amber-900/50 rounded px-1.5 py-0.5 text-[11px] text-amber-100 placeholder-amber-700" />
          </div>
        </div>

        {/* 2 dobbelsteen-avatars */}
        <div className="grid grid-cols-2 gap-2">
          {['basis', 'super'].map(key => {
            const card = cards?.[key];
            const img = card?.image_url ? `${API}${card.image_url}` : null;
            return (
              <button key={key} data-testid={`dice-${key}-btn`}
                onClick={() => roll(key)}
                disabled={rolling}
                className={`relative aspect-square rounded-lg overflow-hidden border-2 transition-all ${key === 'super' ? 'border-amber-500' : 'border-stone-700'} hover:border-amber-300 disabled:opacity-50 group`}
                style={key === 'super' ? { boxShadow: '0 0 14px rgba(245,158,11,0.45)' } : undefined}>
                {img ? (
                  <img src={img} alt={key}
                    className={`w-full h-full object-cover transition-transform ${rolling ? 'animate-spin' : 'group-hover:scale-105'}`} />
                ) : (
                  <div className="w-full h-full bg-stone-800 flex items-center justify-center text-3xl">🎲</div>
                )}
                <div className="absolute bottom-0 inset-x-0 bg-black/85 text-center py-1">
                  <p className={`text-[11px] font-bold uppercase tracking-wider ${key === 'super' ? 'text-amber-300' : 'text-amber-100'}`}>{key}</p>
                </div>
              </button>
            );
          })}
        </div>

        {/* Resultaat */}
        {result && (
          <div data-testid="dice-result" className="rounded-lg border-2 p-2.5 mt-1"
            style={{ borderColor: levelColor[result.uitkomst_niveau], background: 'rgba(0,0,0,0.6)' }}>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl">{result.emoji}</span>
              <span className="font-mono text-amber-100 text-sm font-bold">
                {result.base_roll}{result.stat_bonus ? ` + ${result.stat_bonus}` : ''} = <span style={{ color: levelColor[result.uitkomst_niveau] }}>{result.total}</span>
              </span>
            </div>
            <p className="text-[11px] font-bold mt-1 uppercase tracking-wider" style={{ color: levelColor[result.uitkomst_niveau] }}>
              {result.uitkomst_niveau.replace('_', ' ')}
            </p>
            <p className="text-[10px] italic text-amber-200/80 mt-1 leading-snug">{result.flavor}</p>
          </div>
        )}
      </div>
    </PaperPanel>
  );
}



export default DnDCharacterSheet;
