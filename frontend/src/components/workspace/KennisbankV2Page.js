import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { toast } from 'sonner';
import { useAuth } from '../../context/AuthContext';
import {
  Inbox, BookOpen, Search, Save, X, AlertTriangle,
  ChevronRight, RefreshCw, Eye, Edit3, ArrowRightLeft,
  Mic, Square, Image as ImageIcon, Upload, Trash2, CheckCircle2, Plus, Merge,
  Volume2, Sparkles, Zap, Heart
} from 'lucide-react';
import { KbV2TagCuration } from './KbV2TagCuration';
import { robustFetch, getQueueSize, replayQueue } from '../../utils/robustFetch';

const API = process.env.REACT_APP_BACKEND_URL;

const LADES = [
  { id: 'voelen',   icon: '🌸', naam: 'Voelen',      stroom: 'Emotie & Verbinding', color: '#ec4899' },
  { id: 'spreken',  icon: '💬', naam: 'Spreken',     stroom: 'Communicatie & Taal', color: '#06b6d4' },
  { id: 'weten',    icon: '🧠', naam: 'Weten',       stroom: 'Systeem & Kennis',    color: '#f59e0b' },
  { id: 'doen',     icon: '🎭', naam: 'Doen',        stroom: 'Gedrag & Actie',      color: '#a855f7' },
  { id: 'games',    icon: '🎮', naam: 'Spark Games', stroom: 'Spel & Wereld',       color: '#22c55e' },
];

const REASON_LABEL = {
  tag_tie:        { label: 'Tag-tie',       color: '#f59e0b' },
  // v12_kbv2_inbox_tabs_cleanup_001 — 'no_match' en 'missing_laag1' zijn
  // in de praktijk hetzelfde als de default inbox-lijst (alle onbeantwoord)
  // en zijn daarom weg als aparte filter-tabs. Ze blijven wel bestaan als
  // interne _inbox_reason waarden voor bookkeeping.
};

/**
 * Kennisbank v2 — 4 Lades + Inbox
 * --------------------------------
 *   Tabs: Inbox · Voelen · Spreken · Weten · Doen
 *   • Inbox-kaart: 4 lade-knoppen + edit-form voor lagen/ws5/tags
 *   • Lade-kaarten: zoeken + paged lijst + edit
 *   • #DeWillem-principe in audit-panel zichtbaar
 */
