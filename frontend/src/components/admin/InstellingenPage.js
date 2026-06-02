import React, { useState, useEffect, useCallback } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { SystemArchive } from './SystemArchive';
import { SynapseTab } from './SynapseTab';
import {
  Settings, Monitor, Volume2, Link2, Sparkles, HelpCircle,
  Save, Shield, ShieldCheck, Clock, Bug, RefreshCw, Palette, Sun, Moon,
  Mic, Speech, Music, Upload, Play, Trash2, Edit3, Plus,
  Keyboard, MessageSquare, Brain, Trophy, ChevronDown, ChevronRight,
  Zap, Globe, Wifi, Database, Server, Bell, Eye, EyeOff,
  ToggleLeft, ToggleRight, Archive, X
} from 'lucide-react';
import { BarkModal } from '../shared/BarkModal';

const API = process.env.REACT_APP_BACKEND_URL;

export function InstellingenPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id;
  const userGrad = user?.gradatie ?? 7;
  const [activeTab, setActiveTab] = useState('algemeen');
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  // v4_settings_001: schema + effective settings + overrides from backend
  const [schema, setSchema] = useState({});
  const [systemEditGrad, setSystemEditGrad] = useState(1);
  const [settings, setSettings] = useState({});
  const [overriddenKeys, setOverriddenKeys] = useState([]);
  const [dirty, setDirty] = useState({}); // {key: newValue} pending save
  const [loaded, setLoaded] = useState(false);

  const refresh = useCallback(async () => {
    if (!userId) return;
    try {
      const [schemaR, effR] = await Promise.all([
        fetch(`${API}/api/settings/schema`).then(r => r.json()),
        fetch(`${API}/api/settings/effective/${userId}`).then(r => r.json()),
      ]);
      setSchema(schemaR.schema || {});
      setSystemEditGrad(schemaR.system_edit_gradatie_max ?? 1);
      setSettings(effR.effective || {});
      setOverriddenKeys(effR.overridden_keys || []);
      setLoaded(true);
    } catch (e) { console.error('Settings load failed', e); setLoaded(true); }
  }, [userId]);

  useEffect(() => { refresh(); }, [refresh]);

  const set = (key, val) => {
    setSettings(s => ({ ...s, [key]: val }));
    setDirty(d => ({ ...d, [key]: val }));
  };

  const canEdit = (key) => {
    const s = schema[key];
    if (!s) return false;
    if (s.scope === 'system') return userGrad <= systemEditGrad;
    return true; // user-scope: iedereen voor zichzelf
  };

  const resetKey = async (key) => {
    if (schema[key]?.scope !== 'user') return;
    try {
      await fetch(`${API}/api/settings/user/${userId}/${key}?viewer_id=${userId}`, { method: 'DELETE' });
      await refresh();
      setDirty(d => { const c = { ...d }; delete c[key]; return c; });
    } catch (e) { console.error(e); }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMsg(null);
    const results = { ok: 0, fail: 0, errors: [] };
    for (const [key, value] of Object.entries(dirty)) {
      const s = schema[key];
      if (!s) continue;
      const endpoint = s.scope === 'system'
        ? `${API}/api/settings/system/${key}`
        : `${API}/api/settings/user/${userId}/${key}`;
      try {
        const r = await fetch(endpoint, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ value, viewer_id: userId }),
        });
        if (r.ok) results.ok++;
        else { results.fail++; results.errors.push(`${key}: ${r.status}`); }
      } catch (e) { results.fail++; results.errors.push(`${key}: ${e.message}`); }
    }
    setDirty({});
    await refresh();
    setSaving(false);
    setSaveMsg(results.fail === 0
      ? { type: 'ok', text: `${results.ok} instelling(en) opgeslagen ✓` }
      : { type: 'err', text: `${results.fail} mislukt: ${results.errors.join(', ')}` });
    setTimeout(() => setSaveMsg(null), 3500);
  };

  // Mock sound mappings (later vervangen door echte data)
  const [soundMappings] = useState([
    { id: 1, word: 'succes', file: 'success.mp3', frequency: 'every', play_count: 42 },
    { id: 2, word: 'alarm', file: 'alarm.wav', frequency: 'first_only', play_count: 7 },
    { id: 3, word: 'zagen', file: 'saw_sound.mp3', frequency: 'every_3', play_count: 15 },
  ]);

  const tabs = [
    { id: 'algemeen', label: 'Algemeen', icon: Settings, accent: '#f59e0b' },
    { id: 'beeld', label: 'Beeld', icon: Palette, accent: '#a855f7' },
    { id: 'geluid', label: 'Geluid', icon: Volume2, accent: '#3b82f6' },
    { id: 'archief', label: 'Archief', icon: Archive, accent: '#10b981' },
    { id: 'integraties', label: 'Integraties', icon: Link2, accent: '#06b6d4' },
    { id: 'features', label: 'Features', icon: Sparkles, accent: '#22c55e' },
    { id: 'admin', label: 'Admin', icon: ShieldCheck, accent: '#a855f7' },
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
                <SettingsCard title="App Kleurenschema (admin)" icon={Palette} accent="#a855f7">
                  <p className="text-xs text-slate-400 mb-3">
                    Overkoepelend kleurenschema voor de hele app — geldt voor iedereen.
                    Persoonlijke glow-kleur kan elk lid los aanpassen via <span className="text-purple-300">Mijn Profiel → Instellingen → Beeld</span>.
                  </p>
                  <AdminColorScheme userId={userId} userGrad={userGrad} />
                </SettingsCard>

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
              <SystemArchive currentUserId={user?.id} isAdmin={userGrad <= 2} />
            )}

            {/* ====== SYNAPSLAAG (v6_synapse_001 F6) ====== */}
            {activeTab === 'synapse' && (
              <SynapseTab />
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

            {/* ====== ADMIN ====== v6_admin_role_001 ====== */}
            {activeTab === 'admin' && (
              <AdminSettingsPanel userId={userId} />
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


// ============================================================
// AdminColorScheme (v5_admin_color_scheme_001) — overkoepelende app-kleuren
// Persoonlijke glow staat in Mijn Profiel; dit zijn systeembrede defaults.
// ============================================================
const SCHEME_PRESETS = [
  { name: 'Amber Default',  primary: '#f59e0b', secondary: '#06b6d4', bg: '#0f172a' },
  { name: 'Forest Calm',    primary: '#10b981', secondary: '#84cc16', bg: '#0c1b14' },
  { name: 'Cobalt Night',   primary: '#3b82f6', secondary: '#8b5cf6', bg: '#0b1426' },
  { name: 'Rose Dusk',      primary: '#ec4899', secondary: '#f97316', bg: '#1a0e15' },
  { name: 'Violet Quiet',   primary: '#a855f7', secondary: '#06b6d4', bg: '#120c20' },
  { name: 'Crimson Alert',  primary: '#ef4444', secondary: '#f59e0b', bg: '#1a0a0a' },
];

function AdminColorScheme({ userId, userGrad }) {
  const [scheme, setScheme] = React.useState({ primary: '#f59e0b', secondary: '#06b6d4', bg: '#0f172a' });
  const [busy, setBusy] = React.useState(false);
  const [msg, setMsg] = React.useState(null);
  const canEdit = (userGrad ?? 7) <= 1;

  // Load current system values
  React.useEffect(() => {
    fetch(`${API}/api/settings/system`).then(r => r.json()).then(d => {
      const s = d.settings || {};
      const next = {
        primary: s.app_primary_accent || '#f59e0b',
        secondary: s.app_secondary_accent || '#06b6d4',
        bg: s.app_background_tint || '#0f172a',
      };
      setScheme(next);
      applyToRoot(next);
    }).catch(() => {});
  }, []);

  const applyToRoot = (s) => {
    document.documentElement.style.setProperty('--app-primary', s.primary);
    document.documentElement.style.setProperty('--app-secondary', s.secondary);
    document.documentElement.style.setProperty('--app-bg-tint', s.bg);
  };

  const flash = (kind, text) => { setMsg({ kind, text }); setTimeout(() => setMsg(null), 2500); };

  const saveOne = async (key, value) => {
    const r = await fetch(`${API}/api/settings/system/${key}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ value, viewer_id: userId }),
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || `HTTP ${r.status}`);
    }
  };

  const saveScheme = async (next) => {
    if (!canEdit) { flash('err', 'Alleen gradatie ≤ 1 mag dit aanpassen'); return; }
    setBusy(true);
    try {
      await saveOne('app_primary_accent', next.primary);
      await saveOne('app_secondary_accent', next.secondary);
      await saveOne('app_background_tint', next.bg);
      setScheme(next);
      applyToRoot(next);
      flash('ok', 'Kleurenschema opgeslagen');
    } catch (e) {
      flash('err', e.message);
    } finally {
      setBusy(false);
    }
  };

  const pickPreset = (p) => saveScheme({ primary: p.primary, secondary: p.secondary, bg: p.bg });

  const setHex = (field, val) => {
    const next = { ...scheme, [field]: val };
    setScheme(next);
    applyToRoot(next);
  };

  const commitHex = (field) => {
    const v = (scheme[field] || '').trim();
    if (!/^#[0-9a-fA-F]{6}$/.test(v)) {
      flash('err', `Ongeldige hex: ${v}`);
      return;
    }
    const key = field === 'primary' ? 'app_primary_accent' :
                field === 'secondary' ? 'app_secondary_accent' : 'app_background_tint';
    setBusy(true);
    saveOne(key, v).then(() => flash('ok', 'Opgeslagen')).catch(e => flash('err', e.message)).finally(() => setBusy(false));
  };

  return (
    <div data-testid="admin-color-scheme" className="space-y-4">
      {/* Preview */}
      <div className="rounded-xl p-4 border border-slate-800" style={{ background: scheme.bg }}>
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Live voorbeeld</p>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: `${scheme.primary}22`, color: scheme.primary, border: `1px solid ${scheme.primary}50` }}>Primary</span>
              <span className="px-3 py-1.5 rounded-lg text-xs font-medium" style={{ background: `${scheme.secondary}22`, color: scheme.secondary, border: `1px solid ${scheme.secondary}50` }}>Secondary</span>
              <span className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">Neutral</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-lg" style={{ background: scheme.primary, boxShadow: `0 0 16px ${scheme.primary}80` }} />
            <div className="w-10 h-10 rounded-lg" style={{ background: scheme.secondary, boxShadow: `0 0 16px ${scheme.secondary}80` }} />
          </div>
        </div>
      </div>

      {/* Presets */}
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-2">Presets (snel kiezen)</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" data-testid="scheme-presets">
          {SCHEME_PRESETS.map(p => {
            const active = p.primary.toLowerCase() === scheme.primary.toLowerCase() &&
                           p.secondary.toLowerCase() === scheme.secondary.toLowerCase();
            return (
              <button
                key={p.name}
                data-testid={`scheme-preset-${p.name.toLowerCase().replace(/\s+/g, '-')}`}
                onClick={() => pickPreset(p)}
                disabled={busy || !canEdit}
                className={`p-2.5 rounded-lg border transition-all flex items-center gap-2 ${active ? 'border-white/40 ring-1 ring-white/30' : 'border-slate-800 hover:border-slate-600'} disabled:opacity-40 disabled:cursor-not-allowed`}
                style={{ background: p.bg }}
              >
                <div className="flex items-center -space-x-1">
                  <span className="w-5 h-5 rounded-full ring-1 ring-slate-900" style={{ background: p.primary }} />
                  <span className="w-5 h-5 rounded-full ring-1 ring-slate-900" style={{ background: p.secondary }} />
                </div>
                <span className="text-[11px] font-medium text-white">{p.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Custom hex pickers */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="scheme-customs">
        {[
          { field: 'primary',   label: 'Primary accent',  hint: 'Hoofdkleur (buttons, highlights)' },
          { field: 'secondary', label: 'Secondary accent',hint: 'Secundair (badges, links)' },
          { field: 'bg',        label: 'Background tint', hint: 'Donkere achtergrond' },
        ].map(({ field, label, hint }) => (
          <div key={field} className="p-3 rounded-lg bg-slate-800/40 border border-slate-800">
            <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">{label}</p>
            <div className="flex items-center gap-2 mb-1">
              <input
                type="color"
                data-testid={`scheme-color-${field}`}
                value={scheme[field]}
                onChange={e => setHex(field, e.target.value)}
                onBlur={() => commitHex(field)}
                disabled={!canEdit || busy}
                className="w-10 h-8 rounded bg-transparent border border-slate-700 cursor-pointer disabled:opacity-40"
              />
              <input
                type="text"
                data-testid={`scheme-hex-${field}`}
                value={scheme[field]}
                onChange={e => setHex(field, e.target.value)}
                onBlur={() => commitHex(field)}
                disabled={!canEdit || busy}
                className="flex-1 px-2 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs font-mono text-white disabled:opacity-40"
              />
            </div>
            <p className="text-[9px] text-slate-500">{hint}</p>
          </div>
        ))}
      </div>

      {!canEdit && (
        <p className="text-[11px] text-amber-300/80 italic">
          Alleen gradatie 1 (beheerder) kan dit overkoepelende schema wijzigen.
        </p>
      )}

      {/* v5_bot_color_scheme_001 — per-bot accent kleuren */}
      <BotColorPanel canEdit={canEdit} />

      {msg && (
        <p data-testid="scheme-msg"
          className={`text-[11px] px-3 py-2 rounded-lg border ${msg.kind === 'ok' ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-red-500/10 text-red-300 border-red-500/30'}`}>
          {msg.text}
        </p>
      )}
    </div>
  );
}


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

// v5_bot_color_scheme_001 — admin paneel om per-bot accent te kiezen
const BOT_DEFAULTS = [
  { key: 'bot_color_madelief',   naam: 'Madelief Stouten',   default: '#ec4899', icon: '🌸' },
  { key: 'bot_color_harry',      naam: 'Harry Klokkenmaker', default: '#06b6d4', icon: '⏰' },
  { key: 'bot_color_smith',      naam: 'Mr Smith',           default: '#10b981', icon: '🛡️' },
  { key: 'bot_color_boekhouder', naam: 'De Boekhouder',      default: '#f59e0b', icon: '📊' },
  { key: 'bot_color_dood',       naam: 'De Dood',            default: '#a855f7', icon: '💀' },
];

function BotColorPanel({ canEdit }) {
  const [colors, setColors] = React.useState({});
  const [saving, setSaving] = React.useState('');

  React.useEffect(() => {
    fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings/system`).then(r => r.json()).then(d => {
      const s = d?.settings || {};
      const next = {};
      BOT_DEFAULTS.forEach(b => { next[b.key] = s[b.key] || b.default; });
      setColors(next);
    });
  }, []);

  const saveOne = async (key, value) => {
    setSaving(key);
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings/system`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key, value }),
      });
    } catch {}
    setSaving('');
  };

  return (
    <div data-testid="bot-color-panel" className="space-y-2 pt-4 border-t border-slate-800">
      <div>
        <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">Bot-accent kleuren</p>
        <p className="text-[11px] text-slate-400 leading-relaxed">
          Iedere community-bot heeft zijn eigen kleur in Gesprekken/Community bubbles.
          Bumpt geldt direct voor alle users.
        </p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {BOT_DEFAULTS.map(b => (
          <div key={b.key} className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-800/40 border border-slate-800">
            <span className="text-lg">{b.icon}</span>
            <div className="flex-1">
              <p className="text-[11px] text-slate-200 font-medium">{b.naam}</p>
              <p className="text-[9px] text-slate-500 font-mono">{b.key}</p>
            </div>
            <input
              type="color"
              data-testid={`bot-color-${b.key}`}
              value={colors[b.key] || b.default}
              disabled={!canEdit || saving === b.key}
              onChange={e => setColors(c => ({ ...c, [b.key]: e.target.value }))}
              onBlur={e => saveOne(b.key, e.target.value)}
              className="w-9 h-7 rounded bg-transparent border border-slate-700 cursor-pointer disabled:opacity-40"
            />
            <input
              type="text"
              value={colors[b.key] || b.default}
              disabled={!canEdit || saving === b.key}
              onChange={e => setColors(c => ({ ...c, [b.key]: e.target.value }))}
              onBlur={e => saveOne(b.key, e.target.value)}
              className="w-20 px-2 py-1 bg-slate-900 border border-slate-700 rounded text-[10px] font-mono text-white disabled:opacity-40"
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default InstellingenPage;

// ============================================================
// AdminSettingsPanel (v6_admin_role_001)
// Admin-wachtwoord wijzigen + grant/revoke admins
// Alleen zichtbaar voor users met admin:true
// ============================================================
function AdminSettingsPanel({ userId }) {
  const [isAdmin, setIsAdmin] = useState(null);
  const [admins, setAdmins] = useState([]);
  const [users, setUsers] = useState([]);
  const [targetId, setTargetId] = useState('');
  const [grantPw, setGrantPw] = useState('');
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [showBark, setShowBark] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/admin/is-admin/${userId}`).then(r => r.json()).then(d => setIsAdmin(d.is_admin === true));
  }, [userId]);

  const refresh = useCallback(() => {
    if (isAdmin !== true) return;
    fetch(`${API}/api/admin/list?viewer_id=${userId}`).then(r => r.json()).then(d => setAdmins(d.admins || []));
    fetch(`${API}/api/auth/users`).then(r => r.json()).then(d => setUsers(d.users || d || [])).catch(() => {});
  }, [isAdmin, userId]);

  useEffect(() => { refresh(); }, [refresh]);

  if (isAdmin === null) return <div className="text-xs text-slate-500">Laden...</div>;
  if (isAdmin === false) {
    return (
      <div className="p-8 text-center rounded-xl border border-slate-800 bg-slate-900/40">
        <ShieldCheck className="w-12 h-12 mx-auto text-slate-600 mb-3" />
        <h3 className="text-sm font-semibold text-slate-300 mb-1">Geen toegang</h3>
        <p className="text-[11px] text-slate-500">Deze sectie is alleen zichtbaar voor admins. Vraag een bestaande admin om je rechten toe te kennen.</p>
      </div>
    );
  }

  const grant = async () => {
    if (!targetId || !grantPw) {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Vul beide velden in', text: 'Kies een user en typ het admin-wachtwoord.', tone: 'warn' });
      return;
    }
    setBusy(true);
    const res = await fetch(`${API}/api/admin/grant`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_user_id: targetId, granted_by: userId, password: grantPw }),
    }).then(r => r.json());
    setBusy(false);
    setGrantPw('');
    if (res.success) {
      setShowBark({ begrip: 'Admin geactiveerd', title: `${res.naam || targetId} is nu admin`, text: res.message, tone: 'success' });
      setTargetId('');
      refresh();
    } else {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Admin-grant mislukt', text: res.error, tone: 'error' });
    }
  };

  const revoke = async (target_user_id, naam) => {
    if (!window.confirm(`Admin-rol intrekken voor ${naam}?`)) return;
    setBusy(true);
    const res = await fetch(`${API}/api/admin/revoke`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_user_id, revoked_by: userId }),
    }).then(r => r.json());
    setBusy(false);
    if (res.success) {
      setShowBark({ begrip: 'Admin gedeactiveerd', title: `${naam} is geen admin meer`, text: res.message, tone: 'warn' });
      refresh();
    } else {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Revoke mislukt', text: res.error, tone: 'error' });
    }
  };

  const changePw = async () => {
    if (!oldPw || !newPw) {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Vul beide velden in', text: 'Oud en nieuw wachtwoord verplicht.', tone: 'warn' });
      return;
    }
    if (newPw.length < 6) {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Te kort', text: 'Minstens 6 tekens.', tone: 'warn' });
      return;
    }
    setBusy(true);
    const res = await fetch(`${API}/api/admin/password/reset`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, old_password: oldPw, new_password: newPw }),
    }).then(r => r.json());
    setBusy(false);
    setOldPw(''); setNewPw('');
    if (res.success) {
      setShowBark({ begrip: 'Admin geactiveerd', title: 'Wachtwoord gewijzigd', text: res.message, tone: 'success' });
    } else {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Wachtwoord wijzigen mislukt', text: res.error, tone: 'error' });
    }
  };

  const adminIds = new Set(admins.map(a => a.id));
  const grantableUsers = (users || []).filter(u => u.id && !adminIds.has(u.id));

  return (
    <div data-testid="admin-settings-panel" className="space-y-4">
      <div className="p-5 rounded-xl border border-purple-500/30" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.10), rgba(91,33,182,0.06))' }}>
        <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2"><ShieldCheck className="w-5 h-5 text-purple-300" /> Admin-beheer</h2>
        <p className="text-xs text-slate-400">Admin = technische rol, los van gradatie (familie/lid). Toekenning vereist het admin-wachtwoord.</p>
      </div>

      {/* Huidige admins */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-white mb-3">
          Huidige admins <span className="text-[10px] text-purple-300 ml-1">({admins.length})</span>
        </h3>
        <div className="space-y-1.5">
          {admins.map(a => (
            <div key={a.id} data-testid={`admin-row-${a.id}`} className="flex items-center justify-between bg-slate-950/40 border border-slate-800 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5 text-purple-300" />
                <span className="text-xs text-white">{a.naam || a.id}</span>
                <span className="text-[10px] text-slate-500">g{a.gradatie}</span>
                {a.admin_granted_by === 'system-seed' && (
                  <span className="text-[9px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">seed</span>
                )}
              </div>
              {a.admin_granted_by !== 'system-seed' && admins.length > 1 && (
                <button
                  data-testid={`admin-revoke-${a.id}`}
                  onClick={() => revoke(a.id, a.naam || a.id)}
                  disabled={busy}
                  className="text-[10px] text-rose-300 hover:text-rose-200 px-2 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20"
                >
                  intrekken
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Grant nieuwe admin */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-white">Nieuwe admin toekennen</h3>
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Gebruiker</label>
          <select
            data-testid="admin-grant-user"
            value={targetId}
            onChange={e => setTargetId(e.target.value)}
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-purple-500/50 outline-none"
          >
            <option value="">— kies user —</option>
            {grantableUsers.map(u => (
              <option key={u.id} value={u.id}>{u.naam || u.id} (g{u.gradatie || '?'})</option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Admin-wachtwoord</label>
          <input
            type="password" data-testid="admin-grant-password"
            value={grantPw} onChange={e => setGrantPw(e.target.value)} placeholder="•••••••"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-purple-500/50 outline-none"
          />
        </div>
        <button
          data-testid="admin-grant-btn" onClick={grant} disabled={busy || !targetId || !grantPw}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ShieldCheck className="w-3.5 h-3.5" /> Maak admin
        </button>
      </div>

      {/* Admin wachtwoord wijzigen */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-white">Admin-wachtwoord wijzigen</h3>
        <p className="text-[11px] text-slate-400">Dit is het wachtwoord dat nodig is om <strong className="text-purple-300">nieuwe admins toe te kennen</strong>. Staat los van je eigen sleutelwoord.</p>
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Huidig admin-wachtwoord</label>
          <input type="password" data-testid="admin-pw-old" value={oldPw} onChange={e => setOldPw(e.target.value)} placeholder="•••••••" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-purple-500/50 outline-none" />
        </div>
        <div>
          <label className="block text-[10px] text-slate-500 uppercase tracking-wider mb-1">Nieuw admin-wachtwoord (min. 6 tekens)</label>
          <input type="password" data-testid="admin-pw-new" value={newPw} onChange={e => setNewPw(e.target.value)} placeholder="•••••••" className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:border-purple-500/50 outline-none" />
        </div>
        <button
          data-testid="admin-pw-change-btn" onClick={changePw} disabled={busy || !oldPw || !newPw}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Save className="w-3.5 h-3.5" /> Wijzig admin-wachtwoord
        </button>
      </div>

      <BarkModal
        open={!!showBark}
        onClose={() => setShowBark(null)}
        begrip={showBark?.begrip}
        title={showBark?.title}
        text={showBark?.text}
        tone={showBark?.tone}
      />
    </div>
  );
}
