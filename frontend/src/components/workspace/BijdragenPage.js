import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { HandHeart, SkipForward, Send, Award, Clock, CheckCircle, XCircle, RefreshCw, AlertCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;
const FIELDS = [
  { key: 'wat', label: 'Wat', placeholder: 'Wat is dit kort gezegd?' },
  { key: 'wanneer', label: 'Wanneer', placeholder: 'Wanneer komt dit voor of speelt het?' },
  { key: 'waar', label: 'Waar', placeholder: 'Waar hoort dit bij (locatie of plek)?' },
  { key: 'wie', label: 'Wie', placeholder: 'Wie is er bij betrokken?' },
  { key: 'waarom', label: 'Waarom', placeholder: 'Waarom is dit belangrijk of relevant?' },
  { key: 'hoe', label: 'Hoe', placeholder: 'Hoe werkt dit of hoe ervaar je het?' },
];

function BijdragenPage({ embedded = false }) {
  const { user } = useAuth();
  const userId = user?.id;
  const allowed = [1, 2, 3, 4, 5].includes(user?.gradatie);
  const isAdmin = [1, 2].includes(user?.gradatie);

  const [view, setView] = useState('contribute'); // 'contribute' | 'review'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [card, setCard] = useState(null);
  const [ws5, setWs5] = useState({ wat: '', wanneer: '', waar: '', wie: '', waarom: '', hoe: '' });
  const [stats, setStats] = useState(null);
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [pending, setPending] = useState([]);

  const loadCard = useCallback(async () => {
    if (!userId || !allowed) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/contributions/next-card?user_id=${userId}`);
      const data = await res.json();
      if (data.success && data.card) {
        setCard(data.card);
        setWs5({ ...{ wat: '', wanneer: '', waar: '', wie: '', waarom: '', hoe: '' }, ...(data.card.ws5 || {}) });
      } else {
        setCard(null);
        setError(data.message || 'Geen kaarten beschikbaar.');
      }
    } catch (e) {
      setError(`Fout: ${e.message}`);
    }
    setLoading(false);
  }, [userId, allowed]);

  const loadStats = useCallback(async () => {
    if (!userId || !allowed) return;
    try {
      const res = await fetch(`${API}/api/contributions/my-stats?user_id=${userId}`);
      setStats(await res.json());
    } catch { /* silent */ }
  }, [userId, allowed]);

  useEffect(() => {
    if (view === 'contribute') {
      loadCard();
    }
    loadStats();
  }, [view, loadCard, loadStats]);

  // Admin: load pending list
  const loadPending = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const res = await fetch(`${API}/api/contributions/pending?admin_id=${userId}`);
      const data = await res.json();
      setPending(data.pending || []);
    } catch { /* silent */ }
  }, [isAdmin, userId]);

  useEffect(() => {
    if (view === 'review' && isAdmin) loadPending();
  }, [view, isAdmin, loadPending]);

  const onApprove = async (cardId) => {
    try {
      const res = await fetch(`${API}/api/contributions/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_id: userId, card_id: cardId }),
      });
      const data = await res.json();
      if (data.success) {
        const xp = data.xp_granted?.xp_granted;
        setFeedback({ type: 'success', text: `Goedgekeurd! ${data.eligible_for_xp ? `+${xp} XP voor ${data.contributor_user_id}` : 'Geen XP (onder 75%)'}` });
        loadPending();
        setTimeout(() => setFeedback(null), 4000);
      }
    } catch (e) {
      setFeedback({ type: 'error', text: e.message });
    }
  };

  const onReject = async (cardId) => {
    if (!window.prompt('Reden voor afwijzing? (Enter = leeg laten)') && false) return;
    try {
      const res = await fetch(`${API}/api/contributions/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ admin_id: userId, card_id: cardId, reason: '' }),
      });
      const data = await res.json();
      if (data.success) {
        setFeedback({ type: 'info', text: 'Afgewezen. Kaart blijft in pool zonder XP.' });
        loadPending();
        setTimeout(() => setFeedback(null), 3000);
      }
    } catch (e) {
      setFeedback({ type: 'error', text: e.message });
    }
  };

  // Auto-save tussentijds wanneer veld blur
  const saveField = async (field) => {
    if (!card || saving) return;
    setSaving(true);
    try {
      await fetch(`${API}/api/contributions/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, card_id: card.id, ws5: { [field]: ws5[field] } }),
      });
    } catch { /* silent */ }
    setSaving(false);
  };

  const filledCount = FIELDS.filter(f => (ws5[f.key] || '').trim()).length;
  const percentage = Math.round((filledCount / FIELDS.length) * 100);

  const onSubmit = async () => {
    if (!card || filledCount < 1) return;
    setSaving(true);
    setFeedback(null);
    try {
      const res = await fetch(`${API}/api/contributions/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, card_id: card.id, ws5 }),
      });
      const data = await res.json();
      if (data.success) {
        const xpMsg = data.eligible_for_xp ? ' XP wordt uitbetaald na goedkeuring.' : ' Onder 75% — geen XP, wel ingediend.';
        setFeedback({ type: 'success', text: `Ingediend! ${data.percentage}% gevuld.${xpMsg}` });
        await loadStats();
        setTimeout(() => { setFeedback(null); loadCard(); }, 2500);
      } else {
        setFeedback({ type: 'error', text: 'Indienen mislukt.' });
      }
    } catch (e) {
      setFeedback({ type: 'error', text: `Fout: ${e.message}` });
    }
    setSaving(false);
  };

  const onSkip = async () => {
    if (!card) return;
    setSaving(true);
    setFeedback(null);
    try {
      await fetch(`${API}/api/contributions/skip`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId }),
      });
      setFeedback({ type: 'info', text: 'Overgeslagen — kaart terug naar pool. Volgende kaart laden...' });
      setTimeout(() => { setFeedback(null); loadCard(); }, 1500);
    } catch (e) {
      setFeedback({ type: 'error', text: `Fout: ${e.message}` });
    }
    setSaving(false);
  };

  if (!allowed) {
    const inner = (
      <div className="flex flex-col items-center justify-center h-full p-8 text-center">
        <AlertCircle className="w-12 h-12 text-amber-400 mb-4" />
        <h2 className="text-xl text-white mb-2">Bijdragen niet beschikbaar</h2>
        <p className="text-slate-400 text-sm">Dit portaal is alleen voor gebruikers t/m gradatie 5.</p>
      </div>
    );
    return embedded ? inner : <MainLayout>{inner}</MainLayout>;
  }

  const content = (
    <>
      <div data-testid="bijdragen-page" className="flex flex-col h-full overflow-hidden">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #dc2626)' }}>
              <HandHeart className="w-5 h-5 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-lg font-bold text-white">Bijdragen aan Kennisbank</h1>
              <p className="text-xs text-slate-400">Vul de 5W+H velden in voor onbeantwoorde kaarten. ≥75% = XP na goedkeuring.</p>
            </div>
            <button data-testid="reload-card-btn" onClick={loadCard} className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800 text-xs flex items-center gap-1.5" title="Andere kaart">
              <RefreshCw className="w-3.5 h-3.5" />
              Vernieuwen
            </button>
          </div>
          {isAdmin && (
            <div className="mt-3 flex gap-2">
              <button data-testid="view-contribute-tab" onClick={() => setView('contribute')} className={`px-3 py-1 rounded-md text-xs font-medium ${view === 'contribute' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'bg-slate-800/50 text-slate-400 border border-slate-700'}`}>Zelf bijdragen</button>
              <button data-testid="view-review-tab" onClick={() => setView('review')} className={`px-3 py-1 rounded-md text-xs font-medium ${view === 'review' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40' : 'bg-slate-800/50 text-slate-400 border border-slate-700'}`}>
                Goedkeuren ({pending.length || '—'})
              </button>
            </div>
          )}
          {stats && (
            <div className="mt-3 flex flex-wrap gap-3 text-xs">
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/60 rounded">
                <Send className="w-3.5 h-3.5 text-cyan-400" />
                <span className="text-slate-400">Ingediend:</span>
                <span className="text-white font-medium">{stats.submitted}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/60 rounded">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span className="text-slate-400">Wachtend:</span>
                <span className="text-white font-medium">{stats.pending}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/60 rounded">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-slate-400">Goedgekeurd:</span>
                <span className="text-white font-medium">{stats.approved}</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-slate-800/60 rounded">
                <XCircle className="w-3.5 h-3.5 text-red-400" />
                <span className="text-slate-400">Afgewezen:</span>
                <span className="text-white font-medium">{stats.rejected}</span>
              </div>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {view === 'review' && isAdmin && (
            <div data-testid="admin-review-section" className="max-w-3xl mx-auto">
              <h2 className="text-lg text-white mb-3">Wacht op goedkeuring ({pending.length})</h2>
              {pending.length === 0 ? (
                <p className="text-slate-400 text-sm">Geen kaarten in de review-queue.</p>
              ) : (
                <div className="space-y-3">
                  {pending.map(p => (
                    <div key={p.id} data-testid={`pending-${p.id}`} className="bg-slate-900/60 border border-slate-800 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h3 className="text-base text-white font-semibold">{p.begrip}</h3>
                          <p className="text-xs text-slate-500 mt-0.5">
                            Door <span className="text-slate-300">{p.contributor_user_id}</span> — <span className={p.percentage >= 75 ? 'text-emerald-400' : 'text-amber-300'}>{p.percentage}% gevuld</span>
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <button data-testid={`approve-${p.id}`} onClick={() => onApprove(p.id)} className="px-3 py-1.5 rounded-md text-xs bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 flex items-center gap-1">
                            <CheckCircle className="w-3.5 h-3.5" /> Keur goed
                          </button>
                          <button data-testid={`reject-${p.id}`} onClick={() => onReject(p.id)} className="px-3 py-1.5 rounded-md text-xs bg-red-500/15 border border-red-500/30 text-red-300 hover:bg-red-500/25 flex items-center gap-1">
                            <XCircle className="w-3.5 h-3.5" /> Wijs af
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {FIELDS.map(f => (
                          <div key={f.key} className="p-2 bg-slate-800/40 rounded">
                            <p className="text-[10px] text-slate-500 uppercase">{f.label}</p>
                            <p className="text-xs text-slate-300 mt-0.5">{(p.ws5 || {})[f.key] || <span className="text-slate-600 italic">leeg</span>}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {feedback && (
                <div data-testid="admin-feedback" className={`mt-4 p-3 rounded-lg text-sm border ${
                  feedback.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                  : feedback.type === 'info' ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-200'
                  : 'bg-red-500/10 border-red-500/30 text-red-200'
                }`}>{feedback.text}</div>
              )}
            </div>
          )}

          {view === 'contribute' && loading && <p className="text-slate-400 text-sm">Kaart laden...</p>}
          {view === 'contribute' && error && !loading && (
            <div data-testid="bijdragen-error" className="max-w-2xl mx-auto p-4 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-200 text-sm">
              {error}
            </div>
          )}

          {view === 'contribute' && card && !loading && (
            <div className="max-w-2xl mx-auto">
              <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 mb-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Begrip</p>
                    <h2 data-testid="bijdragen-begrip" className="text-2xl text-white font-semibold">{card.begrip}</h2>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Voortgang</p>
                    <p className={`text-2xl font-bold ${percentage >= 75 ? 'text-emerald-400' : 'text-amber-300'}`}>{percentage}%</p>
                  </div>
                </div>
                {card.snap_context && (
                  <p className="text-xs text-slate-500 mb-1 italic">{card.snap_context.slice(0, 200)}</p>
                )}
              </div>

              <div className="space-y-3">
                {FIELDS.map(f => (
                  <div key={f.key} data-testid={`field-${f.key}`} className="bg-slate-900/40 border border-slate-800 rounded-lg p-3">
                    <label className="block text-xs font-medium text-slate-300 uppercase tracking-wider mb-1.5">{f.label}</label>
                    <textarea
                      data-testid={`input-${f.key}`}
                      value={ws5[f.key]}
                      onChange={e => setWs5({ ...ws5, [f.key]: e.target.value })}
                      onBlur={() => saveField(f.key)}
                      placeholder={f.placeholder}
                      className="w-full bg-slate-800/60 border border-slate-700 rounded-md px-3 py-2 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-amber-500/50 resize-none"
                      rows={2}
                    />
                  </div>
                ))}
              </div>

              <div className="mt-5 flex gap-3 sticky bottom-0 bg-slate-950/90 backdrop-blur-sm py-3">
                <button
                  data-testid="bijdragen-submit-btn"
                  onClick={onSubmit}
                  disabled={saving || filledCount === 0}
                  className="flex-1 py-3 rounded-xl font-medium text-sm text-white transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ background: filledCount === 0 ? '#374151' : 'linear-gradient(135deg, #10b981, #059669)' }}
                >
                  <Send className="w-4 h-4" />
                  Voltooien ({percentage}%){percentage >= 75 ? ' — XP!' : ''}
                </button>
                <button
                  data-testid="bijdragen-skip-btn"
                  onClick={onSkip}
                  disabled={saving}
                  className="px-5 py-3 rounded-xl text-sm text-slate-300 border border-slate-700 hover:bg-slate-800 transition-colors flex items-center gap-2 disabled:opacity-50"
                  title="Te moeilijk? Terug naar pool"
                >
                  <SkipForward className="w-4 h-4" />
                  Overslaan
                </button>
              </div>

              {feedback && (
                <div data-testid="bijdragen-feedback" className={`mt-3 p-3 rounded-lg text-sm border ${
                  feedback.type === 'success'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
                    : feedback.type === 'info'
                      ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-200'
                      : 'bg-red-500/10 border-red-500/30 text-red-200'
                }`}>
                  <div className="flex items-center gap-2">
                    {feedback.type === 'success' && <Award className="w-4 h-4" />}
                    {feedback.text}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );

  return embedded ? content : <MainLayout>{content}</MainLayout>;
}

export default BijdragenPage;
export { BijdragenPage };