export function KennisbankV2Page({ onNavigate }) {
  // v12_admin_gated_triggers_001 — Genereer-knop en LLM-bump verstopt achter Admin-toggle
  const { adminModeActive } = useAuth();
  const [activeTab, setActiveTab] = useState('inbox');     // 'inbox' | lade-id
  const [stats, setStats] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [reasons, setReasons] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [voiceFilter, setVoiceFilter] = useState(false); // v14_ttss_001 — alleen niet-ingesproken kaarten
  const [voiceStats, setVoiceStats] = useState(null);
  // v14_inspreek_tab_001 — eigen tab "In te spreken": alle lades, kaart verdwijnt na inspreken
  const [inspreekLade, setInspreekLade] = useState('');
  const inspreekIdxRef = useRef(0);
  // v14_emotie_veld_001 — tab "Nog geen emotie": kaart verdwijnt na bevestigen
  const [emotieStats, setEmotieStats] = useState(null);
  const [emotieLade, setEmotieLade] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');
  // v6_kbv2_priority_001 — Top 50 prio modus (blijft bestaan, maar niet meer als button;
  // wordt gedreven door sortMode==='hits_desc' via de dropdown hieronder)
  const [priorityMode, setPriorityMode] = useState(false);
  // v12_inbox_incomplete_001 — subtab voor kaarten met leeg 5W of onvolledige lagen
  const [incompleteMode, setIncompleteMode] = useState(false);
  // v12_kbv2_inbox_sort_001 — sort-dropdown voor inbox-lijst
  const [sortMode, setSortMode] = useState('recent');
  // v6_kbv2_text_importer_001 — bulk-import modal state
  const [showImporter, setShowImporter] = useState(false);
  const [priorityMeta, setPriorityMeta] = useState(null);
  const [page, setPage] = useState(0);
  const [selectedCard, setSelectedCard] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editForm, setEditForm] = useState(null);
  // v6_kbv2_inline_new_001 — Lege kaart in rechter paneel zonder window.prompt
  const [creatingNew, setCreatingNew] = useState(false);
  // v6_kbv2_unify_001 — duplicate-begrip check
  const [dupCheck, setDupCheck] = useState({ checking: false, exists: false, info: null });
  // v6_kbv2_delete_001 — permanent verwijderen
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteReason, setDeleteReason] = useState('');
  // v6_kbv2_herzien_001 — KB v1 → KB v2 migratie-modus
  const [herzienV1, setHerzienV1] = useState(null);       // de v1-kaart die nu wordt herzien
  const [herzienRemaining, setHerzienRemaining] = useState(0);
  const [savingClassify, setSavingClassify] = useState(false);
  const [showAudit, setShowAudit] = useState(false);
  const [auditData, setAuditData] = useState(null);
  // v6_kb_llm_generate_001 — LLM-genereer status
  const [llmGenerating, setLlmGenerating] = useState(false);

  const PAGE = 25;

  // Load stats
  const loadStats = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/kb/v2/stats`).then(x => x.json());
      setStats(r);
      const v = await fetch(`${API}/api/kb/v2/voice/missing?limit=1`).then(x => x.json());
      if (v.per_lade) setVoiceStats(v.per_lade);
      const e = await fetch(`${API}/api/kb/v2/emotie/stats`).then(x => x.json());
      if (e.per_lade) setEmotieStats(e.per_lade);
    } catch {}
  }, []);

  // Load list (inbox or lade)
  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) });
      if (search) qs.append('search', search);
      let url;
      if (activeTab === 'inbox' && incompleteMode) {
        // v12_inbox_incomplete_001 — Kaarten uit lades met leeg 5W of onvolledige lagen
        // v12_kbv2_inbox_sort_001 — sort-param meesturen zodat dropdown ook hier werkt
        if (sortMode && sortMode !== 'recent') qs.append('sort', sortMode);
        url = `${API}/api/kb/v2/inbox/incomplete?${qs}`;
      } else if (activeTab === 'inbox' && (sortMode === 'hits_desc' || sortMode === 'hits_asc')) {
        // v12_kbv2_inbox_sort_001 — 'meeste/minste hits' gebruikt cross-lade priority-endpoint
        // (kaarten uit alle 4 lades zonder laag1, gescoord op hits). Was voorheen aparte
        // 'Top 50 prio' toggle; nu een sort-optie in de dropdown.
        url = `${API}/api/kb/v2/priority/missing-laag1?limit=50${sortMode === 'hits_asc' ? '&reverse=true' : ''}`;
      } else if (activeTab === 'inbox') {
        if (reasonFilter) qs.append('reason', reasonFilter);
        if (sortMode && sortMode !== 'recent') qs.append('sort', sortMode);
        url = `${API}/api/kb/v2/inbox?${qs}`;
      } else if (activeTab === 'inspreken') {
        if (inspreekLade) qs.append('lade', inspreekLade);
        url = `${API}/api/kb/v2/voice/missing?${qs}`;
      } else if (activeTab === 'emotie') {
        if (emotieLade) qs.append('lade', emotieLade);
        url = `${API}/api/kb/v2/emotie/missing?${qs}`;
      } else if (voiceFilter) {
        qs.append('lade', activeTab);
        url = `${API}/api/kb/v2/voice/missing?${qs}`;
      } else {
        url = `${API}/api/kb/v2/lade/${activeTab}?${qs}`;
      }
      const r = await fetch(url).then(x => x.json());
      setItems(r.kaarten || []);
      if (r.per_lade && activeTab === 'emotie') setEmotieStats(r.per_lade);
      else if (r.per_lade) setVoiceStats(r.per_lade);
      if (sortMode === 'hits_desc' || sortMode === 'hits_asc') {
        setTotal(r.total_missing_laag1 || r.total || 0);
        setPriorityMeta({ total: r.total_missing_laag1, shown: r.kaarten?.length || 0 });
      } else {
        setTotal(r.total || 0);
        setPriorityMeta(null);
      }
      if (activeTab === 'inbox' && !(sortMode === 'hits_desc' || sortMode === 'hits_asc')) setReasons(r.redenen || {});
    } catch {
      setItems([]); setTotal(0);
    }
    setLoading(false);
  }, [activeTab, page, search, reasonFilter, incompleteMode, sortMode, voiceFilter, inspreekLade, emotieLade]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadItems(); }, [loadItems]);

  // Reset page on tab change
  useEffect(() => { setPage(0); setReasonFilter(''); setPriorityMode(false); setIncompleteMode(false); }, [activeTab]);

  // v14_inspreek_tab_001 — houd de geopende kaart in sync met de lijst: na een media-update
  // de verse versie tonen; in de inspreek-tab springt hij door naar de volgende als de kaart
  // uit de lijst verdwenen is (= ingesproken).
  useEffect(() => {
    if (loading || !selectedCard || creatingNew) return;
    const fresh = items.find(c => c.id === selectedCard.id);
    if (fresh) {
      if (fresh !== selectedCard && JSON.stringify([fresh.media, fresh.emotie, fresh.emotie_bevestigd]) !== JSON.stringify([selectedCard.media, selectedCard.emotie, selectedCard.emotie_bevestigd])) setSelectedCard(fresh);
      return;
    }
    if (activeTab !== 'inspreken' && activeTab !== 'emotie') return;
    const next = items[Math.min(inspreekIdxRef.current, items.length - 1)] || null;
    setSelectedCard(next); setEditMode(false); setEditForm(null);
  }, [items, loading]); // eslint-disable-line react-hooks/exhaustive-deps

  const openCard = (card) => {
    inspreekIdxRef.current = Math.max(0, items.findIndex(c => c.id === card.id));
    setSelectedCard(card);
    setEditMode(false);
    setEditForm(null);
  };

  // v6_kbv2_open_by_id_001 — luister naar window-event om een kaart direct
  // te openen via id (bv. vanuit VerbandenPage NodeDetail). Zoekt eerst in
  // alle lades + inbox, switch naar de juiste tab, en opent de kaart.
  useEffect(() => {
    const handler = async (e) => {
      const id = e?.detail?.cardId;
      if (!id) return;
      // Probeer eerst via /find?begrip= (snelste pad als begrip bekend is)
      const begrip = e?.detail?.begrip;
      const tryFetch = async () => {
        // Strategie: scan inbox + alle lades op id
        const buckets = [
          { tab: 'inbox', url: `${API}/api/kb/v2/inbox?limit=10000` },
          { tab: 'voelen', url: `${API}/api/kb/v2/lade/voelen?limit=10000` },
          { tab: 'spreken', url: `${API}/api/kb/v2/lade/spreken?limit=10000` },
          { tab: 'weten', url: `${API}/api/kb/v2/lade/weten?limit=10000` },
          { tab: 'doen', url: `${API}/api/kb/v2/lade/doen?limit=10000` },
          { tab: 'games', url: `${API}/api/kb/v2/lade/games?limit=10000` },
        ];
        for (const b of buckets) {
          try {
            const r = await fetch(b.url).then(x => x.json());
            const found = (r.kaarten || []).find(k => k.id === id || (begrip && (k.begrip || '').toLowerCase() === begrip.toLowerCase()));
            if (found) {
              setActiveTab(b.tab);
              setPage(0);
              setSearch('');
              setReasonFilter('');
              setPriorityMode(false);
              setTimeout(() => {
                setSelectedCard(found);
                setEditMode(false);
                setEditForm(null);
              }, 50);
              return true;
            }
          } catch {}
        }
        return false;
      };
      tryFetch();
    };
    window.addEventListener('spark:open-kbv2-card', handler);
    return () => window.removeEventListener('spark:open-kbv2-card', handler);
  }, []);

  const startEdit = () => {
    setEditMode(true);
    setEditForm({
      lagen: { ...(selectedCard.lagen || {}) },
      ws5:   { ...(selectedCard.ws5 || {}) },
      tags:  [...(selectedCard.tags || [])],
      begrip: selectedCard.begrip || '',
    });
  };

  // v6_kb_llm_generate_001 — LLM vult lege/onvolledige kaart en opent edit-mode voor review
  const generateWithLLM = async () => {
    if (!selectedCard) return;
    setLlmGenerating(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/cards/${selectedCard.id}/llm-generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }).then(x => x.json());
      if (!r.success) {
        toast.error(r.detail || r.error || 'LLM-genereer mislukt');
        return;
      }
      const p = r.proposal || {};
      const existing = selectedCard.lagen || {};
      const existingWs5 = selectedCard.ws5 || {};
      // v6_kb_llm_generate_002 — Beschermde systeem-tags die NOOIT mogen verdwijnen
      const PROTECTED_TAGS = ['knowledge-snap', 'auto-generated', 'from-diep', 'gap-fill'];
      // v13c_tag_sanitizer_001 — LLM kan multi-line output als tag pushen
      // (bv 'neutraal\n\n🧠 weten\nbegrip'). Strippen vóór merge.
      const sanitizeTag = (t) => {
        if (typeof t !== 'string') return '';
        const first = t.split('\n')[0];
        // Emoji-range strip
        // eslint-disable-next-line no-misleading-character-class
        const noEmoji = first.replace(/[\u{1F300}-\u{1F9FF}\u{1FA00}-\u{1FAFF}\u2600-\u27BF]+/gu, '');
        return noEmoji.trim().replace(/\s+/g, ' ').slice(0, 60);
      };
      const llmTags = (p.extra_tags || [])
        .map(sanitizeTag)
        .filter(t => t && !PROTECTED_TAGS.includes(t));
      const mergedTags = [...new Set([...(selectedCard.tags || []), ...llmTags])];
      setEditForm({
        begrip: selectedCard.begrip || '',
        lagen: {
          laag1: existing.laag1 || p.laag1 || '',
          laag2: existing.laag2 || p.laag2 || '',
          laag3: existing.laag3 || p.laag3 || '',
          laag4: existing.laag4 || p.laag4 || '',
        },
        ws5: {
          wie:     existingWs5.wie     || p.ws5?.wie     || '',
          wat:     existingWs5.wat     || p.ws5?.wat     || '',
          wanneer: existingWs5.wanneer || p.ws5?.wanneer || '',
          waar:    existingWs5.waar    || p.ws5?.waar    || '',
          waarom:  existingWs5.waarom  || p.ws5?.waarom  || '',
          hoe:     existingWs5.hoe     || p.ws5?.hoe     || '',
        },
        tags: mergedTags,
      });
      setEditMode(true);
      const lade = p.voorgestelde_lade ? ` · voorstel: ${p.voorgestelde_lade}` : '';
      toast.success(`LLM voorstel ingevuld (${r.llm_provider}, ${(r.llm_latency_s || 0).toFixed(1)}s)${lade}`, { duration: 6000 });
    } catch (e) {
      toast.error('Fout: ' + e.message);
    }
    setLlmGenerating(false);
  };

  const classifyTo = async (lade) => {
    if (!selectedCard) return;
    setSavingClassify(true);
    try {
      // v10_kbv2_move_from_lade_001 — Willems verzoek: lade-buttons ook zichtbaar
      // wanneer kaart al in lade zit. Detect: als activeTab != 'inbox' → gebruik /move endpoint.
      const isMove = activeTab !== 'inbox';
      const url = isMove ? `${API}/api/kb/v2/move` : `${API}/api/kb/v2/classify`;
      const body = isMove ? {
        card_id: selectedCard.id,
        from_lade: activeTab,
        to_lade: lade,
        user_id: 'user-001',
      } : {
        card_id: selectedCard.id,
        lade,
        updates: editMode ? {
          lagen: editForm?.lagen,
          ws5:   editForm?.ws5,
          tags:  editForm?.tags,
        } : null,
        user_id: 'user-001',
      };
      const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(x => x.json());
      if (r.success) {
        toast.success(isMove
          ? `Kaart verplaatst: ${activeTab} → ${lade}`
          : `Kaart ingedeeld in ${lade}`, { duration: 3000 });
        setSelectedCard(null);
        setEditMode(false);
        await loadStats();
        await loadItems();
      } else {
        // Tag-aware guard-warning: toon message + hint
        const msg = r.message || (isMove ? 'Verplaatsen mislukt' : 'Classify mislukt');
        toast.error(msg, { duration: 8000 });
        if (r.hint) {
          console.warn('KB dupe-guard hint:', r.hint, r);
        }
      }
    } catch (e) { toast.error('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  const saveEdit = async () => {
    if (!selectedCard || !editForm) return;
    // v10_kb_save_robust_001 — retry + timeout + queue voor lag/timeout resilience
    // v12_kbv2_snappy_001 — optimistische UI: pas eerst lokaal aan, dan pas backend
    setSavingClassify(true);
    toast.loading('Opslaan...', { id: 'save-edit' });
    // Optimistische snapshot voor rollback bij fout
    const prevItems = items;
    const prevSelected = selectedCard;
    const optimistic = {
      ...selectedCard,
      begrip: editForm.begrip,
      lagen: editForm.lagen,
      ws5: editForm.ws5,
      tags: editForm.tags,
    };
    setSelectedCard(optimistic);
    setItems(items.map(c => c.id === selectedCard.id ? { ...c, ...optimistic } : c));
    try {
      const r = await robustFetch(`${API}/api/kb/v2/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: selectedCard.id,
          lade: activeTab,
          updates: { lagen: editForm.lagen, ws5: editForm.ws5, tags: editForm.tags, begrip: editForm.begrip },
          user_id: 'user-001',
        }),
      }, { kind: 'kb_edit', description: `Edit kaart ${editForm.begrip}` });
      if (r.success) {
        // Server-truth toepassen (bv. genormaliseerde tags/hooks-updates)
        if (r.kaart) {
          setSelectedCard(r.kaart);
          setItems(curr => curr.map(c => c.id === r.kaart.id ? { ...c, ...r.kaart } : c));
        }
        setEditMode(false);
        toast.success('Opgeslagen', { id: 'save-edit' });
      } else {
        // Rollback bij server-fout
        setItems(prevItems);
        setSelectedCard(prevSelected);
        toast.error(r.message || 'Opslaan mislukt', { id: 'save-edit' });
      }
    } catch (e) {
      // Rollback bij netwerk-fout
      setItems(prevItems);
      setSelectedCard(prevSelected);
      const qSize = getQueueSize();
      toast.error(
        qSize > 0
          ? `Opslaan mislukt — in wachtrij (${qSize}). Klik "Sync" om opnieuw te proberen.`
          : `Fout: ${e.message}`,
        { id: 'save-edit', duration: 5000 }
      );
    }
    setSavingClassify(false);
  };

  // v6_kbv2_inline_new_001 — lege kaart opslaan vanuit rechter paneel
  // Niet-compleet (geen laag1 etc) blijft automatisch in inbox als "onbeantwoord".
  const saveNew = async () => {
    if (!editForm) return;
    if (!(editForm.begrip || '').trim()) { alert('Vul een begrip in'); return; }
    setSavingClassify(true);
    toast.loading('Kaart aanmaken...', { id: 'save-new' });
    try {
      // Stap 1: kaart in inbox aanmaken (v10_kb_save_robust_001)
      const r = await robustFetch(`${API}/api/kb/v2/inbox/add`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ begrip: editForm.begrip.trim(), source: 'manual', user_id: 'user-001' }),
      }, { kind: 'kb_inbox_add', description: `Nieuwe kaart ${editForm.begrip}` });
      if (!r || !r.kaart) {
        toast.error('Aanmaken mislukt: ' + JSON.stringify(r), { id: 'save-new' });
        setSavingClassify(false); return;
      }
      let kaart = r.kaart;
      // Stap 2: lagen / ws5 / tags bewerken als ingevuld
      const hasContent =
        Object.values(editForm.lagen || {}).some(v => (v || '').trim()) ||
        Object.values(editForm.ws5 || {}).some(v => (v || '').trim()) ||
        (editForm.tags || []).length > 0;
      if (hasContent) {
        const ed = await robustFetch(`${API}/api/kb/v2/edit`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            card_id: kaart.id, lade: 'inbox',
            updates: { lagen: editForm.lagen, ws5: editForm.ws5, tags: editForm.tags },
            user_id: 'user-001',
          }),
        }, { kind: 'kb_edit', description: `Vullen ${kaart.begrip}` });
        if (ed.success && ed.kaart) kaart = ed.kaart;
      }
      toast.success('Kaart opgeslagen', { id: 'save-new' });
      // Stap 3: refresh + selecteer nieuwe kaart (blijft in inbox/onbeantwoord)
      setActiveTab('inbox');
      setSearch('');
      setReasonFilter('');
      setPage(0);
      await loadStats();
      await loadItems();
      setCreatingNew(false);
      setSelectedCard(kaart);
      setEditMode(false);
      setEditForm(null);
    } catch (e) {
      const qSize = getQueueSize();
      toast.error(
        qSize > 0
          ? `Opslaan mislukt — in wachtrij (${qSize}). Klik "Sync" om opnieuw te proberen.`
          : `Fout: ${e.message}`,
        { id: 'save-new', duration: 5000 }
      );
    }
    setSavingClassify(false);
  };

  // v10_kb_save_robust_001 — sync queue-items opnieuw
  const syncQueue = async () => {
    toast.loading('Wachtrij syncen...', { id: 'sync-queue' });
    const { succeeded, failed } = await replayQueue();
    if (succeeded > 0 && failed === 0) {
      toast.success(`${succeeded} kaart(en) alsnog opgeslagen`, { id: 'sync-queue' });
      await loadStats(); await loadItems();
    } else if (succeeded > 0) {
      toast.warning(`${succeeded} gelukt, ${failed} nog steeds falend`, { id: 'sync-queue' });
    } else if (failed > 0) {
      toast.error(`Sync mislukt — ${failed} in wachtrij`, { id: 'sync-queue' });
    } else {
      toast.info('Wachtrij is leeg', { id: 'sync-queue' });
    }
  };

  const cancelNew = () => {
    setCreatingNew(false);
    setEditForm(null);
    setEditMode(false);
    setHerzienV1(null);
    setDupCheck({ checking: false, exists: false, info: null });
  };

  // v6_kbv2_delete_001 — permanent verwijderen via /api/kb/v2/delete
  // v12_inbox_incomplete_delete_fix — in Onvolledig-modus zit de kaart in een lade,
  // niet in inbox. Gebruik de kaart-eigen `lade` field i.p.v. activeTab.
  // v12_kbv2_snappy_001 — optimistische UI: verwijder direct uit lijst zonder refetch
  const doDelete = async () => {
    if (!confirmDelete) return;
    const targetLade = (incompleteMode && confirmDelete.lade) ? confirmDelete.lade : activeTab;
    // Snapshot voor rollback
    const prevItems = items;
    const prevSelected = selectedCard;
    const prevTotal = total;
    // Optimistisch: haal kaart direct uit lijst
    setItems(items.filter(c => c.id !== confirmDelete.id));
    setTotal(t => Math.max(0, t - 1));
    setSelectedCard(null);
    setEditMode(false);
    setEditForm(null);
    const cardId = confirmDelete.id;
    const cardBegrip = confirmDelete.begrip || '(leeg)';
    setConfirmDelete(null);
    setDeleteReason('');
    try {
      const r = await fetch(`${API}/api/kb/v2/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: cardId,
          lade: targetLade,
          user_id: 'user-001',
          reason: deleteReason,
        }),
      });
      const j = await r.json();
      if (j.success) {
        toast.success(`Kaart "${j.begrip || cardBegrip}" verwijderd`);
        // Stats refresh op achtergrond zodat tab-tellers kloppen
        loadStats();
      } else {
        // Rollback bij server-fout
        setItems(prevItems);
        setSelectedCard(prevSelected);
        setTotal(prevTotal);
        toast.error(j.message || 'Verwijderen mislukt');
      }
    } catch (e) {
      // Rollback bij netwerk-fout
      setItems(prevItems);
      setSelectedCard(prevSelected);
      setTotal(prevTotal);
      toast.error(`Netwerkfout: ${e.message}`);
    }
  };

  // v6_kbv2_unify_001 — debounced duplicate-check tegen knowledge_index.json
  const checkDuplicateBegrip = useCallback(async (begrip) => {
    const q = (begrip || '').trim();
    if (!q || q.length < 2) { setDupCheck({ checking: false, exists: false, info: null }); return; }
    setDupCheck(d => ({ ...d, checking: true }));
    try {
      const r = await fetch(`${API}/api/kb/v2/find?begrip=${encodeURIComponent(q)}`).then(x => x.json());
      if (r && r.found && r.kaart) {
        setDupCheck({ checking: false, exists: true, info: { kaart_id: r.kaart.id, lade: r.lade || 'inbox', begrip: r.kaart.begrip } });
      } else {
        setDupCheck({ checking: false, exists: false, info: null });
      }
    } catch {
      setDupCheck({ checking: false, exists: false, info: null });
    }
  }, []);

  // v6_kbv2_unify_001 — open bestaande kaart vanuit duplicate-banner
  const openExistingFromDup = async () => {
    if (!dupCheck.info) return;
    const { kaart_id, lade } = dupCheck.info;
    setActiveTab(lade || 'inbox');
    setCreatingNew(false);
    setEditForm(null);
    setHerzienV1(null);
    setDupCheck({ checking: false, exists: false, info: null });
    // Wacht tot items van die lade geladen zijn, dan zoek de kaart
    setTimeout(async () => {
      try {
        const url = lade && lade !== 'inbox'
          ? `${API}/api/kb/v2/lade/${lade}?limit=500`
          : `${API}/api/kb/v2/inbox?limit=500`;
        const r = await fetch(url).then(x => x.json());
        const k = (r.kaarten || []).find(c => c.id === kaart_id);
        if (k) setSelectedCard(k);
      } catch {}
    }, 200);
  };

  // v6_kbv2_herzien_001 — Trek 1 oude KB v1 kaart en open in lege-kaart formulier
  const loadHerzienEntry = async () => {
    try {
      const r = await fetch(`${API}/api/kb/v2/herzien/next?strategy=unanswered_first`).then(x => x.json());
      if (!r.entry) {
        alert(`Geen kaarten meer om te herzien. ${r.remaining || 0} resterend.`);
        return;
      }
      const e = r.entry;
      setHerzienRemaining(r.remaining);
      setHerzienV1(e);
      setSelectedCard(null);
      setEditMode(false);
      // Pre-fill formulier met v1 data
      setEditForm({
        begrip: e.begrip || '',
        lagen: { ...(e.lagen || {}) },
        ws5: { ...(e.ws5 || {}) },
        tags: [...(e.tags || [])],
        topic: e.topic || '',
      });
      setCreatingNew(true);
    } catch (err) {
      alert('Herzien-fout: ' + err.message);
    }
  };

  // Promote (KB v1 herzien-kaart → KB v2 lade)
  const saveHerzien = async () => {
    if (!editForm || !herzienV1) return;
    if (!(editForm.begrip || '').trim()) { alert('Vul een begrip in'); return; }
    setSavingClassify(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/herzien/promote`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          v1_id: herzienV1.id,
          begrip: editForm.begrip.trim(),
          lagen: editForm.lagen,
          ws5: editForm.ws5,
          tags: editForm.tags,
          topic: editForm.topic || '',
          target_lade: null,           // auto-classify
          user_id: 'user-001',
        }),
      }).then(x => x.json());
      if (!r.success) { alert('Promote mislukt: ' + (r.message || JSON.stringify(r))); setSavingClassify(false); return; }
      // Open de gemigreerde kaart in zijn lade
      setActiveTab(r.lade);
      setSearch('');
      setReasonFilter('');
      setPage(0);
      await loadStats();
      await loadItems();
      setCreatingNew(false);
      setHerzienV1(null);
      setSelectedCard(r.kaart);
      setEditMode(false);
      setEditForm(null);
      // Toon kort succes-bericht
      setTimeout(() => {
        // Optionele alert; commentaar als je 't te druk vindt
        // alert(`Kaart gemigreerd naar lade "${r.lade}" ✓`);
      }, 100);
    } catch (err) { alert('Fout: ' + err.message); }
    setSavingClassify(false);
  };

  const runAudit = async () => {
    try {
      const r = await fetch(`${API}/api/kb/v2/audit`).then(x => x.json());
      setAuditData(r);
      setShowAudit(true);
    } catch {}
  };

  const totalPages = Math.ceil(total / PAGE);

  return (
    <MainLayout activePage="knowledge-v2" onNavigate={onNavigate}>
      <div data-testid="kennisbank-v2-page" className="p-4 md:p-6 space-y-4 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" /> Kennisbank
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">5 Lades + Inbox · Piramide-laag 3 (Geheugen) · v2 schema</p>
          </div>
          <div className="flex items-center gap-2">
            <button data-testid="kbv2-new-card-btn" onClick={() => {
                // v6_kbv2_inline_new_001 — open leeg formulier in rechter paneel
                setSelectedCard(null);
                setEditMode(false);
                setEditForm({ begrip: '', lagen: {}, ws5: {}, tags: [] });
                setCreatingNew(true);
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10 flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5" /> Nieuwe kaart
            </button>
            {/* v12_kbv2_ui_rust_001 — Verversen-knop verwijderd. Optimistic UI + auto
                stats-refresh na acties maken 'm overbodig. F5 blijft beschikbaar als
                nood-refresh. Past bij kernwaarde 'rust boven snelheid'. */}
            {/* v6_kbv2_text_importer_001 — Bulk import knop */}
            <button
              data-testid="kbv2-import-text-btn"
              onClick={() => setShowImporter(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-sky-500/40 text-sky-300 hover:bg-sky-500/10 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5" /> Importeer txt
            </button>
            {/* v13d_orphan_tag_scan_ui_001 (sessie 55) — Willem: knop om orphan-scan
                te draaien zodat hij na invullen van skeletons opnieuw kan scannen. */}
            <button
              data-testid="kbv2-orphan-scan-btn"
              onClick={async () => {
                // Eerst dry-run tonen
                try {
                  const r = await fetch(`${API}/api/kb/v2/inbox/orphan-tag-scan?commit=false&min_count=3`, { method: 'POST' });
                  const d = await r.json();
                  const preview = (d.top_20_preview || []).slice(0, 10)
                    .map(x => `  ${x.count}× ${x.tag}`).join('\n');
                  const ok = window.confirm(
                    `Orphan-tag scan resultaat (dry-run):\n\n` +
                    `📊 ${d.total_unique_tags} unieke tags in KB\n` +
                    `📊 ${d.total_known_begrippen} bestaande begrippen\n` +
                    `🔍 ${d.orphans_found} tags zonder eigen kaart (min ${d.min_count_filter}× gebruikt)\n\n` +
                    `Top 10 preview:\n${preview}\n\n` +
                    `Wil je ${d.orphans_found} skeleton-kaarten aanmaken in de inbox?\n` +
                    `(Dubbelingen worden automatisch overgeslagen — idempotent.)`
                  );
                  if (!ok) return;
                  const r2 = await fetch(`${API}/api/kb/v2/inbox/orphan-tag-scan?commit=true&min_count=3`, { method: 'POST' });
                  const d2 = await r2.json();
                  alert(d2.message || `${d2.added || 0} skeletons toegevoegd`);
                  // reload inbox stats
                  if (typeof loadStats === 'function') loadStats();
                  window.location.reload();
                } catch (e) {
                  alert(`Fout: ${e.message}`);
                }
              }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-500/40 text-amber-300 hover:bg-amber-500/10 flex items-center gap-1.5"
              title="Scan alle KB-tags → maak skeleton-kaarten voor tags die nog geen eigen kaart hebben">
              <Zap className="w-3.5 h-3.5" /> Orphan-tag scan
            </button>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <TabButton id="inbox" active={activeTab === 'inbox'} onClick={setActiveTab}
            count={stats?.inbox_count || 0} icon={<Inbox className="w-3.5 h-3.5" />}
            label="Inbox" color="#ef4444" />
          {LADES.map(l => (
            <TabButton key={l.id} id={l.id} active={activeTab === l.id} onClick={setActiveTab}
              count={stats?.lades?.[l.id]?.count || 0} iconEmoji={l.icon}
              label={l.naam} color={l.color} />
          ))}
          <TabButton id="inspreken" active={activeTab === 'inspreken'} onClick={setActiveTab}
            count={voiceStats ? Object.values(voiceStats).reduce((a, s) => a + (s.niet || 0), 0) : 0}
            icon={<Mic className="w-3.5 h-3.5" />}
            label="In te spreken" color="#22d3ee" />
          <TabButton id="emotie" active={activeTab === 'emotie'} onClick={setActiveTab}
            count={emotieStats ? Object.values(emotieStats).reduce((a, s) => a + (s.niet || 0), 0) : 0}
            icon={<Heart className="w-3.5 h-3.5" />}
            label="Nog geen emotie" color="#f472b6" />
          <TabButton id="curatie" active={activeTab === 'curatie'} onClick={setActiveTab}
            icon={<Merge className="w-3.5 h-3.5" />}
            label="Tag-curatie" color="#f59e0b" />
        </div>

        {/* v6_kb_curation_dashboard_001 — Tag-curation view */}
        {activeTab === 'curatie' ? (
          <KbV2TagCuration viewerId="user-001" />
        ) : (
        <>

        {/* Search + filter row */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input data-testid="kbv2-search-input" type="text" value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(0); }}
              placeholder="Zoek op begrip..."
              className="w-full pl-8 pr-3 py-1.5 bg-slate-900/60 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-amber-500/50" />
          </div>
          {activeTab !== 'inbox' && activeTab !== 'inspreken' && activeTab !== 'emotie' && (
            <button data-testid="kbv2-voice-filter" onClick={() => { setVoiceFilter(v => !v); setPage(0); }}
              title="Alleen kaarten zonder ingesproken woord (voor TTSS)"
              className={`flex items-center gap-1 text-[11px] px-2.5 py-1.5 rounded-lg border transition-colors ${voiceFilter ? 'border-cyan-500/50 bg-cyan-500/15 text-cyan-200' : 'border-slate-700 text-slate-400 hover:text-slate-200'}`}>
              🎙️ niet ingesproken{voiceStats?.[activeTab] ? ` (${voiceStats[activeTab].niet}/${voiceStats[activeTab].totaal})` : ''}
            </button>
          )}
          {(activeTab === 'inspreken' || activeTab === 'emotie') && (() => {
            const isEmo = activeTab === 'emotie';
            const cur = isEmo ? emotieLade : inspreekLade;
            const setCur = isEmo ? setEmotieLade : setInspreekLade;
            const st = isEmo ? emotieStats : voiceStats;
            const accent = isEmo ? 'bg-pink-500/20 border-pink-500/40 text-pink-200' : 'bg-cyan-500/20 border-cyan-500/40 text-cyan-200';
            return (
            <div className="flex items-center gap-1.5 flex-wrap">
              <button data-testid={`kbv2-${activeTab}-lade-alle`}
                onClick={() => { setCur(''); setPage(0); }}
                className={`px-2 py-1 rounded text-[10px] font-medium border ${cur === '' ? accent : 'border-slate-700 text-slate-400'}`}>
                alle lades
              </button>
              {LADES.map(l => (
                <button key={l.id} data-testid={`kbv2-${activeTab}-lade-${l.id}`}
                  onClick={() => { setCur(l.id); setPage(0); }}
                  className={`px-2 py-1 rounded text-[10px] font-medium border ${cur === l.id ? 'border-current' : 'border-slate-700 text-slate-400'}`}
                  style={cur === l.id ? { color: l.color, borderColor: l.color, backgroundColor: l.color + '15' } : {}}>
                  {l.icon} {l.naam}{st?.[l.id] ? ` ${st[l.id].niet}/${st[l.id].totaal}` : ''}
                </button>
              ))}
            </div>
            );
          })()}
          {activeTab === 'inbox' && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {/* Alle onbeantwoord (default) */}
              <button data-testid="kbv2-reason-all"
                onClick={() => { setReasonFilter(''); setIncompleteMode(false); setPage(0); }}
                className={`px-2 py-1 rounded text-[10px] font-medium border ${
                  reasonFilter === '' && !incompleteMode ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'border-slate-700 text-slate-400'
                }`}>alle</button>
              {/* Tag-tie blijft — semantisch anders (ambiguïteit tussen 2 lades) */}
              {Object.entries(REASON_LABEL).map(([k, v]) => (
                <button key={k} data-testid={`kbv2-reason-${k}`}
                  onClick={() => { setReasonFilter(k); setIncompleteMode(false); setPage(0); }}
                  className={`px-2 py-1 rounded text-[10px] font-medium border ${
                    reasonFilter === k && !incompleteMode ? 'border-current' : 'border-slate-700 text-slate-400'
                  }`}
                  style={reasonFilter === k && !incompleteMode ? { color: v.color, borderColor: v.color, backgroundColor: v.color + '15' } : {}}>
                  {v.label} {reasons[k] ? `(${reasons[k]})` : ''}
                </button>
              ))}
              {/* v13_incomplete_tab_removed_001 (sessie 54) — Onvolledig-tab was
                  tijdelijk vangnet dat kopieën met dezelfde id maakte (dubbels-bug).
                  Nu ws5-vulling en bulk-import gestopt zijn is deze tab dood spul.
                  Uitgeschakeld in UI (state + fetch-tak blijven staan zodat we
                  makkelijk terug kunnen als bulk-invul ooit weer nodig is). */}
              {/* v12_kbv2_inbox_sort_001 — sort-dropdown werkt op alle 3 filters
                  (alle / Tag-tie / Onvolledig) zodat het geen off-grid tab meer voelt. */}
              <select
                data-testid="kbv2-sort-select"
                value={sortMode}
                onChange={(e) => { setSortMode(e.target.value); setPage(0); }}
                className="ml-2 px-2 py-1 rounded text-[10px] font-medium border border-slate-700 bg-slate-900/60 text-slate-300 focus:outline-none focus:border-amber-500/50"
                title="Sorteervolgorde voor deze lijst"
              >
                <option value="recent">🕒 Nieuwste eerst</option>
                <option value="oud">🕐 Oudste eerst</option>
                <option value="alfa">🔤 A → Z</option>
                <option value="alfa_desc">🔡 Z → A</option>
                <option value="hits_desc">⭐ Meeste hits (Top prio)</option>
                <option value="hits_asc">🌱 Minste hits eerst</option>
              </select>
            </div>
          )}
        </div>

        {/* List + Detail — v12_kbv2_stable_layout_001: min-w-0 voorkomt overflow,
             beide panelen krijgen dezelfde vaste hoogte + interne scroll zodat
             lange kaarten het overzicht niet meer laten "verspringen". */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-3 items-start">
          {/* List */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl min-w-0 h-[75vh] flex flex-col overflow-hidden">
            <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 z-10 shrink-0">
              <p className="text-[11px] text-slate-400 font-medium">
                {activeTab === 'inbox' ? 'Onbeantwoord' : activeTab === 'inspreken' ? '🎙️ Nog in te spreken' : activeTab === 'emotie' ? '💗 Nog geen emotie' : LADES.find(l => l.id === activeTab)?.naam}
                <span className="text-slate-500"> · {total} kaarten</span>
              </p>
              {totalPages > 1 && (
                <div className="flex items-center gap-1">
                  <button data-testid="kbv2-prev-page" onClick={() => setPage(Math.max(0, page - 1))}
                    disabled={page === 0}
                    className="px-1.5 py-0.5 rounded text-[10px] border border-slate-700 text-slate-300 disabled:opacity-40">‹</button>
                  <span className="text-[10px] text-slate-500">{page + 1}/{totalPages}</span>
                  <button data-testid="kbv2-next-page" onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
                    disabled={page >= totalPages - 1}
                    className="px-1.5 py-0.5 rounded text-[10px] border border-slate-700 text-slate-300 disabled:opacity-40">›</button>
                </div>
              )}
            </div>
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <p className="text-xs text-slate-500 p-4 text-center">Laden...</p>
              ) : items.length === 0 ? (
                <p className="text-xs text-slate-500 p-6 text-center">Geen kaarten.</p>
              ) : (
                items.map(card => (
                  <CardListItem key={card.id} card={card} active={selectedCard?.id === card.id}
                    onClick={() => openCard(card)} showReason={activeTab === 'inbox'} />
                ))
              )}
            </div>
          </div>

          {/* Detail / Edit — vaste hoogte + eigen scroll, min-w-0 tegen overflow */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 min-w-0 h-[75vh] overflow-y-auto">
            {creatingNew ? (
              <NewCardInline editForm={editForm} setEditForm={setEditForm}
                saving={savingClassify}
                onSave={herzienV1 ? saveHerzien : saveNew}
                onCancel={cancelNew}
                herzienV1={herzienV1}
                herzienRemaining={herzienRemaining}
                onNextHerzien={loadHerzienEntry}
                dupCheck={dupCheck}
                onCheckDup={checkDuplicateBegrip}
                onOpenExisting={openExistingFromDup} />
            ) : !selectedCard ? (
              <div className="flex flex-col items-center justify-center h-full text-center py-12 text-slate-500">
                <Eye className="w-8 h-8 mb-2 opacity-40" />
                <p className="text-xs">Selecteer een kaart links om te bekijken of in te delen.</p>
                <p className="text-[10px] mt-2 text-slate-600">Of klik <span className="text-emerald-400">Nieuwe kaart</span> rechtsboven om een lege kaart te starten.</p>
              </div>
            ) : (
              <CardDetail card={selectedCard} editMode={editMode} editForm={editForm}
                setEditForm={setEditForm} onStartEdit={startEdit}
                onCancelEdit={() => { setEditMode(false); setEditForm(null); }}
                onClassify={classifyTo} onSaveEdit={saveEdit}
                saving={savingClassify} inInbox={activeTab === 'inbox'}
                currentLade={(activeTab === 'inspreken' || activeTab === 'emotie') ? (selectedCard.lade || null) : activeTab}
                onMediaUpdated={() => { loadItems(); loadStats(); }}
                onGenerateLLM={adminModeActive ? generateWithLLM : null} llmGenerating={llmGenerating}
                onDeleteCard={() => setConfirmDelete(selectedCard)} />
            )}
          </div>
        </div>

        {/* Audit modal */}
        {showAudit && auditData && (
          <AuditModal data={auditData} onClose={() => setShowAudit(false)} />
        )}

        {/* v6_kbv2_delete_001 — Confirm delete modal */}
        {confirmDelete && (
          <div data-testid="kbv2-delete-modal"
            className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setConfirmDelete(null)}>
            <div className="bg-slate-900 border border-red-500/40 rounded-xl p-5 max-w-md w-full" onClick={e => e.stopPropagation()}>
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 rounded-full bg-red-500/15 flex items-center justify-center">
                  <Trash2 className="w-4 h-4 text-red-400" />
                </div>
                <h3 className="text-base font-bold text-white">Kaart permanent verwijderen?</h3>
              </div>
              <p className="text-sm text-slate-300 mb-2">
                Begrip <span className="text-red-300 font-medium">"{confirmDelete.begrip || '(leeg)'}"</span> wordt verwijderd uit <span className="text-slate-400">{activeTab}</span>.
              </p>
              <p className="text-[10px] text-slate-500 mb-4">Dit kan niet ongedaan worden. ID: <code>{confirmDelete.id}</code></p>
              <textarea data-testid="kbv2-delete-reason"
                value={deleteReason} onChange={e => setDeleteReason(e.target.value)}
                placeholder="Reden (optioneel, voor traceability)…"
                rows={2}
                className="w-full text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1 mb-3 resize-none" />
              <div className="flex justify-end gap-2">
                <button data-testid="kbv2-delete-cancel"
                  onClick={() => { setConfirmDelete(null); setDeleteReason(''); }}
                  className="px-4 py-2 text-sm rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">
                  Annuleren
                </button>
                <button data-testid="kbv2-delete-confirm"
                  onClick={doDelete}
                  className="px-4 py-2 text-sm rounded-lg bg-red-500 hover:bg-red-600 text-white font-medium">
                  Ja, verwijderen
                </button>
              </div>
            </div>
          </div>
        )}
        </>
        )}

      {/* v6_kbv2_text_importer_001 — Bulk-import modal */}
      {showImporter && (
        <TextImporterModal
          onClose={() => setShowImporter(false)}
          onSuccess={() => { setShowImporter(false); loadStats(); loadItems(); }}
        />
      )}
      </div>
    </MainLayout>
  );
}

// v6_kbv2_text_importer_001 — modal voor bulk-tekst-import
function TextImporterModal({ onClose, onSuccess }) {
  const [text, setText] = useState('');
  const [dryRun, setDryRun] = useState(true);
  const [overwrite, setOverwrite] = useState(false);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/kb/v2/admin/import-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, dry_run: dryRun, overwrite_existing: overwrite }),
      });
      const data = await res.json();
      setResult(data);
      if (!dryRun && data.success) {
        setTimeout(() => { onSuccess(); }, 1500);
      }
    } catch (err) {
      setResult({ error: String(err) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" data-testid="kbv2-importer-modal">
      <div className="bg-slate-900 border border-sky-500/40 rounded-xl p-5 max-w-3xl w-full mx-4 max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold text-white">Bulk import — txt-kaarten</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white" data-testid="kbv2-importer-close"><X className="w-5 h-5" /></button>
        </div>
        <p className="text-xs text-slate-400 mb-3">
          Plak rijke kaart-dumps (Begrip → Laag 1..4 → 5W → Tags → Lade → Emotie). Parser detecteert auto en
          slaat over wat al gevuld is. Klik eerst <strong>dry-run</strong> om te zien wat hij vindt.
        </p>
        <textarea
          data-testid="kbv2-importer-text"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Plak hier de txt-inhoud..."
          className="w-full h-56 bg-slate-950 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 font-mono mb-3"
        />
        <div className="flex flex-wrap gap-3 mb-3 text-xs text-slate-300">
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={dryRun} onChange={e => setDryRun(e.target.checked)} className="accent-sky-500" data-testid="kbv2-importer-dryrun" />
            Dry-run (alleen tonen, niets opslaan)
          </label>
          <label className="flex items-center gap-1.5 cursor-pointer">
            <input type="checkbox" checked={overwrite} onChange={e => setOverwrite(e.target.checked)} className="accent-rose-500" data-testid="kbv2-importer-overwrite" />
            Overschrijf bestaande (gevulde) kaarten
          </label>
        </div>
        <div className="flex gap-2 mb-3">
          <button
            data-testid="kbv2-importer-run"
            onClick={run}
            disabled={!text.trim() || busy}
            className="px-4 py-2 rounded-lg text-sm bg-sky-500/20 text-sky-200 border border-sky-500/40 hover:bg-sky-500/30 disabled:opacity-40"
          >
            {busy ? 'Bezig...' : (dryRun ? 'Test parse' : 'Importeer nu')}
          </button>
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm text-slate-300 bg-slate-800 hover:bg-slate-700">
            Annuleer
          </button>
        </div>
        {result && (
          <div className="bg-slate-950/60 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 overflow-auto max-h-64" data-testid="kbv2-importer-result">
            {result.error && <p className="text-rose-400">Fout: {result.error}</p>}
            {result.parsed_count !== undefined && (
              <>
                <p className="mb-2">📦 <strong>{result.parsed_count}</strong> kaarten gevonden{result.dry_run ? ' (dry-run)' : ''}</p>
                {!result.dry_run && (
                  <p className="mb-2 text-emerald-300">
                    ✓ v2 toegevoegd: {result.added_v2} · v1 toegevoegd: {result.added_v1} · v1 bijgewerkt: {result.updated_v1} · overgeslagen: {result.skipped}
                    {result.to_inbox > 0 && <span className="text-amber-300"> · naar inbox: {result.to_inbox}</span>}
                  </p>
                )}
                {(result.warnings || []).length > 0 && (
                  <ul data-testid="kbv2-import-warnings" className="mb-2 space-y-0.5 rounded-lg border border-amber-500/30 bg-amber-500/10 p-2">
                    {result.warnings.map((w, i) => <li key={i} className="text-[11px] text-amber-200">{w}</li>)}
                    <li className="text-[10px] text-amber-400/70">Minimaal 5 tags nodig voor een lade. Vul tags aan in de Inbox en keur daarna goed.</li>
                  </ul>
                )}
                <ul className="space-y-0.5">
                  {(result.preview || result.details || []).slice(0, 50).map((p, i) => (
                    <li key={i} className="text-[10.5px] text-slate-400">
                      • {p.begrip || JSON.stringify(p)}
                      {p.lade && <span className="text-sky-400"> → {p.lade}</span>}
                      {p.emotie && <span className="text-purple-400"> ({p.emotie})</span>}
                      {p.v2_action && <span className="text-amber-400"> [{p.v2_action}]</span>}
                      {typeof p.tag_count === 'number' && <span className={p.tag_count < 5 ? 'text-amber-400' : 'text-slate-600'}> · {p.tag_count} tags{p.tag_count < 5 ? ' ⚠ → inbox' : ''}</span>}
                      {p.reason && <span className="text-rose-400"> ⓘ {p.reason}</span>}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function TabButton({ id, active, onClick, count, iconEmoji, icon, label, color }) {
  return (
    <button data-testid={`kbv2-tab-${id}`}
      onClick={() => onClick(id)}
      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors flex items-center gap-1.5 ${
        active ? 'border-current' : 'border-slate-700 text-slate-300 hover:bg-slate-800'
      }`}
      style={active ? { color, borderColor: color, backgroundColor: color + '15' } : {}}>
      {iconEmoji ? <span>{iconEmoji}</span> : icon}
      <span>{label}</span>
      <span className="text-[10px] opacity-70">({count})</span>
    </button>
  );
}

function CardListItem({ card, active, onClick, showReason }) {
  const reason = card._inbox_reason;
  const r = reason ? REASON_LABEL[reason] : null;
  const hasL1 = !!(card.lagen?.laag1 || '').trim();
  // v6_kbv2_priority_001 — score & reasons komen alleen mee in priority-modus
  const hasScore = typeof card.score === 'number';
  return (
    <button data-testid={`kbv2-card-${card.id}`}
      onClick={onClick}
      className={`w-full text-left px-3 py-2 border-b border-slate-800/60 hover:bg-slate-800/40 transition-colors ${
        active ? 'bg-amber-500/10 border-l-2 border-l-amber-500' : ''
      }`}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-slate-200 font-medium truncate">{card.begrip || '(leeg)'}</p>
        {hasScore ? (
          <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300" title={card.reasons?.join(' · ')}>
            prio {card.score}
          </span>
        ) : (showReason && r && (
          <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded"
            style={{ backgroundColor: r.color + '20', color: r.color }}>{r.label}</span>
        ))}
      </div>
      <div className="flex items-center gap-2 mt-0.5 text-[10px] text-slate-500">
        {hasL1 ? <span className="text-emerald-400">✓ laag1</span> : <span className="text-red-400">✗ laag1</span>}
        {card.tags?.length > 0 && <span>{Array.isArray(card.tags) ? card.tags.slice(0, 3).join(', ') : ''}</span>}
        {card.footnote?.vertrouwen != null && <span>· {Math.round(card.footnote.vertrouwen * 100)}%</span>}
        {hasScore && card.has_topic && <span className="text-purple-400">· topic ✓</span>}
      </div>
    </button>
  );
}

function CardDetail({ card, editMode, editForm, setEditForm, onStartEdit, onCancelEdit,
                     onClassify, onSaveEdit, saving, inInbox, currentLade, onMediaUpdated,
                     onGenerateLLM, llmGenerating,
                     onDeleteCard }) {
  const lagen = editMode ? editForm.lagen : (card.lagen || {});
  const ws5 = editMode ? editForm.ws5 : (card.ws5 || {});
  const tags = editMode ? editForm.tags : (card.tags || []);
  const upd = (path, val) => {
    setEditForm(f => ({ ...f, [path]: val }));
  };

  // v6_kbv2_unify_001 — 100%-status (laag1-4 + 5W + tags + foto)
  // v14_emotie_veld_001 (Willem) — 100% = kaart klaar · +10% ingesproken · +10% emotie bevestigd = 120%
  const hasL1 = !!(card.lagen?.laag1 || '').trim();
  const hasL2 = !!(card.lagen?.laag2 || '').trim();
  const hasL3 = !!(card.lagen?.laag3 || '').trim();
  const hasL4 = !!(card.lagen?.laag4 || '').trim();
  const has5w = Object.values(card.ws5 || {}).some(v => (v || '').trim());
  const hasTags = (card.tags || []).length > 0;
  const hasVoice = !!(card.media?.voice_url) && (card.media?.voice_kind || 'spraak') === 'spraak';
  const hasEmotie = !!card.emotie_bevestigd;
  const hasImage = (card.media?.image_urls || []).filter(Boolean).length > 0;
  const filledCount = [hasL1, hasL2, hasL3, hasL4, has5w, hasTags, hasImage].filter(Boolean).length;
  const totalFields = 7;
  const basePct = Math.round((filledCount / totalFields) * 100);
  const isComplete = basePct === 100;
  const pct = isComplete ? 100 + (hasVoice ? 10 : 0) + (hasEmotie ? 10 : 0) : basePct;

  return (
    <div className="space-y-3">
      {/* Header — v12_kbv2_stable_layout_001: flex-wrap + min-w-0 zodat lange
          begrippen de knoppen niet meer uit beeld duwen. */}
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          {editMode ? (
            <input data-testid="kbv2-edit-begrip" value={editForm.begrip}
              onChange={(e) => upd('begrip', e.target.value)}
              className="w-full text-lg font-bold text-white bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
          ) : (
            <h2 className="text-lg font-bold text-white break-words">{card.begrip || '(leeg)'}</h2>
          )}
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">{card.id}</p>
        </div>
        {/* v6_kbv2_unify_001 — Compleetheid-badge */}
        <div data-testid="kbv2-completeness-badge" className={`shrink-0 px-2 py-1 rounded-lg text-[10px] font-semibold border ${
          isComplete
            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
            : pct >= 50
              ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-400'
        }`} title={isComplete ? `100% kaart${hasVoice ? ' · +10% ingesproken' : ''}${hasEmotie ? ' · +10% emotie' : ''}` : undefined}>
          {isComplete ? (pct > 100 ? `✓ ${pct}%${hasVoice ? ' 🎙️' : ''}${hasEmotie ? ' 💗' : ''}` : '✓ 100% gekuurd') : `${pct}% (${filledCount}/${totalFields})`}
        </div>
        {!editMode ? (
          <div className="flex items-center gap-1.5 shrink-0 flex-wrap">
            <button data-testid="kbv2-edit-btn" onClick={onStartEdit}
              className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-300 hover:bg-slate-800 flex items-center gap-1">
              <Edit3 className="w-3 h-3" /> Bewerken
            </button>
            {/* v6_kb_llm_generate_001 — LLM vult lege/onvolledige kaart automatisch */}
            {onGenerateLLM && (
              <button data-testid="kbv2-llm-generate-btn"
                onClick={onGenerateLLM}
                disabled={!!llmGenerating}
                title="LLM vult laag1-4 + 5W in (review verplicht voor opslaan)"
                className="px-2 py-1 text-xs border border-amber-500/40 rounded text-amber-300 hover:bg-amber-500/15 flex items-center gap-1 disabled:opacity-50 disabled:cursor-wait">
                <Sparkles className="w-3 h-3" /> {llmGenerating ? 'Bezig...' : 'Genereer'}
              </button>
            )}
            {/* v6_kbv2_delete_001 — permanent delete-knop */}
            <button data-testid="kbv2-delete-btn"
              onClick={() => onDeleteCard && onDeleteCard()}
              title="Permanent verwijderen (bv. onbruikbare kaart)"
              className="px-2 py-1 text-xs border border-red-500/40 rounded text-red-400 hover:bg-red-500/15 flex items-center gap-1">
              <Trash2 className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <button data-testid="kbv2-cancel-edit" onClick={onCancelEdit}
            className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-400 hover:bg-slate-800 shrink-0">
            <X className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* v6_kbv2_unify_001 — gedeelde form-velden (Laag 1-4 + 5W + Tags) */}
      <CardFormFields
        editForm={editMode ? editForm : { lagen, ws5, tags }}
        setEditForm={setEditForm}
        editable={editMode}
        testIdPrefix="kbv2-edit"
      />

      {/* v6_capability_links_001 — alleen voor doe-lade: koppel deze kaart aan een capability */}
      {!inInbox && currentLade === 'doen' && (
        <CapabilityCoupling cardId={card.id} cardBegrip={card.begrip} />
      )}

      {/* v5_kbv2_media_001 — Voice & Image upload */}
      <EmotieSection card={card} currentLade={inInbox ? 'inbox' : currentLade} onUpdated={onMediaUpdated} />
      <MediaSection card={card} currentLade={inInbox ? null : currentLade} onUpdated={onMediaUpdated} />

      {/* Needs checklist */}
      {(card.needs || []).length > 0 && (
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-2">
          <p className="text-[10px] uppercase text-amber-300 font-medium mb-1">Mist nog:</p>
          <div className="flex flex-wrap gap-1">
            {(card.needs || []).map(n => (
              <span key={n} className="px-1.5 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 border border-amber-500/30">
                {n === 'laag1' ? '📝 laag 1' :
                 n === 'ws5' ? '5️⃣ 5W' :
                 n === 'voice' ? '🎙️ inspraak' :
                 n === 'image' ? '🖼️ foto' : n}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* v6_kbv2_hooks_landing_001 — Verbanden (Hook 3 output) */}
      {(card.verbanden || []).length > 0 && (
        <div data-testid="kbv2-verbanden" className="border-t border-slate-800 pt-2">
          <p className="text-[10px] uppercase text-slate-500 tracking-wide mb-1">🕸️ Gerelateerd ({(card.verbanden || []).length})</p>
          <div className="flex flex-wrap gap-1.5">
            {(card.verbanden || []).slice(0, 5).map((v, i) => (
              <span key={i} data-testid={`kbv2-verband-${i}`}
                title={`Gedeelde tags: ${(v.shared_tags || []).join(', ')}`}
                className="px-2 py-0.5 rounded-md text-[10px] bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                {v.begrip} <span className="text-slate-500">· {v.lade} · ⨯{v.overlap}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Footnote */}
      {card.footnote && (
        <div className="text-[10px] text-slate-500 border-t border-slate-800 pt-2 leading-relaxed">
          <p>📜 Bron: <span className="text-slate-400">{card.footnote.bron}</span>
            {card.footnote.vertrouwen != null && <> · vertrouwen <span className="text-amber-300">{Math.round(card.footnote.vertrouwen * 100)}%</span></>}
          </p>
          {card.footnote.vorige_versie_v1 && <p>Vorige versie (v1): <code className="text-slate-400">{card.footnote.vorige_versie_v1}</code></p>}
          {card.footnote.ingedeeld_op && <p>Ingedeeld: {(card.footnote.ingedeeld_op || '').slice(0, 19).replace('T', ' ')}</p>}
        </div>
      )}

      {/* Actions */}
      {editMode ? (
        <div className="border-t border-slate-800 pt-3">
          <button data-testid="kbv2-save-edit" onClick={onSaveEdit} disabled={saving}
            className="w-full px-3 py-2 text-xs rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 disabled:opacity-50 flex items-center justify-center gap-1.5">
            <Save className="w-3.5 h-3.5" /> {saving ? 'Opslaan...' : 'Bewaar wijzigingen'}
          </button>
          {inInbox && (
            <p className="text-[10px] text-slate-500 mt-2 text-center">Vul de lagen in en kies hieronder een lade om te classificeren.</p>
          )}
        </div>
      ) : null}
      {inInbox ? (
        <div className="space-y-2 border-t border-slate-800 pt-3">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <ArrowRightLeft className="w-3 h-3" /> Indelen in lade:
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {LADES.map(l => (
              <button key={l.id} data-testid={`kbv2-classify-${l.id}`}
                onClick={() => onClassify(l.id)} disabled={saving}
                className="px-2 py-2 text-xs rounded-lg border transition-colors flex items-center gap-1.5 hover:bg-slate-800 disabled:opacity-50"
                style={{ borderColor: l.color + '60', color: l.color }}>
                <span>{l.icon}</span>
                <span>{l.naam}</span>
                <ChevronRight className="w-3 h-3 ml-auto" />
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* v10_kbv2_move_buttons_always_001 — Willems verzoek sessie 47:
           lade-verplaats knoppen ALTIJD zichtbaar, ook in lade-mode.
           Huidige lade is disabled (highlight). Klik op andere = verplaats via /api/kb/v2/move. */
        <div className="space-y-2 border-t border-slate-800 pt-3">
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <ArrowRightLeft className="w-3 h-3" /> Verplaats naar andere lade:
          </p>
          <div className="grid grid-cols-2 gap-1.5">
            {LADES.map(l => {
              const isCurrent = l.id === currentLade;
              return (
                <button key={l.id} data-testid={`kbv2-move-${l.id}`}
                  onClick={() => !isCurrent && onClassify(l.id)}
                  disabled={saving || isCurrent}
                  title={isCurrent ? 'Huidige lade' : `Verplaats naar ${l.naam}`}
                  className={`px-2 py-2 text-xs rounded-lg border transition-colors flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed ${
                    isCurrent ? 'bg-slate-800/60 ring-1 ring-inset' : 'hover:bg-slate-800'
                  }`}
                  style={{ borderColor: l.color + '60', color: l.color }}>
                  <span>{l.icon}</span>
                  <span>{l.naam}{isCurrent ? ' ✓' : ''}</span>
                  {!isCurrent && <ChevronRight className="w-3 h-3 ml-auto" />}
                </button>
              );
            })}
          </div>
          <p className="text-[10px] text-slate-600 italic">
            💡 Homoniemen (bv. banken = geld én meubel) kunnen ook in zelfde lade — geef beide kaarten unieke tags.
          </p>
        </div>
      )}
    </div>
  );
}

// ============================================================
// v6_kbv2_unify_001 — Gedeelde form-velden (Laag 1-4 + 5W + Tags)
// Gebruikt door zowel CardDetail (edit-mode) als NewCardInline.
// ============================================================
function CardFormFields({ editForm, setEditForm, editable, testIdPrefix, openWs5 = false, highlightLaag1 = false }) {
  const lagen = editForm.lagen || {};
  const ws5 = editForm.ws5 || {};
  const tags = editForm.tags || [];
  const updLaag = (k, v) => setEditForm(f => ({ ...f, lagen: { ...(f.lagen || {}), [k]: v } }));
  const updWs5  = (k, v) => setEditForm(f => ({ ...f, ws5:   { ...(f.ws5 || {}),   [k]: v } }));

  return (
    <>
      {/* Lagen 1-4 */}
      <div className="space-y-1.5">
        {['laag1','laag2','laag3','laag4'].map((k, i) => (
          <div key={k}>
            <label className="text-[10px] uppercase text-slate-500 tracking-wide">
              Laag {i+1}{highlightLaag1 && i === 0 && <span className="text-red-400 ml-1">(belangrijk)</span>}
            </label>
            {editable ? (
              <textarea data-testid={`${testIdPrefix}-${k}`} value={lagen[k] || ''} rows={2}
                onChange={(e) => updLaag(k, e.target.value)}
                placeholder={i === 0 ? 'Kort antwoord / definitie' : ''}
                className="w-full mt-0.5 text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1 resize-y focus:outline-none focus:border-emerald-500/40" />
            ) : (
              <p className={`text-xs px-2 py-1 rounded ${lagen[k] ? 'text-slate-200 bg-slate-800/40' : 'text-slate-600 italic'}`}>
                {lagen[k] || '(leeg)'}
              </p>
            )}
          </div>
        ))}
      </div>

      {/* WS5 */}
      <details className="border border-slate-800 rounded-lg" {...(openWs5 ? { open: true } : {})}>
        <summary className="px-2 py-1.5 text-[11px] text-slate-400 cursor-pointer">5W (wie/wat/wanneer/waar/waarom/hoe)</summary>
        <div className="p-2 space-y-1">
          {['wie','wat','wanneer','waar','waarom','hoe'].map(k => (
            <div key={k} className="flex items-start gap-2">
              <span className="text-[10px] text-slate-500 w-14 mt-0.5 uppercase">{k}</span>
              {editable ? (
                <input data-testid={`${testIdPrefix}-ws5-${k}`} value={ws5[k] || ''}
                  onChange={(e) => updWs5(k, e.target.value)}
                  className="flex-1 text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-0.5 focus:outline-none focus:border-emerald-500/40" />
              ) : (
                <span className="text-xs text-slate-300">{ws5[k] || '—'}</span>
              )}
            </div>
          ))}
        </div>
      </details>

      {/* Tags */}
      <div>
        <label className="text-[10px] uppercase text-slate-500 tracking-wide">Tags</label>
        {editable ? (
          <input data-testid={`${testIdPrefix}-tags`} value={(tags || []).join(', ')}
            onChange={(e) => setEditForm(f => ({ ...f, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) }))}
            placeholder="emotie, verbinding, ..."
            className="w-full text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-emerald-500/40" />
        ) : (
          <div className="flex flex-wrap gap-1 mt-0.5">
            {(tags || []).slice(0, 25).map((t, i) => (
              <span key={i} className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800/60 text-slate-300">{t}</span>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

// v6_capability_links_001 — koppel een doe-kaart aan een Spark capability
function CapabilityCoupling({ cardId, cardBegrip }) {
  const [caps, setCaps] = React.useState([]);
  const [currentLink, setCurrentLink] = React.useState(null); // { capability_id, capability_naam, has_handler }
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);

  const reload = React.useCallback(async () => {
    setLoading(true);
    try {
      const [capsR, linksR] = await Promise.all([
        fetch(`${API}/api/admin/capabilities`).then(r => r.json()),
        fetch(`${API}/api/admin/capabilities/links`).then(r => r.json()),
      ]);
      setCaps(capsR.capabilities || []);
      const mine = (linksR.links || []).find(l => l.card_id === cardId);
      setCurrentLink(mine || null);
    } catch (e) {
      console.warn('capability load failed', e);
    } finally {
      setLoading(false);
    }
  }, [cardId]);

  React.useEffect(() => { reload(); }, [reload]);

  const saveLink = async (capabilityId) => {
    setSaving(true);
    try {
      if (!capabilityId) {
        // Ontkoppel
        await fetch(`${API}/api/admin/capabilities/links/${cardId}`, { method: 'DELETE' });
      } else {
        await fetch(`${API}/api/admin/capabilities/links`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ card_id: cardId, capability_id: capabilityId }),
        });
      }
      await reload();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="border border-purple-500/20 bg-purple-500/5 rounded-lg p-2">
        <p className="text-[10px] uppercase text-purple-300 tracking-wide">🤲 Capability-koppeling</p>
        <p className="text-[11px] text-slate-500 mt-0.5">Laden…</p>
      </div>
    );
  }

  return (
    <div data-testid="kbv2-capability-coupling" className="border border-purple-500/20 bg-purple-500/5 rounded-lg p-2 space-y-1">
      <div className="flex items-center justify-between">
        <p className="text-[10px] uppercase text-purple-300 tracking-wide">🤲 Capability-koppeling</p>
        {currentLink && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${currentLink.has_handler ? 'bg-emerald-500/15 text-emerald-300' : 'bg-amber-500/15 text-amber-300'}`}>
            {currentLink.has_handler ? '● handler live' : '○ geen handler'}
          </span>
        )}
      </div>
      <p className="text-[10px] text-slate-500 leading-tight">
        Koppel {cardBegrip ? <strong>{cardBegrip}</strong> : 'deze kaart'} aan een actie die Spark daadwerkelijk kan uitvoeren.
        Zo wordt een doe-woord een echte vaardigheid.
      </p>
      <select
        data-testid="kbv2-capability-select"
        value={currentLink?.capability_id || ''}
        disabled={saving}
        onChange={(e) => saveLink(e.target.value || null)}
        className="w-full text-xs text-slate-200 bg-slate-800/80 border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-purple-500/40"
      >
        <option value="">— niet gekoppeld —</option>
        {caps.map(c => (
          <option key={c.id} value={c.id}>
            {c.has_handler ? '● ' : '○ '}{c.naam || c.id} ({c.categorie || '?'})
          </option>
        ))}
      </select>
    </div>
  );
}

function AuditModal({ data, onClose }) {
  const s = data.summary || {};
  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-amber-500/30 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}>
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-amber-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" /> KB v2 Self-Audit
            </h3>
            <p className="text-[10px] text-slate-500 mt-0.5">#DeWillem principe — Spark scant zichzelf op gaten</p>
          </div>
          <button data-testid="kbv2-audit-close" onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-4 h-4" /></button>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-3 gap-2">
          <Stat label="Lege laag1 in lades" value={s.empty_laag1_count} color="#ef4444" />
          <Stat label="Ontbrekende footnote" value={s.missing_footnote_count} color="#f59e0b" />
          <Stat label="Laag vertrouwen (<50%)" value={s.low_confidence_count} color="#f59e0b" />
          <Stat label="Kaarten zonder tags" value={s.no_tags_count} color="#94a3b8" />
          <Stat label="Inbox: tag-tie" value={s.inbox_ties} color="#f59e0b" />
          <Stat label="Inbox: no-match" value={s.inbox_no_match} color="#94a3b8" />
          <Stat label="Inbox: zonder laag1" value={s.inbox_missing_laag1} color="#ef4444" />
        </div>
        <div className="p-4 border-t border-slate-800 text-[11px] text-slate-400 leading-relaxed">
          <p>Gevonden gaten zijn geen fouten — het zijn kaarten die wachten op een mens-in-de-loop.
          Open de Inbox-tab en geef ze hun lade. Hoe meer je doet, hoe sterker Spark's geheugen wordt.</p>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, color }) {
  return (
    <div className="bg-slate-800/40 rounded-lg p-2 border border-slate-800">
      <p className="text-[10px] text-slate-500 uppercase tracking-wide">{label}</p>
      <p className="text-xl font-bold mt-0.5" style={{ color }}>{value || 0}</p>
    </div>
  );
}

/**
 * EmotieSection — v14_emotie_veld_001: 5 basis-emoties, bevestigen met één klik.
 * 'neutraal' is een echte keuze. Suggestie (uit tag/importer) licht op maar telt niet.
 */
const EMOTIES = [
  { id: 'blij', label: 'Blij', color: '#facc15' },
  { id: 'boos', label: 'Boos', color: '#f87171' },
  { id: 'bang', label: 'Bang', color: '#a78bfa' },
  { id: 'bedroefd', label: 'Bedroefd', color: '#60a5fa' },
  { id: 'neutraal', label: 'Neutraal', color: '#94a3b8' },
];

function EmotieSection({ card, currentLade, onUpdated }) {
  const [saving, setSaving] = useState(false);
  const confirmed = !!card.emotie_bevestigd;
  const current = confirmed ? card.emotie : null;
  const suggestie = !confirmed ? (card.emotie_suggestie || card.emotie || null) : null;

  const kies = async (emotie) => {
    if (saving || !currentLade) return;
    setSaving(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/edit`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: card.id, lade: currentLade, updates: { emotie }, user_id: 'user-001' }),
      }).then(x => x.json());
      if (!r.success) toast.error(r.message || 'Emotie opslaan mislukt');
      else onUpdated && onUpdated();
    } catch (e) { toast.error('Emotie fout: ' + e.message); }
    setSaving(false);
  };

  return (
    <div data-testid="kbv2-emotie-section" className="bg-slate-800/30 rounded-lg p-2 space-y-1.5">
      <div className="flex items-center justify-between">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide">Emotie</p>
        <span className="text-[10px] text-slate-500">
          {confirmed ? <span className="text-pink-300">💗 bevestigd</span>
            : suggestie ? <>suggestie: <span className="text-slate-300">{suggestie}</span> (nog niet bevestigd)</>
            : 'nog niet gekozen'}
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {EMOTIES.map(e => {
          const active = current === e.id;
          const hint = !confirmed && suggestie === e.id;
          return (
            <button key={e.id} data-testid={`kbv2-emotie-${e.id}`} onClick={() => kies(e.id)} disabled={saving}
              className={`px-2.5 py-1 rounded-md text-[11px] font-medium border transition-colors disabled:opacity-50 ${
                active ? 'border-current' : hint ? 'border-dashed border-current opacity-80' : 'border-slate-700 text-slate-400 hover:text-slate-200'}`}
              style={(active || hint) ? { color: e.color, borderColor: e.color, backgroundColor: active ? e.color + '22' : 'transparent' } : {}}>
              {e.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * MediaSection — voice (Whisper STT) + image upload bij een kaart.
 * Voor inbox-kaarten: currentLade = null, backend leidt lade af via index.
 */
function MediaSection({ card, currentLade, onUpdated }) {
  const media = card.media || {};
  const [recording, setRecording] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  // v7_media_dedup_001 — Image picker uit archief
  const [showImagePicker, setShowImagePicker] = useState(false);
  const [archiveImages, setArchiveImages] = useState([]);
  const [loadingArchive, setLoadingArchive] = useState(false);
  const [archiveSearch, setArchiveSearch] = useState('');

  useEffect(() => {
    if (!showImagePicker) return;
    setLoadingArchive(true);
    fetch(`${API}/api/kb/v2/media/archive/list?limit=500`)
      .then(r => r.json())
      .then(d => setArchiveImages(d.items || []))
      .catch(() => setArchiveImages([]))
      .finally(() => setLoadingArchive(false));
  }, [showImagePicker]);

  const [err, setErr] = useState('');
  const linkArchiveImage = async (archive_id) => {
    try {
      const r = await fetch(`${API}/api/kb/v2/media/image/link-existing`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ card_id: card.id, archive_id, lade: currentLade || undefined, user_id: 'user-000' }),
      }).then(x => x.json());
      if (r.success && r.image_url) {
        setShowImagePicker(false);
        onUpdated && onUpdated();
      } else {
        setErr(r.error || 'Kon foto niet koppelen');
      }
    } catch (e) {
      setErr(e.message);
    }
  };
  // v6_kbv2_media_audio2_001 — 2e audio
  const [extraKind, setExtraKind] = useState('spraak'); // 'spraak' = transcribe, 'geluid' = alleen opslaan
  const [recordingExtra, setRecordingExtra] = useState(false);
  const [uploadingExtra, setUploadingExtra] = useState(false);
  const mediaRecRef = useRef(null);
  const chunksRef = useRef([]);
  const extraRecRef = useRef(null);
  const extraChunksRef = useRef([]);
  const imgInputRef = useRef(null);
  const extraInputRef = useRef(null);

  const startRecord = async () => {
    setErr('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      chunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data && e.data.size > 0) chunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(t => t.stop());
        await uploadVoice(blob);
      };
      mediaRecRef.current = mr;
      mr.start();
      setRecording(true);
    } catch (e) {
      setErr('Microfoon geweigerd of niet beschikbaar.');
    }
  };

  const stopRecord = () => {
    try { mediaRecRef.current?.stop(); } catch {}
    setRecording(false);
  };

  const uploadVoice = async (blob) => {
    setUploadingVoice(true);
    try {
      const fd = new FormData();
      fd.append('audio', blob, 'inspraak.webm');
      fd.append('card_id', card.id);
      if (currentLade) fd.append('lade', currentLade);
      fd.append('user_id', 'user-001');
      const r = await fetch(`${API}/api/kb/v2/media/voice`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) setErr(r.error || 'Voice-upload mislukt');
      onUpdated && onUpdated();
    } catch (e) { setErr('Voice-upload fout: ' + e.message); }
    setUploadingVoice(false);
  };

  const handleImageSelect = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingImage(true);
    setErr('');
    try {
      const fd = new FormData();
      fd.append('image', file);
      fd.append('card_id', card.id);
      if (currentLade) fd.append('lade', currentLade);
      fd.append('user_id', 'user-001');
      const r = await fetch(`${API}/api/kb/v2/media/image`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) setErr('Image-upload mislukt');
      onUpdated && onUpdated();
    } catch (ex) { setErr('Image fout: ' + ex.message); }
    setUploadingImage(false);
    if (imgInputRef.current) imgInputRef.current.value = '';
  };

  // v6_kbv2_media_delete_001 — verwijder voice / image
  const deleteVoice = async () => {
    if (!window.confirm('Voice + transcript verwijderen van deze kaart?')) return;
    const qs = new URLSearchParams({ user_id: 'user-001', ...(currentLade ? { lade: currentLade } : {}) });
    await fetch(`${API}/api/kb/v2/media/voice/${card.id}?${qs}`, { method: 'DELETE' });
    onUpdated && onUpdated();
  };

  const deleteImage = async (url) => {
    if (!window.confirm('Foto verwijderen van deze kaart?')) return;
    const qs = new URLSearchParams({ image_url: url, user_id: 'user-001', ...(currentLade ? { lade: currentLade } : {}) });
    await fetch(`${API}/api/kb/v2/media/image/${card.id}?${qs}`, { method: 'DELETE' });
    onUpdated && onUpdated();
  };

  const deleteExtraAudio = async (archive_id) => {
    if (!window.confirm('Extra audio verwijderen van deze kaart?')) return;
    const qs = new URLSearchParams({ archive_id, user_id: 'user-001', ...(currentLade ? { lade: currentLade } : {}) });
    await fetch(`${API}/api/kb/v2/media/voice/secondary/${card.id}?${qs}`, { method: 'DELETE' });
    onUpdated && onUpdated();
  };

  // v6_kbv2_audio_kind_001 — toggle audio-kind (spraak ↔ geluid)
  const togglePrimaryKind = async () => {
    const cur = (media.voice_kind || 'spraak');
    const next = cur === 'spraak' ? 'geluid' : 'spraak';
    const qs = new URLSearchParams({ kind: next, user_id: 'user-001', ...(currentLade ? { lade: currentLade } : {}) });
    await fetch(`${API}/api/kb/v2/media/voice/kind/${card.id}?${qs}`, { method: 'PATCH' });
    onUpdated && onUpdated();
  };

  const toggleExtraKind = async (archive_id, currentKind) => {
    const next = (currentKind || 'spraak') === 'spraak' ? 'geluid' : 'spraak';
    const qs = new URLSearchParams({ archive_id, kind: next, user_id: 'user-001', ...(currentLade ? { lade: currentLade } : {}) });
    await fetch(`${API}/api/kb/v2/media/voice/secondary/kind/${card.id}?${qs}`, { method: 'PATCH' });
    onUpdated && onUpdated();
  };

  // v6_kbv2_media_audio2_001 — 2e audio opname (spraak of geluid)
  const startExtraRecord = async () => {
    setErr('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      extraChunksRef.current = [];
      mr.ondataavailable = (e) => { if (e.data?.size > 0) extraChunksRef.current.push(e.data); };
      mr.onstop = async () => {
        const blob = new Blob(extraChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(t => t.stop());
        await uploadExtra(blob, `extra_${Date.now()}.webm`);
      };
      extraRecRef.current = mr;
      mr.start();
      setRecordingExtra(true);
    } catch (e) { setErr('Microfoon geweigerd.'); }
  };
  const stopExtraRecord = () => { try { extraRecRef.current?.stop(); } catch {} setRecordingExtra(false); };

  const uploadExtra = async (file, filename) => {
    setUploadingExtra(true);
    try {
      const fd = new FormData();
      fd.append('audio', file, filename || (file.name || 'extra.webm'));
      fd.append('card_id', card.id);
      if (currentLade) fd.append('lade', currentLade);
      fd.append('user_id', 'user-001');
      fd.append('audio_kind', extraKind);
      fd.append('transcribe', extraKind === 'spraak' ? 'true' : 'false');
      const r = await fetch(`${API}/api/kb/v2/media/voice/secondary`, { method: 'POST', body: fd }).then(x => x.json());
      if (!r.success) setErr(r.error || 'Audio-upload mislukt');
      onUpdated && onUpdated();
    } catch (e) { setErr('Audio fout: ' + e.message); }
    setUploadingExtra(false);
    if (extraInputRef.current) extraInputRef.current.value = '';
  };

  const handleExtraSelect = (e) => {
    const f = e.target.files?.[0];
    if (f) uploadExtra(f);
  };

  return (
    <div className="border-t border-slate-800 pt-3 space-y-2">
      <p className="text-[10px] uppercase text-slate-500 tracking-wide">Media</p>

      {/* Voice */}
      <div className="bg-slate-800/30 rounded-lg p-2 space-y-2">
        <div className="flex items-center gap-2">
          {!recording ? (
            <button data-testid="kbv2-voice-record"
              onClick={startRecord} disabled={uploadingVoice}
              className="px-2 py-1 text-xs rounded-md bg-rose-500/15 border border-rose-500/40 text-rose-300 hover:bg-rose-500/25 disabled:opacity-50 flex items-center gap-1.5">
              <Mic className="w-3.5 h-3.5" /> {uploadingVoice ? 'Transcriberen...' : 'Spreek in'}
            </button>
          ) : (
            <button data-testid="kbv2-voice-stop" onClick={stopRecord}
              className="px-2 py-1 text-xs rounded-md bg-red-500/30 border border-red-500/60 text-red-200 animate-pulse flex items-center gap-1.5">
              <Square className="w-3.5 h-3.5" /> Stop & verstuur
            </button>
          )}
          {media.voice_url && (
            <>
              {/* v6_kbv2_audio_kind_001 — Klikbare kind-toggle (🎤 spraak ↔ 🔊 geluid) */}
              <button data-testid="kbv2-voice-kind-toggle" onClick={togglePrimaryKind}
                title={`Wissel naar ${(media.voice_kind || 'spraak') === 'spraak' ? 'geluid' : 'spraak'}`}
                className={`flex items-center gap-1 px-1.5 py-1 rounded text-[10px] font-semibold border transition-colors ${
                  (media.voice_kind || 'spraak') === 'spraak'
                    ? 'bg-rose-500/20 text-rose-200 border-rose-500/40 hover:bg-rose-500/30'
                    : 'bg-indigo-500/20 text-indigo-200 border-indigo-500/40 hover:bg-indigo-500/30'
                }`}>
                {(media.voice_kind || 'spraak') === 'spraak'
                  ? <><Mic className="w-3 h-3" /> SPRAAK</>
                  : <><Volume2 className="w-3 h-3" /> GELUID</>}
              </button>
              <audio data-testid="kbv2-voice-audio" controls className="h-7 flex-1" src={API + media.voice_url} />
              <button data-testid="kbv2-voice-delete" onClick={deleteVoice}
                title="Voice + transcript wissen"
                className="px-2 py-1 text-xs rounded-md bg-red-500/15 border border-red-500/40 text-red-300 hover:bg-red-500/25">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </>
          )}
        </div>
        {media.voice_transcript && (
          <div className="text-[11px] text-slate-300 italic bg-slate-900/50 rounded px-2 py-1 border-l-2 border-rose-500/40">
            <span className="text-slate-500">Transcript: </span>"{media.voice_transcript}"
          </div>
        )}
      </div>

      {/* v6_kbv2_media_audio2_001 — Extra audio (spraak of geluid) */}
      <div className="bg-slate-800/30 rounded-lg p-2 space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] text-slate-400 uppercase tracking-wider">Extra audio:</span>
          <div className="flex bg-slate-900 rounded-md p-0.5">
            <button data-testid="kbv2-extra-kind-spraak" onClick={() => setExtraKind('spraak')}
              className={`px-2 py-0.5 text-[10px] rounded ${extraKind === 'spraak' ? 'bg-rose-500/30 text-rose-200' : 'text-slate-400'}`}>
              Spraak (→ transcript)
            </button>
            <button data-testid="kbv2-extra-kind-geluid" onClick={() => setExtraKind('geluid')}
              className={`px-2 py-0.5 text-[10px] rounded ${extraKind === 'geluid' ? 'bg-indigo-500/30 text-indigo-200' : 'text-slate-400'}`}>
              Geluid
            </button>
          </div>
          {!recordingExtra ? (
            <button data-testid="kbv2-extra-record" onClick={startExtraRecord} disabled={uploadingExtra}
              className="px-2 py-1 text-xs rounded-md bg-rose-500/15 border border-rose-500/40 text-rose-300 hover:bg-rose-500/25 disabled:opacity-50 flex items-center gap-1.5">
              <Mic className="w-3.5 h-3.5" /> {uploadingExtra ? 'Opslaan...' : 'Opnemen'}
            </button>
          ) : (
            <button data-testid="kbv2-extra-stop" onClick={stopExtraRecord}
              className="px-2 py-1 text-xs rounded-md bg-red-500/30 border border-red-500/60 text-red-200 animate-pulse flex items-center gap-1.5">
              <Square className="w-3.5 h-3.5" /> Stop
            </button>
          )}
          <input ref={extraInputRef} type="file" accept="audio/*" onChange={handleExtraSelect} className="hidden" data-testid="kbv2-extra-input" />
          <button data-testid="kbv2-extra-upload" onClick={() => extraInputRef.current?.click()} disabled={uploadingExtra}
            className="px-2 py-1 text-xs rounded-md bg-slate-700/40 border border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-50">
            Upload bestand
          </button>
        </div>
        {(media.extra_audio || []).length > 0 && (
          <div className="space-y-1">
            {(media.extra_audio || []).map((a, i) => (
              <div key={a.archive_id || i} data-testid={`kbv2-extra-audio-${i}`} className="flex items-center gap-2 bg-slate-900/50 rounded px-2 py-1">
                {/* v6_kbv2_audio_kind_001 — Klikbare kind-toggle */}
                <button data-testid={`kbv2-extra-kind-toggle-${i}`}
                  onClick={() => toggleExtraKind(a.archive_id, a.kind)}
                  title={`Wissel naar ${a.kind === 'spraak' ? 'geluid' : 'spraak'}`}
                  className={`flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded font-semibold transition-colors ${
                    a.kind === 'spraak'
                      ? 'bg-rose-500/20 text-rose-300 hover:bg-rose-500/30'
                      : 'bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30'
                  }`}>
                  {a.kind === 'spraak' ? <><Mic className="w-3 h-3" /> SPRAAK</> : <><Volume2 className="w-3 h-3" /> GELUID</>}
                </button>
                <audio controls className="h-6 flex-1" src={API + a.url} />
                <button onClick={() => deleteExtraAudio(a.archive_id)}
                  data-testid={`kbv2-extra-delete-${i}`}
                  className="p-1 rounded hover:bg-red-500/20 text-red-300">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
            {(media.extra_audio || []).filter(a => a.transcript).map((a, i) => (
              <p key={`tr-${i}`} className="text-[10px] text-slate-400 italic pl-2 border-l-2 border-rose-500/30">"{a.transcript}"</p>
            ))}
          </div>
        )}
      </div>

      {/* Image */}
      <div className="bg-slate-800/30 rounded-lg p-2 space-y-2">
        <div className="flex items-center gap-2">
          <input ref={imgInputRef} type="file" accept="image/*" onChange={handleImageSelect}
            className="hidden" data-testid="kbv2-image-input" />
          <button data-testid="kbv2-image-upload" onClick={() => imgInputRef.current?.click()}
            disabled={uploadingImage}
            className="px-2 py-1 text-xs rounded-md bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/25 disabled:opacity-50 flex items-center gap-1.5">
            <ImageIcon className="w-3.5 h-3.5" /> {uploadingImage ? 'Uploaden...' : 'Foto toevoegen'}
          </button>
          <button data-testid="kbv2-image-picker" onClick={() => setShowImagePicker(true)}
            className="px-2 py-1 text-xs rounded-md bg-cyan-500/15 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/25 flex items-center gap-1.5"
            title="Kies uit bestaande foto's in archief (bespaart opslag)">
            <ImageIcon className="w-3.5 h-3.5" /> Uit archief
          </button>
          {(media.image_urls || []).filter(Boolean).length > 0 && (
            <span className="text-[10px] text-slate-500">{media.image_urls.filter(Boolean).length} foto's</span>
          )}
        </div>
        {(media.image_urls || []).filter(Boolean).length > 0 && (
          <div className="flex flex-wrap gap-2">
            {(media.image_urls || []).filter(Boolean).map((url, i) => (
              <div key={i} className="relative">
                <img src={API + url} alt={`media-${i}`}
                  className="w-16 h-16 object-cover rounded border border-slate-700" />
                {/* v6_kbv2_image_delete_visibility_001 — knop altijd zichtbaar (was opacity-0 group-hover) */}
                <button data-testid={`kbv2-image-delete-${i}`} onClick={() => deleteImage(url)}
                  title="Foto verwijderen"
                  aria-label="Foto verwijderen"
                  className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center shadow-md ring-1 ring-slate-900 transition-colors">
                  <X className="w-3 h-3 text-white" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {err && <p className="text-[10px] text-red-400">{err}</p>}

      {/* v7_media_dedup_001 — Image Archive Picker Modal */}
      {showImagePicker && (
        <div
          data-testid="kbv2-image-picker-modal"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
          onClick={() => setShowImagePicker(false)}
        >
          <div
            className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <div>
                <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                  <ImageIcon className="w-4 h-4 text-cyan-400" /> Kies uit archief
                </h3>
                <p className="text-[10px] text-slate-500 mt-0.5">Hergebruik een bestaande foto — bespaart opslag (geen re-upload).</p>
              </div>
              <button
                data-testid="kbv2-image-picker-close"
                onClick={() => setShowImagePicker(false)}
                className="w-7 h-7 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-3 border-b border-slate-800">
              <input
                data-testid="kbv2-image-picker-search"
                type="text"
                placeholder="Zoek op naam..."
                value={archiveSearch}
                onChange={(e) => setArchiveSearch(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {loadingArchive ? (
                <p className="text-xs text-slate-500 text-center py-8">Archief laden...</p>
              ) : archiveImages.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-8">Geen foto's in archief.</p>
              ) : (
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-2">
                  {archiveImages
                    .filter(a => !archiveSearch || (a.original_name || '').toLowerCase().includes(archiveSearch.toLowerCase()))
                    .map((a) => (
                      <button
                        key={a.id}
                        data-testid={`kbv2-image-picker-item-${a.id}`}
                        onClick={() => linkArchiveImage(a.id)}
                        className="group relative aspect-square rounded-lg overflow-hidden border border-slate-700 hover:border-cyan-400 transition-colors bg-slate-800"
                        title={`${a.original_name || a.id} — hergebruikt ${a.reuse_count || 0}x`}
                      >
                        <img
                          src={API + a.url}
                          alt={a.original_name || a.id}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        {(a.reuse_count || 0) > 0 && (
                          <span className="absolute top-1 right-1 text-[9px] bg-cyan-500/80 text-white px-1.5 py-0.5 rounded-full font-semibold">
                            {a.reuse_count}x
                          </span>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <p className="text-[9px] text-white truncate">{a.original_name || a.id}</p>
                        </div>
                      </button>
                    ))}
                </div>
              )}
            </div>

            <div className="p-3 border-t border-slate-800 text-[10px] text-slate-500 flex items-center justify-between">
              <span>{archiveImages.length} foto's beschikbaar</span>
              <span className="text-cyan-400">Klik een foto om te koppelen</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================
// v6_kbv2_inline_new_001 — Lege kaart in rechter paneel (geen window.prompt)
// v6_kbv2_unify_001 — gebruikt CardFormFields voor identieke velden als CardDetail
// ============================================================
function NewCardInline({ editForm, setEditForm, saving, onSave, onCancel, herzienV1, herzienRemaining, onNextHerzien,
                        dupCheck, onCheckDup, onOpenExisting }) {
  // v6_kbv2_unify_001 — debounce duplicate check op begrip (hook MOET vóór early return)
  const dupTimer = useRef(null);
  if (!editForm) return null;
  const lagen = editForm.lagen || {};
  const ws5 = editForm.ws5 || {};
  const tags = editForm.tags || [];

  const hasL1 = !!(lagen.laag1 || '').trim();
  const has5w = Object.values(ws5).some(v => (v || '').trim());
  const hasTags = (tags || []).length > 0;
  const compleet = hasL1 && has5w;
  const isHerzien = !!herzienV1;

  const onBegripChange = (val) => {
    setEditForm(f => ({ ...f, begrip: val }));
    if (isHerzien) return; // herzien is een v1-kaart promoveren, geen nieuw begrip
    if (dupTimer.current) clearTimeout(dupTimer.current);
    dupTimer.current = setTimeout(() => onCheckDup && onCheckDup(val), 400);
  };

  // Auto-suggest lade op basis van topic + tags
  const _autoLade = () => {
    const pool = [(editForm.topic || '').toLowerCase(), ...(tags || []).map(t => t.toLowerCase())];
    const map = {
      voelen: ['emotie','voelen','gevoel','relatie','verbinding','empathie','compassie'],
      spreken: ['taal','communicatie','gesprek','schrijven','spreken','praten'],
      weten: ['kennis','systeem','feit','logica','definitie','concept','model','theorie','weten','geheugen'],
      doen: ['gedrag','actie','praktijk','doen','uitvoeren','stap','methode','proces'],
    };
    for (const token of pool) {
      for (const [lade, kws] of Object.entries(map)) {
        if (kws.some(k => token.includes(k))) return lade;
      }
    }
    return 'weten';
  };
  const suggestedLade = isHerzien ? _autoLade() : null;

  // v6_kbv2_unify_001 — compleetheid-meter (zelfde 8-velden score als CardDetail)
  const hasL2 = !!(lagen.laag2 || '').trim();
  const hasL3 = !!(lagen.laag3 || '').trim();
  const hasL4 = !!(lagen.laag4 || '').trim();
  const filledCount = [hasL1, hasL2, hasL3, hasL4, has5w, hasTags, false, false].filter(Boolean).length;
  const totalFields = 8;
  const pct = Math.round((filledCount / totalFields) * 100);

  const dupBlocking = !isHerzien && dupCheck && dupCheck.exists;

  return (
    <div className="space-y-3" data-testid="kbv2-inline-newcard">
      {/* Herzien banner */}
      {isHerzien && (
        <div data-testid="kbv2-herzien-banner" className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-purple-300">♻️</span>
            <div className="min-w-0">
              <p className="text-[11px] text-purple-200 font-semibold">Herzien: KB v1 kaart</p>
              <p className="text-[10px] text-slate-400 truncate">id {herzienV1.id} · nog {herzienRemaining} te gaan · auto-lade: <span className="text-purple-300">{suggestedLade}</span></p>
            </div>
          </div>
          <button data-testid="kbv2-herzien-skip" onClick={onNextHerzien}
            className="px-2 py-1 text-[10px] border border-purple-500/40 text-purple-300 hover:bg-purple-500/15 rounded">
            Skip → volgende
          </button>
        </div>
      )}

      {/* v6_kbv2_unify_001 — Duplicate-banner */}
      {dupBlocking && (
        <div data-testid="kbv2-dup-banner" className="bg-red-500/10 border border-red-500/40 rounded-lg p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <div className="min-w-0">
              <p className="text-[11px] text-red-200 font-semibold truncate">"{dupCheck.info?.begrip}" bestaat al</p>
              <p className="text-[10px] text-slate-400 truncate">Lade: <span className="text-red-300">{dupCheck.info?.lade || 'inbox'}</span> · id {dupCheck.info?.kaart_id}</p>
            </div>
          </div>
          <button data-testid="kbv2-dup-open-existing" onClick={onOpenExisting}
            className="px-2 py-1 text-[10px] border border-red-500/40 text-red-200 hover:bg-red-500/15 rounded shrink-0">
            Open bestaande →
          </button>
        </div>
      )}

      <div className="flex items-start justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="flex-1">
          <p className="text-[10px] uppercase text-emerald-400 tracking-wider font-bold">
            {isHerzien ? 'Herzien & promoten naar KB v2' : 'Nieuwe kaart'}
          </p>
          <input data-testid="kbv2-new-begrip" type="text" value={editForm.begrip || ''}
            onChange={e => onBegripChange(e.target.value)} autoFocus
            placeholder="Begrip (verplicht)"
            className={`mt-1 w-full text-lg font-bold text-white bg-slate-800/60 border rounded px-2 py-1 focus:outline-none ${
              dupBlocking ? 'border-red-500/60 focus:border-red-500' : 'border-slate-700 focus:border-emerald-500/60'
            }`} />
          <p className="text-[10px] text-slate-500 mt-1">
            {dupCheck?.checking && <span className="text-slate-400">Bezig met controle…</span>}
            {!dupCheck?.checking && isHerzien && (
              compleet
                ? <>Wordt opgeslagen in lade <span className="text-purple-300">{suggestedLade}</span> (op basis van topic + tags).</>
                : <>Vul minimaal <span className="text-amber-300">laag 1</span> in om kaart te promoveren naar KB v2.</>
            )}
            {!dupCheck?.checking && !isHerzien && (
              <>Nieuwe kaart komt eerst in <span className="text-amber-300">inbox</span>.
              {!compleet && <> Niet compleet ingevuld → blijft in <span className="text-red-400">onbeantwoord</span>.</>}</>
            )}
          </p>
        </div>
        {/* v6_kbv2_unify_001 — Compleetheid badge ook in NewCardInline */}
        <div data-testid="kbv2-new-completeness-badge" className={`px-2 py-1 rounded-lg text-[10px] font-semibold border self-start ${
          pct === 100
            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
            : pct >= 50
              ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-400'
        }`}>
          {pct}%
        </div>
        <button data-testid="kbv2-new-cancel" onClick={onCancel}
          className="p-1 hover:bg-slate-800 rounded text-slate-400">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Topic (alleen voor herzien — drives auto-classify) */}
      {isHerzien && (
        <div>
          <label className="text-[10px] uppercase text-slate-500 tracking-wide">
            Topic <span className="text-purple-300">(stuurt auto-lade)</span>
          </label>
          <input data-testid="kbv2-herzien-topic" value={editForm.topic || ''}
            onChange={e => setEditForm(f => ({ ...f, topic: e.target.value }))}
            placeholder="bv. systeem / emotie / actie / taal"
            className="w-full text-xs text-slate-200 bg-slate-800/60 border border-slate-700 rounded px-2 py-1 focus:outline-none focus:border-amber-500/40" />
        </div>
      )}

      {/* v6_kbv2_unify_001 — gedeelde form-velden */}
      <CardFormFields
        editForm={editForm}
        setEditForm={setEditForm}
        editable={true}
        testIdPrefix="kbv2-new"
        openWs5={true}
        highlightLaag1={true}
      />

      {/* Completeness hint */}
      <div className="text-[10px] text-slate-500 border-t border-slate-800 pt-2 leading-relaxed">
        Status na opslaan:{' '}
        {isHerzien
          ? (hasL1
              ? <span className="text-purple-400 font-semibold">Promoveert naar lade {suggestedLade}</span>
              : <span className="text-red-400 font-semibold">Geen laag 1 → kan niet promoten</span>)
          : (compleet
              ? <span className="text-emerald-400 font-semibold">Compleet (laag 1 + 5W) — klaar voor indelen</span>
              : <span className="text-red-400 font-semibold">Onbeantwoord — blijft in inbox</span>)}
      </div>

      <div className="flex justify-end gap-2 border-t border-slate-800 pt-3">
        <button data-testid="kbv2-new-cancel-btn" onClick={onCancel}
          className="px-3 py-1.5 text-xs text-slate-400 hover:bg-slate-800 rounded-lg">Annuleren</button>
        <button data-testid="kbv2-new-save-btn" onClick={onSave}
          disabled={saving || !(editForm.begrip || '').trim() || (isHerzien && !hasL1) || dupBlocking}
          title={dupBlocking ? 'Begrip bestaat al — open bestaande kaart of pas naam aan' : ''}
          className={`px-4 py-1.5 text-xs font-medium rounded-lg text-white disabled:opacity-40 flex items-center gap-1.5 ${
            isHerzien ? 'bg-amber-500 hover:bg-amber-600' : 'bg-emerald-500 hover:bg-emerald-600'
          }`}>
            <Save className="w-3 h-3" /> {saving ? 'Opslaan...' : (isHerzien ? `Promoveer naar ${suggestedLade}` : 'Opslaan in inbox')}
        </button>
      </div>
    </div>
  );
}

export default KennisbankV2Page;
