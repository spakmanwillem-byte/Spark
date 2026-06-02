/**
 * v6_help_001 — Help-bark component.
 * Toont gradatie-afhankelijke help met zoekveld + topic-lijst.
 * Bij klik op topic: navigeer + glow op tab via 'spark:nav-glow' event.
 * Bij admin: extra knop naar Admin-help-modus.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { HelpCircle, Search, ShieldCheck, ChevronRight, X, ArrowLeft } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function HelpBark({ open, onClose, userId }) {
  const [helpData, setHelpData] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);  // voor diepe uitleg
  const [showAdmin, setShowAdmin] = useState(false);
  const [helpImg, setHelpImg] = useState(null);

  // Load help-content on open
  useEffect(() => {
    if (!open || !userId) return;
    fetch(`${API}/api/help/for-viewer?user_id=${userId}`)
      .then(r => r.json())
      .then(setHelpData)
      .catch(() => setHelpData(null));
    // Load Help bark-image (begrip = "Help" of "Hulp")
    fetch(`${API}/api/admin/bark-image?begrip=Help`)
      .then(r => r.json())
      .then(d => {
        if (d.image_url) setHelpImg(d.image_url);
        else fetch(`${API}/api/admin/bark-image?begrip=Hulp`).then(r => r.json()).then(d2 => setHelpImg(d2.image_url || null));
      })
      .catch(() => {});
  }, [open, userId]);

  // Reset state on close
  useEffect(() => {
    if (!open) {
      setSearchQuery('');
      setSearchResult(null);
      setActiveTopic(null);
      setShowAdmin(false);
    }
  }, [open]);

  const doSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      setSearchResult(null);
      return;
    }
    try {
      const res = await fetch(`${API}/api/help/find`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, query: searchQuery }),
      }).then(r => r.json());
      setSearchResult(res);
    } catch { setSearchResult({ success: false, error: 'fout' }); }
  }, [searchQuery, userId]);

  const navigateToTopic = (topic) => {
    if (!topic) return;
    if (topic.nav_testid && topic.nav_path) {
      window.dispatchEvent(new CustomEvent('spark:nav-glow', {
        detail: { targetId: topic.nav_testid, navigateTo: topic.nav_path },
      }));
      onClose();
    }
  };

  if (!open) return null;

  // Diepe uitleg mode
  if (activeTopic) {
    return (
      <div data-testid="help-bark-modal" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
        <div className="relative max-w-lg w-full bg-slate-900 border border-slate-700 rounded-2xl ring-2 ring-amber-500/40 shadow-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
          <button onClick={onClose} className="absolute right-3 top-3 z-10 text-slate-400 hover:text-white p-1 rounded-full bg-slate-800/80">
            <X className="w-4 h-4" />
          </button>
          <div className="p-5 space-y-3">
            <button onClick={() => setActiveTopic(null)} data-testid="help-bark-back" className="flex items-center gap-1 text-[11px] text-amber-300 hover:text-amber-200 mb-2">
              <ArrowLeft className="w-3.5 h-3.5" /> terug naar overzicht
            </button>
            <h3 className="text-base font-semibold text-amber-200">{activeTopic.label}</h3>
            <p className="text-xs text-slate-300 leading-relaxed">{activeTopic.korte_uitleg}</p>
            {activeTopic.deep_uitleg && (
              <div className="mt-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                <p className="text-[11px] text-amber-300 uppercase tracking-wider mb-1">verdieping</p>
                <p className="text-xs text-slate-200 leading-relaxed">{activeTopic.deep_uitleg}</p>
              </div>
            )}
            {activeTopic.nav_testid && (
              <button
                data-testid="help-bark-deep-nav"
                onClick={() => navigateToTopic(activeTopic)}
                className="w-full mt-3 px-4 py-2 rounded-lg text-xs font-medium bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 border border-amber-500/40 flex items-center justify-center gap-2"
              >
                Breng me erheen <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  const topics = showAdmin ? (helpData?.admin_topics || []) : (helpData?.topics || []);
  const intro = showAdmin ? helpData?.admin_intro : helpData?.intro;
  const canShowAdmin = helpData?.is_admin && (helpData?.admin_topics || []).length > 0;

  return (
    <div data-testid="help-bark-modal" className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
      <div className={`relative max-w-2xl w-full max-h-[88vh] bg-slate-900 border border-slate-700 rounded-2xl ring-2 ${showAdmin ? 'ring-purple-500/40' : 'ring-amber-500/40'} shadow-2xl overflow-hidden flex flex-col`} onClick={e => e.stopPropagation()}>
        <button data-testid="help-bark-close" onClick={onClose} className="absolute right-3 top-3 z-10 text-slate-400 hover:text-white p-1 rounded-full bg-slate-800/80">
          <X className="w-4 h-4" />
        </button>

        {/* Header met afbeelding */}
        <div className="flex-shrink-0 bg-gradient-to-b from-slate-800 to-slate-900 px-6 py-5 border-b border-slate-800">
          <div className="flex items-center gap-4">
            {helpImg ? (
              <img src={`${API}${helpImg}`} alt="Help" className="w-16 h-16 rounded-lg object-cover ring-2 ring-amber-500/40" />
            ) : (
              <div className="w-16 h-16 rounded-lg bg-amber-500/10 ring-2 ring-amber-500/30 flex items-center justify-center">
                <HelpCircle className="w-8 h-8 text-amber-300" />
              </div>
            )}
            <div className="flex-1">
              <h2 className={`text-lg font-bold ${showAdmin ? 'text-purple-200' : 'text-amber-200'}`}>
                {showAdmin ? 'Help (Admin)' : 'Help'}
              </h2>
              <p className="text-[11px] text-slate-400">
                {helpData ? `Gradatie ${helpData.gradatie}` : 'Laden...'} {helpData?.is_admin && !showAdmin ? '• admin' : ''}
              </p>
            </div>
            {canShowAdmin && (
              <button
                data-testid="help-bark-toggle-admin"
                onClick={() => setShowAdmin(s => !s)}
                className={`px-3 py-1.5 rounded-lg text-[11px] font-medium flex items-center gap-1.5 ${showAdmin ? 'bg-amber-500/20 text-amber-200 border border-amber-500/40' : 'bg-purple-500/20 text-purple-200 border border-purple-500/40 hover:bg-purple-500/30'}`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                {showAdmin ? 'Naar normale help' : 'Naar admin-help'}
              </button>
            )}
          </div>
        </div>

        {/* Zoekveld */}
        <div className="flex-shrink-0 px-6 py-3 border-b border-slate-800 bg-slate-950/40">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
            <input
              data-testid="help-bark-search"
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && doSearch()}
              placeholder="Waar wil je heen? bv. 'winkel' of 'trade'"
              className="w-full pl-9 pr-20 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-amber-500/50 outline-none"
            />
            <button
              data-testid="help-bark-search-btn"
              onClick={doSearch}
              disabled={!searchQuery.trim()}
              className="absolute right-1.5 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded text-[10px] font-medium bg-amber-500/20 text-amber-200 hover:bg-amber-500/30 disabled:opacity-40"
            >
              Vind
            </button>
          </div>
          {searchResult && (
            <div className="mt-2">
              {searchResult.success ? (
                <button
                  data-testid="help-bark-search-result"
                  onClick={() => navigateToTopic(searchResult.topic)}
                  className="w-full flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/15"
                >
                  <div className="text-left">
                    <p className="text-xs font-semibold text-emerald-200">→ {searchResult.topic.label}</p>
                    <p className="text-[10px] text-emerald-300/70">{searchResult.topic.korte_uitleg?.slice(0, 70)}...</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-emerald-300" />
                </button>
              ) : (
                <p className="text-[11px] text-amber-300">
                  Geen match. Probeer een korter trefwoord of kijk in de lijst hieronder.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Topic-lijst scrollbaar */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-2">
          {intro && (
            <p className="text-[11px] text-slate-400 italic mb-3">{intro}</p>
          )}
          {topics.length === 0 && (
            <p className="text-[11px] text-slate-500">Geen topics beschikbaar.</p>
          )}
          {topics.map(t => (
            <div
              key={t.id}
              data-testid={`help-topic-${t.id}`}
              className="bg-slate-950/40 border border-slate-800 rounded-lg p-3 hover:border-amber-500/30 transition-colors"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h4 className={`text-sm font-semibold ${showAdmin ? 'text-purple-200' : 'text-amber-200'}`}>{t.label}</h4>
                  <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{t.korte_uitleg}</p>
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {t.deep_uitleg && (
                    <button
                      data-testid={`help-topic-deep-${t.id}`}
                      onClick={() => setActiveTopic(t)}
                      className="px-2 py-1 rounded text-[10px] bg-slate-800 text-slate-300 hover:bg-slate-700"
                    >
                      verdieping
                    </button>
                  )}
                  {t.nav_testid && (
                    <button
                      data-testid={`help-topic-nav-${t.id}`}
                      onClick={() => navigateToTopic(t)}
                      className={`px-2 py-1 rounded text-[10px] ${showAdmin ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30' : 'bg-amber-500/20 text-amber-200 hover:bg-amber-500/30'}`}
                    >
                      naar →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default HelpBark;
