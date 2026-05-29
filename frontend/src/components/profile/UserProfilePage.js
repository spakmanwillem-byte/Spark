import React, { useState, useEffect, useCallback, useRef } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import {
  User, Save, X, Heart, Target, AlertTriangle, Eye, Ear, Brain, Globe,
  Camera, MapPin, Upload, Check, MessageSquare, Calendar,
  Image as ImageIcon, Sparkles, ChevronDown, ChevronRight, Trash2,
  Backpack, Award, Plus, Settings, Palette, Volume2, Link2, KeyRound, RotateCcw,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const TABS = [
  { id: 'algemeen', label: 'Algemeen', accent: '#f59e0b' },
  { id: 'achtergrond', label: 'Achtergrond', accent: '#10b981' },
  { id: 'persoonlijkheid', label: 'Persoonlijkheid', accent: '#a855f7' },
  { id: 'gesprekken', label: 'Gesprekken', accent: '#3b82f6' },
  { id: 'avatar', label: 'Avatar', accent: '#ec4899' },
  { id: 'instellingen', label: 'Instellingen', accent: '#06b6d4' },
];

export function UserProfilePage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [activeTab, setActiveTab] = useState('algemeen');
  const [saving, setSaving] = useState(false);
  const [savedFlash, setSavedFlash] = useState(false);
  const [extProfile, setExtProfile] = useState({});
  const [persona, setPersona] = useState({
    geslacht: 'man',
    introvert_extravert: 65,
    analytisch_creatief: 45,
    planmatig_spontaan: 70,
    rationeel_emotioneel: 50,
    traditioneel_vernieuwend: 80,
    zelfstandig_teamspeler: 55,
  });

  useEffect(() => {
    fetch(`${API}/api/profile/extended/${userId}`)
      .then(r => r.json())
      .then(d => { if (d.profile) setExtProfile(d.profile); })
      .catch(() => {});
  }, [userId]);

  const updateField = (k, v) => setExtProfile(p => ({ ...p, [k]: v }));

  const saveProfile = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/profile/extended/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(extProfile),
      });
      setSavedFlash(true);
      setTimeout(() => setSavedFlash(false), 2000);
    } finally {
      setSaving(false);
    }
  };

  return (
    <MainLayout activePage="profiel" onNavigate={onNavigate}>
      <div data-testid="user-profile-page" className="h-full flex flex-col">
        {/* Header */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <User className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
              <h1 className="text-base font-bold text-white leading-tight">Mijn Profiel</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">
                {user?.naam || 'Gebruiker'} · {user?.gradatie_titel || `Gradatie ${user?.gradatie ?? '?'}`}
              </p>
            </div>
          </div>
          <div className="flex overflow-x-auto gap-0 scrollbar-hide">
            {TABS.map(t => {
              const a = activeTab === t.id;
              return (
                <button
                  key={t.id}
                  data-testid={`profile-tab-${t.id}`}
                  onClick={() => setActiveTab(t.id)}
                  className="relative px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap"
                  style={{ color: a ? t.accent : '#94a3b8' }}
                >
                  {t.label}
                  {a && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: t.accent }} />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-4xl mx-auto">
            {activeTab === 'algemeen' && (
              <AlgemeenTab
                user={user} userId={userId}
                profile={extProfile} updateField={updateField}
                persona={persona} setPersona={setPersona}
                onSave={saveProfile} saving={saving} savedFlash={savedFlash}
              />
            )}
            {activeTab === 'achtergrond' && (
              <AchtergrondTab
                profile={extProfile} updateField={updateField}
                onSave={saveProfile} saving={saving} savedFlash={savedFlash}
              />
            )}
            {activeTab === 'persoonlijkheid' && (
              <PersoonlijkheidTab
                persona={persona} setPersona={setPersona}
                onSave={saveProfile} saving={saving} savedFlash={savedFlash}
              />
            )}
            {activeTab === 'gesprekken' && (
              <GesprekkenTab userId={userId} />
            )}
            {activeTab === 'avatar' && (
              <AvatarTab userId={userId} isAdmin={(user?.gradatie ?? 99) <= 2} />
            )}
            {activeTab === 'instellingen' && (
              <InstellingenTab userId={userId} />
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// ============================================================
// TAB: ALGEMEEN — basis user-info
// ============================================================
function AlgemeenTab({ user, userId, profile, updateField, persona, setPersona, onSave, saving, savedFlash }) {
  const [avatarUrl, setAvatarUrl] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/avatar/current/${userId}`)
      .then(r => r.json())
      .then(d => setAvatarUrl(d.url ? `${API}${d.url}` : null))
      .catch(() => {});
  }, [userId]);

  return (
    <div className="space-y-4">
      <Card title="Wie ben jij?" accent="#f59e0b">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
          {/* Avatar */}
          <div className="text-center">
            <div className="w-32 h-32 mx-auto bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center overflow-hidden">
              {avatarUrl ? (
                <img src={avatarUrl} alt="" className="w-full h-full object-cover" />
              ) : (
                <User className="w-16 h-16 text-white" />
              )}
            </div>
            <p className="text-[10px] text-slate-500 mt-2 uppercase tracking-wider">Verander via "Avatar" tab</p>
          </div>

          {/* Basisvelden */}
          <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <InputField label="Naam (login)" value={user?.naam || ''} disabled />
            <InputField label="Rol" value={user?.rol || ''} disabled />
            <InputField label="Leeftijd" value={profile.leeftijd || ''}
              placeholder="Bijv. 35" onChange={v => updateField('leeftijd', v)} />
            <InputField label="Beroep" value={profile.beroep || ''}
              placeholder="Bijv. Ondernemer" onChange={v => updateField('beroep', v)} />
            <InputField label="Locatie (kort)" value={profile.locatie || ''}
              placeholder="Bijv. Groningen, NL" onChange={v => updateField('locatie', v)} />
            <InputField label="Opleiding" value={profile.opleiding || ''}
              placeholder="Bijv. MBO Techniek" onChange={v => updateField('opleiding', v)} />
          </div>
        </div>

        <div className="mt-5 pt-5 border-t border-slate-800">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Geslacht</p>
          <div className="flex gap-2">
            {[
              { v: 'man', s: '♂', c: 'cyan' },
              { v: 'vrouw', s: '♀', c: 'pink' },
              { v: 'anders', s: '⚧', c: 'purple' },
            ].map(g => (
              <button key={g.v} data-testid={`gender-${g.v}`}
                onClick={() => setPersona({ ...persona, geslacht: g.v })}
                className={`px-4 py-2 rounded-lg border-2 transition-all ${
                  persona.geslacht === g.v
                    ? `border-${g.c}-500 bg-${g.c}-500/20`
                    : 'border-slate-700 hover:border-slate-600'
                }`}>
                <span className="text-lg">{g.s}</span>
                <span className="text-xs ml-2 capitalize">{g.v}</span>
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card title="Sociale Media" accent="#3b82f6" subtitle="Wat je deelt, mag Spark gebruiken">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <InputField label="Instagram" value={profile.social_instagram || ''}
            placeholder="@gebruikersnaam" onChange={v => updateField('social_instagram', v)} />
          <InputField label="Facebook" value={profile.social_facebook || ''}
            placeholder="naam of url" onChange={v => updateField('social_facebook', v)} />
          <InputField label="LinkedIn" value={profile.social_linkedin || ''}
            placeholder="profiel url" onChange={v => updateField('social_linkedin', v)} />
          <InputField label="YouTube / TikTok" value={profile.social_youtube || ''}
            placeholder="kanaal/handle" onChange={v => updateField('social_youtube', v)} />
        </div>
      </Card>

      <SaveBar onSave={onSave} saving={saving} savedFlash={savedFlash} />
    </div>
  );
}

// ============================================================
// TAB: ACHTERGROND — NAW + contact + bank
// ============================================================
function AchtergrondTab({ profile, updateField, onSave, saving, savedFlash }) {
  return (
    <div className="space-y-4">
      <Card title="Identiteit" accent="#10b981" icon={User}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField label="Volledige Naam" value={profile.volledige_naam || ''}
            placeholder="Voor- en achternaam" onChange={v => updateField('volledige_naam', v)} />
          <InputField label="Roepnaam" value={profile.roepnaam || ''}
            placeholder="" onChange={v => updateField('roepnaam', v)} />
          <InputField label="Geboortedatum" value={profile.geboortedatum || ''}
            placeholder="DD-MM-JJJJ" onChange={v => updateField('geboortedatum', v)} />
          <InputField label="Geboorteplaats" value={profile.geboorteplaats || ''}
            placeholder="Stad" onChange={v => updateField('geboorteplaats', v)} />
          <InputField label="Nationaliteit" value={profile.nationaliteit || ''}
            placeholder="Nederlands" onChange={v => updateField('nationaliteit', v)} />
          <InputField label="Burgerlijke Staat" value={profile.burgerlijke_staat || ''}
            placeholder="Alleenstaand, gehuwd, ..." onChange={v => updateField('burgerlijke_staat', v)} />
        </div>
      </Card>

      <Card title="Contact" accent="#06b6d4" icon={MessageSquare}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField label="E-mail" value={profile.email || ''}
            placeholder="email@voorbeeld.nl" onChange={v => updateField('email', v)} />
          <InputField label="Telefoon" value={profile.telefoon || ''}
            placeholder="+31 6 ..." onChange={v => updateField('telefoon', v)} />
        </div>
      </Card>

      <Card title="Adres" accent="#f59e0b" icon={MapPin}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField label="Straat + Nr" value={profile.straat || ''}
            placeholder="Straatnaam 1" onChange={v => updateField('straat', v)} />
          <InputField label="Postcode" value={profile.postcode || ''}
            placeholder="1234 AB" onChange={v => updateField('postcode', v)} />
          <InputField label="Plaats" value={profile.plaats || ''}
            placeholder="Amsterdam" onChange={v => updateField('plaats', v)} />
          <InputField label="Land" value={profile.land || ''}
            placeholder="Nederland" onChange={v => updateField('land', v)} />
        </div>
      </Card>

      <Card title="Noodcontact" accent="#ef4444" icon={AlertTriangle}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField label="Naam" value={profile.noodcontact_naam || ''}
            placeholder="Contactpersoon" onChange={v => updateField('noodcontact_naam', v)} />
          <InputField label="Telefoon" value={profile.noodcontact_telefoon || ''}
            placeholder="+31 6 ..." onChange={v => updateField('noodcontact_telefoon', v)} />
        </div>
      </Card>

      <Card title="Bankgegevens" accent="#22c55e" icon={Globe}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <InputField label="IBAN" value={profile.iban || ''}
            placeholder="NL00 BANK 0000 0000 00" onChange={v => updateField('iban', v)} />
          <InputField label="Bank" value={profile.bank_provider || ''}
            placeholder="ING, Rabobank, ABN..." onChange={v => updateField('bank_provider', v)} />
        </div>
      </Card>

      <SaveBar onSave={onSave} saving={saving} savedFlash={savedFlash} />
    </div>
  );
}

// ============================================================
// TAB: PERSOONLIJKHEID — sliders + shadow info
// ============================================================
function PersoonlijkheidTab({ persona, setPersona, onSave, saving, savedFlash }) {
  const sliders = [
    ['introvert_extravert', 'Introvert', 'Extravert'],
    ['analytisch_creatief', 'Analytisch', 'Creatief'],
    ['planmatig_spontaan', 'Planmatig', 'Spontaan'],
    ['rationeel_emotioneel', 'Rationeel', 'Emotioneel'],
    ['traditioneel_vernieuwend', 'Traditioneel', 'Vernieuwend'],
    ['zelfstandig_teamspeler', 'Zelfstandig', 'Teamspeler'],
  ];

  return (
    <div className="space-y-4">
      <Card title="Persoonlijkheid" accent="#a855f7" icon={Brain}
        subtitle="Stel zelf in — Spark stelt later bij op basis van wat hij leert">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
          {sliders.map(([key, left, right]) => (
            <Slider key={key} left={left} right={right}
              value={persona[key]}
              onChange={v => setPersona({ ...persona, [key]: v })} />
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Doelen, Behoeften & Verlangens" accent="#22c55e" icon={Target}
          subtitle="Wat wil je bereiken — vrij in te vullen">
          <ListInputs storageKey="doelen" rows={3} placeholder="Wat wil je bereiken?" />
          <div className="h-2" />
          <ListInputs storageKey="behoeften" rows={3} placeholder="Wat heb je nodig?" label="Behoeften" />
          <div className="h-2" />
          <ListInputs storageKey="verlangens" rows={3} placeholder="Waar verlang je naar?" label="Verlangens" />
        </Card>

        <Card title="Pijn & Angst" accent="#ef4444" icon={AlertTriangle}
          subtitle="Spark observeert dit — vul niets in tenzij je het zelf wilt delen">
          <div className="rounded-lg bg-slate-900/60 border border-red-500/20 p-3 text-xs text-slate-400 leading-relaxed">
            <Sparkles className="w-3 h-3 text-red-400 inline mr-1" />
            Spark houdt dit voor zichzelf bij in een shadow-profiel. Wat hier verschijnt is wat Spark in gesprekken merkt.
            Je hoeft dit niet zelf in te vullen.
          </div>
          <p className="text-[10px] text-slate-600 mt-3 italic">Coming soon: shadow-inzichten lezen</p>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card title="Hoe je je laat leiden" accent="#06b6d4" icon={Eye}>
          <ListInputs storageKey="hoort" rows={2} placeholder="Wat hoor je vaak?" label="Hoort" iconEl={Ear} />
          <div className="h-2" />
          <ListInputs storageKey="ziet" rows={2} placeholder="Wat zie je?" label="Ziet" iconEl={Eye} />
          <div className="h-2" />
          <ListInputs storageKey="voelt" rows={2} placeholder="Wat voel je?" label="Voelt" iconEl={Heart} />
        </Card>

        <Card title="Mediagedrag & Communicatie" accent="#3b82f6" icon={Globe}>
          <ListInputs storageKey="mediagedrag" rows={2} placeholder="Welke platforms gebruik je?" label="Platforms" />
          <div className="h-2" />
          <ListInputs storageKey="communicatie" rows={2} placeholder="Hoe communiceer je het liefst?" label="Stijl" />
          <div className="h-2" />
          <ListInputs storageKey="invloeden" rows={2} placeholder="Wie volg je / inspireert je?" label="Invloeden" />
        </Card>
      </div>

      <SaveBar onSave={onSave} saving={saving} savedFlash={savedFlash} />
    </div>
  );
}

// ============================================================
// TAB: GESPREKKEN — eigen chat-history per jaar/maand/dag
// ============================================================
function GesprekkenTab({ userId }) {
  const [tree, setTree] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [openYears, setOpenYears] = useState({});
  const [openMonths, setOpenMonths] = useState({});
  const [openDays, setOpenDays] = useState({});

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/profile/chat-history/${userId}?limit=1000`)
      .then(r => r.json())
      .then(d => {
        setTree(d.years || []);
        setTotal(d.total || 0);
        // open meest recente jaar/maand standaard
        if (d.years?.[0]) {
          setOpenYears({ [d.years[0].year]: true });
          if (d.years[0].months?.[0]) {
            setOpenMonths({ [`${d.years[0].year}-${d.years[0].months[0].month}`]: true });
          }
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [userId]);

  const monthName = m => ['', 'januari', 'februari', 'maart', 'april', 'mei', 'juni',
    'juli', 'augustus', 'september', 'oktober', 'november', 'december'][parseInt(m, 10)] || m;

  if (loading) return <div className="text-center text-slate-500 py-12">Gesprekken laden...</div>;

  return (
    <div className="space-y-3">
      <Card title="Jouw gesprekken met Spark" accent="#3b82f6" icon={MessageSquare}
        subtitle={`${total} gesprek-item${total === 1 ? '' : 's'} · gesorteerd nieuwste eerst`}>
        {tree.length === 0 && (
          <p data-testid="no-chats" className="text-center text-slate-500 py-8">Nog geen gesprekken opgenomen.</p>
        )}
        {tree.map(y => {
          const yOpen = openYears[y.year];
          return (
            <div key={y.year} className="mb-2">
              <button
                data-testid={`year-${y.year}`}
                onClick={() => setOpenYears({ ...openYears, [y.year]: !yOpen })}
                className="w-full flex items-center gap-2 px-3 py-2 bg-slate-800/60 hover:bg-slate-800 rounded-lg text-left">
                {yOpen ? <ChevronDown className="w-4 h-4 text-blue-400" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                <Calendar className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-sm font-bold text-white">{y.year}</span>
                <span className="text-xs text-slate-500 ml-auto">{y.count} gesprek{y.count === 1 ? '' : 'ken'}</span>
              </button>
              {yOpen && (
                <div className="ml-4 mt-1">
                  {y.months.map(m => {
                    const mKey = `${y.year}-${m.month}`;
                    const mOpen = openMonths[mKey];
                    return (
                      <div key={m.month} className="mb-1">
                        <button
                          onClick={() => setOpenMonths({ ...openMonths, [mKey]: !mOpen })}
                          className="w-full flex items-center gap-2 px-3 py-1.5 hover:bg-slate-800/40 rounded text-left">
                          {mOpen ? <ChevronDown className="w-3 h-3 text-slate-400" /> : <ChevronRight className="w-3 h-3 text-slate-500" />}
                          <span className="text-xs text-slate-300 capitalize">{monthName(m.month)}</span>
                          <span className="text-[10px] text-slate-600 ml-auto">{m.count}</span>
                        </button>
                        {mOpen && (
                          <div className="ml-4 mt-1 space-y-1">
                            {m.days.map(d => {
                              const dKey = `${mKey}-${d.day}`;
                              const dOpen = openDays[dKey];
                              return (
                                <div key={d.day}>
                                  <button
                                    onClick={() => setOpenDays({ ...openDays, [dKey]: !dOpen })}
                                    className="w-full flex items-center gap-2 px-3 py-1 hover:bg-slate-800/30 rounded text-left">
                                    {dOpen ? <ChevronDown className="w-3 h-3 text-slate-500" /> : <ChevronRight className="w-3 h-3 text-slate-600" />}
                                    <span className="text-[11px] text-slate-400">{d.day} {monthName(m.month)}</span>
                                    <span className="text-[10px] text-slate-700 ml-auto">{d.count}</span>
                                  </button>
                                  {dOpen && (
                                    <div className="ml-5 mt-1 space-y-2 pb-2">
                                      {d.items.map(it => (
                                        <div key={it.id} className="bg-slate-900/60 border border-slate-800 rounded-lg p-2.5">
                                          <div className="text-[10px] text-slate-600 mb-1">{it.time}</div>
                                          {it.user_message && (
                                            <div className="text-xs text-slate-300 mb-1.5">
                                              <span className="text-amber-400 font-semibold">Jij:</span> {it.user_message}
                                            </div>
                                          )}
                                          {it.spark_response && (
                                            <div className="text-xs text-slate-400 whitespace-pre-wrap">
                                              <span className="text-cyan-400 font-semibold">Spark:</span> {it.spark_response}
                                            </div>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </Card>
    </div>
  );
}

// ============================================================
// TAB: AVATAR — galerij + upload
// ============================================================
function AvatarTab({ userId, isAdmin }) {
  const [gallery, setGallery] = useState([]);
  const [current, setCurrent] = useState({ avatar_ref: null, url: null });
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState(null);
  const fileRef = useRef(null);
  const [hasUserPortrait, setHasUserPortrait] = useState(false);

  const loadGallery = useCallback(() => {
    fetch(`${API}/api/avatar/gallery`)
      .then(r => r.json()).then(d => setGallery(d.avatars || []));
  }, []);
  const loadCurrent = useCallback(() => {
    fetch(`${API}/api/avatar/current/${userId}`).then(r => r.json()).then(d => {
      setCurrent(d);
      setHasUserPortrait(d.avatar_ref === 'user');
    });
  }, [userId]);

  useEffect(() => { loadGallery(); loadCurrent(); }, [loadGallery, loadCurrent]);

  const flash = (type, text) => { setMsg({ type, text }); setTimeout(() => setMsg(null), 2500); };

  const selectAvatar = async ref => {
    const r = await fetch(`${API}/api/avatar/select/${userId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ avatar_ref: ref }),
    });
    if (r.ok) { flash('ok', 'Avatar ingesteld'); loadCurrent(); }
    else flash('err', 'Instellen mislukt');
  };

  const uploadPortrait = async file => {
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const r = await fetch(`${API}/api/avatar/user/${userId}`, { method: 'POST', body: fd });
      const d = await r.json();
      if (r.ok && d.success) { flash('ok', `Geüpload (${d.width}×${d.height})`); loadCurrent(); }
      else flash('err', d.detail || 'Upload mislukt');
    } catch (e) { flash('err', e.message); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ''; }
  };

  return (
    <div className="space-y-4">
      {/* v4_inventory_001 — Persoonskaart (Stats + Inventory) */}
      <PersoonskaartCard userId={userId} isAdmin={isAdmin} />

      <Card title="Huidige Avatar" accent="#ec4899" icon={Camera}>
        <div className="flex items-center gap-5">
          <div className="w-28 h-28 rounded-2xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center overflow-hidden flex-shrink-0">
            {current.url ? (
              <img src={`${API}${current.url}?t=${Date.now()}`} alt="" className="w-full h-full object-cover" />
            ) : (
              <User className="w-14 h-14 text-white" />
            )}
          </div>
          <div className="flex-1">
            <p className="text-sm text-white font-medium">
              {current.avatar_ref === 'user' ? 'Eigen portret' :
                current.avatar_ref?.startsWith('gallery:') ? 'Uit galerij' : 'Standaard (initialen)'}
            </p>
            <p className="text-xs text-slate-500 mt-1">Foto's worden geschaald naar max 512×512 om opslag te besparen.</p>
            {current.avatar_ref && (
              <button data-testid="clear-avatar" onClick={() => selectAvatar(null)}
                className="mt-3 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center gap-1.5">
                <X className="w-3 h-3" /> Verwijder selectie
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* Upload eigen */}
      <Card title="Eigen Portret Uploaden" accent="#22c55e" icon={Upload}
        subtitle="Wordt alleen voor jouw profiel gebruikt (niet in algemeen archief)">
        <input data-testid="portrait-upload" ref={fileRef} type="file" accept="image/*"
          onChange={e => uploadPortrait(e.target.files?.[0])} className="hidden" />
        <div className="flex flex-wrap gap-3">
          <button onClick={() => fileRef.current?.click()} disabled={uploading}
            data-testid="upload-portrait-btn"
            className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/40 rounded-lg flex items-center gap-2 text-sm disabled:opacity-50">
            <Upload className="w-4 h-4" />
            {uploading ? 'Uploaden...' : 'Kies een foto'}
          </button>
          {hasUserPortrait && (
            <button onClick={() => selectAvatar('user')}
              className="px-4 py-2 bg-pink-500/20 hover:bg-pink-500/30 text-pink-400 border border-pink-500/40 rounded-lg flex items-center gap-2 text-sm">
              <Check className="w-4 h-4" /> Gebruik mijn portret
            </button>
          )}
        </div>
        {msg && (
          <p className={`mt-3 text-xs ${msg.type === 'ok' ? 'text-green-400' : 'text-red-400'}`}>{msg.text}</p>
        )}
      </Card>

      {/* Galerij — v4_avatar_categories_001 — 2 tabs (Persoonlijk / D&D Archief) */}
      <Card title={`Galerij (${gallery.length})`} accent="#a855f7" icon={ImageIcon}
        subtitle="Voorbeeld-avatars beheerd door het systeem. Kies er één om als jouw avatar in te stellen.">
        <GalleryTabs gallery={gallery} current={current} onSelect={selectAvatar} apiUrl={API} />
        {isAdmin && (
          <p className="text-[10px] text-amber-400/70 mt-4 italic">
            Beheer galerij via: Beheer → Gebruikers → kies user → Avatar Beheer
          </p>
        )}
      </Card>
    </div>
  );
}

// v4_avatar_categories_001 — Tabs voor User vs D&D Archief
function GalleryTabs({ gallery, current, onSelect, apiUrl }) {
  const [tab, setTab] = useState('user');
  const userAvatars = gallery.filter(a => (a.category || (a.locked ? 'system' : 'user')) === 'user');
  const dndAvatars = gallery.filter(a => a.category === 'dnd');
  const lockedCount = dndAvatars.filter(a => a.locked).length;
  const list = tab === 'user' ? userAvatars : dndAvatars;
  return (
    <>
      <div className="flex items-center gap-1 mb-3 p-1 bg-slate-800/40 rounded-lg w-fit">
        <button data-testid="gallery-tab-user" onClick={() => setTab('user')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            tab === 'user' ? 'bg-pink-500/20 text-pink-300' : 'text-slate-400 hover:text-slate-200'
          }`}>
          Persoonlijk <span className="opacity-60">({userAvatars.length})</span>
        </button>
        <button data-testid="gallery-tab-dnd" onClick={() => setTab('dnd')}
          className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
            tab === 'dnd' ? 'bg-amber-500/20 text-amber-300' : 'text-slate-400 hover:text-slate-200'
          }`}>
          D&D Archief <span className="opacity-60">({dndAvatars.length}{lockedCount > 0 ? ` · ${lockedCount} 🔒` : ''})</span>
        </button>
      </div>
      {tab === 'dnd' && (
        <div className="mb-3 px-3 py-2 bg-amber-500/5 border border-amber-500/20 rounded-lg">
          <p className="text-[11px] text-amber-300/90">
            🎒 D&D-avatars zijn onderdeel van de Spark World D&D-laag. Sommige zijn gereserveerd voor specifieke bots/Spark — die unlock je via XP, achievements of tokens.
          </p>
        </div>
      )}
      {list.length === 0 ? (
        <p className="text-center text-slate-500 py-6 text-sm">
          {tab === 'dnd' ? 'Nog geen D&D-avatars in archief. Admin kan via gallery-edit een avatar verplaatsen naar D&D.' : 'Nog geen persoonlijke avatars beschikbaar.'}
        </p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {list.map(a => {
            const isSel = current.avatar_ref === `gallery:${a.id}`;
            const owner = a.bot_owner;
            return (
              <button key={a.id} data-testid={`gallery-${a.id}`}
                onClick={() => onSelect(`gallery:${a.id}`)}
                className={`group relative rounded-xl overflow-hidden border-2 transition-all ${
                  isSel ? 'border-pink-500 ring-2 ring-pink-500/40' : 'border-slate-800 hover:border-slate-600'
                }`}
                title={a.locked ? `Gereserveerd voor ${owner}` : a.title}>
                <img src={`${apiUrl}/api/avatar/gallery/${a.id}/image`} alt={a.title}
                  className={`w-full aspect-square object-cover ${a.locked ? 'opacity-50' : ''}`} />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-2">
                  <p className="text-[11px] text-white font-medium truncate">{a.title}</p>
                </div>
                {isSel && (
                  <div className="absolute top-1.5 right-1.5 w-6 h-6 bg-pink-500 rounded-full flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 text-white" />
                  </div>
                )}
                {a.locked && !isSel && (
                  <div className="absolute top-1.5 right-1.5 w-6 h-6 bg-amber-500/90 rounded-full flex items-center justify-center text-[12px]">
                    🔒
                  </div>
                )}
              </button>
            );
          })}
        </div>
      )}
    </>
  );
}

// ============================================================
// HERBRUIKBARE BOUWSTENEN
// ============================================================
function Card({ title, subtitle, accent = '#f59e0b', icon: Icon, children }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
        {Icon && <div className="w-7 h-7 rounded-lg flex items-center justify-center"
          style={{ background: `${accent}22` }}>
          <Icon className="w-3.5 h-3.5" style={{ color: accent }} />
        </div>}
        <div className="flex-1">
          <h3 className="text-sm font-bold text-white">{title}</h3>
          {subtitle && <p className="text-[10px] text-slate-500">{subtitle}</p>}
        </div>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function InputField({ label, value, placeholder, disabled, onChange }) {
  return (
    <div>
      <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">{label}</label>
      <input
        type="text" value={value || ''} placeholder={placeholder} disabled={disabled}
        onChange={e => onChange?.(e.target.value)}
        data-testid={`input-${label.toLowerCase().replace(/[^a-z0-9]/g, '-')}`}
        className={`w-full px-3 py-2 bg-slate-800/60 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-600 focus:border-amber-500 focus:outline-none ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      />
    </div>
  );
}

function Slider({ left, right, value, onChange }) {
  return (
    <div>
      <div className="flex justify-between text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider">
        <span>{left}</span><span>{right}</span>
      </div>
      <div className="relative h-7">
        <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-1.5 bg-slate-800 rounded-full" />
        <div className="absolute left-0 top-1/2 -translate-y-1/2 h-1.5 rounded-full bg-gradient-to-r from-amber-500 to-orange-500"
          style={{ width: `${value}%` }} />
        <input type="range" min="0" max="100" value={value}
          onChange={e => onChange(parseInt(e.target.value, 10))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer" />
        <div className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-purple-500"
          style={{ left: `calc(${value}% - 8px)` }} />
      </div>
    </div>
  );
}

function ListInputs({ storageKey, label, placeholder, rows = 3, iconEl: IconEl }) {
  const [items, setItems] = useState(Array(rows).fill(''));
  const update = (i, v) => { const c = [...items]; c[i] = v; setItems(c); };
  return (
    <div>
      {label && (
        <div className="flex items-center gap-1.5 mb-1.5">
          {IconEl && <IconEl className="w-3 h-3 text-slate-400" />}
          <span className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">{label}</span>
        </div>
      )}
      <div className="space-y-1">
        {items.map((v, i) => (
          <input key={i} type="text" value={v} placeholder={placeholder}
            onChange={e => update(i, e.target.value)}
            data-testid={`list-${storageKey}-${i}`}
            className="w-full px-2.5 py-1.5 bg-slate-800/40 border border-slate-700/50 rounded text-xs text-slate-300 placeholder-slate-600 focus:border-amber-500/60 focus:outline-none" />
        ))}
      </div>
    </div>
  );
}

function SaveBar({ onSave, saving, savedFlash }) {
  return (
    <div className="sticky bottom-0 -mx-4 md:-mx-6 px-4 md:px-6 py-3 bg-slate-950/95 backdrop-blur border-t border-slate-800 flex items-center justify-between">
      <p className="text-xs text-slate-500">Wijzigingen blijven lokaal opgeslagen.</p>
      <button onClick={onSave} disabled={saving}
        data-testid="profile-save"
        className="px-5 py-2 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white text-sm font-medium rounded-lg flex items-center gap-2 disabled:opacity-50">
        {savedFlash ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
        {saving ? 'Opslaan...' : (savedFlash ? 'Opgeslagen' : 'Opslaan')}
      </button>
    </div>
  );
}

export default UserProfilePage;

// ============================================================
// v4_inventory_001 — Persoonskaart (Stats + Inventory)
// ============================================================
function PersoonskaartCard({ userId, isAdmin }) {
  const [inv, setInv] = useState(null);
  const [aura, setAura] = useState(null);
  const [catalog, setCatalog] = useState([]);
  const [busy, setBusy] = useState(false);
  const [showShop, setShowShop] = useState(false);
  const [err, setErr] = useState(null);

  const reload = useCallback(() => {
    fetch(`${API}/api/inventory/${userId}`).then(r => r.json()).then(setInv).catch(() => {});
    fetch(`${API}/api/dnd/aura/${userId}`).then(r => r.json()).then(setAura).catch(() => {});
  }, [userId]);
  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    fetch(`${API}/api/inventory/catalog/all`).then(r => r.json()).then(d => setCatalog(d.items || []));
  }, []);

  const addItem = async (itemId) => {
    setBusy(true); setErr(null);
    try {
      const r = await fetch(`${API}/api/inventory/${userId}/items`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_id: itemId, source: 'shop' }),
      });
      const d = await r.json();
      if (r.ok) { setInv(d); setShowShop(false); }
      else setErr(d.detail || 'Toevoegen mislukt');
    } finally { setBusy(false); }
  };

  const removeItem = async (slotId) => {
    if (!isAdmin) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/inventory/${userId}/items/${slotId}`, { method: 'DELETE' });
      if (r.ok) setInv(await r.json());
    } finally { setBusy(false); }
  };

  if (!inv) {
    return (
      <Card title="Persoonskaart" accent="#a855f7" icon={Award}>
        <p className="text-slate-500 text-sm">Laden…</p>
      </Card>
    );
  }

  const s = inv.stats || {};
  const c = inv.capacity || {};
  const slotsPct = c.slots_total ? Math.round(100 * c.slots_used / c.slots_total) : 0;
  const weightPct = c.weight_max ? Math.round(100 * c.weight_used / c.weight_max) : 0;
  const ownedIds = (inv.slots || []).map(sl => sl.item_id);
  const availableInShop = catalog.filter(it => !ownedIds.includes(it.id) || it.kind !== 'carry');

  return (
    <Card title="Persoonskaart" accent="#a855f7" icon={Award}>
      {/* v4_dnd_001 — Aura/Glow visualisatie */}
      {aura && aura.total_events > 0 && (
        <div data-testid="aura-section" className="mb-4 p-3 rounded-xl border relative overflow-hidden"
          style={{ background: `linear-gradient(135deg, ${aura.primary_color}15, transparent)`, borderColor: `${aura.primary_color}40` }}>
          {/* Particles laag */}
          <div className="pointer-events-none absolute inset-0 opacity-40">
            {[...Array(8)].map((_, i) => (
              <span key={i} className="absolute rounded-full"
                style={{
                  width: `${4 + (i % 3) * 2}px`,
                  height: `${4 + (i % 3) * 2}px`,
                  background: aura.layers[i % aura.layers.length]?.color || aura.primary_color,
                  left: `${(i * 13 + 7) % 95}%`,
                  top: `${(i * 17 + 11) % 80}%`,
                  animation: `aura-float-${i % 3} ${3 + (i % 4)}s ease-in-out infinite`,
                  filter: 'blur(0.5px)',
                }} />
            ))}
          </div>
          <div className="flex items-center gap-3 relative">
            <div className="relative">
              <div className="w-12 h-12 rounded-full flex items-center justify-center"
                style={{ background: `radial-gradient(circle, ${aura.primary_color}80, ${aura.primary_color}20)`, boxShadow: `0 0 24px ${aura.primary_color}80` }}>
                <Sparkles className="w-5 h-5 text-white" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[9px] uppercase tracking-wider text-slate-500">Aura — gedrag → identiteit</p>
              <p className="text-sm font-bold text-white">{aura.layers[0].label}</p>
              <div className="flex items-center gap-1 mt-1">
                {aura.layers.map(l => (
                  <span key={l.category} className="h-1.5 rounded-full" style={{ background: l.color, width: `${Math.max(l.ratio * 80, 6)}px` }} title={`${l.label}: ${Math.round(l.ratio * 100)}%`} />
                ))}
                <span className="text-[10px] text-slate-500 ml-2">{aura.total_events} events</span>
              </div>
            </div>
          </div>
          {aura.unlocks?.length > 0 && (
            <div className="mt-2 pt-2 border-t border-slate-800/50 relative">
              <p className="text-[10px] text-slate-500 mb-1">Unlocks (top categorie):</p>
              <div className="flex flex-wrap gap-1">
                {aura.unlocks.map(u => (
                  <span key={u} className="text-[10px] px-1.5 py-0.5 rounded-full"
                    style={{ background: `${aura.primary_color}20`, color: aura.primary_color }}>{u}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
        <StatTile label="Rang" value={s.rang || '—'} />
        <StatTile label="Level" value={s.level ?? 0} sub={`${s.xp ?? 0} XP`} />
        <StatTile label="Gradatie" value={s.gradatie ?? 7} />
        <StatTile label="Trust" value={s.trust ?? 0} />
      </div>

      {/* Capacity bars */}
      <div className="space-y-3 mb-4 p-3 bg-slate-900/40 rounded-xl border border-slate-800/60">
        <div>
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Backpack className="w-3 h-3" /> Slots
            </span>
            <span data-testid="inv-slots" className="text-slate-300 font-mono">{c.slots_used} / {c.slots_total}</span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded overflow-hidden">
            <div className={`h-full transition-all ${slotsPct >= 90 ? 'bg-red-500' : slotsPct >= 70 ? 'bg-amber-500' : 'bg-emerald-500'}`}
              style={{ width: `${Math.min(100, slotsPct)}%` }} />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-[11px] mb-1">
            <span className="text-slate-400">Gewicht</span>
            <span data-testid="inv-weight" className="text-slate-300 font-mono">{c.weight_used} / {c.weight_max} kg</span>
          </div>
          <div className="h-1.5 bg-slate-800 rounded overflow-hidden">
            <div className={`h-full transition-all ${weightPct >= 90 ? 'bg-red-500' : weightPct >= 70 ? 'bg-amber-500' : 'bg-cyan-500'}`}
              style={{ width: `${Math.min(100, weightPct)}%` }} />
          </div>
        </div>
      </div>

      {/* Inventory slots */}
      <div className="space-y-2 mb-3">
        <p className="text-[10px] uppercase tracking-wider text-slate-500">Items ({inv.slots?.length || 0})</p>
        {(inv.slots || []).length === 0 ? (
          <p className="text-xs text-slate-500 italic">Nog geen items.</p>
        ) : (
          <div className="space-y-1.5">
            {inv.slots.map(slot => (
              <div key={slot.id} data-testid={`inv-slot-${slot.id}`}
                className="flex items-center gap-3 p-2.5 bg-slate-800/40 hover:bg-slate-800/60 border border-slate-800/60 rounded-lg transition-colors">
                <div className="text-2xl">{slot.icon || '📦'}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-white truncate">{slot.naam}</p>
                    {slot.rarity && slot.rarity !== 'common' && (
                      <span className="text-[9px] px-1 py-0.5 rounded bg-amber-500/15 text-amber-300 uppercase">{slot.rarity}</span>
                    )}
                  </div>
                  <p className="text-[10px] text-slate-500 truncate">
                    {slot.weight}kg
                    {slot.capacity_bonus ? ` · +${slot.capacity_bonus} slots` : ''}
                    {slot.weight_bonus ? ` · +${slot.weight_bonus}kg` : ''}
                  </p>
                </div>
                {isAdmin && (
                  <button data-testid={`inv-remove-${slot.id}`} onClick={() => removeItem(slot.id)} disabled={busy}
                    className="p-1.5 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Achievements */}
      {(s.achievements || []).length > 0 && (
        <div className="mb-3">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Achievements</p>
          <div className="flex flex-wrap gap-1.5">
            {s.achievements.map(a => (
              <span key={a.code} data-testid={`achievement-${a.code}`}
                className="text-[10px] px-2 py-1 bg-amber-500/10 border border-amber-500/30 text-amber-300 rounded-full">
                🏅 {a.naam || a.code}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Shop */}
      <div className="pt-3 border-t border-slate-800">
        <button onClick={() => setShowShop(s => !s)}
          data-testid="inv-toggle-shop"
          className="w-full px-3 py-2 bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 rounded-lg text-xs font-medium transition-colors flex items-center justify-center gap-1.5">
          <Plus className="w-3.5 h-3.5" /> {showShop ? 'Sluit catalogus' : 'Voeg item toe (catalogus)'}
        </button>
        {err && <p className="mt-2 text-xs text-red-400">{err}</p>}
        {showShop && (
          <div className="mt-2 space-y-1.5 p-2 bg-slate-800/30 rounded-lg max-h-48 overflow-y-auto">
            {availableInShop.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-3">Geen items beschikbaar (alle carry-items zijn al gepakt).</p>
            ) : availableInShop.map(it => (
              <button key={it.id} onClick={() => addItem(it.id)} disabled={busy}
                data-testid={`shop-add-${it.id}`}
                className="w-full flex items-center gap-2 p-2 hover:bg-slate-800/60 rounded text-left transition-colors">
                <span className="text-lg">{it.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-white truncate">{it.naam}</p>
                  <p className="text-[9px] text-slate-500 truncate">{it.description}</p>
                </div>
                <Plus className="w-3 h-3 text-slate-500 group-hover:text-amber-400" />
              </button>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

function StatTile({ label, value, sub }) {
  return (
    <div className="bg-slate-800/40 border border-slate-800/60 rounded-lg p-2.5">
      <p className="text-[9px] uppercase tracking-wider text-slate-500">{label}</p>
      <p className="text-sm font-bold text-white truncate">{value}</p>
      {sub && <p className="text-[9px] text-slate-500">{sub}</p>}
    </div>
  );
}

// ============================================================
// TAB: INSTELLINGEN (v5_ui_prefs_001)
// Beeld (glow base color) — Geluid (placeholder) — Connecties (Bitvavo)
// ============================================================
const GLOW_PRESETS = [
  { hex: '#f59e0b', label: 'Amber',   note: 'Standaard Spark' },
  { hex: '#06b6d4', label: 'Cyan',    note: 'Rustig / Kalm' },
  { hex: '#a855f7', label: 'Violet',  note: 'Mystiek' },
  { hex: '#10b981', label: 'Emerald', note: 'Groei' },
  { hex: '#ec4899', label: 'Roze',    note: 'Warm' },
  { hex: '#ef4444', label: 'Rood',    note: 'Alert' },
  { hex: '#eab308', label: 'Goud',    note: 'Trots' },
  { hex: '#3b82f6', label: 'Blauw',   note: 'Helder' },
];

function InstellingenTab({ userId }) {
  const [prefs, setPrefs] = useState(null);
  const [saving, setSaving] = useState(false);
  const [bvStatus, setBvStatus] = useState(null);
  const [savedFlash, setSavedFlash] = useState(false);

  useEffect(() => {
    fetch(`${API}/api/profile/ui-preferences/${userId}`)
      .then(r => r.json())
      .then(d => setPrefs(d.preferences || null))
      .catch(() => setPrefs({ glow_base_color: '#f59e0b', sound_enabled: true, auto_bark_enabled: false }));
    fetch(`${API}/api/trade/bitvavo/status/${userId}`)
      .then(r => r.json())
      .then(d => setBvStatus(d))
      .catch(() => setBvStatus({ connected: false }));
  }, [userId]);

  const updatePref = (key, val) => {
    setPrefs(p => ({ ...(p || {}), [key]: val }));
  };

  const savePrefs = async (overrides = {}) => {
    setSaving(true);
    try {
      const payload = { ...(prefs || {}), ...overrides };
      const res = await fetch(`${API}/api/profile/ui-preferences/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }).then(r => r.json());
      if (res.success) {
        setPrefs(res.preferences);
        // Live-apply naar root: CSS variable
        if (res.preferences?.glow_base_color) {
          document.documentElement.style.setProperty('--glow-base', res.preferences.glow_base_color);
        }
        setSavedFlash(true);
        setTimeout(() => setSavedFlash(false), 1800);
      }
    } finally {
      setSaving(false);
    }
  };

  const pickColor = (hex) => {
    updatePref('glow_base_color', hex);
    // Live preview
    document.documentElement.style.setProperty('--glow-base', hex);
    savePrefs({ glow_base_color: hex });
  };

  if (!prefs) {
    return <div className="bg-slate-900 border border-slate-800 rounded-xl p-4"><p className="text-xs text-slate-500">Voorkeuren laden…</p></div>;
  }

  const currentColor = prefs.glow_base_color || '#f59e0b';

  // Lokale paneel-wrapper (de bestaande `Card` verwacht title/icon props; wij gebruiken kale wrapper)
  const Panel = ({ children }) => (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">{children}</div>
  );

  return (
    <div data-testid="instellingen-tab" className="space-y-4">
      {/* Header info */}
      <Panel>
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
            <Settings className="w-4 h-4 text-cyan-400" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white">Persoonlijke instellingen</h2>
            <p className="text-[10px] text-slate-500">Account · Beeld · Geluid · Connecties — geldt alleen voor jouw account</p>
          </div>
          {savedFlash && (
            <span className="ml-auto text-[10px] text-emerald-400 flex items-center gap-1">
              <Check className="w-3 h-3" /> Opgeslagen
            </span>
          )}
        </div>
      </Panel>

      {/* === ACCOUNT === */}
      <AccountSection userId={userId} />

      {/* === BEELD === */}
      <Panel>
        <div className="flex items-center gap-2 mb-3">
          <Palette className="w-4 h-4 text-amber-400" />
          <h3 className="text-sm font-semibold text-white">Beeld — Glow basiskleur</h3>
        </div>
        <p className="text-[11px] text-slate-400 mb-3">
          Kies de basiskleur voor je gloed-effecten in de app. Later worden hier kleurverlopen op
          basis van humeur toegevoegd (rustig → kalme tint, alert → fellere tint).
        </p>

        {/* Preview ring */}
        <div className="flex items-center gap-3 mb-4">
          <div
            data-testid="glow-preview"
            className="w-14 h-14 rounded-2xl flex items-center justify-center transition-all"
            style={{
              background: `${currentColor}1a`,
              border: `1px solid ${currentColor}80`,
              boxShadow: `0 0 24px ${currentColor}66`,
            }}
          >
            <Sparkles className="w-6 h-6" style={{ color: currentColor }} />
          </div>
          <div>
            <p className="text-xs font-mono text-white" data-testid="glow-current-hex">{currentColor.toUpperCase()}</p>
            <p className="text-[10px] text-slate-500">Live voorbeeld — wijziging is direct actief</p>
          </div>
        </div>

        {/* Preset swatches */}
        <div className="grid grid-cols-4 sm:grid-cols-8 gap-2 mb-3" data-testid="glow-presets">
          {GLOW_PRESETS.map(p => {
            const active = currentColor.toLowerCase() === p.hex.toLowerCase();
            return (
              <button
                key={p.hex}
                data-testid={`glow-preset-${p.label.toLowerCase()}`}
                onClick={() => pickColor(p.hex)}
                disabled={saving}
                title={`${p.label} — ${p.note}`}
                className={`group aspect-square rounded-xl transition-all flex items-center justify-center ${active ? 'ring-2 ring-white/80 scale-105' : 'ring-1 ring-slate-700 hover:ring-slate-500'}`}
                style={{
                  background: `${p.hex}24`,
                  boxShadow: active ? `0 0 16px ${p.hex}80` : `0 0 4px ${p.hex}40`,
                }}
              >
                <span className="w-5 h-5 rounded-full" style={{ background: p.hex }} />
              </button>
            );
          })}
        </div>

        {/* Custom hex */}
        <div className="flex items-center gap-2">
          <label className="text-[11px] text-slate-400">Eigen hex:</label>
          <input
            type="color"
            data-testid="glow-color-picker"
            value={currentColor}
            onChange={e => updatePref('glow_base_color', e.target.value)}
            onBlur={() => savePrefs({})}
            className="w-10 h-8 rounded cursor-pointer bg-transparent border border-slate-700"
          />
          <input
            type="text"
            data-testid="glow-color-hex-input"
            value={currentColor}
            onChange={e => updatePref('glow_base_color', e.target.value)}
            onBlur={() => {
              const v = (prefs.glow_base_color || '').trim();
              if (/^#[0-9a-fA-F]{6}$/.test(v)) savePrefs({ glow_base_color: v });
            }}
            placeholder="#f59e0b"
            className="flex-1 max-w-[140px] px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs font-mono text-white"
          />
          <span className="text-[10px] text-slate-500">Toekomstig: kleurverloop op basis van humeur</span>
        </div>
      </Panel>

      {/* === GELUID === */}
      <Panel>
        <div className="flex items-center gap-2 mb-3">
          <Volume2 className="w-4 h-4 text-violet-400" />
          <h3 className="text-sm font-semibold text-white">Geluid</h3>
          <span className="text-[9px] uppercase tracking-wider text-slate-500 ml-auto">In ontwikkeling</span>
        </div>

        <div className="space-y-3">
          <label className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 cursor-pointer">
            <div>
              <p className="text-xs font-medium text-white">TTS — Spark spreekt antwoorden uit</p>
              <p className="text-[10px] text-slate-500">Stem-uitvoer in gesprekken</p>
            </div>
            <input
              type="checkbox"
              data-testid="toggle-tts"
              checked={prefs.tts_enabled !== false}
              onChange={e => { updatePref('tts_enabled', e.target.checked); savePrefs({ tts_enabled: e.target.checked }); }}
              className="w-4 h-4 accent-violet-500"
            />
          </label>

          <label className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 cursor-pointer">
            <div>
              <p className="text-xs font-medium text-white">Geluidseffecten</p>
              <p className="text-[10px] text-slate-500">UI-feedback geluiden (klik, notificatie)</p>
            </div>
            <input
              type="checkbox"
              data-testid="toggle-sound"
              checked={prefs.sound_enabled !== false}
              onChange={e => { updatePref('sound_enabled', e.target.checked); savePrefs({ sound_enabled: e.target.checked }); }}
              className="w-4 h-4 accent-violet-500"
            />
          </label>

          <label className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800 cursor-pointer opacity-60">
            <div>
              <p className="text-xs font-medium text-white">Auto-bark <span className="text-[10px] text-slate-500 ml-1">(binnenkort)</span></p>
              <p className="text-[10px] text-slate-500">Spark schiet uit eigen beweging een berichtje af</p>
            </div>
            <input
              type="checkbox"
              data-testid="toggle-autobark"
              checked={!!prefs.auto_bark_enabled}
              onChange={e => { updatePref('auto_bark_enabled', e.target.checked); savePrefs({ auto_bark_enabled: e.target.checked }); }}
              className="w-4 h-4 accent-violet-500"
            />
          </label>
        </div>
      </Panel>

      {/* === CONNECTIES === */}
      <Panel>
        <div className="flex items-center gap-2 mb-3">
          <Link2 className="w-4 h-4 text-emerald-400" />
          <h3 className="text-sm font-semibold text-white">Connecties</h3>
        </div>

        <div className="space-y-2">
          <div data-testid="conn-bitvavo" className="flex items-center justify-between gap-3 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 text-xs font-bold">BV</div>
              <div>
                <p className="text-xs font-medium text-white">Bitvavo trading</p>
                <p className="text-[10px] text-slate-500">
                  {bvStatus?.connected
                    ? `Verbonden ${bvStatus.connected_at ? '· ' + new Date(bvStatus.connected_at).toLocaleDateString('nl-NL') : ''}`
                    : bvStatus?.placeholder ? 'Test-key ingesteld' : 'Niet verbonden'}
                </p>
              </div>
            </div>
            <span
              className={`text-[10px] font-medium px-2 py-1 rounded-full ${bvStatus?.connected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-700 text-slate-400'}`}
              data-testid="conn-bitvavo-status"
            >
              {bvStatus?.connected ? 'Actief' : 'Inactief'}
            </span>
          </div>

          <p className="text-[10px] text-slate-500 italic px-1">
            Meer connecties (Google Agenda, Moneybird, Telegram) volgen later.
          </p>
        </div>
      </Panel>
    </div>
  );
}


// ============================================================
// AccountSection (v5_self_password_001) — eigen sleutelwoord wijzigen + reset
// ============================================================
function AccountSection({ userId }) {
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);

  const submitChange = async (newOverride) => {
    setMsg(null);
    if (!currentPw) {
      setMsg({ kind: 'err', text: 'Vul je huidige sleutelwoord in' });
      return;
    }
    const target = (newOverride ?? newPw).trim();
    if (!target) {
      setMsg({ kind: 'err', text: 'Vul een nieuw sleutelwoord in' });
      return;
    }
    setBusy(true);
    try {
      const res = await fetch(`${API}/api/auth/users/${userId}/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ current_sleutelwoord: currentPw, new_sleutelwoord: target }),
      }).then(r => r.json()).catch(() => ({ success: false, error: 'Verbindingsfout' }));
      if (res.success) {
        setMsg({ kind: 'ok', text: newOverride ? 'Gereset naar Welkom01' : 'Sleutelwoord gewijzigd' });
        setCurrentPw('');
        setNewPw('');
      } else {
        setMsg({ kind: 'err', text: res.error || 'Onbekende fout' });
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-testid="account-section" className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-3">
        <KeyRound className="w-4 h-4 text-rose-400" />
        <h3 className="text-sm font-semibold text-white">Account — Sleutelwoord</h3>
      </div>
      <p className="text-[11px] text-slate-400 mb-3">
        Wijzig je eigen sleutelwoord. Reset zet hem terug op <code className="text-rose-300 bg-rose-500/10 px-1 rounded">Welkom01</code> (standaard).
      </p>

      <div className="space-y-2.5 max-w-md">
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Huidig sleutelwoord</label>
          <div className="relative">
            <input
              type={showCurrent ? 'text' : 'password'}
              data-testid="pw-current"
              value={currentPw}
              onChange={e => setCurrentPw(e.target.value)}
              placeholder="•••••••"
              className="w-full px-3 py-2 pr-16 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-rose-500/50 outline-none"
            />
            <button type="button" data-testid="pw-current-toggle"
              onClick={() => setShowCurrent(v => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 hover:text-white px-1.5 py-0.5">
              {showCurrent ? 'verberg' : 'toon'}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Nieuw sleutelwoord</label>
          <div className="relative">
            <input
              type={showNew ? 'text' : 'password'}
              data-testid="pw-new"
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
              placeholder="minstens 4 tekens"
              className="w-full px-3 py-2 pr-16 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-rose-500/50 outline-none"
            />
            <button type="button" data-testid="pw-new-toggle"
              onClick={() => setShowNew(v => !v)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-slate-400 hover:text-white px-1.5 py-0.5">
              {showNew ? 'verberg' : 'toon'}
            </button>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            data-testid="pw-change-btn"
            onClick={() => submitChange()}
            disabled={busy || !currentPw || !newPw}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="w-3.5 h-3.5" /> Wijzig sleutelwoord
          </button>
          <button
            data-testid="pw-reset-btn"
            onClick={() => {
              if (window.confirm('Reset je sleutelwoord naar "Welkom01"?')) submitChange('Welkom01');
            }}
            disabled={busy || !currentPw}
            title={!currentPw ? 'Vul eerst je huidige sleutelwoord in' : 'Reset naar Welkom01'}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset naar Welkom01
          </button>

          {msg && (
            <span
              data-testid="pw-msg"
              className={`text-[11px] ml-auto px-2 py-1 rounded ${msg.kind === 'ok' ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'}`}
            >
              {msg.text}
            </span>
          )}
        </div>

        <p className="text-[10px] text-slate-500 pt-1">
          Tip: na een wijziging blijf je ingelogd op deze sessie. Bij volgende login gebruik je het nieuwe sleutelwoord.
        </p>
      </div>
    </div>
  );
}

