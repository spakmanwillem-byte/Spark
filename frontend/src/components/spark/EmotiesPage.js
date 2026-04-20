import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Sparkles, Heart, Smile, Frown, AlertTriangle, Cloud,
  Activity, Zap, BookOpen, ChevronDown, ChevronRight,
  MessageSquare, Target, Shield
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const emotieConfig = [
  { id: 'blij', label: 'Blij', color: '#22c55e', icon: Smile, desc: 'Positieve emoties: blijdschap, vreugde, euforie' },
  { id: 'boos', label: 'Boos', color: '#ef4444', icon: Frown, desc: 'Woede, irritatie, frustratie' },
  { id: 'bang', label: 'Bang', color: '#a855f7', icon: AlertTriangle, desc: 'Angst, bezorgdheid, nervositeit' },
  { id: 'bedroefd', label: 'Bedroefd', color: '#3b82f6', icon: Cloud, desc: 'Verdriet, teleurstelling, gemis' },
];

export function EmotiesPage({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('overzicht');
  const [sparkState, setSparkState] = useState(null);
  const [learnedCounts, setLearnedCounts] = useState(null);
  const [allEmotions, setAllEmotions] = useState(null);
  const [testText, setTestText] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [expandedEmo, setExpandedEmo] = useState(null);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/chat/emotions/state`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/chat/emotions/learned`).then(r => r.json()).catch(() => null),
      fetch(`${API}/api/chat/emotions/all`).then(r => r.json()).catch(() => null),
    ]).then(([state, learned, all]) => {
      setSparkState(state);
      setLearnedCounts(learned);
      setAllEmotions(all);
    });
  }, []);

  const handleTestEmotion = async () => {
    if (!testText.trim()) return;
    setTesting(true);
    try {
      const res = await fetch(`${API}/api/chat/emotions/detect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: testText }),
      });
      const data = await res.json();
      setTestResult(data);
    } catch {
      setTestResult({ detected: false, error: true });
    }
    setTesting(false);
  };

  const tabs = [
    { id: 'overzicht', label: 'Overzicht', icon: Activity },
    { id: 'detectie', label: 'Live Detectie', icon: Zap },
    { id: 'sub-emoties', label: 'Sub-Emoties', icon: Heart },
    { id: 'systeem', label: 'Hoe het werkt', icon: BookOpen },
  ];

  const totalLearned = learnedCounts ? Object.values(learnedCounts).reduce((a, b) => a + b, 0) : 0;

  return (
    <MainLayout activePage="emotions" onNavigate={onNavigate}>
      <div data-testid="emoties-page" className="h-full flex flex-col">

        {/* Banner */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #f43f5e)' }}>
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Emotie Systeem</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Hybride Detectie Engine</p>
            </div>
            {sparkState && (
              <div className="ml-auto flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-800/50">
                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-[10px] text-slate-400 capitalize">Spark: {sparkState.state || 'neutral'}</span>
                <span className="text-[10px] text-slate-500">({Math.round((sparkState.intensity || 0.5) * 100)}%)</span>
              </div>
            )}
          </div>
          <div className="flex overflow-x-auto gap-0">
            {tabs.map(t => {
              const isActive = activeTab === t.id;
              return (
                <button key={t.id} data-testid={`emotie-tab-${t.id}`} onClick={() => setActiveTab(t.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
                  style={{ color: isActive ? '#ec4899' : '#94a3b8' }}>
                  <t.icon className="w-3.5 h-3.5" />
                  {t.label}
                  {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full bg-pink-500" />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* OVERZICHT */}
            {activeTab === 'overzicht' && (
              <>
                {/* Huidige staat */}
                <div className="p-5 rounded-2xl border border-green-500/20" style={{ background: 'linear-gradient(135deg, rgba(34,197,94,0.06), rgba(16,185,129,0.04))' }}>
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center">
                      <Smile className="w-8 h-8 text-green-400" />
                    </div>
                    <div>
                      <p className="text-[10px] text-green-400 uppercase tracking-wider mb-1">Spark's Huidige Staat</p>
                      <p className="text-xl font-bold text-white capitalize">{sparkState?.state || 'Neutral'}</p>
                      <p className="text-xs text-slate-400">Intensiteit: {Math.round((sparkState?.intensity || 0.5) * 100)}%</p>
                      {sparkState?.triggered_by && <p className="text-[10px] text-slate-500 mt-0.5">Trigger: {sparkState.triggered_by}</p>}
                    </div>
                  </div>
                </div>

                {/* 4 Basis Emoties */}
                <div className="grid grid-cols-2 gap-3">
                  {emotieConfig.map(e => {
                    const EIcon = e.icon;
                    const learnedCount = learnedCounts?.[e.id] || 0;
                    return (
                      <div key={e.id} data-testid={`emotie-card-${e.id}`} className="p-4 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                        <div className="flex items-center gap-2 mb-2">
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${e.color}15` }}>
                            <EIcon className="w-4 h-4" style={{ color: e.color }} />
                          </div>
                          <h4 className="text-sm font-semibold text-white">{e.label}</h4>
                        </div>
                        <p className="text-[11px] text-slate-400 mb-3">{e.desc}</p>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">Static triggers</span>
                          {learnedCount > 0 && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: `${e.color}15`, color: e.color }}>
                              +{learnedCount} geleerd
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                    <p className="text-lg font-bold text-white">4</p>
                    <p className="text-[10px] text-slate-500">Basis Emoties</p>
                  </div>
                  <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                    <p className="text-lg font-bold text-pink-400">{totalLearned}</p>
                    <p className="text-[10px] text-slate-500">Geleerde Woorden</p>
                  </div>
                  <div className="p-3 bg-slate-900/50 border border-slate-800 rounded-xl text-center">
                    <p className="text-lg font-bold text-amber-400">6</p>
                    <p className="text-[10px] text-slate-500">Stappen Pipeline</p>
                  </div>
                </div>

                {/* Dynamisch leren uitleg */}
                <Card title="Dynamisch Leren" icon={BookOpen} accent="#3b82f6">
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Tag knowledge cards met <code className="px-1.5 py-0.5 bg-slate-800 rounded text-green-400 text-[10px]">#emotie-blij</code>, <code className="px-1.5 py-0.5 bg-slate-800 rounded text-red-400 text-[10px]">#emotie-boos</code>, <code className="px-1.5 py-0.5 bg-slate-800 rounded text-purple-400 text-[10px]">#emotie-bang</code> of <code className="px-1.5 py-0.5 bg-slate-800 rounded text-blue-400 text-[10px]">#emotie-bedroefd</code> om Spark nieuwe emotie-woorden te leren.
                  </p>
                </Card>
              </>
            )}

            {/* LIVE DETECTIE */}
            {activeTab === 'detectie' && (
              <>
                <Card title="Test Emotie Detectie" icon={Zap} accent="#f59e0b">
                  <div className="space-y-3">
                    <p className="text-xs text-slate-400">Typ een zin om te testen welke emotie Spark detecteert:</p>
                    <div className="flex gap-2">
                      <input
                        data-testid="emotie-test-input"
                        type="text"
                        value={testText}
                        onChange={e => setTestText(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleTestEmotion()}
                        placeholder="Bijv: Ik ben zo blij vandaag!"
                        className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-xl text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
                      />
                      <button
                        data-testid="emotie-test-btn"
                        onClick={handleTestEmotion}
                        disabled={testing}
                        className="px-4 py-2 bg-amber-500/20 text-amber-400 rounded-xl hover:bg-amber-500/30 transition-colors text-sm font-medium disabled:opacity-50"
                      >
                        {testing ? 'Bezig...' : 'Detecteer'}
                      </button>
                    </div>
                  </div>
                </Card>

                {testResult && (
                  <div data-testid="emotie-test-result" className={`p-5 rounded-xl border ${testResult.detected ? 'border-green-500/20 bg-green-500/5' : 'border-slate-700 bg-slate-900/50'}`}>
                    {testResult.detected && testResult.emotion ? (
                      <div className="space-y-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ background: `${emotieConfig.find(e => e.id === testResult.emotion.emotion)?.color || '#64748b'}15` }}>
                            {testResult.emotion.emoji || '?'}
                          </div>
                          <div>
                            <p className="text-lg font-bold text-white capitalize">{testResult.emotion.emotion}</p>
                            <p className="text-xs text-slate-400">Score: {testResult.emotion.score} | Intensiteit: {Math.round(testResult.emotion.intensity * 100)}%</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-[10px] text-slate-500">Triggers:</span>
                          {testResult.emotion.triggered_words?.map((w, i) => (
                            <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400">{w}</span>
                          ))}
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-500">Bron:</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">{testResult.emotion.source}</span>
                        </div>
                        {testResult.emotion.empathic_response && (
                          <div className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/50">
                            <p className="text-[10px] text-pink-400 uppercase tracking-wider mb-1">Empathisch Antwoord</p>
                            <p className="text-sm text-white">{testResult.emotion.empathic_response}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-4">
                        <p className="text-sm text-slate-400">Geen emotie gedetecteerd in deze tekst.</p>
                        <p className="text-[10px] text-slate-500 mt-1">Probeer woorden zoals "blij", "boos", "bang" of "verdrietig"</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Snelle tests */}
                <Card title="Snelle Tests" icon={MessageSquare} accent="#06b6d4">
                  <div className="flex flex-wrap gap-2">
                    {['Ik ben zo blij vandaag!', 'Dit maakt me boos', 'Ik ben bang voor morgen', 'Ik voel me verdrietig', 'Geweldig nieuws!', 'Ik ben woedend en gefrustreerd'].map((t, i) => (
                      <button key={i} onClick={() => { setTestText(t); }}
                        className="text-[11px] px-3 py-1.5 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-300 hover:text-white hover:border-slate-600 transition-colors">
                        {t}
                      </button>
                    ))}
                  </div>
                </Card>
              </>
            )}

            {/* SUB-EMOTIES */}
            {activeTab === 'sub-emoties' && (
              <>
                <div className="p-4 rounded-xl border border-pink-500/20" style={{ background: 'linear-gradient(135deg, rgba(236,72,153,0.06), rgba(244,63,94,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Spark's Emotie Profielen</h2>
                  <p className="text-xs text-slate-400">Elke emotie heeft sub-toestanden met eigen gedrag, woordenlimiet en XP modifier.</p>
                </div>

                {allEmotions?.emotions && Object.entries(allEmotions.emotions).map(([key, emo]) => {
                  const isExpanded = expandedEmo === key;
                  const config = emotieConfig.find(e => key.startsWith(e.id) || (key === 'happy' && e.id === 'blij') || (key === 'angry' && e.id === 'boos') || (key === 'scared' && e.id === 'bang') || (key === 'sad' && e.id === 'bedroefd'));
                  const color = config?.color || '#94a3b8';
                  const subEmotions = emo.sub_emotions || {};

                  return (
                    <div key={key} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                      <button onClick={() => setExpandedEmo(isExpanded ? null : key)}
                        className="w-full flex items-center justify-between p-4 hover:bg-slate-800/20 transition-colors">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
                            <Heart className="w-4 h-4" style={{ color }} />
                          </div>
                          <div className="text-left">
                            <h4 className="text-sm font-semibold text-white capitalize">{key}</h4>
                            <p className="text-[10px] text-slate-500">{emo.description?.slice(0, 60)}...</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{Object.keys(subEmotions).length} sub</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: `${color}15`, color }}>{emo.tone}</span>
                          {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                        </div>
                      </button>
                      {isExpanded && (
                        <div className="px-4 pb-4 space-y-2">
                          {Object.entries(subEmotions).map(([subKey, sub]) => (
                            <div key={subKey} className="p-3 bg-slate-800/30 rounded-xl border border-slate-700/30">
                              <div className="flex items-center justify-between mb-1">
                                <h5 className="text-sm text-white font-medium capitalize">{subKey}</h5>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-400 rounded-full">max {sub.max_words}w</span>
                                  <span className="text-[10px] px-2 py-0.5 rounded-full" style={{ background: `${color}15`, color }}>XP x{sub.xp_modifier}</span>
                                </div>
                              </div>
                              <p className="text-[11px] text-slate-400 mb-2">{sub.description}</p>
                              {sub.examples?.length > 0 && (
                                <div className="flex flex-wrap gap-1.5">
                                  {sub.examples.map((ex, i) => (
                                    <span key={i} className="text-[10px] px-2 py-0.5 bg-slate-800/50 text-slate-500 rounded italic">"{ex}"</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </>
            )}

            {/* HOE HET WERKT */}
            {activeTab === 'systeem' && (
              <>
                <div className="p-4 rounded-xl border border-amber-500/20" style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.06), rgba(234,88,12,0.04))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Emotie Detectie Pipeline</h2>
                  <p className="text-xs text-slate-400">Hybride systeem: statische triggers + dynamisch geleerde woorden uit knowledge cards</p>
                </div>

                <Card title="6-Stappen Pipeline" icon={Target} accent="#f59e0b">
                  <div className="space-y-3">
                    <Step num={1} text="Bericht binnenkomt → woorden worden geanalyseerd" color="#f59e0b" />
                    <Step num={2} text="Statische triggers checken (emotion_triggers.json)" color="#3b82f6" />
                    <Step num={3} text="Geleerde triggers checken (knowledge cards met #emotie-* tags)" color="#22c55e" />
                    <Step num={4} text="Score berekenen per emotie (anti-misbruik: max 3x per woord)" color="#a855f7" />
                    <Step num={5} text="Dominante emotie bepalen + intensiteit (0-100%)" color="#ec4899" />
                    <Step num={6} text="Empathisch antwoord genereren op basis van emotie" color="#06b6d4" />
                  </div>
                </Card>

                <Card title="Anti-Misbruik" icon={Shield} accent="#ef4444">
                  <div className="space-y-2">
                    <p className="text-xs text-slate-400">Elk woord telt maximaal <strong className="text-white">3x</strong> per bericht. Herhaling van "blij blij blij blij blij" telt dus maar 3x.</p>
                    <p className="text-xs text-slate-400">Minimale score drempel: <strong className="text-white">3 punten</strong>. Lage scores worden genegeerd.</p>
                  </div>
                </Card>

                <Card title="Bronnen" icon={BookOpen} accent="#22c55e">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg">
                      <span className="text-[10px] px-2 py-0.5 bg-amber-500/10 text-amber-400 rounded-full font-medium">Static</span>
                      <span className="text-xs text-slate-300">emotion_triggers.json — vaste trigger woorden met puntenwaarde</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg">
                      <span className="text-[10px] px-2 py-0.5 bg-green-500/10 text-green-400 rounded-full font-medium">Learned</span>
                      <span className="text-xs text-slate-300">Knowledge cards met #emotie-* tags — dynamisch geleerd</span>
                    </div>
                    <div className="flex items-center gap-2 p-2 bg-slate-800/30 rounded-lg">
                      <span className="text-[10px] px-2 py-0.5 bg-pink-500/10 text-pink-400 rounded-full font-medium">Both</span>
                      <span className="text-xs text-slate-300">Combinatie van static + learned triggers op hetzelfde woord</span>
                    </div>
                  </div>
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

function Step({ num, text, color = '#f59e0b' }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0" style={{ background: `${color}15`, color }}>
        {num}
      </div>
      <span className="text-xs text-slate-300">{text}</span>
    </div>
  );
}

export default EmotiesPage;
