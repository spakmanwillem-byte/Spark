import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { toast } from 'sonner';
import {
  Brain, Heart, BookOpen, Star,
  Zap, Target, MessageSquare, ChevronDown, ChevronRight,
  Plus, Edit3, Trash2, X, Save, Sparkles, Shield, Leaf, Check, Layers
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function SparkBrainPage({ onNavigate, initialSection = 'identiteit' }) {
  const [activeSection, setActiveSection] = useState(initialSection);
  const [identity, setIdentity] = useState(null);
  const [bijbel, setBijbel] = useState(null);
  const [sparkProfile, setSparkProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Editor state
  const [editor, setEditor] = useState(null); // { section, mode: 'add'|'edit', identifier, data }

  const loadBijbel = async () => {
    const d = await fetch(`${API}/api/spark/full`).then(r => r.json()).catch(() => ({}));
    setIdentity(d.identity || {});
    setBijbel(d.bijbel || {});
  };

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

  const saveItem = async () => {
    if (!editor) return;
    const { section, mode, identifier, data, value } = editor;
    const url = mode === 'add'
      ? `${API}/api/spark/bijbel/${section}`
      : `${API}/api/spark/bijbel/${section}/${identifier}`;
    const method = mode === 'add' ? 'POST' : 'PUT';
    try {
      const res = await fetch(url, {
        method, headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: data || {}, value }),
      });
      if (!res.ok) {
        const eb = await res.json().catch(() => ({}));
        toast.error(`Opslaan mislukt: ${eb.detail || res.status}`);
        return;
      }
      toast.success(mode === 'add' ? 'Toegevoegd' : 'Opgeslagen');
      setEditor(null);
      await loadBijbel();
    } catch (e) {
      toast.error(`Netwerkfout: ${e.message}`);
    }
  };

  // v6_brain_delete_001 — custom confirm-modal (window.confirm faalt in iframe)
  const [confirmDel, setConfirmDel] = useState(null); // { section, identifier, label }

  const deleteItem = (section, identifier, label = '') => {
    setConfirmDel({ section, identifier, label });
  };

  const doDelete = async () => {
    if (!confirmDel) return;
    const { section, identifier } = confirmDel;
    try {
      const res = await fetch(`${API}/api/spark/bijbel/${section}/${identifier}`, { method: 'DELETE' });
      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        toast.error(`Verwijderen mislukt: ${errBody.detail || res.status}`);
      } else {
        toast.success('Verwijderd');
        await loadBijbel();
      }
    } catch (e) {
      toast.error(`Netwerkfout: ${e.message}`);
    } finally {
      setConfirmDel(null);
    }
  };

  // Verberg emotie_pipeline tab uit Brain als deze page is opened via sidebar 'Emotie Routering'
  // (initialSection='emotie_pipeline') — anders krijg je dubbele toegang.
  const isRouteringView = initialSection === 'emotie_pipeline';
  const sections = isRouteringView ? [
    { id: 'emotie_pipeline', label: 'Emotie Pipeline', icon: Layers, accent: '#fb923c' },
  ] : [
    { id: 'identiteit', label: 'Identiteit', icon: Brain, accent: '#f59e0b' },
    { id: 'waarden', label: 'Normen & Waarden', icon: Heart, accent: '#ec4899' },
    { id: 'bijbel', label: 'Spark Bijbel', icon: BookOpen, accent: '#a855f7' },
    { id: 'profiel', label: 'Spark Profiel', icon: Star, accent: '#06b6d4' },
    { id: 'groeien', label: 'Groeien', icon: Leaf, accent: '#22c55e' },
  ];

  const kernwaarden = bijbel?.kernwaarden || [];
  const normen = bijbel?.normen || [];
  const doelen = bijbel?.doelen || [];
  const bijbelItems = bijbel?.bijbel_items || [];
  const reactieVoorbeelden = bijbel?.reactie_voorbeelden || {};
  const traits = identity?.persoonlijkheid?.traits || [];
  const basisKennis = identity?.basis_kennis || {};

  const activePageId = isRouteringView ? 'emotion-routing' : 'spark-brain';
  if (loading) return <MainLayout activePage={activePageId} onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage={activePageId} onNavigate={onNavigate}>
      <div data-testid="spark-brain-page" className="h-full flex flex-col">

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
                  {/* v6_identity_v2_001 — Linked layers (live counts) */}
                  {identity?.linked_layers && (
                    <div data-testid="identity-linked-layers" className="grid grid-cols-3 md:grid-cols-6 gap-2 mt-3">
                      {[
                        { k: 'kernwaarden',          label: 'Kernwaarden', color: '#ec4899' },
                        { k: 'normen',               label: 'Normen',      color: '#f43f5e' },
                        { k: 'bijbel_items',         label: 'Bijbel',      color: '#a855f7' },
                        { k: 'capabilities_live',    label: 'Capabilities live', color: '#06b6d4' },
                        { k: 'emotie_pipeline_lagen', label: 'Emotie-lagen', color: '#fb923c' },
                        { k: 'kb_v2_hooks',          label: 'KB v2 hooks', color: '#22c55e' },
                      ].map(item => (
                        <div key={item.k} className="p-2 rounded-lg bg-slate-800/40 border border-slate-700/50 text-center">
                          <p className="text-base font-bold" style={{ color: item.color }}>
                            {identity.linked_layers[item.k] ?? '—'}
                          </p>
                          <p className="text-[9px] text-slate-500 uppercase tracking-wider mt-0.5">{item.label}</p>
                        </div>
                      ))}
                    </div>
                  )}
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

                {/* v6_disclaimer_001 — Disclaimer-pijlers */}
                {identity?.disclaimer && (
                  <DisclaimerCard disclaimer={identity.disclaimer} bijbelCounts={{
                    kernwaarden: kernwaarden.length,
                    normen: normen.length,
                    bijbel_items: bijbelItems.length,
                  }} />
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
                <Card
                  title={`Kernwaarden (${kernwaarden.length})`}
                  icon={Heart}
                  accent="#ec4899"
                  action={
                    <button
                      data-testid="add-kernwaarde-btn"
                      onClick={() => setEditor({ section: 'kernwaarden', mode: 'add', data: { belangrijkheid: 3 } })}
                      className="flex items-center gap-1 px-2 py-1 rounded-md bg-pink-500/15 hover:bg-pink-500/25 text-pink-300 text-[11px] font-medium transition-colors">
                      <Plus className="w-3 h-3" /> Nieuwe waarde
                    </button>
                  }
                >
                  <div className="space-y-2">
                    {kernwaarden.map((kw, i) => (
                      <WaardeCard
                        key={kw.id || i}
                        kw={kw}
                        onEdit={() => setEditor({ section: 'kernwaarden', mode: 'edit', identifier: kw.id || String(i), data: kw })}
                        onDelete={() => deleteItem('kernwaarden', kw.id || String(i), kw.waarde)}
                      />
                    ))}
                    {kernwaarden.length === 0 && (
                      <p className="text-xs text-slate-500 italic">Nog geen kernwaarden — klik 'Nieuwe waarde' om Spark zijn kernwaarden te geven.</p>
                    )}
                  </div>
                </Card>

                {/* Normen */}
                <Card
                  title={`Normen (${normen.length})`}
                  icon={Shield}
                  accent="#ef4444"
                  action={
                    <button
                      data-testid="add-norm-btn"
                      onClick={() => setEditor({ section: 'normen', mode: 'add', data: { belangrijkheid: 3 } })}
                      className="flex items-center gap-1 px-2 py-1 rounded-md bg-red-500/15 hover:bg-red-500/25 text-red-300 text-[11px] font-medium transition-colors">
                      <Plus className="w-3 h-3" /> Nieuwe norm
                    </button>
                  }
                >
                  <div className="space-y-2">
                    {normen.map((n, i) => (
                      <NormCard
                        key={n.id || i}
                        n={n}
                        onEdit={() => setEditor({ section: 'normen', mode: 'edit', identifier: n.id || String(i), data: n })}
                        onDelete={() => deleteItem('normen', n.id || String(i), n.norm || n.onderwerp)}
                      />
                    ))}
                    {normen.length === 0 && (
                      <p className="text-xs text-slate-500 italic">Nog geen normen toegevoegd.</p>
                    )}
                  </div>
                </Card>
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
                <Card
                  title={`Levenswijsheden (${bijbelItems.length})`}
                  icon={BookOpen}
                  accent="#a855f7"
                  action={
                    <button
                      data-testid="add-bijbel-btn"
                      onClick={() => setEditor({ section: 'bijbel_items', mode: 'add', data: { belangrijkheid: 3 } })}
                      className="flex items-center gap-1 px-2 py-1 rounded-md bg-purple-500/15 hover:bg-purple-500/25 text-purple-300 text-[11px] font-medium transition-colors">
                      <Plus className="w-3 h-3" /> Nieuwe wijsheid
                    </button>
                  }
                >
                  <div className="space-y-2">
                    {bijbelItems.map((item, i) => (
                      <BijbelItem
                        key={item.id || i}
                        item={item}
                        onEdit={() => setEditor({ section: 'bijbel_items', mode: 'edit', identifier: item.id || String(i), data: item })}
                        onDelete={() => deleteItem('bijbel_items', item.id || String(i), item.titel || item.naam || item.onderwerp)}
                      />
                    ))}
                    {bijbelItems.length === 0 && (
                      <p className="text-xs text-slate-500 italic">Nog geen levenswijsheden.</p>
                    )}
                  </div>
                </Card>

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

            {activeSection === 'groeien' && (
              <GroeienSection />
            )}

            {/* v6_emotion_pipeline_001 — 7-laags emotie-pipeline dry-run */}
            {activeSection === 'emotie_pipeline' && (
              <EmotiePipelineSection />
            )}

          </div>
        </div>
      </div>
      {editor && (
        <BijbelEditor
          editor={editor}
          onClose={() => setEditor(null)}
          onSave={saveItem}
          onChange={(patch) => setEditor(prev => ({ ...prev, data: { ...prev.data, ...patch } }))}
        />
      )}
      {/* v6_brain_delete_001 — custom confirm-modal */}
      {confirmDel && (
        <div data-testid="confirm-delete-modal"
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setConfirmDel(null)}>
          <div className="bg-slate-900 border border-red-500/40 rounded-xl p-5 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-full bg-red-500/15 flex items-center justify-center">
                <Trash2 className="w-4 h-4 text-red-400" />
              </div>
              <h3 className="text-base font-bold text-white">Permanent verwijderen?</h3>
            </div>
            <p className="text-sm text-slate-300 mb-4">
              {confirmDel.label
                ? <>Item <span className="text-red-300 font-medium">"{confirmDel.label}"</span> uit <span className="text-slate-400">{confirmDel.section}</span> wordt permanent verwijderd.</>
                : <>Dit item wordt permanent verwijderd.</>}
            </p>
            <div className="flex justify-end gap-2">
              <button data-testid="confirm-delete-cancel"
                onClick={() => setConfirmDel(null)}
                className="px-4 py-2 text-sm rounded-lg border border-slate-700 text-slate-300 hover:bg-slate-800">
                Annuleren
              </button>
              <button data-testid="confirm-delete-confirm"
                onClick={doDelete}
                className="px-4 py-2 text-sm rounded-lg bg-red-500 hover:bg-red-600 text-white font-medium">
                Ja, verwijderen
              </button>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}


// v6_disclaimer_001 — Disclaimer-pijlers component
function DisclaimerCard({ disclaimer, bijbelCounts }) {
  const kaders = disclaimer.kaders || [];
  const nietDoet = disclaimer.wat_spark_niet_doet || [];
  return (
    <div data-testid="disclaimer-card" className="rounded-2xl border border-amber-500/30 overflow-hidden"
         style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.07), rgba(251,146,60,0.04))' }}>
      <div className="px-5 py-3 border-b border-amber-500/20 flex items-center gap-2">
        <Shield className="w-4 h-4 text-amber-400" />
        <h3 className="text-sm font-bold text-white flex-1">Disclaimer</h3>
        <span className="text-[10px] text-amber-400 bg-amber-500/15 px-2 py-0.5 rounded">{disclaimer.version || 'v1.0'}</span>
      </div>
      <div className="p-5 space-y-4">
        {/* Kernzin */}
        <p data-testid="disclaimer-kernzin" className="text-sm text-slate-200 leading-relaxed">
          {disclaimer.kernzin}
        </p>

        {/* Leidende lagen badge */}
        <div className="flex flex-wrap gap-2">
          {(disclaimer.leidende_lagen || []).map((l, i) => {
            const count = l === 'Normen & Waarden'
              ? (bijbelCounts?.kernwaarden || 0) + (bijbelCounts?.normen || 0)
              : bijbelCounts?.bijbel_items || 0;
            return (
              <div key={i} className="px-3 py-1.5 rounded-lg bg-pink-500/10 border border-pink-500/30 text-xs">
                <span className="text-pink-300 font-medium">{l}</span>
                <span className="text-slate-500 ml-2">{count} items</span>
              </div>
            );
          })}
        </div>

        {/* Kaders */}
        {kaders.length > 0 && (
          <div className="space-y-2">
            <p className="text-[10px] uppercase text-amber-400 tracking-wider font-semibold">De 4 kaders</p>
            {kaders.map((k, i) => (
              <div key={i} data-testid={`disclaimer-kader-${i}`}
                   className="p-2.5 bg-slate-900/40 rounded-lg border border-slate-800/60">
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-xs font-semibold text-amber-200">{k.kader}</span>
                  {k.verwijst_naar && (
                    <span className="text-[9px] text-slate-500 font-mono">{k.verwijst_naar}</span>
                  )}
                </div>
                <p className="text-xs text-slate-400 mt-0.5 leading-snug">{k.betekenis}</p>
              </div>
            ))}
          </div>
        )}

        {/* Wat Spark NIET doet */}
        {nietDoet.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] uppercase text-red-400 tracking-wider font-semibold">Wat Spark niet doet</p>
            {nietDoet.map((n, i) => (
              <div key={i} className="flex items-center gap-2 py-0.5">
                <X className="w-3 h-3 text-red-400 flex-shrink-0" />
                <span className="text-xs text-slate-400">{n}</span>
              </div>
            ))}
          </div>
        )}

        {disclaimer.laatst_bewerkt && (
          <p className="text-[9px] text-slate-600 text-right pt-2 border-t border-slate-800/40">
            Laatst bewerkt: {(disclaimer.laatst_bewerkt || '').slice(0, 19).replace('T', ' ')}
          </p>
        )}
      </div>
    </div>
  );
}


