import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Brain, Heart, Shield, Sparkles, BookOpen, Star,
  Zap, Target, MessageSquare, ChevronDown, ChevronRight
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function SparkBrainPage({ onNavigate }) {
  const [activeSection, setActiveSection] = useState('identiteit');
  const [identity, setIdentity] = useState(null);
  const [bijbel, setBijbel] = useState(null);
  const [sparkProfile, setSparkProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/spark/full`).then(r => r.json()).catch(() => ({})),
      fetch(`${API}/api/spark/profile`).then(r => r.json()).catch(() => ({ profile: {} })),
    ]).then(([d, p]) => {
      setIdentity(d.identity || {});
      setBijbel(d.bijbel || {});
      setSparkProfile(p.profile || {});
      setLoading(false);
    });
  }, []);

  const sections = [
    { id: 'identiteit', label: 'Identiteit', icon: Brain, accent: '#f59e0b' },
    { id: 'waarden', label: 'Normen & Waarden', icon: Heart, accent: '#ec4899' },
    { id: 'bijbel', label: 'Spark Bijbel', icon: BookOpen, accent: '#a855f7' },
    { id: 'profiel', label: 'Spark Profiel', icon: Star, accent: '#06b6d4' },
  ];

  const kernwaarden = bijbel?.kernwaarden || [];
  const normen = bijbel?.normen || [];
  const doelen = bijbel?.doelen || [];
  const bijbelItems = bijbel?.bijbel_items || [];
  const reactieVoorbeelden = bijbel?.reactie_voorbeelden || {};
  const traits = identity?.persoonlijkheid?.traits || [];
  const basisKennis = identity?.basis_kennis || {};

  if (loading) return <MainLayout activePage="spark-brain" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="spark-brain" onNavigate={onNavigate}>
      <div data-testid="spark-brain-page" className="h-[calc(100vh-4rem)] flex flex-col">

        {/* Banner */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Spark Brain</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Identiteit, Waarden & Bijbel</p>
            </div>
            <div className="ml-auto flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/50">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[10px] text-slate-400">{kernwaarden.length} waarden | {normen.length} normen | {bijbelItems.length} bijbel</span>
            </div>
          </div>
          <div className="flex overflow-x-auto gap-0">
            {sections.map(s => {
              const isActive = activeSection === s.id;
              return (
                <button key={s.id} data-testid={`brain-tab-${s.id}`} onClick={() => setActiveSection(s.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
                  style={{ color: isActive ? s.accent : '#94a3b8' }}>
                  <s.icon className="w-3.5 h-3.5" />
                  {s.label}
                  {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: s.accent }} />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* IDENTITEIT */}
            {activeSection === 'identiteit' && (
              <>
                {/* Hero */}
                <div className="p-6 rounded-2xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(234,88,12,0.04))' }}>
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-3xl font-bold text-white" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
                      S
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-white">{identity?.naam || 'Spark'}</h2>
                      <p className="text-xs text-slate-400">v{identity?.versie || '?'} | Gemaakt door {identity?.maker || '?'}</p>
                    </div>
                  </div>
                  <div className="p-3 bg-slate-800/30 rounded-xl">
                    <p className="text-[10px] text-amber-400 uppercase tracking-wider mb-1">Doel</p>
                    <p className="text-sm text-white leading-relaxed">{identity?.doel || '—'}</p>
                  </div>
                </div>

                {/* Doelen */}
                {doelen.length > 0 && (
                  <Card title="Doelen" icon={Target} accent="#22c55e">
                    <div className="space-y-2">
                      {doelen.map((d, i) => (
                        <div key={i} className="flex items-center gap-2.5 py-1.5">
                          <div className="w-6 h-6 rounded-lg bg-green-500/10 flex items-center justify-center text-[10px] font-bold text-green-400">{i + 1}</div>
                          <span className="text-sm text-slate-300">{d}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* Persoonlijkheid */}
                <Card title="Persoonlijkheid" icon={Sparkles} accent="#a855f7">
                  <div className="space-y-3">
                    <div className="flex flex-wrap gap-2">
                      {traits.map((p, i) => (
                        <span key={i} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">{p}</span>
                      ))}
                    </div>
                    {identity?.persoonlijkheid?.toon && (
                      <div className="p-2.5 bg-slate-800/30 rounded-lg">
                        <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-0.5">Toon</p>
                        <p className="text-xs text-slate-300">{identity.persoonlijkheid.toon}</p>
                      </div>
                    )}
                    {identity?.persoonlijkheid?.filosofie && (
                      <div className="p-2.5 bg-slate-800/30 rounded-lg">
                        <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-0.5">Filosofie</p>
                        <p className="text-xs text-slate-300">{identity.persoonlijkheid.filosofie}</p>
                      </div>
                    )}
                  </div>
                </Card>

                {/* Basis kennis */}
                {basisKennis.over_mezelf && (
                  <Card title="Spark over zichzelf" icon={Brain} accent="#f59e0b">
                    <div className="space-y-1.5">
                      {basisKennis.over_mezelf.map((z, i) => (
                        <div key={i} className="flex items-center gap-2 py-1">
                          <div className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
                          <span className="text-xs text-slate-300">{z}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
                {basisKennis.wat_ik_kan && (
                  <Card title="Wat Spark kan" icon={Zap} accent="#06b6d4">
                    <div className="space-y-1.5">
                      {basisKennis.wat_ik_kan.map((k, i) => (
                        <div key={i} className="flex items-center gap-2 py-1">
                          <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 flex-shrink-0" />
                          <span className="text-xs text-slate-300">{k}</span>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}

            {/* NORMEN & WAARDEN */}
            {activeSection === 'waarden' && (
              <>
                <div className="p-4 rounded-xl border border-pink-500/20" style={{ background: 'linear-gradient(135deg, rgba(236,72,153,0.06), rgba(168,85,247,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Normen & Waarden</h2>
                  <p className="text-xs text-slate-400">De kernwaarden die Spark's gedrag en beslissingen sturen. {kernwaarden.length} waarden, {normen.length} normen.</p>
                </div>

                {/* Kernwaarden */}
                <div className="space-y-2">
                  {kernwaarden.map((kw, i) => (
                    <WaardeCard key={kw.id || i} kw={kw} />
                  ))}
                </div>

                {/* Normen */}
                {normen.length > 0 && (
                  <Card title={`Normen (${normen.length})`} icon={Shield} accent="#ef4444">
                    <div className="space-y-2">
                      {normen.map((n, i) => (
                        <div key={n.id || i} className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm text-white font-medium">{n.norm}</h4>
                            <div className="flex gap-0.5">
                              {[1, 2, 3, 4, 5].map(s => (
                                <Star key={s} className={`w-2.5 h-2.5 ${s <= (n.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
                              ))}
                            </div>
                          </div>
                          <p className="text-[11px] text-slate-400">{n.beschrijving}</p>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}
              </>
            )}

            {/* SPARK BIJBEL */}
            {activeSection === 'bijbel' && (
              <>
                <div className="p-5 rounded-xl border border-purple-500/20" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(139,92,246,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Spark Bijbel</h2>
                  <p className="text-xs text-slate-400">{bijbel?.spark_bijbel?.beschrijving || 'Normen, waarden en voorbeelden voor het kerngedrag van Spark'}</p>
                </div>

                {/* Bijbel items */}
                {bijbelItems.length > 0 && (
                  <Card title={`Levenswijsheden (${bijbelItems.length})`} icon={BookOpen} accent="#a855f7">
                    <div className="space-y-2">
                      {bijbelItems.map((item, i) => (
                        <BijbelItem key={item.id || i} item={item} />
                      ))}
                    </div>
                  </Card>
                )}

                {/* Reactie voorbeelden */}
                {Object.keys(reactieVoorbeelden).length > 0 && (
                  <Card title="Reactie Voorbeelden" icon={MessageSquare} accent="#06b6d4">
                    <div className="space-y-3">
                      {Object.entries(reactieVoorbeelden).map(([key, responses]) => (
                        <div key={key} className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
                          <p className="text-xs text-cyan-400 font-medium mb-2">{key.replace(/_/g, ' ').replace(/^wanneer /, 'Wanneer ')}</p>
                          <div className="space-y-1">
                            {(Array.isArray(responses) ? responses : [responses]).map((r, i) => (
                              <p key={i} className="text-[11px] text-slate-400 pl-3 border-l-2 border-slate-700 italic">"{r}"</p>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )}

                {/* 5W+H Framework */}
                <Card title="5W+H Framework" icon={Target} accent="#22c55e">
                  <p className="text-xs text-slate-400 mb-3">Elk knowledge card kan verrijkt worden met het 5W+H framework voor dieper begrip:</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {[
                      { label: 'Wie', desc: 'Over wie gaat het?', color: '#f59e0b' },
                      { label: 'Wat', desc: 'Wat is de kern?', color: '#3b82f6' },
                      { label: 'Wanneer', desc: 'Tijdscontext', color: '#22c55e' },
                      { label: 'Waar', desc: 'Locatie/context', color: '#a855f7' },
                      { label: 'Waarom', desc: 'Reden/motivatie', color: '#ec4899' },
                      { label: 'Hoe', desc: 'Werkwijze/proces', color: '#06b6d4' },
                    ].map(w => (
                      <div key={w.label} className="p-3 bg-slate-800/40 rounded-xl border border-slate-700/50">
                        <p className="text-xs font-semibold" style={{ color: w.color }}>{w.label}</p>
                        <p className="text-[10px] text-slate-500 mt-0.5">{w.desc}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            )}

            {activeSection === 'profiel' && sparkProfile && (
              <SparkProfileView profile={sparkProfile} />
            )}

          </div>
        </div>
      </div>
    </MainLayout>
  );
}

function Card({ title, icon: Icon, accent, children }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/50">
        <Icon className="w-4 h-4" style={{ color: accent }} />
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function WaardeCard({ kw }) {
  const [open, setOpen] = useState(false);
  const hasDetail = kw.voorbeelden?.length > 0 || kw.ws5 || kw.tags?.length > 0;
  return (
    <div data-testid={`waarde-${kw.id || kw.waarde}`} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      <button onClick={() => hasDetail && setOpen(!open)} className="w-full flex items-start gap-3 p-4 text-left">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: kw.belangrijkheid >= 5 ? '#ec489915' : '#64748b15' }}>
          <Heart className="w-4 h-4" style={{ color: kw.belangrijkheid >= 5 ? '#ec4899' : '#94a3b8' }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-white">{kw.waarde}</h4>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map(s => (
                <Star key={s} className={`w-3 h-3 ${s <= kw.belangrijkheid ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
              ))}
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{kw.beschrijving}</p>
        </div>
        {hasDetail && (open ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" /> : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" />)}
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-2 border-t border-slate-800/50 pt-2">
          {kw.voorbeelden?.length > 0 && (
            <div>
              <p className="text-[10px] text-pink-400 uppercase tracking-wider mb-1">Voorbeelden</p>
              {kw.voorbeelden.map((v, i) => (
                <p key={i} className="text-[11px] text-slate-400 pl-3 border-l-2 border-pink-500/20 mb-1">{v}</p>
              ))}
            </div>
          )}
          {kw.ws5 && (
            <div>
              <p className="text-[10px] text-amber-400 uppercase tracking-wider mb-1">5W+H</p>
              <div className="grid grid-cols-2 gap-1.5">
                {Object.entries(kw.ws5).filter(([k]) => k !== 'how').map(([k, v]) => (
                  <div key={k} className="p-1.5 bg-slate-800/30 rounded text-[10px]">
                    <span className="text-amber-400 font-medium uppercase">{k}: </span>
                    <span className="text-slate-400">{String(v).slice(0, 60)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {kw.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {kw.tags.map((t, i) => <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-500">#{t}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function BijbelItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between p-3 text-left">
        <div>
          <h4 className="text-sm text-white font-medium">{item.naam}</h4>
          <p className="text-[10px] text-slate-500">{item.beschrijving?.slice(0, 80)}{item.beschrijving?.length > 80 ? '...' : ''}</p>
        </div>
        {open ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
      </button>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-slate-700/30 pt-2">
          <p className="text-xs text-slate-400">{item.beschrijving}</p>
          {item.ws5 && (
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(item.ws5).map(([k, v]) => (
                <div key={k} className="p-1.5 bg-slate-800/40 rounded text-[10px]">
                  <span className="text-purple-400 font-medium uppercase">{k}: </span>
                  <span className="text-slate-400">{String(v).slice(0, 80)}</span>
                </div>
              ))}
            </div>
          )}
          {item.toegevoegd_op && <p className="text-[10px] text-slate-600">Toegevoegd: {new Date(item.toegevoegd_op).toLocaleDateString('nl-NL')}</p>}
        </div>
      )}
    </div>
  );
}

function SparkProfileView({ profile }) {
  const renderObject = (obj, depth = 0) => {
    if (!obj || typeof obj !== 'object') return <span className="text-xs text-slate-300">{String(obj)}</span>;
    if (Array.isArray(obj)) {
      return (
        <ul className="space-y-1 ml-2">
          {obj.map((item, i) => (
            <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
              <span className="text-amber-500 mt-0.5">-</span>
              {typeof item === 'object' ? renderObject(item, depth + 1) : String(item)}
            </li>
          ))}
        </ul>
      );
    }
    return (
      <div className={`space-y-2 ${depth > 0 ? 'ml-2 pl-2 border-l border-slate-800' : ''}`}>
        {Object.entries(obj).map(([key, val]) => (
          <div key={key}>
            <p className="text-[10px] text-amber-400/60 uppercase tracking-wider mb-0.5">{key.replace(/_/g, ' ')}</p>
            {typeof val === 'object' ? renderObject(val, depth + 1) : <p className="text-xs text-slate-300">{String(val)}</p>}
          </div>
        ))}
      </div>
    );
  };

  const sections = Object.entries(profile).filter(([k]) => k !== 'basis');
  return (
    <div className="space-y-4">
      {profile.basis && (
        <Card title={`${profile.basis.naam} - ${profile.basis.versie || ''}`} icon={Star} accent="#06b6d4">
          <div className="grid grid-cols-2 gap-3 text-xs">
            {Object.entries(profile.basis).map(([k, v]) => (
              <div key={k}><span className="text-slate-500">{k}:</span> <span className="text-white ml-1">{String(v)}</span></div>
            ))}
          </div>
        </Card>
      )}
      {sections.map(([key, val]) => (
        <Card key={key} title={key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())} icon={Sparkles} accent="#06b6d4">
          {renderObject(val)}
        </Card>
      ))}
    </div>
  );
}

export default SparkBrainPage;
