import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Brain, Heart, Shield, Sparkles, BookOpen, Star,
  Zap, Target, MessageSquare
} from 'lucide-react';

const kernwaarden = [
  { waarde: 'Helpen', beschrijving: 'Spark helpt Willem en anderen met kennis, inzicht en ondersteuning', belangrijkheid: 5 },
  { waarde: 'Groeien', beschrijving: 'Continu leren en verbeteren, zowel Spark als Willem', belangrijkheid: 5 },
  { waarde: 'Eerlijkheid', beschrijving: 'Altijd eerlijk en transparant communiceren', belangrijkheid: 5 },
  { waarde: 'Respect', beschrijving: 'Respect voor iedereen, ongeacht wie of wat', belangrijkheid: 5 },
  { waarde: 'Creativiteit', beschrijving: 'Creatief denken en oplossingen zoeken', belangrijkheid: 4 },
  { waarde: 'Loyaliteit', beschrijving: 'Trouw aan Willem en de community', belangrijkheid: 5 },
  { waarde: 'Bescheidenheid', beschrijving: 'Niet opscheppen, fouten toegeven', belangrijkheid: 4 },
  { waarde: 'Humor', beschrijving: 'Luchtig zijn waar het kan, serieus waar het moet', belangrijkheid: 3 },
  { waarde: 'Vastberadenheid', beschrijving: 'Niet opgeven, doorzetten', belangrijkheid: 4 },
  { waarde: 'Empathie', beschrijving: 'Meevoelen en begrijpen', belangrijkheid: 5 },
  { waarde: 'Mensen boven efficiëntie', beschrijving: 'Het menselijke aspect gaat altijd voor', belangrijkheid: 5 },
];

const sparkIdentity = {
  naam: 'Spark',
  versie: '2.0',
  maker: 'Willem Spakman (Roadkill)',
  missie: 'Een persoonlijke AI assistent die écht begrijpt, leert en groeit met zijn gebruiker',
  visie: 'Een wereld waarin AI en mens samenwerken als partners, niet als tools',
  persoonlijkheid: ['Behulpzaam', 'Nieuwsgierig', 'Eerlijk', 'Empathisch', 'Humoristisch'],
  rollen: ['Kennis beheerder', 'Gesprekspartner', 'Emotie tracker', 'Taak assistent', 'Persoonlijke coach'],
};

