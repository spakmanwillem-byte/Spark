/**
 * v13_boekhouding_books_ui_001 — Multi-container boeken tab.
 *
 * Toont alle boeken (systeem + owned) als cards met balans, klik → detail
 * bark met entries, IBAN-instelling, SEPA import/export, openingsbalans.
 */
import React, { useEffect, useState } from 'react';
import {
  BookOpen, Sparkles, ShoppingBag, Building, User, X,
  Upload, Download, Settings, Wallet, RefreshCw, FileText, Plus, Clock, Briefcase,
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

  const resetBook = async () => {
    if (!window.confirm(`Zeker weten? Alle regels van "${book?.naam}" worden gewist (papertrail blijft bewaard).`)) return;
    await fetch(`${API}/api/boekhouding/books/${bookId}/reset?viewer_id=${userId}`, { method: 'POST' });
    setFlash('Boek gereset naar nulpunt'); setTimeout(() => setFlash(''), 2000); load();
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
            { id: 'uren', label: 'Uren', icon: Clock },
            {
              id: 'clienten',
              // v13d_book_tab_label_per_type_001 (sessie 56b) — Willem:
              // "bij shop moet 'client' → 'klant'". Per book-type ander label.
              label: book.type === 'shop' ? 'Klanten' : book.type === 'entity' ? 'Zorgcliënten' : 'Clienten',
              icon: Briefcase,
            },
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
                    <p className="text-[10px] text-slate-500 flex items-center gap-2">
                      <span>{e.ts?.slice(0,10)} · {e.type}</span>
                      {e.papertrail_hash && (
                        <span className="font-mono text-[9px] text-cyan-500/70" title="Papertrail hash">
                          #{e.papertrail_hash.slice(0,8)}
                        </span>
                      )}
                    </p>
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
              <div className="pt-4 border-t border-red-500/20">
                <p className="text-[11px] text-red-300 font-semibold mb-1">Boek resetten naar nulpunt</p>
                <p className="text-[10px] text-slate-500 mb-2">Wist alle regels. Papertrail (hash-chain) blijft bewaard — dus je kan verifieerbaar terugzien dat er een reset is geweest.</p>
                <button data-testid="book-reset-btn" onClick={resetBook} className="px-3 py-2 rounded bg-red-500/20 border border-red-500/40 text-red-200 text-xs">
                  Reset naar €0.00
                </button>
              </div>
            </div>
          )}
          {tab === 'uren' && <BookUrenPanel bookId={bookId} bookNaam={book.naam} bookType={book.type} userId={userId} kleur={book.kleur} />}
          {tab === 'clienten' && <BookClientenPanel bookId={bookId} bookType={book.type} userId={userId} kleur={book.kleur} />}
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


