/**
 * v13_boekhouding_books_ui_001 — Multi-container boeken tab.
 *
 * Toont alle boeken (systeem + owned) als cards met balans, klik → detail
 * bark met entries, IBAN-instelling, SEPA import/export, openingsbalans.
 */
import React, { useEffect, useState } from 'react';
import {
  BookOpen, Sparkles, ShoppingBag, Building, User, X,
  Upload, Download, Settings, Wallet, RefreshCw, FileText, Plus,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const ICON_MAP = {
  sparkles: Sparkles,
  'shopping-bag': ShoppingBag,
  building: Building,
  user: User,
  book: BookOpen,
};

export function BoekhoudingBoekenTab({ userId }) {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openBook, setOpenBook] = useState(null); // book_id of null

  const load = () => {
    setLoading(true);
    fetch(`${API}/api/boekhouding/books?viewer_id=${userId}`)
      .then((r) => r.json())
      .then(async (d) => {
        const items = d.books || [];
        // Fetch summary per book (parallel)
        const withSummary = await Promise.all(items.map(async (b) => {
          try {
            const r = await fetch(`${API}/api/boekhouding/books/${b.id}?viewer_id=${userId}`);
            const detail = await r.json();
            return { ...b, summary: detail.summary };
          } catch { return b; }
        }));
        setBooks(withSummary);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { if (userId) load(); }, [userId]); // eslint-disable-line

  if (loading) return <div className="text-slate-400 text-sm p-4">Boeken laden…</div>;

  return (
    <div className="space-y-4" data-testid="boekhouding-boeken-tab">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-white">Boeken ({books.length})</h3>
          <p className="text-[11px] text-slate-500">Elk boek is een eigen container met IBAN + kasboek + SEPA</p>
        </div>
        <button data-testid="reload-books-btn" onClick={load}
          className="flex items-center gap-1 px-2 py-1 rounded text-[11px] bg-slate-800 border border-slate-700 text-slate-300 hover:bg-slate-700">
          <RefreshCw className="w-3 h-3" /> Ververs
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {books.map((b) => {
          const Ico = ICON_MAP[b.icoon] || BookOpen;
          const bal = b.summary?.balance_eur ?? 0;
          const positive = bal >= 0;
          return (
            <button
              key={b.id}
              data-testid={`book-card-${b.id}`}
              onClick={() => setOpenBook(b.id)}
              className="text-left bg-slate-900/60 border border-slate-800 rounded-xl p-4 hover:border-slate-600 transition-all"
              style={{ boxShadow: `0 0 20px ${b.kleur}20` }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${b.kleur}20`, color: b.kleur }}>
                    <Ico className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-white">{b.naam}</p>
                    <p className="text-[10px] text-slate-500 uppercase">{b.type.replace('_', ' ')}</p>
                  </div>
                </div>
                <p className={`text-lg font-bold ${positive ? 'text-emerald-400' : 'text-red-400'}`}>
                  €{bal.toFixed(2)}
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[10px]">
                <div>
                  <p className="text-slate-500">Inkomsten</p>
                  <p className="text-emerald-300 font-semibold">€{(b.summary?.income_eur ?? 0).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Uitgaven</p>
                  <p className="text-red-300 font-semibold">€{(b.summary?.expense_eur ?? 0).toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Regels</p>
                  <p className="text-slate-300 font-semibold">{b.summary?.n_entries ?? 0}</p>
                </div>
              </div>
              <div className="mt-3 flex items-center gap-2 text-[10px] text-slate-500">
                <span>IBAN: {b.iban ? <span className="font-mono text-slate-300">{b.iban}</span> : <span className="text-amber-400">niet ingesteld</span>}</span>
              </div>
            </button>
          );
        })}
      </div>

      {openBook && (
        <BookDetailBark
          bookId={openBook}
          userId={userId}
          onClose={() => { setOpenBook(null); load(); }}
        />
      )}
    </div>
  );
}


function BookDetailBark({ bookId, userId, onClose }) {
  const [book, setBook] = useState(null);
  const [entries, setEntries] = useState([]);
  const [tab, setTab] = useState('entries'); // entries | instellingen | sepa
  const [iban, setIban] = useState('');
  const [bankNaam, setBankNaam] = useState('');
  const [openingAmt, setOpeningAmt] = useState('');
  const [flash, setFlash] = useState('');

  const load = () => {
    fetch(`${API}/api/boekhouding/books/${bookId}?viewer_id=${userId}`)
      .then((r) => r.json()).then((d) => { setBook(d.book); setIban(d.book?.iban || ''); setBankNaam(d.book?.bank_naam || ''); });
    fetch(`${API}/api/boekhouding/books/${bookId}/entries?viewer_id=${userId}`)
      .then((r) => r.json()).then((d) => setEntries(d.entries || []));
  };
  useEffect(() => { load(); }, [bookId]); // eslint-disable-line

  const saveIban = async () => {
    const r = await fetch(`${API}/api/boekhouding/books/${bookId}?viewer_id=${userId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ iban, bank_naam: bankNaam }),
    });
    const d = await r.json();
    if (d.success) { setFlash('IBAN opgeslagen'); setTimeout(() => setFlash(''), 1500); load(); }
    else setFlash('IBAN ongeldig');
  };

  const setOpening = async () => {
    if (!openingAmt) return;
    await fetch(`${API}/api/boekhouding/books/${bookId}/opening-balance?viewer_id=${userId}&amount_eur=${parseFloat(openingAmt)}`, { method: 'POST' });
    setFlash('Openingsbalans gezet'); setTimeout(() => setFlash(''), 1500); setOpeningAmt(''); load();
  };

  const uploadCamt = async (file) => {
    const fd = new FormData(); fd.append('file', file);
    const r = await fetch(`${API}/api/boekhouding/books/${bookId}/sepa/import-camt?viewer_id=${userId}`, { method: 'POST', body: fd });
    const d = await r.json();
    setFlash(`CAMT: ${d.imported || 0} tx geïmporteerd`);
    setTimeout(() => setFlash(''), 2500); load();
  };
  const uploadMt940 = async (file) => {
    const fd = new FormData(); fd.append('file', file);
    const r = await fetch(`${API}/api/boekhouding/books/${bookId}/sepa/import-mt940?viewer_id=${userId}`, { method: 'POST', body: fd });
    const d = await r.json();
    setFlash(`MT940: ${d.imported || 0} tx geïmporteerd`);
    setTimeout(() => setFlash(''), 2500); load();
  };

  const exportPain001 = async () => {
    if (!book?.iban) { setFlash('Vul eerst IBAN in bij Instellingen'); return; }
    // demo-payment
    const r = await fetch(`${API}/api/boekhouding/books/${bookId}/sepa/export-pain001?viewer_id=${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ payments: [{ amount_eur: 10.00, creditor_naam: 'Test', creditor_iban: 'NL02RABO0300065264', remittance: 'Test-batch vanuit UI' }] }),
    });
    const d = await r.json();
    if (d.success) {
      const blob = new Blob([d.xml], { type: 'application/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `sepa-${bookId}-${Date.now()}.xml`;
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
      setFlash('SEPA XML gedownload');
    } else setFlash(d.detail || 'Export mislukt');
    setTimeout(() => setFlash(''), 2500);
  };

  if (!book) return null;

  return (
    <div data-testid="book-detail-bark-overlay" className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-sm p-4" onClick={onClose}>
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}
        style={{ borderColor: book.kleur, boxShadow: `0 0 40px ${book.kleur}66` }}>
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${book.kleur}22`, color: book.kleur }}>
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-white font-bold" data-testid="book-detail-naam">{book.naam}</h2>
              <p className="text-[10px] text-slate-500 uppercase">{book.type}</p>
            </div>
          </div>
          <button data-testid="book-detail-close" onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>

        <div className="flex border-b border-slate-800">
          {[
            { id: 'entries', label: 'Kasboek', icon: FileText },
            { id: 'instellingen', label: 'Instellingen', icon: Settings },
            { id: 'sepa', label: 'SEPA', icon: Wallet },
          ].map((t) => {
            const Ic = t.icon;
            const active = tab === t.id;
            return (
              <button key={t.id} data-testid={`book-tab-${t.id}`} onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium border-b-2 transition-colors ${active ? 'border-current text-white' : 'border-transparent text-slate-400 hover:text-slate-200'}`}
                style={active ? { color: book.kleur, borderColor: book.kleur } : {}}>
                <Ic className="w-3.5 h-3.5" />{t.label}
              </button>
            );
          })}
        </div>

        {flash && <div className="px-4 py-2 text-xs bg-emerald-500/10 text-emerald-300 border-b border-emerald-500/30">{flash}</div>}

        <div className="flex-1 overflow-y-auto p-4">
          {tab === 'entries' && (
            <div className="space-y-1" data-testid="book-entries-list">
              {entries.length === 0 ? (
                <p className="text-slate-500 text-sm text-center py-8">Nog geen regels — voeg openingsbalans toe of importeer een SEPA-afschrift.</p>
              ) : entries.map((e) => (
                <div key={e.id} className="flex items-center justify-between p-2 rounded bg-slate-800/40 border border-slate-800">
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-white truncate">{e.naam}</p>
                    <p className="text-[10px] text-slate-500">{e.ts?.slice(0,10)} · {e.type}</p>
                  </div>
                  <p className={`text-sm font-semibold ${e.amount_eur >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>€{e.amount_eur.toFixed(2)}</p>
                </div>
              ))}
            </div>
          )}
          {tab === 'instellingen' && (
            <div className="space-y-4">
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">IBAN</label>
                <input data-testid="book-iban-input" value={iban} onChange={(e) => setIban(e.target.value)} placeholder="NL91 ABNA 0417 1643 00"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm font-mono text-white" />
              </div>
              <div>
                <label className="text-[11px] text-slate-400 block mb-1">Bank naam</label>
                <input data-testid="book-bank-input" value={bankNaam} onChange={(e) => setBankNaam(e.target.value)} placeholder="ABN AMRO"
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-white" />
              </div>
              <button data-testid="book-save-iban-btn" onClick={saveIban} className="px-4 py-2 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-sm">
                IBAN opslaan
              </button>
              <div className="pt-4 border-t border-slate-800">
                <label className="text-[11px] text-slate-400 block mb-1">Openingsbalans instellen (€)</label>
                <div className="flex gap-2">
                  <input data-testid="book-opening-input" type="number" step="0.01" value={openingAmt} onChange={(e) => setOpeningAmt(e.target.value)} placeholder="0.00"
                    className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded text-sm text-white" />
                  <button data-testid="book-set-opening-btn" onClick={setOpening} className="px-3 py-2 rounded bg-amber-500/20 border border-amber-500/40 text-amber-200 text-sm">
                    <Plus className="w-4 h-4 inline mr-1" />Zet
                  </button>
                </div>
                <p className="text-[10px] text-slate-500 mt-1">Overschrijft eventuele bestaande opening.</p>
              </div>
            </div>
          )}
          {tab === 'sepa' && (
            <div className="space-y-4" data-testid="book-sepa-tab">
              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800">
                <p className="text-xs text-slate-300 font-semibold mb-1">Bank-afschrift importeren</p>
                <p className="text-[10px] text-slate-500 mb-3">Upload een CAMT.053 XML of MT940 tekstbestand. Transacties worden automatisch geboekt (duplicate-check op datum+bedrag+iban).</p>
                <div className="flex gap-2">
                  <label className="flex-1 cursor-pointer">
                    <input data-testid="book-camt-file" type="file" accept=".xml" hidden onChange={(e) => e.target.files?.[0] && uploadCamt(e.target.files[0])} />
                    <div className="flex items-center justify-center gap-2 px-3 py-2 rounded bg-sky-500/20 border border-sky-500/40 text-sky-200 text-xs">
                      <Upload className="w-3.5 h-3.5" /> CAMT.053
                    </div>
                  </label>
                  <label className="flex-1 cursor-pointer">
                    <input data-testid="book-mt940-file" type="file" accept=".txt,.mt940,.sta" hidden onChange={(e) => e.target.files?.[0] && uploadMt940(e.target.files[0])} />
                    <div className="flex items-center justify-center gap-2 px-3 py-2 rounded bg-purple-500/20 border border-purple-500/40 text-purple-200 text-xs">
                      <Upload className="w-3.5 h-3.5" /> MT940
                    </div>
                  </label>
                </div>
              </div>
              <div className="p-3 rounded-lg bg-slate-800/40 border border-slate-800">
                <p className="text-xs text-slate-300 font-semibold mb-1">SEPA batch exporteren</p>
                <p className="text-[10px] text-slate-500 mb-3">Genereer een pain.001.001.03 XML voor uitgaande betalingen. Upload bij je bank.</p>
                <button data-testid="book-export-pain001-btn" onClick={exportPain001} className="flex items-center gap-2 px-3 py-2 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-200 text-xs">
                  <Download className="w-3.5 h-3.5" /> Genereer &amp; download test-batch
                </button>
                {!book.iban && <p className="text-[10px] text-amber-400 mt-2">⚠ Stel eerst IBAN in bij Instellingen.</p>}
              </div>
              <p className="text-[10px] text-slate-500 text-center">Volledig lokaal — geen cloud-koppeling, geen bank-API.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