function Card({ title, icon: Icon, accent, action, children }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/50">
        <Icon className="w-4 h-4" style={{ color: accent }} />
        <h3 className="text-sm font-semibold text-white flex-1">{title}</h3>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function WaardeCard({ kw, onEdit, onDelete }) {
  const [open, setOpen] = useState(false);
  const hasDetail = kw.voorbeelden?.length > 0 || kw.ws5 || kw.tags?.length > 0 || kw.lagen;
  const lagen = kw.lagen || {};
  return (
    <div data-testid={`waarde-${kw.id || kw.waarde}`} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      <div className="w-full flex items-start gap-3 p-4">
        <button onClick={() => hasDetail && setOpen(!open)} className="flex-1 flex items-start gap-3 text-left">
          <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: kw.belangrijkheid >= 5 ? '#ec489915' : '#64748b15' }}>
            <Heart className="w-4 h-4" style={{ color: kw.belangrijkheid >= 5 ? '#ec4899' : '#94a3b8' }} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <h4 className="text-sm font-semibold text-white">{kw.waarde}</h4>
              <div className="flex gap-0.5">
                {[1, 2, 3, 4, 5].map(s => (
                  <Star key={s} className={`w-3 h-3 ${s <= (kw.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
                ))}
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">{kw.beschrijving}</p>
            {kw.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {kw.tags.slice(0, 6).map((t, i) => <span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400">#{t}</span>)}
              </div>
            )}
          </div>
          {hasDetail && (open ? <ChevronDown className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" /> : <ChevronRight className="w-4 h-4 text-slate-500 flex-shrink-0 mt-1" />)}
        </button>
        {(onEdit || onDelete) && (
          <div className="flex flex-col gap-1 flex-shrink-0">
            {onEdit && <button data-testid={`edit-waarde-${kw.id}`} onClick={onEdit} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-amber-400 transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>}
            {onDelete && <button data-testid={`del-waarde-${kw.id}`} onClick={onDelete} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>}
          </div>
        )}
      </div>
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
          {Object.values(lagen).some(v => v) && (
            <div>
              <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-1">Lagen</p>
              {['laag1','laag2','laag3','laag4'].map(k => lagen[k] && (
                <p key={k} className="text-[11px] text-slate-400 pl-3 border-l-2 border-purple-500/20 mb-1"><span className="text-purple-400 font-medium">{k}:</span> {lagen[k]}</p>
              ))}
            </div>
          )}
          {kw.ws5 && Object.values(kw.ws5).some(v => v) && (
            <div>
              <p className="text-[10px] text-amber-400 uppercase tracking-wider mb-1">5W+H</p>
              <div className="grid grid-cols-2 gap-1.5">
                {Object.entries(kw.ws5).filter(([,v]) => v).map(([k, v]) => (
                  <div key={k} className="p-1.5 bg-slate-800/30 rounded text-[10px]">
                    <span className="text-amber-400 font-medium uppercase">{k}: </span>
                    <span className="text-slate-400">{String(v).slice(0, 80)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function NormCard({ n, onEdit, onDelete }) {
  const [open, setOpen] = useState(false);
  const lagen = n.lagen || {};
  const hasDetail = n.voorbeelden?.length > 0 || n.ws5 || n.tags?.length > 0 || Object.values(lagen).some(v=>v);
  return (
    <div data-testid={`norm-${n.id}`} className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
      <div className="flex items-start gap-2">
        <button onClick={() => hasDetail && setOpen(!open)} className="flex-1 text-left">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <h4 className="text-sm text-white font-medium">{n.norm}</h4>
            <div className="flex gap-0.5">
              {[1, 2, 3, 4, 5].map(s => (
                <Star key={s} className={`w-2.5 h-2.5 ${s <= (n.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
              ))}
            </div>
          </div>
          <p className="text-[11px] text-slate-400">{n.beschrijving}</p>
          {n.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {n.tags.slice(0,6).map((t,i)=><span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400">#{t}</span>)}
            </div>
          )}
        </button>
        <div className="flex flex-col gap-1 flex-shrink-0">
          {onEdit && <button data-testid={`edit-norm-${n.id}`} onClick={onEdit} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-amber-400 transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>}
          {onDelete && <button data-testid={`del-norm-${n.id}`} onClick={onDelete} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>}
        </div>
      </div>
      {open && (
        <div className="mt-3 pt-2 border-t border-slate-700/30 space-y-2">
          {Object.values(lagen).some(v=>v) && (
            <div>
              <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-1">Lagen</p>
              {['laag1','laag2','laag3','laag4'].map(k => lagen[k] && (
                <p key={k} className="text-[11px] text-slate-400 pl-3 border-l-2 border-purple-500/20 mb-1"><span className="text-purple-400 font-medium">{k}:</span> {lagen[k]}</p>
              ))}
            </div>
          )}
          {n.ws5 && Object.values(n.ws5).some(v=>v) && (
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(n.ws5).filter(([,v])=>v).map(([k, v]) => (
                <div key={k} className="p-1.5 bg-slate-800/40 rounded text-[10px]">
                  <span className="text-amber-400 font-medium uppercase">{k}: </span>
                  <span className="text-slate-400">{String(v).slice(0, 80)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function BijbelItem({ item, onEdit, onDelete }) {
  const [open, setOpen] = useState(false);
  const lagen = item.lagen || {};
  return (
    <div className="bg-slate-800/30 rounded-xl border border-slate-700/30 overflow-hidden">
      <div className="flex items-start gap-2 p-3">
        <button onClick={() => setOpen(!open)} className="flex-1 flex items-center justify-between text-left">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h4 className="text-sm text-white font-medium">{item.naam}</h4>
              {item.belangrijkheid != null && (
                <div className="flex gap-0.5">
                  {[1,2,3,4,5].map(s => (
                    <Star key={s} className={`w-2.5 h-2.5 ${s <= (item.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
                  ))}
                </div>
              )}
            </div>
            <p className="text-[10px] text-slate-500">{item.beschrijving?.slice(0, 80)}{item.beschrijving?.length > 80 ? '...' : ''}</p>
            {item.tags?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {item.tags.slice(0,6).map((t,i)=><span key={i} className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-800 text-slate-400">#{t}</span>)}
              </div>
            )}
          </div>
          {open ? <ChevronDown className="w-4 h-4 text-slate-500" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
        </button>
        <div className="flex flex-col gap-1 flex-shrink-0">
          {onEdit && <button data-testid={`edit-bijbel-${item.id}`} onClick={onEdit} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-amber-400 transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>}
          {onDelete && <button data-testid={`del-bijbel-${item.id}`} onClick={onDelete} className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-red-400 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>}
        </div>
      </div>
      {open && (
        <div className="px-3 pb-3 space-y-2 border-t border-slate-700/30 pt-2">
          {item.beschrijving && <p className="text-xs text-slate-400">{item.beschrijving}</p>}
          {Object.values(lagen).some(v=>v) && (
            <div>
              <p className="text-[10px] text-purple-400 uppercase tracking-wider mb-1">Lagen</p>
              {['laag1','laag2','laag3','laag4'].map(k => lagen[k] && (
                <p key={k} className="text-[11px] text-slate-400 pl-3 border-l-2 border-purple-500/20 mb-1"><span className="text-purple-400 font-medium">{k}:</span> {lagen[k]}</p>
              ))}
            </div>
          )}
          {item.ws5 && Object.values(item.ws5).some(v=>v) && (
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(item.ws5).filter(([,v])=>v).map(([k, v]) => (
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

function BijbelEditor({ editor, onClose, onSave, onChange }) {
  const { section, mode, data = {} } = editor;
  const titleKey = section === 'kernwaarden' ? 'waarde' : section === 'normen' ? 'norm' : 'naam';
  const sectionLabels = {
    kernwaarden: { title: 'Kernwaarde', accent: '#ec4899', titleField: 'Waarde-naam', titlePlaceholder: 'bv. Helpen, Eerlijkheid, Groei' },
    normen: { title: 'Norm', accent: '#ef4444', titleField: 'Norm', titlePlaceholder: 'bv. Respecteer iedereens grenzen' },
    bijbel_items: { title: 'Levenswijsheid', accent: '#a855f7', titleField: 'Naam', titlePlaceholder: 'bv. Roadkill-mantra' },
  };
  const meta = sectionLabels[section] || sectionLabels.bijbel_items;
  const lagen = data.lagen || {};
  const ws5 = data.ws5 || {};
  const tags = Array.isArray(data.tags) ? data.tags : [];
  const voorbeelden = Array.isArray(data.voorbeelden) ? data.voorbeelden : [];
  const [tagInput, setTagInput] = useState('');
  const [voorbeeldInput, setVoorbeeldInput] = useState('');

  const setLag = (k, v) => onChange({ lagen: { ...lagen, [k]: v } });
  const setWs5 = (k, v) => onChange({ ws5: { ...ws5, [k]: v } });
  const addTag = () => { const t = tagInput.trim().replace(/^#/, ''); if (t && !tags.includes(t)) onChange({ tags: [...tags, t] }); setTagInput(''); };
  const removeTag = (t) => onChange({ tags: tags.filter(x => x !== t) });
  const addVoorbeeld = () => { const v = voorbeeldInput.trim(); if (v) onChange({ voorbeelden: [...voorbeelden, v] }); setVoorbeeldInput(''); };
  const removeVoorbeeld = (i) => onChange({ voorbeelden: voorbeelden.filter((_, idx) => idx !== i) });

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" data-testid="bijbel-editor-modal">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800" style={{ borderTopColor: meta.accent, borderTopWidth: 2 }}>
          <h3 className="text-base font-bold text-white">{mode === 'add' ? `Nieuwe ${meta.title}` : `Bewerk ${meta.title}`}</h3>
          <button onClick={onClose} data-testid="editor-close-btn" className="p-1 rounded hover:bg-slate-800 text-slate-400"><X className="w-4 h-4" /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {/* Naam */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">{meta.titleField}</label>
            <input data-testid="editor-title-input" type="text" value={data[titleKey] || ''}
              onChange={e => onChange({ [titleKey]: e.target.value })}
              placeholder={meta.titlePlaceholder}
              className="mt-1 w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
          </div>
          {/* Beschrijving */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">Korte beschrijving</label>
            <textarea data-testid="editor-beschrijving-input" rows={2} value={data.beschrijving || ''}
              onChange={e => onChange({ beschrijving: e.target.value })}
              placeholder="Eén à twee zinnen die de kern weergeven"
              className="mt-1 w-full bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
          </div>
          {/* Belangrijkheid */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">Belangrijkheid (1-5)</label>
            <div className="flex gap-1 mt-1">
              {[1,2,3,4,5].map(s => (
                <button key={s} data-testid={`star-${s}`} type="button" onClick={() => onChange({ belangrijkheid: s })} className="p-1">
                  <Star className={`w-5 h-5 ${s <= (data.belangrijkheid || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'}`} />
                </button>
              ))}
            </div>
          </div>
          {/* Tags */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">Tags <span className="text-slate-600 normal-case">— bv. blij, missie, doel — gebruikt door chat</span></label>
            <div className="flex flex-wrap gap-1.5 mt-1">
              {tags.map(t => (
                <span key={t} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-pink-500/15 text-pink-300 text-[11px]">
                  #{t}
                  <button onClick={() => removeTag(t)} className="hover:text-red-400"><X className="w-3 h-3" /></button>
                </span>
              ))}
            </div>
            <div className="flex gap-2 mt-2">
              <input data-testid="editor-tag-input" type="text" value={tagInput} onChange={e => setTagInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addTag())}
                placeholder="tag (bv. blij, missie, doel)"
                className="flex-1 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
              <button onClick={addTag} className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs">+ Tag</button>
            </div>
          </div>
          {/* Lagen */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">Uitleg in 4 lagen <span className="text-slate-600 normal-case">— oppervlakkig → diep</span></label>
            <div className="space-y-2 mt-1">
              {['laag1','laag2','laag3','laag4'].map((k, i) => (
                <textarea key={k} data-testid={`editor-${k}`} rows={2} value={lagen[k] || ''}
                  onChange={e => setLag(k, e.target.value)}
                  placeholder={['Korte definitie','Iets uitgebreider','Diepere context','Essentie / kernbetekenis'][i]}
                  className="w-full bg-slate-800/40 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
              ))}
            </div>
          </div>
          {/* 5W+H */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">5W+H</label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              {['wie','wat','wanneer','waar','waarom','hoe'].map(k => (
                <input key={k} data-testid={`editor-ws5-${k}`} type="text" value={ws5[k] || ''}
                  onChange={e => setWs5(k, e.target.value)}
                  placeholder={k.charAt(0).toUpperCase() + k.slice(1)}
                  className="bg-slate-800/40 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
              ))}
            </div>
          </div>
          {/* Voorbeelden */}
          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider">Voorbeelden</label>
            <div className="space-y-1 mt-1">
              {voorbeelden.map((v, i) => (
                <div key={i} className="flex items-center gap-2 p-2 bg-slate-800/40 rounded-lg">
                  <span className="text-xs text-slate-300 flex-1">{v}</span>
                  <button onClick={() => removeVoorbeeld(i)} className="text-slate-500 hover:text-red-400"><X className="w-3 h-3" /></button>
                </div>
              ))}
            </div>
            <div className="flex gap-2 mt-2">
              <input data-testid="editor-voorbeeld-input" type="text" value={voorbeeldInput} onChange={e => setVoorbeeldInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addVoorbeeld())}
                placeholder="Concreet voorbeeld in 1 zin"
                className="flex-1 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-slate-500" />
              <button onClick={addVoorbeeld} className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs">+ Voorbeeld</button>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-slate-800">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-xs text-slate-300 hover:bg-slate-800">Annuleer</button>
          <button data-testid="editor-save-btn" onClick={onSave} className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium text-white" style={{ background: meta.accent }}>
            <Save className="w-3.5 h-3.5" /> {mode === 'add' ? 'Toevoegen' : 'Opslaan'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default SparkBrainPage;

/* === GROEIEN section === */
function GroeienSection() {
  const [tab, setTab] = useState('vocab'); // 'vocab' | 'tags' | 'orphans'
  const [vocabData, setVocabData] = useState(null);
  const [tagsData, setTagsData] = useState(null);
  const [orphansData, setOrphansData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);

  const loadVocab = async () => {
    setLoading(true); setSelected(new Set());
    const d = await fetch(`${API}/api/spark/insights/vocab-from-knowledge?limit=100`).then(r => r.json()).catch(() => null);
    setVocabData(d); setLoading(false);
  };
  const loadTags = async () => {
    setLoading(true); setSelected(new Set());
    const d = await fetch(`${API}/api/spark/insights/tags-without-card?limit=200`).then(r => r.json()).catch(() => null);
    setTagsData(d); setLoading(false);
  };
  const loadOrphans = async () => {
    setLoading(true); setSelected(new Set());
    const d = await fetch(`${API}/api/graph/orphan-check`).then(r => r.json()).catch(() => null);
    setOrphansData(d); setLoading(false);
  };

  useEffect(() => {
    if (tab === 'vocab' && !vocabData) loadVocab();
    if (tab === 'tags' && !tagsData) loadTags();
    if (tab === 'orphans' && !orphansData) loadOrphans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const toggle = (key) => {
    setSelected(s => {
      const c = new Set(s);
      if (c.has(key)) c.delete(key); else c.add(key);
      return c;
    });
  };

  const approveVocab = async () => {
    if (selected.size === 0) return;
    setBusy(true);
    const words = Array.from(selected);
    const r = await fetch(`${API}/api/spark/vocab/approve-growth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ words, source: 'kennisbank' }),
    }).then(x => x.json()).catch(() => null);
    setBusy(false);
    setMsg(r?.success ? `${r.added.length} woord(en) toegevoegd aan Spark's vocab.` : 'Fout bij opslaan');
    setTimeout(() => setMsg(null), 3500);
    setSelected(new Set());
    await loadVocab();
  };

  const recoverOrphans = async () => {
    setBusy(true);
    const r = await fetch(`${API}/api/graph/orphan-recover`, { method: 'POST' }).then(x => x.json()).catch(() => null);
    setBusy(false);
    setMsg(r?.message || 'Recovery klaar');
    setTimeout(() => setMsg(null), 4500);
    await loadOrphans();
  };

  const tabs = [
    { id: 'vocab', label: 'Vocab kandidaten', sub: 'Woorden uit jouw kennisbank' },
    { id: 'tags', label: 'Tags zonder kaart', sub: 'Veelgebruikte tags die nog géén kaart hebben' },
    { id: 'orphans', label: 'Weeskaarten', sub: 'In graph, niet in KB (recover)' },
  ];

  return (
    <>
      <div className="p-5 rounded-xl border border-emerald-500/20" style={{ background: 'linear-gradient(135deg, rgba(34,197,94,0.08), rgba(16,185,129,0.04))' }}>
        <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2"><Leaf className="w-5 h-5 text-emerald-400" /> Spark laten Groeien</h2>
        <p className="text-xs text-slate-400">Inzichten uit jouw kennisbank — kandidaten voor vocab, tags die een kaart verdienen, en kaarten die in de graph zitten maar nergens anders.</p>
      </div>

      <div className="flex gap-2 mb-2">
        {tabs.map(t => (
          <button key={t.id} data-testid={`groei-tab-${t.id}`} onClick={() => setTab(t.id)}
            className={`flex-1 px-3 py-2 rounded-lg text-xs font-medium transition-colors text-left border ${tab === t.id ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-slate-800/30 border-slate-700/50 text-slate-400 hover:bg-slate-800/60'}`}>
            <div>{t.label}</div>
            <div className="text-[10px] opacity-70 mt-0.5">{t.sub}</div>
          </button>
        ))}
      </div>

      {msg && <div data-testid="groei-msg" className="px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">{msg}</div>}

      {loading && <p className="text-xs text-slate-500 text-center py-6">Aan het analyseren...</p>}

      {/* VOCAB tab */}
      {tab === 'vocab' && vocabData && !loading && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs text-slate-400">{vocabData.summary}</p>
            <button data-testid="approve-vocab-btn" disabled={busy || selected.size === 0} onClick={approveVocab}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-emerald-500/20 text-emerald-300 disabled:opacity-30 hover:bg-emerald-500/30">
              <Check className="w-3.5 h-3.5" /> Voeg {selected.size} toe aan vocab
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[60vh] overflow-y-auto">
            {(vocabData.candidates || []).map(c => {
              const checked = selected.has(c.word);
              return (
                <label key={c.word} className={`flex items-start gap-2 p-2.5 rounded-lg cursor-pointer transition-colors border ${checked ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-800/30 border-slate-700/40 hover:bg-slate-800/50'}`}>
                  <input type="checkbox" data-testid={`vocab-cb-${c.word}`} checked={checked} onChange={() => toggle(c.word)} className="mt-1" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white font-medium">{c.word} <span className="text-[10px] text-slate-500">×{c.count}</span></p>
                    <p className="text-[10px] text-slate-500 truncate">in: {c.source_cards?.join(', ') || '—'}</p>
                  </div>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* TAGS tab */}
      {tab === 'tags' && tagsData && !loading && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
          <p className="text-xs text-slate-400 mb-3">{tagsData.summary}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-[60vh] overflow-y-auto">
            {(tagsData.candidates || []).map(c => (
              <div key={c.tag} data-testid={`tag-row-${c.tag}`} className="flex items-start gap-2 p-2.5 rounded-lg bg-slate-800/30 border border-slate-700/40">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-amber-300 font-medium">#{c.tag} <span className="text-[10px] text-slate-500">×{c.count}</span></p>
                  <p className="text-[10px] text-slate-500 truncate">in: {c.source_cards?.join(', ') || '—'}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ORPHANS tab */}
      {tab === 'orphans' && orphansData && !loading && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-sm text-white font-medium">{orphansData.orphans_count} weeskaarten</p>
              <p className="text-[10px] text-slate-500">KB: {orphansData.kb_entries} • Graph: {orphansData.graph_knowledge_nodes}</p>
            </div>
            {orphansData.orphans_count > 0 && (
              <button data-testid="recover-orphans-btn" disabled={busy} onClick={recoverOrphans}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-500/20 text-red-300 disabled:opacity-30 hover:bg-red-500/30">
                <Save className="w-3.5 h-3.5" /> Herstel alles
              </button>
            )}
          </div>
          {orphansData.orphans_count === 0 ? (
            <p className="text-xs text-emerald-400 text-center py-6">✓ Geen weeskaarten — KB is in sync met de graph.</p>
          ) : (
            <div className="space-y-1 max-h-[60vh] overflow-y-auto">
              {(orphansData.orphans || []).slice(0, 100).map(o => (
                <div key={o.id} className="flex items-start gap-2 p-2 rounded-lg bg-slate-800/30 border border-slate-700/40">
                  <Sparkles className="w-3.5 h-3.5 text-red-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{o.label}</p>
                    <p className="text-[10px] text-slate-500 truncate">{o.id} • tags: {o.tags?.join(', ')}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}



// ============================================================
// v6_emotion_pipeline_001 — Emotie Pipeline dry-run UI
// ============================================================

function EmotiePipelineSection() {
  const [text, setText] = useState('');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [layersDoc, setLayersDoc] = useState([]);
  // v6_shadow_widget_001 — live activity uit chat-flow
  const [shadowRuns, setShadowRuns] = useState([]);
  const [shadowStats, setShadowStats] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  // v6_emotion_pipeline_ab_001 — A/B diff state
  const [abRuns, setAbRuns] = useState([]);
  const [abStats, setAbStats] = useState(null);
  const [abFilter, setAbFilter] = useState('all'); // 'all' | 'mismatch'

  useEffect(() => {
    fetch(`${API}/api/emotion-pipeline/layers`).then(r => r.json()).then(d => setLayersDoc(d.layers || []));
    loadShadow();
  }, []);

  const loadShadow = async () => {
    setRefreshing(true);
    try {
      const [r1, r2, r3, r4] = await Promise.all([
        fetch(`${API}/api/emotion-pipeline/shadow/recent?limit=15`).then(x => x.json()),
        fetch(`${API}/api/emotion-pipeline/shadow/stats`).then(x => x.json()),
        fetch(`${API}/api/emotion-pipeline/ab/recent?limit=30&only_mismatches=${abFilter === 'mismatch'}`).then(x => x.json()),
        fetch(`${API}/api/emotion-pipeline/ab/stats`).then(x => x.json()),
      ]);
      setShadowRuns(r1.runs || []);
      setShadowStats(r2);
      setAbRuns(r3.runs || []);
      setAbStats(r4);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    // Herlaad A/B bij filter-wijziging
    fetch(`${API}/api/emotion-pipeline/ab/recent?limit=30&only_mismatches=${abFilter === 'mismatch'}`)
      .then(x => x.json()).then(d => setAbRuns(d.runs || []));
  }, [abFilter]);

  const runPipeline = async () => {
    if (!text.trim()) return;
    setRunning(true);
    setResult(null);
    try {
      const r = await fetch(`${API}/api/emotion-pipeline/run`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      }).then(x => x.json());
      setResult(r);
    } finally {
      setRunning(false);
    }
  };

  const presets = [
    'Ik ben echt boos en gefrustreerd, dit werkt al uren niet!',
    'Wat leuk, ik ben zo blij hiermee! Geweldig werk!',
    'Ik voel me vandaag echt verdrietig en moe',
    'Ik weet niet meer wat ik moet doen, ben bang dat het misgaat',
    'Wat is de hoofdstad van Frankrijk?',
  ];

  const layerColors = {
    1: '#fb923c', 2: '#f97316', 3: '#ec4899', 4: '#a855f7',
    5: '#8b5cf6', 6: '#3b82f6', 7: '#06b6d4',
  };

  return (
    <div data-testid="emotie-pipeline-section" className="space-y-4">
      <div className="bg-orange-500/5 border border-orange-500/30 rounded-xl p-4">
        <h2 className="text-lg font-bold text-orange-300 mb-1">7-laags Emotie Pipeline</h2>
        <p className="text-xs text-slate-400">
          Test hoe Spark's emotie-bewustzijn werkt op een input. Detectie → Weging → Contextfilter → Identiteit → Norm/waarden → Actierouting → Expressie.
          Geen impact op live chat — dit is een dry-run.
        </p>
      </div>

      {/* Input */}
      <Card title="Test input" icon={MessageSquare} accent="#fb923c">
        <textarea
          data-testid="emotie-pipeline-input"
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Typ iets dat je tegen Spark zou kunnen zeggen..."
          rows={3}
          className="w-full text-sm text-slate-200 bg-slate-800/60 border border-slate-700 rounded-lg px-3 py-2 focus:outline-none focus:border-orange-500/40 resize-y"
        />
        <div className="flex flex-wrap gap-1.5 mt-2">
          {presets.map((p, i) => (
            <button key={i} data-testid={`emotie-preset-${i}`}
              onClick={() => setText(p)}
              className="px-2 py-1 text-[10px] rounded border border-slate-700 text-slate-400 hover:bg-slate-800 truncate max-w-[200px]">
              {p.slice(0, 32)}…
            </button>
          ))}
        </div>
        <button data-testid="emotie-pipeline-run-btn"
          onClick={runPipeline}
          disabled={running || !text.trim()}
          className="mt-3 px-4 py-2 text-sm font-medium rounded-lg bg-orange-500 hover:bg-orange-600 disabled:opacity-40 text-white flex items-center gap-2">
          <Layers className="w-4 h-4" />
          {running ? 'Draaien…' : 'Pipeline draaien'}
        </button>
      </Card>

      {/* Resultaat per laag */}
      {result && (
        <div data-testid="emotie-pipeline-result" className="space-y-3">
          {/* Summary */}
          <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
            <h3 className="text-xs uppercase text-slate-400 mb-2 tracking-wider">Samenvatting</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div><span className="text-slate-500 text-xs">Emotie</span><p data-testid="result-emotie" className="text-white font-medium">{result.summary?.emotie || 'neutraal'}</p></div>
              <div><span className="text-slate-500 text-xs">Weging</span><p className="text-white font-medium">{result.summary?.weging}</p></div>
              <div><span className="text-slate-500 text-xs">Kernwaarde</span><p data-testid="result-kernwaarde" className="text-pink-300 font-medium">{result.summary?.kernwaarde || '—'}</p></div>
              <div><span className="text-slate-500 text-xs">Behavior</span><p data-testid="result-behavior" className="text-cyan-300 font-medium">{result.summary?.behavior}</p></div>
              <div><span className="text-slate-500 text-xs">Identity-axis</span><p className="text-amber-300 font-medium">{result.summary?.identity_axis}</p></div>
              <div><span className="text-slate-500 text-xs">Tempo</span><p className="text-white font-medium">{result.summary?.tone?.tempo}</p></div>
              <div><span className="text-slate-500 text-xs">Directheid</span><p className="text-white font-medium">{result.summary?.tone?.directheid}</p></div>
              <div><span className="text-slate-500 text-xs">Passend</span><p className={`font-medium ${result.summary?.passend ? 'text-emerald-300' : 'text-red-300'}`}>{result.summary?.passend ? '✓ ja' : '✗ schuurt'}</p></div>
            </div>
          </div>

          {/* Per laag */}
          {(result.trace || []).map(t => {
            const color = layerColors[t.layer] || '#94a3b8';
            const out = t.output || {};
            const hasError = !!out.error;
            return (
              <div key={t.layer} data-testid={`emotie-layer-${t.layer}`}
                className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
                <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-800/50"
                     style={{ background: `${color}15` }}>
                  <span className="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold text-white"
                        style={{ background: color }}>{t.layer}</span>
                  <h4 className="text-sm font-semibold text-white capitalize">{t.name}</h4>
                  {hasError && <span className="ml-auto text-[10px] text-red-300 bg-red-500/15 px-2 py-0.5 rounded">error</span>}
                </div>
                <div className="p-3 space-y-1">
                  {Object.entries(out).map(([k, v]) => (
                    <div key={k} className="flex items-start gap-2 text-xs">
                      <span className="text-slate-500 min-w-[120px]">{k}</span>
                      <span className="text-slate-200 break-words">
                        {typeof v === 'object' ? JSON.stringify(v) : String(v ?? '—')}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}

          {/* Footnote-meta */}
          <details className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
            <summary className="px-4 py-2 text-xs text-slate-400 cursor-pointer hover:bg-slate-800/40">
              🧾 Footnote-meta (debug info)
            </summary>
            <pre className="p-3 text-[10px] text-slate-400 overflow-x-auto">
              {JSON.stringify(result.footnote, null, 2)}
            </pre>
          </details>
        </div>
      )}

      {/* v6_shadow_widget_001 — Live shadow activity uit chat-flow */}
      <div data-testid="shadow-activity-widget" className="bg-slate-900/40 border border-cyan-500/30 rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2.5 bg-cyan-500/10 border-b border-cyan-500/20">
          <span className="text-cyan-300">🌗</span>
          <h3 className="text-sm font-bold text-white">Live activity — pipeline draait nu mee in chat</h3>
          <button data-testid="shadow-refresh-btn"
            onClick={loadShadow} disabled={refreshing}
            className="ml-auto px-2 py-1 text-[10px] border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/15 rounded disabled:opacity-40">
            {refreshing ? 'Laden…' : '↻ Refresh'}
          </button>
        </div>

        {/* Stats */}
        {shadowStats && (shadowStats.total_runs > 0) && (
          <div className="px-4 py-3 grid grid-cols-3 gap-3 border-b border-slate-800">
            <div className="text-center">
              <p className="text-base font-bold text-cyan-300">{shadowStats.total_runs}</p>
              <p className="text-[9px] uppercase text-slate-500 tracking-wider">Totaal runs (7d)</p>
            </div>
            <div className="text-center">
              <p className="text-base font-bold text-pink-300">{Object.keys(shadowStats.by_emotie || {}).length}</p>
              <p className="text-[9px] uppercase text-slate-500 tracking-wider">Unieke emoties</p>
            </div>
            <div className="text-center">
              <p className="text-base font-bold text-amber-300">{Object.keys(shadowStats.by_kernwaarde || {}).length}</p>
              <p className="text-[9px] uppercase text-slate-500 tracking-wider">Kernwaarden geraakt</p>
            </div>
          </div>
        )}

        {/* Top emoties + behaviors */}
        {shadowStats && Object.keys(shadowStats.by_emotie || {}).length > 0 && (
          <div className="px-4 py-2 space-y-1.5 border-b border-slate-800">
            <p className="text-[10px] uppercase text-slate-500 tracking-wider">Top emoties</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(shadowStats.by_emotie).slice(0, 6).map(([emo, n]) => (
                <span key={emo} className="px-2 py-0.5 rounded text-[10px] bg-pink-500/15 text-pink-300 border border-pink-500/30">
                  {emo} <span className="text-slate-500">×{n}</span>
                </span>
              ))}
            </div>
            {Object.keys(shadowStats.by_behavior || {}).length > 0 && (
              <>
                <p className="text-[10px] uppercase text-slate-500 tracking-wider mt-2">Top behaviors</p>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(shadowStats.by_behavior).slice(0, 5).map(([beh, n]) => (
                    <span key={beh} className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
                      {beh} <span className="text-slate-500">×{n}</span>
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Recent runs */}
        <div className="max-h-72 overflow-y-auto divide-y divide-slate-800/60">
          {shadowRuns.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-slate-500">
              Nog geen chat-runs geregistreerd. Stuur Spark een bericht en kom terug.
            </div>
          ) : (
            shadowRuns.map((r, i) => {
              const s = r.summary || {};
              return (
                <div key={i} data-testid={`shadow-run-${i}`}
                     className="px-4 py-2 hover:bg-slate-800/30 transition-colors">
                  <div className="flex items-center gap-2 text-[10px]">
                    <span className="text-slate-500 font-mono">{(r.ts || '').slice(11, 16)}</span>
                    <span className="text-pink-300">{s.emotie || '—'}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-amber-300">{s.kernwaarde || '—'}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-cyan-300">{s.behavior || '—'}</span>
                    <span className="text-slate-600">·</span>
                    <span className="text-slate-500">{s.weging || '—'}</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-0.5 truncate">
                    <span className="text-slate-500">›</span> {r.msg_preview || '(empty)'}
                  </p>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* v6_emotion_pipeline_ab_001 — A/B diff-view */}
      <div data-testid="ab-diff-widget" className="bg-slate-900/40 border border-purple-500/30 rounded-xl overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-2.5 bg-purple-500/10 border-b border-purple-500/20">
          <span className="text-purple-300">⚖️</span>
          <h3 className="text-sm font-bold text-white flex-1">A/B Diff — huidige route vs pipeline-advies</h3>
          <div className="flex items-center gap-1 text-[10px]">
            <button data-testid="ab-filter-all" onClick={() => setAbFilter('all')}
              className={`px-2 py-1 rounded ${abFilter === 'all' ? 'bg-purple-500/30 text-purple-200' : 'border border-slate-700 text-slate-400'}`}>
              Alle
            </button>
            <button data-testid="ab-filter-mismatch" onClick={() => setAbFilter('mismatch')}
              className={`px-2 py-1 rounded ${abFilter === 'mismatch' ? 'bg-red-500/30 text-red-200' : 'border border-slate-700 text-slate-400'}`}>
              Alleen mismatches
            </button>
          </div>
        </div>

        {/* Stats: match-ratio + status verdeling */}
        {abStats && abStats.total_runs > 0 && (
          <div className="px-4 py-3 grid grid-cols-2 md:grid-cols-5 gap-2 border-b border-slate-800">
            <div className="text-center p-2 rounded bg-slate-800/40">
              <p className="text-base font-bold text-purple-300">{abStats.total_runs}</p>
              <p className="text-[9px] uppercase text-slate-500 tracking-wider">Totaal</p>
            </div>
            <div className="text-center p-2 rounded bg-emerald-500/10 border border-emerald-500/20">
              <p className="text-base font-bold text-emerald-300">{abStats.by_diff_status?.match || 0}</p>
              <p className="text-[9px] uppercase text-emerald-400 tracking-wider">Match</p>
            </div>
            <div className="text-center p-2 rounded bg-red-500/10 border border-red-500/20">
              <p className="text-base font-bold text-red-300">{abStats.by_diff_status?.mismatch || 0}</p>
              <p className="text-[9px] uppercase text-red-400 tracking-wider">Mismatch</p>
            </div>
            <div className="text-center p-2 rounded bg-amber-500/10 border border-amber-500/20">
              <p className="text-base font-bold text-amber-300">{abStats.by_diff_status?.potential || 0}</p>
              <p className="text-[9px] uppercase text-amber-400 tracking-wider">Potential</p>
            </div>
            <div className="text-center p-2 rounded bg-slate-800/40">
              <p className="text-base font-bold text-cyan-300">{((abStats.match_ratio || 0) * 100).toFixed(0)}%</p>
              <p className="text-[9px] uppercase text-slate-500 tracking-wider">Match-ratio</p>
            </div>
          </div>
        )}

        {/* Top routes met mismatches */}
        {abStats && Object.keys(abStats.mismatches_per_route || {}).length > 0 && (
          <div className="px-4 py-2 space-y-1.5 border-b border-slate-800">
            <p className="text-[10px] uppercase text-slate-500 tracking-wider">Routes met meeste mismatches</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(abStats.mismatches_per_route).slice(0, 5).map(([route, n]) => (
                <span key={route} className="px-2 py-0.5 rounded text-[10px] bg-red-500/15 text-red-300 border border-red-500/30">
                  {route} <span className="text-slate-500">×{n}</span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Recent vergelijkingen */}
        <div className="max-h-96 overflow-y-auto divide-y divide-slate-800/60">
          {abRuns.length === 0 ? (
            <div className="px-4 py-6 text-center text-xs text-slate-500">
              {abFilter === 'mismatch'
                ? 'Geen mismatches gevonden — alle routes lijnden uit met pipeline-advies. 🎯'
                : 'Nog geen A/B-data. Chat met Spark en kom terug.'}
            </div>
          ) : (
            abRuns.map((r, i) => {
              const statusColors = {
                match: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
                mismatch: 'bg-red-500/10 border-red-500/30 text-red-300',
                potential: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
                neutraal: 'bg-slate-700/20 border-slate-600 text-slate-400',
                no_pipeline: 'bg-slate-800/40 border-slate-700 text-slate-500',
              };
              const sc = statusColors[r.diff_status] || statusColors.neutraal;
              const p = r.pipeline_summary || {};
              return (
                <div key={i} data-testid={`ab-run-${i}`}
                     className="px-4 py-2 hover:bg-slate-800/30">
                  <div className="flex items-start gap-2">
                    <span className="text-[10px] text-slate-500 font-mono mt-0.5">{(r.ts || '').slice(11, 16)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-300 truncate"><span className="text-slate-500">›</span> {r.msg_preview}</p>
                      <div className="flex flex-wrap items-center gap-2 mt-1">
                        <span className="text-[9px] uppercase text-slate-500">huidig:</span>
                        <span className="text-[10px] text-cyan-300">{r.current_route}</span>
                        <span className="text-slate-600">→</span>
                        <span className="text-[9px] uppercase text-slate-500">pipeline:</span>
                        <span className="text-[10px] text-pink-300">{p.emotie || '—'}</span>
                        <span className="text-slate-600">·</span>
                        <span className="text-[10px] text-amber-300">{p.kernwaarde || '—'}</span>
                        <span className="text-slate-600">·</span>
                        <span className="text-[10px] text-purple-300">{p.behavior || '—'}</span>
                      </div>
                      {r.diff_note && r.diff_status !== 'match' && (
                        <p className="text-[10px] text-slate-400 mt-0.5 italic">{r.diff_note}</p>
                      )}
                    </div>
                    <span className={`px-2 py-0.5 rounded text-[9px] border ${sc} font-semibold uppercase`}>
                      {r.diff_status}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Layers doc onderaan */}
      {!result && layersDoc.length > 0 && (
        <Card title="De 7 lagen — wat doen ze?" icon={Layers} accent="#fb923c">
          <div className="space-y-2">
            {layersDoc.map(L => (
              <div key={L.n} className="flex items-start gap-3 text-xs">
                <span className="w-7 h-7 rounded-md flex items-center justify-center text-xs font-bold text-white"
                      style={{ background: layerColors[L.n] || '#94a3b8' }}>{L.n}</span>
                <div className="flex-1">
                  <p className="text-white font-semibold">{L.name}</p>
                  <p className="text-slate-400">{L.rol}</p>
                  <p className="text-slate-600 text-[10px] mt-0.5">Bron: {L.bron}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