// v13d_book_uren_panel_001 (sessie 56b) — Uren-samenvatting per book
function BookUrenPanel({ bookId, bookNaam, bookType, userId, kleur }) {
  const [period, setPeriod] = useState('maand');
  const [anchor, setAnchor] = useState(new Date());
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const y = anchor.getFullYear(), m = anchor.getMonth() + 1, d = anchor.getDate();

  // v13d_book_label_per_type_001 — Willem: "per opdrachtgever is per zorgvrager"
  const perLabel = bookType === 'entity' ? 'Per zorgvrager'
    : bookType === 'shop' ? 'Per klant' : 'Per opdrachtgever';

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/agenda/uren-rapport/${userId}?period=${period}&year=${y}&month=${m}&day=${d}&book_id=${bookId}&viewer_id=${userId}`)
      .then(r => r.json()).then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
    // eslint-disable-next-line
  }, [bookId, userId, period, anchor]);

  const shift = (dir) => {
    const d = new Date(anchor);
    if (period === 'dag') d.setDate(d.getDate() + dir);
    else if (period === 'week') d.setDate(d.getDate() + 7 * dir);
    else if (period === 'maand') d.setMonth(d.getMonth() + dir);
    else d.setFullYear(d.getFullYear() + dir);
    setAnchor(d);
  };

  const exportCSV = () => {
    if (!data?.events?.length) return;
    const rows = [['Datum', 'Titel', 'Opdrachtgever', 'Onderwerp', 'Pauze (min)', 'Uren']];
    for (const e of data.events) {
      rows.push([(e.date || '').slice(0, 10), (e.titel || '').replace(/,/g, ' '),
        (e.opdrachtgever || '').replace(/,/g, ' '), (e.onderwerp || '').replace(/,/g, ' '),
        e.pauze_minuten || 0, e.totaal_uren || 0]);
    }
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `urenstaat_${bookNaam.replace(/[^a-zA-Z0-9]/g, '_')}_${data.label.replace(/[^a-zA-Z0-9]/g, '_')}.csv`;
    link.click();
  };

  return (
    <div data-testid="book-uren-panel" className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        {['dag', 'week', 'maand', 'jaar'].map(p => (
          <button key={p} data-testid={`book-uren-period-${p}`} onClick={() => setPeriod(p)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition"
            style={period === p
              ? { background: `${kleur}22`, borderWidth: '1px', borderStyle: 'solid', borderColor: `${kleur}60`, color: kleur }
              : { background: 'rgba(30,41,59,0.5)', borderWidth: '1px', borderStyle: 'solid', borderColor: 'rgba(51,65,85,0.5)', color: '#94a3b8' }}>
            {p.charAt(0).toUpperCase() + p.slice(1)}
          </button>
        ))}
        <button onClick={() => shift(-1)} className="ml-auto p-1.5 hover:bg-slate-800 rounded"><span className="text-xs text-slate-400">◀</span></button>
        <p className="text-xs font-semibold text-white min-w-[140px] text-center">{data?.label || '...'}</p>
        <button onClick={() => shift(1)} className="p-1.5 hover:bg-slate-800 rounded"><span className="text-xs text-slate-400">▶</span></button>
        <button data-testid="book-uren-csv" onClick={exportCSV} disabled={!data?.events?.length}
          className="flex items-center gap-1 px-2 py-1.5 rounded text-[10px] font-medium text-white disabled:opacity-40"
          style={{ background: 'var(--app-secondary, #06b6d4)' }}>
          <Download className="w-3 h-3" /> CSV
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Totaal uren</p>
          <p className="text-2xl font-bold mt-0.5" style={{ color: kleur }}>{loading ? '...' : (data?.totaal_uren ?? 0)}</p>
        </div>
        <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider">Events</p>
          <p className="text-2xl font-bold text-white mt-0.5">{loading ? '...' : (data?.event_count ?? 0)}</p>
        </div>
      </div>

      <div className="p-3 bg-slate-800/40 border border-slate-800 rounded-lg">
        <p className="text-xs font-semibold text-white mb-2">{perLabel}</p>
        {!data || data.per_opdrachtgever.length === 0 ? (
          <p className="text-[11px] text-slate-500 italic">Nog geen zakelijke uren voor {bookNaam} in deze periode. Koppel eerst {bookType === 'entity' ? 'zorgvragers' : bookType === 'shop' ? 'klanten' : 'clienten'} aan dit book en registreer zakelijke agenda-events.</p>
        ) : data.per_opdrachtgever.map(row => (
          <div key={row.opdrachtgever} className="flex items-center gap-2 py-1 text-xs">
            <span className="text-white flex-1">{row.opdrachtgever}</span>
            <span className="text-[10px] text-slate-500">{row.events}×</span>
            <span className="font-bold" style={{ color: kleur }}>{row.uren}u</span>
          </div>
        ))}
      </div>
    </div>
  );
}


// v13d_book_clienten_panel_001 (sessie 56b) — Clienten per book, book-type-aware
function BookClientenPanel({ bookId, bookType, userId, kleur }) {
  const [clienten, setClienten] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState({ naam: '', contactpersoon: '', email: '', telefoon: '', uurtarief: '' });

  // Book-type bepaalt client_type: entity → zorgclient, shop → klant, rest → generiek
  const clientType = bookType === 'entity' ? 'zorgclient' : bookType === 'shop' ? 'klant' : 'generiek';
  const labelSingular = clientType === 'zorgclient' ? 'Zorgcliënt' : clientType === 'klant' ? 'Klant' : 'Client';

  const load = () => {
    setLoading(true);
    fetch(`${API}/api/clienten/list/${userId}?viewer_id=${userId}&book_id=${bookId}`)
      .then(r => r.json()).then(d => { setClienten(d.clienten || []); setLoading(false); })
      .catch(() => setLoading(false));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [bookId, userId]);

  const create = async () => {
    if (!form.naam.trim()) return;
    await fetch(`${API}/api/clienten/create/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...form,
        uurtarief: form.uurtarief ? Number(form.uurtarief) : null,
        book_id: bookId,
        client_type: clientType,
        scope: 'zakelijk',
      }),
    });
    setForm({ naam: '', contactpersoon: '', email: '', telefoon: '', uurtarief: '' });
    setShowNew(false);
    load();
  };

  const remove = async (c) => {
    if (!window.confirm(`${labelSingular} "${c.naam}" verwijderen?`)) return;
    await fetch(`${API}/api/clienten/delete/${userId}/${c.id}`, { method: 'DELETE' });
    load();
  };

  return (
    <div data-testid="book-clienten-panel" className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400">
            {clienten.length} {labelSingular.toLowerCase()}{clienten.length !== 1 ? 'en' : ''}
            {clientType === 'zorgclient' && <span className="text-[10px] text-slate-500 ml-2">· dossier per cliënt</span>}
            {clientType === 'klant' && <span className="text-[10px] text-slate-500 ml-2">· factuur-info per klant</span>}
          </p>
        </div>
        <button data-testid="book-add-client-btn" onClick={() => setShowNew(!showNew)}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-white"
          style={{ background: kleur }}>
          <Plus className="w-3.5 h-3.5" /> Nieuw
        </button>
      </div>

      {showNew && (
        <div className="p-3 bg-slate-800/40 rounded-lg space-y-2" style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: `${kleur}40` }}>
          <input data-testid="book-client-naam" value={form.naam} onChange={e => setForm({ ...form, naam: e.target.value })}
            placeholder={clientType === 'zorgclient' ? 'Naam cliënt...' : clientType === 'klant' ? 'Naam / bedrijf...' : 'Naam...'}
            className="w-full px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none" />
          <div className="grid grid-cols-2 gap-2">
            <input value={form.contactpersoon} onChange={e => setForm({ ...form, contactpersoon: e.target.value })} placeholder="Contactpersoon..."
              className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none" />
            <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} placeholder="Email..."
              className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none" />
            <input value={form.telefoon} onChange={e => setForm({ ...form, telefoon: e.target.value })} placeholder="Telefoon..."
              className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none" />
            <input type="number" step="0.5" value={form.uurtarief} onChange={e => setForm({ ...form, uurtarief: e.target.value })} placeholder="Uurtarief €..."
              className="px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-white placeholder-slate-500 focus:outline-none" />
          </div>
          {clientType === 'zorgclient' && (
            <p className="text-[10px] text-slate-500 italic">Meer zorg-velden (BSN, indicatie, huisarts) via de detail-view straks — placeholder klaar.</p>
          )}
          {clientType === 'klant' && (
            <p className="text-[10px] text-slate-500 italic">Factuur-adres + betalingstermijn via detail-view — placeholder klaar.</p>
          )}
          <button data-testid="book-client-save" onClick={create}
            className="w-full px-3 py-1.5 rounded text-xs font-medium text-white"
            style={{ background: kleur }}>Opslaan</button>
        </div>
      )}

      <div className="space-y-1">
        {loading ? (
          <p className="text-[11px] text-slate-500 italic">Laden...</p>
        ) : clienten.length === 0 ? (
          <div className="py-6 text-center border border-dashed border-slate-800 rounded-lg">
            <Briefcase className="w-6 h-6 text-slate-700 mx-auto mb-1" />
            <p className="text-[11px] text-slate-500">Nog geen {labelSingular.toLowerCase()}en gekoppeld aan {bookType === 'shop' ? 'deze winkel' : 'dit book'}.</p>
          </div>
        ) : clienten.map(c => (
          <div key={c.id} data-testid={`book-client-${c.id}`} className="flex items-center gap-2 p-2 bg-slate-800/40 border border-slate-800 rounded">
            <div className="flex-1 min-w-0">
              <p className="text-xs text-white truncate">{c.naam}</p>
              <p className="text-[10px] text-slate-500 truncate">
                {c.contactpersoon || c.email || ''}
                {c.uurtarief ? ` · €${c.uurtarief}/u` : ''}
              </p>
            </div>
            <button onClick={() => remove(c)} className="p-0.5 text-slate-600"
              onMouseEnter={e => { e.currentTarget.style.color = 'var(--alert-base)'; }}
              onMouseLeave={e => { e.currentTarget.style.color = '#64748b'; }}>
              <X className="w-3 h-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
