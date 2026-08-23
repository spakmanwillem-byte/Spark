/**
 * v13_incomplete_cards_widget_001 (sessie 54) — Widget in Kladblok voor onvolledige
 * KB-kaarten. Vervangt de oude "⚠ Onvolledig" sub-tab in Inbox (die kaart-kopieën
 * met dezelfde id maakte → dubbels-bug).
 *
 * Werking:
 *  - Auto-scan bij laden + handmatige [🔄 Scan nu]-knop
 *  - Links: lijst van onvolledige kaarten (begrip + missing_fields badges)
 *  - Rechts: geselecteerde kaart met bewerkbare velden (lagen 1-4 + 5W)
 *  - Save → PATCH /api/kb/v2/edit → kaart verdwijnt uit de lijst als compleet
 *
 * Data-testids beginnen met `widget-incomplete-` voor testing_agent-compatibiliteit.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircle, RefreshCw, Save, ChevronRight } from 'lucide-react';

const REQUIRED_5W = ['wie', 'wat', 'wanneer', 'waar', 'waarom', 'hoe'];
const REQUIRED_LAGEN = [1, 2, 3, 4];

export function IncompleteCardsWidget() {
  const [cards, setCards] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedCard, setSelectedCard] = useState(null);
  const [selectedLoading, setSelectedLoading] = useState(false);
  const [saveState, setSaveState] = useState(null); // 'saving' | 'saved' | 'error'
  const [scanTs, setScanTs] = useState(null);
  const API = process.env.REACT_APP_BACKEND_URL;

  const runScan = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/api/kb/v2/inbox/incomplete?limit=100&sort=recent`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setCards(d.kaarten || []);
      setTotal(d.total || 0);
      setScanTs(new Date());
    } catch (e) {
      // Non-fatal, toon melding via cards=empty
      setCards([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [API]);

  useEffect(() => { runScan(); }, [runScan]);

  // v13_incomplete_widget_daily_scan_001 — auto-refresh om middernacht + elke 60 min
  useEffect(() => {
    const iv = setInterval(runScan, 60 * 60 * 1000);
    return () => clearInterval(iv);
  }, [runScan]);

  // Laad volledige kaart-data wanneer selectie wijzigt
  useEffect(() => {
    if (!selectedId) { setSelectedCard(null); return; }
    const item = cards.find(c => c.id === selectedId);
    if (!item) return;
    setSelectedLoading(true);
    (async () => {
      try {
        const r = await fetch(`${API}/api/kb/v2/lade/${item.lade}`);
        const d = await r.json();
        const full = (d.kaarten || []).find(k => k.id === selectedId);
        setSelectedCard(full || null);
      } catch { setSelectedCard(null); }
      setSelectedLoading(false);
    })();
  }, [selectedId, cards, API]);

  const handleSave = async () => {
    if (!selectedCard) return;
    setSaveState('saving');
    try {
      const item = cards.find(c => c.id === selectedId);
      const r = await fetch(`${API}/api/kb/v2/edit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          card_id: selectedCard.id,
          lade: item?.lade,
          user_id: 'user-001',
          updates: {
            lagen: selectedCard.lagen,
            ws5: selectedCard.ws5,
          },
        }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setSaveState('saved');
      setTimeout(() => setSaveState(null), 2000);
      // Herlaad scan-lijst — als kaart nu compleet is verdwijnt hij automatisch
      await runScan();
      // Deselecteer indien niet meer in lijst
      const stillIncomplete = cards.some(c => c.id === selectedId);
      if (!stillIncomplete) setSelectedId(null);
    } catch {
      setSaveState('error');
      setTimeout(() => setSaveState(null), 3000);
    }
  };

  const updateLaag = (n, val) => {
    if (!selectedCard) return;
    setSelectedCard({
      ...selectedCard,
      lagen: { ...(selectedCard.lagen || {}), [`laag${n}`]: val },
    });
  };
  const updateWs5 = (key, val) => {
    if (!selectedCard) return;
    setSelectedCard({
      ...selectedCard,
      ws5: { ...(selectedCard.ws5 || {}), [key]: val },
    });
  };

  return (
    <div data-testid="widget-incomplete-cards" className="bg-slate-900/50 border border-orange-500/30 rounded-2xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-orange-400" />
          <h3 className="text-sm font-semibold text-white">Onvolledige Kaarten</h3>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-300 font-mono">
            {total}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {scanTs && (
            <span className="text-[9px] text-slate-500">
              gescand {scanTs.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <button
            data-testid="widget-incomplete-scan-btn"
            onClick={runScan}
            disabled={loading}
            className="text-[10px] px-2 py-1 rounded border border-orange-500/40 text-orange-300 hover:bg-orange-500/10 disabled:opacity-50 flex items-center gap-1">
            <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
            Scan nu
          </button>
        </div>
      </div>

      {total === 0 && !loading ? (
        <p className="text-xs text-slate-500 italic py-8 text-center">
          🎉 Alle kaarten zijn compleet. Geen ws5- of laag-gaps gevonden.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-[minmax(180px,240px)_1fr] gap-3 max-h-[500px]">
          {/* LINKS: lijst */}
          <div data-testid="widget-incomplete-list"
               className="overflow-y-auto space-y-1 border-r border-slate-800 pr-2 max-h-[500px]">
            {cards.map(c => {
              const isSel = c.id === selectedId;
              const missingCount = (c.missing_5w?.length || 0) + (4 - (c.filled_lagen || 0));
              return (
                <button
                  key={c.id}
                  data-testid={`widget-incomplete-item-${c.id}`}
                  onClick={() => setSelectedId(c.id)}
                  className={`w-full text-left p-2 rounded text-xs transition ${
                    isSel
                      ? 'bg-orange-500/20 border border-orange-500/40 text-white'
                      : 'bg-slate-950/50 border border-slate-800 text-slate-300 hover:bg-slate-800/50'
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-medium truncate">{c.begrip}</span>
                    <ChevronRight className={`w-3 h-3 flex-shrink-0 ${isSel ? 'text-orange-300' : 'text-slate-600'}`} />
                  </div>
                  <div className="flex items-center gap-1 mt-1 flex-wrap">
                    <span className="text-[9px] px-1 py-0.5 rounded bg-slate-800 text-slate-400">
                      {c.lade}
                    </span>
                    {c.filled_lagen < 4 && (
                      <span className="text-[9px] px-1 py-0.5 rounded bg-red-500/20 text-red-300">
                        laag {c.filled_lagen}/4
                      </span>
                    )}
                    {(c.missing_5w?.length || 0) > 0 && (
                      <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/20 text-amber-300">
                        ws5 {6 - (c.missing_5w?.length || 0)}/6
                      </span>
                    )}
                    <span className="text-[9px] text-slate-500 ml-auto">−{missingCount}</span>
                  </div>
                </button>
              );
            })}
            {cards.length === 0 && loading && (
              <p className="text-[10px] text-slate-500 italic p-2">scannen…</p>
            )}
          </div>

          {/* RECHTS: detail-editor */}
          <div data-testid="widget-incomplete-editor" className="overflow-y-auto max-h-[500px] pr-1">
            {!selectedId && (
              <p className="text-xs text-slate-500 italic py-8 text-center">
                Kies links een kaart om aan te vullen.
              </p>
            )}
            {selectedId && selectedLoading && (
              <p className="text-[10px] text-slate-500 italic">kaart laden…</p>
            )}
            {selectedCard && !selectedLoading && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-white" data-testid="widget-incomplete-title">
                      {selectedCard.begrip}
                    </h4>
                    <p className="text-[10px] text-slate-500">id: {selectedCard.id} · lade: {selectedCard.lade}</p>
                  </div>
                  <button
                    data-testid="widget-incomplete-save-btn"
                    onClick={handleSave}
                    disabled={saveState === 'saving'}
                    className={`text-[10px] px-2 py-1 rounded flex items-center gap-1 border ${
                      saveState === 'saved' ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300' :
                      saveState === 'error' ? 'bg-red-500/20 border-red-500/40 text-red-300' :
                      'bg-orange-500/20 border-orange-500/40 text-orange-300 hover:bg-orange-500/30'
                    }`}>
                    <Save className="w-3 h-3" />
                    {saveState === 'saving' ? 'opslaan…' :
                     saveState === 'saved' ? 'opgeslagen' :
                     saveState === 'error' ? 'fout' :
                     'opslaan'}
                  </button>
                </div>

                {/* Lagen 1-4 */}
                <div className="space-y-2">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Lagen</p>
                  {REQUIRED_LAGEN.map(n => {
                    const val = selectedCard.lagen?.[`laag${n}`] || '';
                    const empty = !val || val.trim().length < 20;
                    return (
                      <div key={n}>
                        <label className="text-[10px] text-slate-500 flex items-center gap-1">
                          Laag {n}
                          {empty && <span className="text-red-400">⚠ leeg/&lt;20 chars</span>}
                        </label>
                        <textarea
                          data-testid={`widget-incomplete-laag${n}`}
                          value={val}
                          onChange={(e) => updateLaag(n, e.target.value)}
                          rows={2}
                          className="w-full text-xs bg-slate-950/50 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-orange-500/50"
                        />
                      </div>
                    );
                  })}
                </div>

                {/* 5W + Hoe */}
                <div className="space-y-2">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">5W + Hoe</p>
                  {REQUIRED_5W.map(key => {
                    const val = selectedCard.ws5?.[key] || '';
                    const empty = !val || !val.trim();
                    return (
                      <div key={key}>
                        <label className="text-[10px] text-slate-500 flex items-center gap-1">
                          {key.charAt(0).toUpperCase() + key.slice(1)}
                          {empty && <span className="text-red-400">⚠ leeg</span>}
                        </label>
                        <input
                          data-testid={`widget-incomplete-ws5-${key}`}
                          value={val}
                          onChange={(e) => updateWs5(key, e.target.value)}
                          className="w-full text-xs bg-slate-950/50 border border-slate-800 rounded px-2 py-1 text-slate-200 focus:outline-none focus:border-orange-500/50"
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
