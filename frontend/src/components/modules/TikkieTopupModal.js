// v5_tikkie_topup_001 — Wallet opwaarderen via Tikkie (user-facing modal)
import React, { useState, useEffect } from 'react';
import { X, Loader2, Check, AlertCircle, Euro, QrCode, Send } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function TikkieTopupModal({ open, onClose, user }) {
  const [amount, setAmount] = useState('');
  const [naam, setNaam] = useState(user?.naam || user?.volledige_naam || '');
  const [step, setStep] = useState('form'); // form → confirm → sent
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [tikkieUrl, setTikkieUrl] = useState('');
  const [myTopups, setMyTopups] = useState([]);

  useEffect(() => {
    if (!open) return;
    setNaam(user?.naam || user?.volledige_naam || '');
    setAmount('');
    setStep('form');
    setError(null);
    setResult(null);
    fetch(`${API}/api/wallet/tikkie/config`).then(r => r.json()).then(d => setTikkieUrl(d.tikkie_url || '')).catch(() => {});
    if (user?.id) {
      fetch(`${API}/api/wallet/tikkie/mine?user_id=${user.id}`).then(r => r.json()).then(d => setMyTopups(d.topups || [])).catch(() => {});
    }
  }, [open, user?.id, user?.naam, user?.volledige_naam]);

  if (!open) return null;

  const suggestions = [10, 15, 20];

  const goConfirm = () => {
    setError(null);
    const n = parseFloat(amount);
    if (!n || n <= 0) { setError('Vul een geldig bedrag in.'); return; }
    if (!naam.trim()) { setError('Vul je naam in zodat we weten van wie de Tikkie komt.'); return; }
    setStep('confirm');
  };

  const submit = async () => {
    setSending(true);
    setError(null);
    try {
      const res = await fetch(`${API}/api/wallet/tikkie/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.id,
          naam_invoer: naam.trim(),
          amount_eur: parseFloat(amount),
        }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.detail || 'Mislukt');
      setResult(data.topup);
      setStep('sent');
      if (user?.id) {
        fetch(`${API}/api/wallet/tikkie/mine?user_id=${user.id}`).then(r => r.json()).then(d => setMyTopups(d.topups || [])).catch(() => {});
      }
    } catch (e) {
      setError(e.message || 'Verzenden mislukt.');
    } finally {
      setSending(false);
    }
  };

  return (
    <div data-testid="tikkie-modal" className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="w-full max-w-md bg-slate-900 border border-amber-500/30 rounded-2xl overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between" style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.15), rgba(34, 197, 94, 0.10))' }}>
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-violet-500/15 border border-violet-500/30 flex items-center justify-center">
              <Euro className="w-4 h-4 text-violet-300" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Wallet opwaarderen — Tikkie</h3>
              <p className="text-[10px] text-slate-400">Scan, betaal, druk Verzenden</p>
            </div>
          </div>
          <button onClick={onClose} data-testid="tikkie-close" className="p-1.5 hover:bg-slate-800 rounded-lg">
            <X className="w-4 h-4 text-slate-400" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {step === 'form' && (
            <>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Bedrag (€) — vul zelf het bedrag in dat je via Tikkie betaalt</label>
                <input data-testid="tikkie-amount" type="number" min="1" step="0.50" value={amount}
                  onChange={e => setAmount(e.target.value)}
                  autoFocus
                  className="mt-1 w-full px-3 py-3 bg-slate-800 border border-slate-700 rounded-lg text-base text-white focus:outline-none focus:border-amber-500"
                  placeholder="Bijv. 10, 15, 20, 27.50..." />
                <div className="mt-2 flex gap-2">
                  <span className="text-[10px] text-slate-500 self-center">Snel:</span>
                  {suggestions.map(p => (
                    <button key={p} data-testid={`preset-${p}`} onClick={() => setAmount(String(p))}
                      className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                        parseFloat(amount) === p
                          ? 'bg-amber-500 text-slate-900 ring-2 ring-amber-400'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}>
                      €{p}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 uppercase tracking-wider">Jouw naam (zoals in Tikkie)</label>
                <input data-testid="tikkie-naam" value={naam} onChange={e => setNaam(e.target.value)}
                  placeholder="Voornaam achternaam"
                  className="mt-1 w-full px-3 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                <p className="text-[10px] text-slate-500 mt-1">Zo kan de boekhouder je betaling matchen.</p>
              </div>
              {error && (
                <div className="flex items-center gap-2 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg p-2">
                  <AlertCircle className="w-3.5 h-3.5" /> {error}
                </div>
              )}
              <button data-testid="tikkie-next" onClick={goConfirm}
                className="w-full py-3 rounded-lg font-bold text-slate-900 transition-all"
                style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                Volgende — toon QR
              </button>
            </>
          )}

          {step === 'confirm' && (
            <>
              <div className="text-center space-y-2">
                <div className="inline-block bg-white p-3 rounded-xl">
                  <img src={`${API}/api/wallet/tikkie/qr`} alt="Tikkie QR" data-testid="tikkie-qr" className="w-48 h-48 object-contain" />
                </div>
                <p className="text-sm text-white">Scan deze QR en vul <b className="text-amber-400">€{parseFloat(amount).toFixed(2)}</b> in.</p>
                <p className="text-[10px] text-slate-400">Gebruik je naam <b className="text-white">{naam}</b> in het bericht.</p>
                {tikkieUrl && (
                  <a href={tikkieUrl} target="_blank" rel="noreferrer"
                    className="inline-flex items-center gap-2 text-xs text-violet-300 underline mt-2" data-testid="tikkie-link">
                    <QrCode className="w-3.5 h-3.5" /> Of open Tikkie direct
                  </a>
                )}
              </div>
              <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-[11px] text-amber-200">
                Druk pas op <b>Verzenden</b> als je Tikkie hebt voltooid. De boekhouder krijgt dan een melding en bevestigt zo snel mogelijk.
              </div>
              {error && (
                <div className="flex items-center gap-2 text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded-lg p-2">
                  <AlertCircle className="w-3.5 h-3.5" /> {error}
                </div>
              )}
              <div className="flex gap-2">
                <button data-testid="tikkie-back" onClick={() => setStep('form')}
                  className="flex-1 py-2.5 rounded-lg text-sm font-medium bg-slate-800 text-slate-300 hover:bg-slate-700">
                  Terug
                </button>
                <button data-testid="tikkie-submit" onClick={submit} disabled={sending}
                  className="flex-1 py-2.5 rounded-lg text-sm font-bold text-white flex items-center justify-center gap-2 disabled:opacity-60"
                  style={{ background: 'linear-gradient(135deg, #22c55e, #16a34a)' }}>
                  {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                  Verzenden
                </button>
              </div>
            </>
          )}

          {step === 'sent' && result && (
            <>
              <div className="text-center space-y-3 py-4">
                <div className="w-14 h-14 rounded-full bg-green-500/15 border border-green-500/40 mx-auto flex items-center justify-center">
                  <Check className="w-7 h-7 text-green-400" />
                </div>
                <h4 className="text-lg font-bold text-white">Aanvraag verzonden</h4>
                <p className="text-xs text-slate-400">
                  Referentie: <span className="font-mono text-amber-400">#{result.id?.slice(0, 10)}</span><br />
                  De boekhouder bevestigt zodra de Tikkie van <b>€{result.amount_eur.toFixed(2)}</b> binnen is.
                </p>
              </div>
              <button data-testid="tikkie-done" onClick={onClose}
                className="w-full py-2.5 rounded-lg font-bold text-slate-900"
                style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                Sluiten
              </button>
            </>
          )}

          {/* Eigen historie */}
          {myTopups.length > 0 && step !== 'sent' && (
            <div className="pt-3 border-t border-slate-800">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Jouw recente Tikkies</p>
              <div className="space-y-1.5 max-h-32 overflow-y-auto">
                {myTopups.slice(0, 5).map(t => (
                  <div key={t.id} data-testid={`my-topup-${t.id}`} className="flex items-center justify-between text-[11px] bg-slate-800/50 rounded-lg px-2.5 py-1.5">
                    <span className="text-slate-300">€{t.amount_eur.toFixed(2)}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${
                      t.status === 'confirmed' ? 'bg-green-500/15 text-green-300' :
                      t.status === 'cancelled' ? 'bg-red-500/15 text-red-300' :
                      'bg-amber-500/15 text-amber-300'
                    }`}>{t.status === 'pending' ? 'wacht op bevestiging' : t.status === 'confirmed' ? 'bevestigd' : 'geannuleerd'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TikkieTopupModal;
