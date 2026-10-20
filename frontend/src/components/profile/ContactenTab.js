import React, { useState, useEffect, useCallback } from 'react';
import { Users, Briefcase, Plus, Pencil, Trash2, Phone, Mail, MapPin, X, Save, Printer, Globe } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

// v14_contacten_klapper_001 — telefoonklapper met twee lagen (privé / zakelijk)
const ROLLEN = {
  prive: ['familie', 'vriend', 'overig'],
  zakelijk: ['leverancier', 'klant', 'partner', 'overig'],
};
const BRON_LABEL = { klapper: null, bel: 'bel-contact', clienten: 'cliënt' }; // bewerken/verwijderen schrijft terug naar die module
const LEEG = { laag: 'prive', naam: '', rol: '', bedrijf: '', contactpersoon: '', email: '', email2: '', telefoon: '', telefoon2: '', fax: '', website: '', adres: '', postcode: '', plaats: '', notities: '' };

export function ContactenTab({ userId }) {
  const [laag, setLaag] = useState('prive');
  const [items, setItems] = useState([]);
  const [perLaag, setPerLaag] = useState({});
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(null);
  const [saving, setSaving] = useState(false);
  const [zoek, setZoek] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await fetch(`${API}/api/contacten/${userId}?laag=${laag}`).then(r => r.json());
      setItems(d.contacten || []); setPerLaag(d.per_laag || {});
    } catch { setItems([]); }
    setLoading(false);
  }, [userId, laag]);
  useEffect(() => { load(); }, [load]);

  const save = async () => {
    if (!form.naam.trim()) { toast.error('Naam is verplicht'); return; }
    setSaving(true);
    const isNew = !form.id;
    const url = isNew ? `${API}/api/contacten/${userId}` : `${API}/api/contacten/${userId}/${form.id}`;
    const { id, bron, readonly, created_at, updated_at, ...body } = form;
    try {
      const r = await fetch(url, { method: isNew ? 'POST' : 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(x => x.json());
      if (r.success) { toast.success(isNew ? 'Contact toegevoegd' : 'Contact bijgewerkt'); setForm(null); load(); }
      else toast.error(r.detail || r.message || 'Opslaan mislukt');
    } catch (e) { toast.error(e.message); }
    setSaving(false);
  };

  const remove = async (c) => {
    const waar = c.bron === 'bel' ? ' (ook uit je bel-contacten)' : c.bron === 'clienten' ? ' (ook uit je cliënten, incl. dossier)' : '';
    if (!window.confirm(`"${c.naam}" verwijderen${waar}?`)) return;
    const r = await fetch(`${API}/api/contacten/${userId}/${c.id}`, { method: 'DELETE' }).then(x => x.json());
    if (r.success) { toast.success('Verwijderd'); load(); } else toast.error('Verwijderen mislukt');
  };

  const q = zoek.toLowerCase();
  const shown = items.filter(c => !q || [c.naam, c.bedrijf, c.email, c.telefoon, c.rol].some(v => (v || '').toLowerCase().includes(q)));

  return (
    <div className="space-y-4" data-testid="contacten-tab">
      <div className="flex flex-wrap items-center gap-2">
        {[['prive', 'Privé', Users, '#22d3ee'], ['zakelijk', 'Zakelijk', Briefcase, '#f59e0b']].map(([id, label, Icon, color]) => (
          <button key={id} data-testid={`contacten-laag-${id}`} onClick={() => { setLaag(id); setForm(null); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${laag === id ? '' : 'border-slate-700 text-slate-400 hover:text-slate-200'}`}
            style={laag === id ? { color, borderColor: color, backgroundColor: color + '18' } : {}}>
            <Icon className="w-3.5 h-3.5" /> {label} <span className="opacity-70">({perLaag[id] ?? 0})</span>
          </button>
        ))}
        <input data-testid="contacten-zoek" value={zoek} onChange={e => setZoek(e.target.value)} placeholder="Zoek…"
          className="ml-auto bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white w-40" />
        <button data-testid="contacten-nieuw" onClick={() => setForm({ ...LEEG, laag, rol: ROLLEN[laag][0] })}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950" style={{ background: 'var(--glow-base, #f59e0b)' }}>
          <Plus className="w-3.5 h-3.5" /> Nieuw contact
        </button>
      </div>

      {form && <ContactForm form={form} setForm={setForm} onSave={save} saving={saving} onCancel={() => setForm(null)} />}

      {loading ? <p className="text-xs text-slate-500 py-6 text-center">Laden…</p>
        : shown.length === 0 ? (
          <div className="text-center py-12 border border-dashed border-slate-700 rounded-xl text-xs text-slate-500">
            Nog geen {laag === 'prive' ? 'privé' : 'zakelijke'} contacten{q ? ' gevonden' : ''}.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {shown.map(c => (
              <div key={c.id} data-testid={`contact-${c.id}`} className="bg-slate-900 border border-slate-800 rounded-xl p-3 flex gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm text-white font-medium truncate">{c.naam}</p>
                    {c.rol && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">{c.rol}</span>}
                    {BRON_LABEL[c.bron] && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/60 text-slate-500" title="Komt uit een andere module; bewerken hier werkt door in die module">{BRON_LABEL[c.bron]}</span>}
                  </div>
                  {(c.bedrijf && c.bedrijf !== c.naam) && <p className="text-[11px] text-slate-400 truncate">{c.bedrijf}</p>}
                  {c.contactpersoon && <p className="text-[11px] text-slate-400 truncate">t.a.v. {c.contactpersoon}</p>}
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5 mt-1 text-[11px] text-slate-400">
                    {c.telefoon && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.telefoon}</span>}
                    {c.telefoon2 && <span className="flex items-center gap-1"><Phone className="w-3 h-3" />{c.telefoon2}</span>}
                    {c.fax && <span className="flex items-center gap-1"><Printer className="w-3 h-3" />fax {c.fax}</span>}
                    {c.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{c.email}</span>}
                    {c.email2 && <span className="flex items-center gap-1"><Mail className="w-3 h-3" />{c.email2}</span>}
                    {c.website && <a href={c.website.startsWith('http') ? c.website : `https://${c.website}`} target="_blank" rel="noreferrer" className="flex items-center gap-1 hover:text-white"><Globe className="w-3 h-3" />{c.website}</a>}
                    {(c.plaats || c.adres) && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{[c.adres, c.postcode, c.plaats].filter(Boolean).join(', ')}</span>}
                  </div>
                  {c.notities && <p className="text-[11px] text-slate-500 mt-1 italic truncate">{c.notities}</p>}
                </div>
                {!c.readonly && (
                  <div className="flex flex-col gap-1">
                    <button data-testid={`contact-edit-${c.id}`} onClick={() => setForm({ ...LEEG, ...c })} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"><Pencil className="w-3.5 h-3.5" /></button>
                    <button data-testid={`contact-delete-${c.id}`} onClick={() => remove(c)} className="p-1.5 rounded-lg hover:bg-red-500/20 text-slate-400 hover:text-red-300"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

function F({ label, k, form, setForm, placeholder, type = 'text' }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-wider text-slate-500">{label}</span>
      <input data-testid={`contact-form-${k}`} type={type} value={form[k] || ''} placeholder={placeholder}
        onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
        className="mt-0.5 w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white" />
    </label>
  );
}

function ContactForm({ form, setForm, onSave, saving, onCancel }) {
  const zak = form.laag === 'zakelijk';
  return (
    <div data-testid="contact-form" className="bg-slate-900 border border-slate-700 rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-white">{form.id ? 'Contact bewerken' : 'Nieuw contact'} · {zak ? 'zakelijk' : 'privé'}</p>
        <button onClick={onCancel} className="text-slate-500 hover:text-white"><X className="w-4 h-4" /></button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <F label={zak ? 'Naam / bedrijf' : 'Naam'} k="naam" form={form} setForm={setForm} placeholder={zak ? 'Leverancier BV' : 'Voornaam Achternaam'} />
        <label className="block">
          <span className="text-[10px] uppercase tracking-wider text-slate-500">Rol</span>
          <select data-testid="contact-form-rol" value={form.rol || ''} onChange={e => setForm(f => ({ ...f, rol: e.target.value }))}
            className="mt-0.5 w-full bg-slate-800 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white">
            {ROLLEN[form.laag].map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </label>
        {zak && <F label="Contactpersoon" k="contactpersoon" form={form} setForm={setForm} placeholder="Naam contactpersoon" />}
        <F label="Telefoon" k="telefoon" form={form} setForm={setForm} placeholder="+31 6 …" />
        <F label="Telefoon 2 (optioneel)" k="telefoon2" form={form} setForm={setForm} placeholder="vast / mobiel" />
        {zak && <F label="Fax (optioneel)" k="fax" form={form} setForm={setForm} placeholder="050 …" />}
        <F label="E-mail" k="email" form={form} setForm={setForm} placeholder="naam@voorbeeld.nl" type="email" />
        <F label="E-mail 2 (optioneel)" k="email2" form={form} setForm={setForm} placeholder="info@…" type="email" />
        {zak && <F label="Website" k="website" form={form} setForm={setForm} placeholder="www.voorbeeld.nl" />}
        <F label="Adres" k="adres" form={form} setForm={setForm} placeholder="Straat 1" />
        <F label="Postcode" k="postcode" form={form} setForm={setForm} placeholder="1234 AB" />
        <F label="Plaats" k="plaats" form={form} setForm={setForm} placeholder="Plaats" />
        <F label="Notities" k="notities" form={form} setForm={setForm} placeholder="…" />
      </div>
      <div className="flex justify-end gap-2">
        <button onClick={onCancel} className="px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white">Annuleren</button>
        <button data-testid="contact-form-save" onClick={onSave} disabled={saving}
          className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-950 disabled:opacity-50" style={{ background: 'var(--glow-base, #f59e0b)' }}>
          <Save className="w-3.5 h-3.5" /> {saving ? 'Opslaan…' : 'Opslaan'}
        </button>
      </div>
    </div>
  );
}
