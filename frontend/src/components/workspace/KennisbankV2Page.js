import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { toast } from 'sonner';
import {
  Inbox, BookOpen, Search, Save, X, AlertTriangle,
  ChevronRight, RefreshCw, Eye, Edit3, ArrowRightLeft,
  Mic, Square, Image as ImageIcon, Upload, Trash2, CheckCircle2, Plus, Merge,
  Volume2, Sparkles
} from 'lucide-react';
import { KbV2TagCuration } from './KbV2TagCuration';

const API = process.env.REACT_APP_BACKEND_URL;

const LADES = [
  { id: 'voelen',   icon: '🌸', naam: 'Voelen',      stroom: 'Emotie & Verbinding', color: '#ec4899' },
  { id: 'spreken',  icon: '💬', naam: 'Spreken',     stroom: 'Communicatie & Taal', color: '#06b6d4' },
  { id: 'weten',    icon: '🧠', naam: 'Weten',       stroom: 'Systeem & Kennis',    color: '#f59e0b' },
  { id: 'doen',     icon: '🎭', naam: 'Doen',        stroom: 'Gedrag & Actie',      color: '#a855f7' },
];

const REASON_LABEL = {
  tag_tie:        { label: 'Tag-tie',       color: '#f59e0b' },
  no_match:       { label: 'Geen match',     color: '#94a3b8' },
  missing_laag1:  { label: 'Geen laag 1',    color: '#ef4444' },
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
  const [activeTab, setActiveTab] = useState('inbox');     // 'inbox' | lade-id
  const [stats, setStats] = useState(null);
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [reasons, setReasons] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [reasonFilter, setReasonFilter] = useState('');
  // v6_kbv2_priority_001 — Top 50 prio modus
  const [priorityMode, setPriorityMode] = useState(false);
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
    } catch {}
  }, []);

  // Load list (inbox or lade)
  const loadItems = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) });
      if (search) qs.append('search', search);
      let url;
      if (activeTab === 'inbox' && priorityMode) {
        // v6_kbv2_priority_001 — Top 50 belangrijkste kaarten zonder laag1
        url = `${API}/api/kb/v2/priority/missing-laag1?limit=50`;
      } else if (activeTab === 'inbox') {
        if (reasonFilter) qs.append('reason', reasonFilter);
        url = `${API}/api/kb/v2/inbox?${qs}`;
      } else {
        url = `${API}/api/kb/v2/lade/${activeTab}?${qs}`;
      }
      const r = await fetch(url).then(x => x.json());
      setItems(r.kaarten || []);
      if (priorityMode) {
        setTotal(r.total_missing_laag1 || 0);
        setPriorityMeta({ total: r.total_missing_laag1, shown: r.kaarten?.length || 0 });
      } else {
        setTotal(r.total || 0);
        setPriorityMeta(null);
      }
      if (activeTab === 'inbox' && !priorityMode) setReasons(r.redenen || {});
    } catch {
      setItems([]); setTotal(0);
    }
    setLoading(false);
  }, [activeTab, page, search, reasonFilter, priorityMode]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadItems(); }, [loadItems]);

  // Reset page on tab change
  useEffect(() => { setPage(0); setReasonFilter(''); setPriorityMode(false); }, [activeTab]);

  const openCard = (card) => {
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
      const mergedTags = [...new Set([...(selectedCard.tags || []), ...(p.extra_tags || [])])];
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
      const body = {
        card_id: selectedCard.id,
        lade,
        updates: editMode ? {
          lagen: editForm?.lagen,
          ws5:   editForm?.ws5,
          tags:  editForm?.tags,
        } : null,
        user_id: 'user-001',
      };
      const r = await fetch(`${API}/api/kb/v2/classify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      }).then(x => x.json());
      if (r.success) {
        setSelectedCard(null);
        setEditMode(false);
        await loadStats();
        await loadItems();
      } else {
        alert(r.message || 'Classify mislukt');
      }
    } catch (e) { alert('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  const saveEdit = async () => {
    if (!selectedCard || !editForm) return;
    // v6_kbv2_edit_inbox_001 — inbox-kaarten kunnen nu ook bewerkt worden
    setSavingClassify(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: selectedCard.id,
          lade: activeTab,
          updates: { lagen: editForm.lagen, ws5: editForm.ws5, tags: editForm.tags, begrip: editForm.begrip },
          user_id: 'user-001',
        }),
      }).then(x => x.json());
      if (r.success) {
        setSelectedCard(r.kaart);
        setEditMode(false);
        await loadItems();
      } else { alert(r.message || 'Opslaan mislukt'); }
    } catch (e) { alert('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  // v6_kbv2_inline_new_001 — lege kaart opslaan vanuit rechter paneel
  // Niet-compleet (geen laag1 etc) blijft automatisch in inbox als "onbeantwoord".
  const saveNew = async () => {
    if (!editForm) return;
    if (!(editForm.begrip || '').trim()) { alert('Vul een begrip in'); return; }
    setSavingClassify(true);
    try {
      // Stap 1: kaart in inbox aanmaken
      const r = await fetch(`${API}/api/kb/v2/inbox/add`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ begrip: editForm.begrip.trim(), source: 'manual', user_id: 'user-001' }),
      }).then(x => x.json());
      if (!r || !r.kaart) { alert('Aanmaken mislukt: ' + JSON.stringify(r)); setSavingClassify(false); return; }
      let kaart = r.kaart;
      // Stap 2: lagen / ws5 / tags bewerken als ingevuld
      const hasContent =
        Object.values(editForm.lagen || {}).some(v => (v || '').trim()) ||
        Object.values(editForm.ws5 || {}).some(v => (v || '').trim()) ||
        (editForm.tags || []).length > 0;
      if (hasContent) {
        const ed = await fetch(`${API}/api/kb/v2/edit`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            card_id: kaart.id, lade: 'inbox',
            updates: { lagen: editForm.lagen, ws5: editForm.ws5, tags: editForm.tags },
            user_id: 'user-001',
          }),
        }).then(x => x.json());
        if (ed.success && ed.kaart) kaart = ed.kaart;
      }
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
    } catch (e) { alert('Fout: ' + e.message); }
    setSavingClassify(false);
  };

  const cancelNew = () => {
    setCreatingNew(false);
    setEditForm(null);
    setEditMode(false);
    setHerzienV1(null);
    setDupCheck({ checking: false, exists: false, info: null });
  };

  // v6_kbv2_delete_001 — permanent verwijderen via /api/kb/v2/delete
  const doDelete = async () => {
    if (!confirmDelete) return;
    try {
      const r = await fetch(`${API}/api/kb/v2/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: confirmDelete.id,
          lade: activeTab,
          user_id: 'user-001',
          reason: deleteReason,
        }),
      });
      const j = await r.json();
      if (j.success) {
        toast.success(`Kaart "${j.begrip}" verwijderd`);
        setSelectedCard(null);
        setEditMode(false);
        setEditForm(null);
        await loadItems();
      } else {
        toast.error(j.message || 'Verwijderen mislukt');
      }
    } catch (e) {
      toast.error(`Netwerkfout: ${e.message}`);
    } finally {
      setConfirmDelete(null);
      setDeleteReason('');
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
    <MainLayout onNavigate={onNavigate}>
      <div data-testid="kennisbank-v2-page" className="p-4 md:p-6 space-y-4 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-amber-400" /> Kennisbank
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">4 Lades + Inbox · Piramide-laag 3 (Geheugen) · v2 schema</p>
          </div>
          <div className="flex items-center gap-2">
            <button data-testid="kbv2-audit-btn" onClick={runAudit}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-amber-500/30 text-amber-300 hover:bg-amber-500/10 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5" /> Self-audit
            </button>
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
            {/* v6_kbv2_herzien_001 — Herzien knop trekt 1 oude KB v1 kaart */}
            <button data-testid="kbv2-herzien-btn" onClick={loadHerzienEntry}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-purple-500/40 text-purple-300 hover:bg-purple-500/10 flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Herzien (KB v1)
            </button>
            <button data-testid="kbv2-refresh-btn" onClick={() => { loadStats(); loadItems(); }}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-slate-700 text-slate-300 hover:bg-slate-800 flex items-center gap-1.5">
              <RefreshCw className="w-3.5 h-3.5" /> Verversen
            </button>
            {/* v6_kbv2_text_importer_001 — Bulk import knop */}
            <button
              data-testid="kbv2-import-text-btn"
              onClick={() => setShowImporter(true)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium border border-sky-500/40 text-sky-300 hover:bg-sky-500/10 flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5" /> Importeer txt
            </button>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex flex-wrap gap-1.5">
          <TabButton id="inbox" active={activeTab === 'inbox'} onClick={setActiveTab}
            count={stats?.inbox_count || 0} icon={<Inbox className="w-3.5 h-3.5" />}
            label="Inbox" color="#ef4444" />
          {LADES.map(l => (
            <TabButton key={l.id} id={l.id} active={activeTab === l.id} onClick={setActiveTab}
              count={stats?.lades?.[l.id]?.count || 0} iconEmoji={l.icon}
              label={l.naam} color={l.color} />
          ))}
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
          {activeTab === 'inbox' && (
            <div className="flex items-center gap-1 flex-wrap">
              <button data-testid="kbv2-reason-all" onClick={() => { setReasonFilter(''); setPriorityMode(false); setPage(0); }}
                className={`px-2 py-1 rounded text-[10px] font-medium border ${
                  reasonFilter === '' && !priorityMode ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' : 'border-slate-700 text-slate-400'
                }`}>alle</button>
              {Object.entries(REASON_LABEL).map(([k, v]) => (
                <button key={k} data-testid={`kbv2-reason-${k}`}
                  onClick={() => { setReasonFilter(k); setPriorityMode(false); setPage(0); }}
                  className={`px-2 py-1 rounded text-[10px] font-medium border ${
                    reasonFilter === k && !priorityMode ? 'border-current' : 'border-slate-700 text-slate-400'
                  }`}
                  style={reasonFilter === k && !priorityMode ? { color: v.color, borderColor: v.color, backgroundColor: v.color + '15' } : {}}>
                  {v.label} {reasons[k] ? `(${reasons[k]})` : ''}
                </button>
              ))}
              <button
                data-testid="kbv2-priority-laag1"
                onClick={() => { setPriorityMode(!priorityMode); setReasonFilter(''); setPage(0); }}
                title="Top 50 kaarten zonder laag1, gesorteerd op belangrijkheid (verbanden + tags + topic)"
                className={`px-2 py-1 rounded text-[10px] font-medium border ml-1 ${
                  priorityMode ? 'bg-purple-500/20 border-purple-500/40 text-purple-300' : 'border-purple-700/40 text-purple-400 hover:bg-purple-500/10'
                }`}>
                ⭐ Top 50 prio (laag1)
              </button>
            </div>
          )}
        </div>

        {/* List + Detail */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.2fr] gap-3">
          {/* List */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl">
            <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between sticky top-0 bg-slate-900/90 z-10">
              <p className="text-[11px] text-slate-400 font-medium">
                {activeTab === 'inbox' ? 'Onbeantwoord' : LADES.find(l => l.id === activeTab)?.naam}
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
            <div className="max-h-[70vh] overflow-y-auto">
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

          {/* Detail / Edit */}
          <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3">
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
                saving={savingClassify} inInbox={activeTab === 'inbox'} currentLade={activeTab}
                onMediaUpdated={loadItems}
                onGenerateLLM={generateWithLLM} llmGenerating={llmGenerating}
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
                  </p>
                )}
                <ul className="space-y-0.5">
                  {(result.preview || result.details || []).slice(0, 50).map((p, i) => (
                    <li key={i} className="text-[10.5px] text-slate-400">
                      • {p.begrip || JSON.stringify(p)}
                      {p.lade && <span className="text-sky-400"> → {p.lade}</span>}
                      {p.emotie && <span className="text-purple-400"> ({p.emotie})</span>}
                      {p.v2_action && <span className="text-amber-400"> [{p.v2_action}]</span>}
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

  // v6_kbv2_unify_001 — bereken 100%-status (laag1 + 5W + tags + media voice/image)
  const hasL1 = !!(card.lagen?.laag1 || '').trim();
  const hasL2 = !!(card.lagen?.laag2 || '').trim();
  const hasL3 = !!(card.lagen?.laag3 || '').trim();
  const hasL4 = !!(card.lagen?.laag4 || '').trim();
  const has5w = Object.values(card.ws5 || {}).some(v => (v || '').trim());
  const hasTags = (card.tags || []).length > 0;
  const hasVoice = !!(card.media?.voice_url);
  const hasImage = (card.media?.image_urls || []).filter(Boolean).length > 0;
  const filledCount = [hasL1, hasL2, hasL3, hasL4, has5w, hasTags, hasVoice, hasImage].filter(Boolean).length;
  const totalFields = 8;
  const pct = Math.round((filledCount / totalFields) * 100);
  const isComplete = pct === 100;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          {editMode ? (
            <input data-testid="kbv2-edit-begrip" value={editForm.begrip}
              onChange={(e) => upd('begrip', e.target.value)}
              className="w-full text-lg font-bold text-white bg-slate-800/60 border border-slate-700 rounded px-2 py-1" />
          ) : (
            <h2 className="text-lg font-bold text-white">{card.begrip || '(leeg)'}</h2>
          )}
          <p className="text-[10px] text-slate-500 mt-0.5">{card.id}</p>
        </div>
        {/* v6_kbv2_unify_001 — Compleetheid-badge */}
        <div data-testid="kbv2-completeness-badge" className={`px-2 py-1 rounded-lg text-[10px] font-semibold border ${
          isComplete
            ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
            : pct >= 50
              ? 'bg-amber-500/15 border-amber-500/40 text-amber-300'
              : 'bg-slate-800/60 border-slate-700 text-slate-400'
        }`}>
          {isComplete ? '✓ 100% gekuurd' : `${pct}% (${filledCount}/${totalFields})`}
        </div>
        {!editMode ? (
          <>
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
          </>
        ) : (
          <button data-testid="kbv2-cancel-edit" onClick={onCancelEdit}
            className="px-2 py-1 text-xs border border-slate-700 rounded text-slate-400 hover:bg-slate-800">
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
      ) : null}
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
 * MediaSection — voice (Whisper STT) + image upload bij een kaart.
 * Voor inbox-kaarten: currentLade = null, backend leidt lade af via index.
 */
function MediaSection({ card, currentLade, onUpdated }) {
  const media = card.media || {};
  const [recording, setRecording] = useState(false);
  const [uploadingVoice, setUploadingVoice] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [err, setErr] = useState('');
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