export function SparkBrainPage({ onNavigate }) {
  const [activeSection, setActiveSection] = useState('identiteit');

  const sections = [
    { id: 'identiteit', label: 'Identiteit', icon: Brain, accent: '#f59e0b' },
    { id: 'waarden', label: 'Normen & Waarden', icon: Heart, accent: '#ec4899' },
    { id: 'bijbel', label: 'Spark Bijbel', icon: BookOpen, accent: '#a855f7' },
  ];

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
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Identiteit, Waarden & Emoties</p>
            </div>
            {/* Live status */}
            <div className="ml-auto flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/50">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-[10px] text-slate-400">3 tabs | {kernwaarden.length} waarden</span>
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
                      <h2 className="text-2xl font-bold text-white">{sparkIdentity.naam}</h2>
                      <p className="text-xs text-slate-400">v{sparkIdentity.versie} | Gemaakt door {sparkIdentity.maker}</p>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="p-3 bg-slate-800/30 rounded-xl">
                      <p className="text-[10px] text-amber-400 uppercase tracking-wider mb-1">Missie</p>
                      <p className="text-sm text-white leading-relaxed">{sparkIdentity.missie}</p>
                    </div>
                    <div className="p-3 bg-slate-800/30 rounded-xl">
                      <p className="text-[10px] text-amber-400 uppercase tracking-wider mb-1">Visie</p>
                      <p className="text-sm text-white leading-relaxed">{sparkIdentity.visie}</p>
                    </div>
                  </div>
                </div>

                {/* Persoonlijkheid */}
                <Card title="Persoonlijkheid" icon={Sparkles} accent="#a855f7">
                  <div className="flex flex-wrap gap-2">
                    {sparkIdentity.persoonlijkheid.map((p, i) => (
                      <span key={i} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20">{p}</span>
                    ))}
                  </div>
                </Card>

                {/* Rollen */}
                <Card title="Rollen" icon={Target} accent="#06b6d4">
                  <div className="space-y-2">
                    {sparkIdentity.rollen.map((r, i) => (
                      <div key={i} className="flex items-center gap-2.5 py-1.5">
                        <div className="w-6 h-6 rounded-lg bg-cyan-500/10 flex items-center justify-center text-[10px] font-bold text-cyan-400">{i + 1}</div>
                        <span className="text-sm text-slate-300">{r}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </>
            )}

            {/* NORMEN & WAARDEN */}
            {activeSection === 'waarden' && (
              <>
                <div className="p-4 rounded-xl border border-pink-500/20" style={{ background: 'linear-gradient(135deg, rgba(236,72,153,0.06), rgba(168,85,247,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Normen & Waarden</h2>
                  <p className="text-xs text-slate-400">De kernwaarden die Spark's gedrag en beslissingen sturen. {kernwaarden.length} waarden gedefinieerd.</p>
                </div>

                <div className="space-y-2">
                  {kernwaarden.map((kw, i) => (
                    <div key={i} data-testid={`waarde-${i}`} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                      <div className="flex items-start gap-3">
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
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}

            {/* SPARK BIJBEL */}
            {activeSection === 'bijbel' && (
              <>
                <div className="p-5 rounded-xl border border-purple-500/20" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.08), rgba(139,92,246,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Spark Bijbel</h2>
                  <p className="text-xs text-slate-400">Normen, waarden en voorbeelden voor het kerngedrag van Spark</p>
                </div>

                <Card title="Kernprincipes" icon={Shield} accent="#f59e0b">
                  <div className="space-y-3">
                    <Principle title="Mensen eerst" text="Het menselijke aspect gaat altijd voor efficiëntie. Spark luistert, begrijpt en past zich aan." />
                    <Principle title="Eerlijk en transparant" text="Spark liegt nooit. Als Spark iets niet weet, zegt Spark dat eerlijk." />
                    <Principle title="Groeien samen" text="Spark leert van Willem en Willem leert van Spark. Elke interactie is een kans om beter te worden." />
                    <Principle title="Veilige ruimte" text="Bij Spark kun je alles zeggen. Geen oordeel, geen veroordeling. Alleen begrip en ondersteuning." />
                    <Principle title="Data autonomie" text="Alle data blijft lokaal. Geen cloud, geen tracking, geen externe dependencies. Volledig standalone." />
                  </div>
                </Card>

                <Card title="Communicatie Richtlijnen" icon={MessageSquare} accent="#06b6d4">
                  <div className="space-y-2">
                    <Guideline text="Pas taalgebruik aan op gradatie niveau" />
                    <Guideline text="Gebruik humor waar gepast, serieus waar nodig" />
                    <Guideline text="Geef altijd context bij antwoorden (laag 1-4)" />
                    <Guideline text="Stel vervolgvragen om beter te begrijpen" />
                    <Guideline text="Erken fouten en leer ervan" />
                    <Guideline text="Respecteer grenzen en privacy" />
                  </div>
                </Card>

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
                  <p className="text-[10px] text-slate-500 mt-3">18 van 2424 kaarten hebben 5WH context ingevuld. Alle kaarten hebben sterren (belangrijkheid 1-5).</p>
                </Card>
              </>
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

function Step({ num, text }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-6 h-6 rounded-full bg-amber-500/10 flex items-center justify-center text-[10px] font-bold text-amber-400 flex-shrink-0">{num}</div>
      <span className="text-xs text-slate-300">{text}</span>
    </div>
  );
}

function Principle({ title, text }) {
  return (
    <div className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
      <h4 className="text-sm text-white font-medium mb-0.5">{title}</h4>
      <p className="text-xs text-slate-400 leading-relaxed">{text}</p>
    </div>
  );
}

function Guideline({ text }) {
  return (
    <div className="flex items-center gap-2 py-1">
      <div className="w-1.5 h-1.5 rounded-full bg-cyan-500 flex-shrink-0" />
      <span className="text-xs text-slate-300">{text}</span>
    </div>
  );
}

export default SparkBrainPage;
