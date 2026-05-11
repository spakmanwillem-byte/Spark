import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { SystemArchive } from './SystemArchive';
import {
  Settings, Monitor, Volume2, Link2, Sparkles, HelpCircle,
  Save, Shield, Clock, Bug, RefreshCw, Palette, Sun, Moon,
  Mic, Speech, Music, Upload, Play, Trash2, Edit3, Plus,
  Keyboard, MessageSquare, Brain, Trophy, ChevronDown, ChevronRight,
  Zap, Globe, Wifi, Database, Server, Bell, Eye, EyeOff,
  ToggleLeft, ToggleRight, Archive
} from 'lucide-react';

export function InstellingenPage({ onNavigate }) {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('algemeen');
  const [saving, setSaving] = useState(false);

  // Local state for all settings (frontend-only for now)
  const [settings, setSettings] = useState({
    heartbeat_interval: 30,
    session_timeout: 5,
    debug_mode: false,
    auto_save: true,
    mood_colors: true,
    theme: 'dark',
    notification_sound: true,
    master_volume: 70,
    enable_user_sounds: false,
    tts_enabled: false,
    tts_voice: 'nova',
    tts_speed: 1.0,
    tts_auto_play: false,
    stt_enabled: false,
    stt_language: 'nl',
    stt_push_to_talk: true,
  });

  const [soundMappings] = useState([
    { id: 1, word: 'succes', file: 'success.mp3', frequency: 'every', play_count: 42 },
    { id: 2, word: 'alarm', file: 'alarm.wav', frequency: 'first_only', play_count: 7 },
    { id: 3, word: 'zagen', file: 'saw_sound.mp3', frequency: 'every_3', play_count: 15 },
  ]);

  const set = (key, val) => setSettings(s => ({ ...s, [key]: val }));

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 800);
  };

  const tabs = [
    { id: 'algemeen', label: 'Algemeen', icon: Settings, accent: '#f59e0b' },
    { id: 'beeld', label: 'Beeld', icon: Palette, accent: '#a855f7' },
    { id: 'geluid', label: 'Geluid', icon: Volume2, accent: '#3b82f6' },
    { id: 'archief', label: 'Archief', icon: Archive, accent: '#10b981' },
    { id: 'integraties', label: 'Integraties', icon: Link2, accent: '#06b6d4' },
    { id: 'features', label: 'Features', icon: Sparkles, accent: '#22c55e' },
    { id: 'tips', label: 'Tips & Hulp', icon: HelpCircle, accent: '#f97316' },
  ];

  return (
    <MainLayout activePage="settings" onNavigate={onNavigate}>
      <div data-testid="instellingen-page" className="h-full flex flex-col">

        {/* Top banner with tabs */}
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-0">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #f59e0b, #ea580c)' }}>
              <Settings className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Instellingen</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">Spark Core Configuratie</p>
            </div>
          </div>
          <div className="flex overflow-x-auto gap-0 scrollbar-hide">
            {tabs.map(tab => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  data-testid={`settings-tab-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium transition-colors whitespace-nowrap flex-shrink-0"
                  style={{ color: isActive ? tab.accent : '#94a3b8' }}
                >
                  <tab.icon className="w-3.5 h-3.5" />
                  {tab.label}
                  {isActive && <span className="absolute bottom-0 left-0 right-0 h-[2px] rounded-full" style={{ background: tab.accent }} />}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* ====== ALGEMEEN ====== */}
            {activeTab === 'algemeen' && (
              <>
                <SettingsCard title="Sessie Instellingen" icon={Shield} accent="#f59e0b">
                  <NumberField label="Heartbeat Interval" sub="Hoe vaak de sessie wordt ge-refresh (seconden)" value={settings.heartbeat_interval} onChange={v => set('heartbeat_interval', v)} unit="sec" />
                  <NumberField label="Sessie Timeout" sub="Minuten inactiviteit voor auto-logout" value={settings.session_timeout} onChange={v => set('session_timeout', v)} unit="min" />
                  <Divider />
                  <Toggle label="Auto-save" sub="Wijzigingen automatisch opslaan" checked={settings.auto_save} onChange={v => set('auto_save', v)} color="#22c55e" />
                  <Toggle label="Debug Mode" sub="Extra logging en diagnostische informatie" checked={settings.debug_mode} onChange={v => set('debug_mode', v)} color="#ef4444" />
                </SettingsCard>

                <SettingsCard title="Systeem Info" icon={Server} accent="#3b82f6">
                  <InfoRow label="Versie" value="Spark Core 2.0" />
                  <InfoRow label="Backend" value="FastAPI + JSON Storage" />
                  <InfoRow label="Frontend" value="React + Tailwind CSS" />
                  <InfoRow label="Modules" value="Auth, Knowledge, Files, Achievements" />
                  <InfoRow label="Database" value="Lokale JSON bestanden (standalone)" />
                </SettingsCard>

                <SaveButton saving={saving} onClick={handleSave} />
              </>
            )}

            {/* ====== BEELD ====== */}
            {activeTab === 'beeld' && (
              <>
                <SettingsCard title="Visuele Instellingen" icon={Palette} accent="#a855f7">
                  <Toggle label="Mood Colors" sub="Interface kleurt mee met Spark's emotie" checked={settings.mood_colors} onChange={v => set('mood_colors', v)} color="#a855f7" />
                  <Divider />
                  <SelectField label="Theme" value={settings.theme} onChange={v => set('theme', v)} options={[
                    { value: 'dark', label: 'Dark (standaard)' },
                    { value: 'light', label: 'Light (coming soon)', disabled: true },
                    { value: 'auto', label: 'Auto (coming soon)', disabled: true },
                  ]} />
                </SettingsCard>

                <SettingsCard title="Sidebar" icon={Monitor} accent="#06b6d4">
                  <InfoRow label="Positie" value="Links (vast)" />
                  <InfoRow label="Inklapbaar" value="Ja" />
                  <InfoRow label="Secties" value="Workspace, Spark AI, Modules, Beheer" />
                </SettingsCard>

                <SaveButton saving={saving} onClick={handleSave} />
              </>
            )}

            {/* ====== GELUID ====== */}
            {activeTab === 'geluid' && (
              <>
                <SettingsCard title="Audio Instellingen" icon={Volume2} accent="#3b82f6">
                  <SliderField label="Master Volume" value={settings.master_volume} onChange={v => set('master_volume', v)} unit="%" color="#3b82f6" />
                  <Toggle label="Notification Sounds" sub="Geluiden bij meldingen" checked={settings.notification_sound} onChange={v => set('notification_sound', v)} color="#3b82f6" />
                </SettingsCard>

                <SettingsCard title="Geluid Uploaden" icon={Upload} accent="#22c55e">
                  <p className="text-xs text-slate-400 mb-4">
                    Upload geluiden en koppel ze aan woorden. Bijvoorbeeld: "zagen" → zaag-geluid.mp3
                  </p>
                  <div className="p-6 border-2 border-dashed border-slate-700 rounded-xl text-center hover:border-blue-500/40 transition-colors cursor-pointer">
                    <Music className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-sm text-slate-400">Sleep een audio bestand hierheen</p>
                    <p className="text-[10px] text-slate-600 mt-1">Ondersteund: MP3, WAV, OGG</p>
                  </div>
                </SettingsCard>

                <SettingsCard title={`Jouw Geluiden (${soundMappings.length})`} icon={Music} accent="#a855f7">
                  {soundMappings.length === 0 ? (
                    <p className="text-sm text-slate-500 text-center py-6">Nog geen geluiden geüpload</p>
                  ) : (
                    <div className="space-y-2">
                      {soundMappings.map(m => (
                        <div key={m.id} className="flex items-center gap-3 p-3 bg-slate-800/40 rounded-xl">
                          <div className="w-9 h-9 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                            <Music className="w-4 h-4 text-purple-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-white font-medium">{m.word}</p>
                            <p className="text-[10px] text-slate-500">{m.file} &middot; {m.frequency === 'every' ? 'Elke keer' : m.frequency === 'first_only' ? 'Eerste keer' : `Elke ${m.frequency.split('_')[1]}e keer`} &middot; {m.play_count}x afgespeeld</p>
                          </div>
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <button className="p-1.5 hover:bg-blue-500/10 text-blue-400 rounded-lg transition-colors"><Play className="w-3.5 h-3.5" /></button>
                            <button className="p-1.5 hover:bg-amber-500/10 text-amber-400 rounded-lg transition-colors"><Edit3 className="w-3.5 h-3.5" /></button>
                            <button className="p-1.5 hover:bg-red-500/10 text-red-400 rounded-lg transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </SettingsCard>

                <SaveButton saving={saving} onClick={handleSave} />
              </>
            )}

            {/* ====== ARCHIEF (Systeem) ====== */}
            {activeTab === 'archief' && (
              <SystemArchive currentUserId={user?.id} />
            )}

            {/* ====== INTEGRATIES ====== */}
            {activeTab === 'integraties' && (
              <>
                <SettingsCard title="Externe Koppelingen" icon={Globe} accent="#06b6d4">
                  <IntegrationRow name="Bitvavo" sub="Crypto trading API" status="niet verbonden" color="#f59e0b" />
                  <IntegrationRow name="OpenAI" sub="GPT & TTS/STT" status="niet verbonden" color="#10b981" />
                  <IntegrationRow name="Telegram" sub="Bot notificaties" status="niet verbonden" color="#3b82f6" />
                  <IntegrationRow name="Discord" sub="Community webhook" status="niet verbonden" color="#5865f2" />
                </SettingsCard>

                <SettingsCard title="API Configuratie" icon={Database} accent="#a855f7">
                  <InfoRow label="Storage" value="Lokale JSON bestanden" />
                  <InfoRow label="Auth" value="JWT Token-based" />
                  <InfoRow label="Modules" value="4 actief" />
                  <p className="text-xs text-slate-500 mt-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/50">
                    Spark Core draait volledig standalone. Geen cloud dependencies nodig. Alle data blijft lokaal.
                  </p>
                </SettingsCard>
              </>
            )}

            {/* ====== FEATURES ====== */}
            {activeTab === 'features' && (
              <>
                <SettingsCard title="Feature Toggles" icon={Sparkles} accent="#22c55e">
                  <FeatureToggle icon={Speech} label="Text-to-Speech (TTS)" sub="Spark's antwoorden voorlezen" checked={settings.tts_enabled} onChange={v => set('tts_enabled', v)} color="#22c55e" />
                  {settings.tts_enabled && (
                    <div className="ml-8 pl-4 border-l-2 border-green-500/20 space-y-3 mt-2">
                      <SelectField label="Stem" value={settings.tts_voice} onChange={v => set('tts_voice', v)} options={[
                        { value: 'nova', label: 'Nova (vrouwelijk)' },
                        { value: 'onyx', label: 'Onyx (mannelijk)' },
                        { value: 'echo', label: 'Echo (neutraal)' },
                        { value: 'alloy', label: 'Alloy (warm)' },
                      ]} />
                      <SliderField label="Snelheid" value={settings.tts_speed * 100} onChange={v => set('tts_speed', v / 100)} unit="x" color="#22c55e" max={200} />
                      <Toggle label="Auto-play" sub="Automatisch afspelen na antwoord" checked={settings.tts_auto_play} onChange={v => set('tts_auto_play', v)} color="#22c55e" />
                    </div>
                  )}
                  <Divider />
                  <FeatureToggle icon={Mic} label="Speech-to-Text (STT)" sub="Spraakherkenning voor input" checked={settings.stt_enabled} onChange={v => set('stt_enabled', v)} color="#3b82f6" />
                  {settings.stt_enabled && (
                    <div className="ml-8 pl-4 border-l-2 border-blue-500/20 space-y-3 mt-2">
                      <SelectField label="Taal" value={settings.stt_language} onChange={v => set('stt_language', v)} options={[
                        { value: 'nl', label: 'Nederlands' },
                        { value: 'en', label: 'English' },
                        { value: 'de', label: 'Deutsch' },
                      ]} />
                      <Toggle label="Push-to-Talk" sub="Houd knop ingedrukt om te spreken" checked={settings.stt_push_to_talk} onChange={v => set('stt_push_to_talk', v)} color="#3b82f6" />
                    </div>
                  )}
                  <Divider />
                  <FeatureToggle icon={Music} label="Eigen Geluiden" sub="Speel privé geluiden af (standaard uit tegen overlap)" checked={settings.enable_user_sounds} onChange={v => set('enable_user_sounds', v)} color="#a855f7" />
                </SettingsCard>

                <SaveButton saving={saving} onClick={handleSave} />
              </>
            )}

            {/* ====== TIPS & HULP ====== */}
            {activeTab === 'tips' && (
              <>
                <div className="p-5 rounded-xl border border-orange-500/20" style={{ background: 'linear-gradient(135deg, rgba(249,115,22,0.08), rgba(245,158,11,0.05))' }}>
                  <h2 className="text-lg font-bold text-white mb-1">Tips & Hulp</h2>
                  <p className="text-xs text-slate-400">Leer Spark Core beter kennen en ontdek handige shortcuts</p>
                </div>

                <SettingsCard title="Keyboard Shortcuts" icon={Keyboard} accent="#f97316">
                  <ShortcutRow keys="Enter" desc="Verstuur bericht" />
                  <ShortcutRow keys="Shift + Enter" desc="Nieuwe regel in bericht" />
                  <ShortcutRow keys="Ctrl + K" desc="Focus op chat input" />
                  <ShortcutRow keys="Ctrl + S" desc="Bestand opslaan (in editor)" />
                </SettingsCard>

                <SettingsCard title="Feature Tips" icon={Zap} accent="#22c55e">
                  <TipCard icon={MessageSquare} title="Natuurlijke Taal" color="#3b82f6"
                    text='Gebruik natuurlijke taal! Probeer "bekijk mijn achievements" of "hoeveel XP heb ik?". Spark begrijpt je vragen.' />
                  <TipCard icon={Brain} title="Knowledge Cards" color="#22c55e"
                    text='Voeg nieuwe woorden toe via de Kennisbank. Je verdient XP voor elke nieuwe card! Gebruik sterren voor belangrijkheid.' />
                  <TipCard icon={Trophy} title="Achievements" color="#a855f7"
                    text="Unlock achievements door woorden te leren en XP te verzamelen. Check je voortgang onder Modules → Achievements!" />
                  <TipCard icon={Volume2} title="Geluiden Koppelen" color="#f59e0b"
                    text="Upload audio bestanden en koppel ze aan keywords in Geluid tab. Handig voor soundeffects of eigen triggers!" />
                </SettingsCard>

                <SettingsCard title="Veelgestelde Vragen" icon={HelpCircle} accent="#f97316">
                  <FaqItem q="Hoe verdien ik XP?" a="Je verdient XP door nieuwe knowledge cards te maken, achievements te unlocken, en actief te zijn in gesprekken met Spark." />
                  <FaqItem q="Wat is Gradatie?" a="Gradatie bepaalt je toegangsniveau: 1 = Eigenaar, 2 = Familie, 3 = Vrienden, 4 = Collega's, 5-7 = Community/Winkel." />
                  <FaqItem q="Hoe werkt de Verbanden pagina?" a="De Verbanden pagina toont alle knowledge cards als een netwerk met relaties. Je kunt inzoomen, filteren en kaarten bekijken." />
                  <FaqItem q="Waar wordt mijn data opgeslagen?" a="Alles wordt lokaal opgeslagen in JSON bestanden. Geen cloud, geen externe dependencies. Volledig standalone." />
                </SettingsCard>
              </>
            )}

          </div>
        </div>
      </div>
    </MainLayout>
  );
}

/* === Reusable Components === */

function SettingsCard({ title, icon: Icon, accent, children }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800/50">
        <Icon className="w-4 h-4" style={{ color: accent }} />
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <div className="p-4 space-y-3">{children}</div>
    </div>
  );
}

function Toggle({ label, sub, checked, onChange, color }) {
  return (
    <label className="flex items-center justify-between cursor-pointer group">
      <div>
        <p className="text-sm text-white">{label}</p>
        {sub && <p className="text-[10px] text-slate-500">{sub}</p>}
      </div>
      <button
        data-testid={`toggle-${label.toLowerCase().replace(/\s/g, '-')}`}
        onClick={() => onChange(!checked)}
        className="relative w-10 h-5 rounded-full transition-colors flex-shrink-0"
        style={{ background: checked ? color : '#334155' }}
      >
        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${checked ? 'translate-x-5.5 left-[22px]' : 'left-[2px]'}`} />
      </button>
    </label>
  );
}

function NumberField({ label, sub, value, onChange, unit }) {
  return (
    <div>
      <p className="text-sm text-white mb-1">{label}</p>
      {sub && <p className="text-[10px] text-slate-500 mb-2">{sub}</p>}
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value}
          onChange={e => onChange(parseInt(e.target.value) || 0)}
          className="w-24 px-3 py-1.5 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none focus:border-amber-500/40"
        />
        {unit && <span className="text-xs text-slate-500">{unit}</span>}
      </div>
    </div>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <div>
      <p className="text-xs text-slate-400 mb-1.5">{label}</p>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none"
      >
        {options.map(o => (
          <option key={o.value} value={o.value} disabled={o.disabled}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

function SliderField({ label, value, onChange, unit, color, max = 100 }) {
  return (
    <div>
      <div className="flex justify-between mb-1.5">
        <p className="text-xs text-slate-400">{label}</p>
        <p className="text-xs font-medium text-white">{unit === 'x' ? (value / 100).toFixed(1) + 'x' : value + unit}</p>
      </div>
      <input
        type="range" min="0" max={max} value={value}
        onChange={e => onChange(parseInt(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{ background: `linear-gradient(to right, ${color} ${(value/max)*100}%, #1e293b ${(value/max)*100}%)` }}
      />
    </div>
  );
}

function FeatureToggle({ icon: Icon, label, sub, checked, onChange, color }) {
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${color}15` }}>
        <Icon className="w-4 h-4" style={{ color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium">{label}</p>
        <p className="text-[10px] text-slate-500">{sub}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className="relative w-10 h-5 rounded-full transition-colors flex-shrink-0"
        style={{ background: checked ? color : '#334155' }}
      >
        <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${checked ? 'left-[22px]' : 'left-[2px]'}`} />
      </button>
    </div>
  );
}

function IntegrationRow({ name, sub, status, color }) {
  const connected = status === 'verbonden';
  return (
    <div className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
      <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0" style={{ background: `${color}15` }}>
        <Globe className="w-4 h-4" style={{ color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium">{name}</p>
        <p className="text-[10px] text-slate-500">{sub}</p>
      </div>
      <span className={`text-[10px] px-2.5 py-1 rounded-full font-medium ${connected ? 'bg-green-500/10 text-green-400' : 'bg-slate-700/50 text-slate-500'}`}>
        {status}
      </span>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-center justify-between py-1.5">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs text-slate-300 font-medium">{value}</span>
    </div>
  );
}

function ShortcutRow({ keys, desc }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 bg-slate-800/30 rounded-lg">
      <span className="text-xs text-slate-300">{desc}</span>
      <code className="text-[10px] px-2.5 py-1 bg-slate-800 border border-slate-700 rounded text-slate-400 font-mono">{keys}</code>
    </div>
  );
}

function TipCard({ icon: Icon, title, text, color }) {
  return (
    <div className="p-3 rounded-xl border" style={{ background: `${color}08`, borderColor: `${color}20` }}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color }} />
        <div>
          <p className="text-sm text-white font-medium mb-0.5">{title}</p>
          <p className="text-xs text-slate-400 leading-relaxed">{text}</p>
        </div>
      </div>
    </div>
  );
}

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <button onClick={() => setOpen(!open)} className="w-full text-left p-3 bg-slate-800/30 rounded-xl transition-colors hover:bg-slate-800/50">
      <div className="flex items-center justify-between">
        <span className="text-sm text-white font-medium">{q}</span>
        {open ? <ChevronDown className="w-3.5 h-3.5 text-slate-500" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-500" />}
      </div>
      {open && <p className="text-xs text-slate-400 mt-2 leading-relaxed">{a}</p>}
    </button>
  );
}

function Divider() {
  return <div className="border-t border-slate-800" />;
}

function SaveButton({ saving, onClick }) {
  return (
    <button
      data-testid="save-settings-btn"
      onClick={onClick}
      disabled={saving}
      className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-medium text-white transition-all"
      style={{ background: saving ? '#334155' : 'linear-gradient(135deg, #f59e0b, #ea580c)' }}
    >
      <Save className="w-4 h-4" /> {saving ? 'Opgeslagen!' : 'Instellingen Opslaan'}
    </button>
  );
}

export default InstellingenPage;
