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
  ToggleLeft, ToggleRight, Archive, X, Wallet, Pencil, Lock
} from 'lucide-react';
import { BarkModal } from '../shared/BarkModal';
import { InputBark } from '../shared/InputBark';

const API = process.env.REACT_APP_BACKEND_URL;

export function InstellingenPage({ onNavigate }) {
  const { user, isAdmin } = useAuth();
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

                {/* v13s_login_glow_config_001 — Login Glow + Spark Logo (systeem) */}
                <SettingsCard title="Login Glow & Spark-logo (systeem)" icon={Sparkles} accent="#f59e0b">
                  <p className="text-xs text-slate-400 mb-3">
                    Achtergrond-animatie + Spark-logo op het inlog-scherm. Losstaand van
                    persoonlijke glow — dit is de systeem-huid die alle gasten zien.
                  </p>
                  <SystemLoginGlow userId={userId} userGrad={userGrad} />
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
              <SystemArchive currentUserId={user?.id} isAdmin={isAdmin} />
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

                {/* v7_achievement_agents_001 — Achievement Config Placeholder (admin only) */}
                {/* v12_admin_toggle_001 — was legacy user.admin flag, nu AuthContext-toggle */}
                {isAdmin && <AchievementBlueprintPanel />}

                {/* v10_finance_hub_001 — Boekhouder Finance Hub (admin only) */}
                {isAdmin && <FinanceHubPanel />}

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


// ============================================================
// v13s_login_glow_config_001 — SystemLoginGlow
// Beheer voor inlog-scherm glow-orbs, hoek-glows, dot-count, contrast & Spark-logo upload.
// System-scope: alle gasten zien wat hier is ingesteld.
// ============================================================
function SystemLoginGlow({ userId, userGrad }) {
  const [cfg, setCfg] = React.useState({
    dots_count: 8,
    dots_contrast: 0.6,
    dots_size: 1.0,
    dots_fade: 0.0,  // v13s_login_glow_extras_002 — radial fade sterkte 0-1
    corner_enabled: true,
    corner_a: '#f59e0b',
    corner_b: '#f97316',
    spark_logo_url: null,
  });
  const [busy, setBusy] = React.useState(false);
  const [msg, setMsg] = React.useState(null);
  const [uploading, setUploading] = React.useState(false);
  const canEdit = (userGrad ?? 7) <= 1;

  const flash = (kind, text) => { setMsg({ kind, text }); setTimeout(() => setMsg(null), 2500); };

  const load = React.useCallback(() => {
    fetch(`${API}/api/settings/system`).then(r => r.json()).then(d => {
      const s = d.settings || {};
      setCfg({
        dots_count: Number.isFinite(s.login_dots_count) ? s.login_dots_count : 8,
        dots_contrast: Number.isFinite(s.login_dots_contrast) ? s.login_dots_contrast : 0.6,
        dots_size: Number.isFinite(s.login_dots_size) ? s.login_dots_size : 1.0,
        dots_fade: Number.isFinite(s.login_dots_fade) ? s.login_dots_fade : 0.0,
        corner_enabled: s.login_corner_glow_enabled !== false,
        // v13_corner_glow_follow_scheme_001 — hoeken volgen app-kleurenschema
        primary: s.app_primary_accent || '#f59e0b',
        secondary: s.app_secondary_accent || '#06b6d4',
        spark_logo_url: s.spark_logo_url || null,
      });
    }).catch(() => {});
  }, []);
  React.useEffect(() => { load(); }, [load]);

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

  const update = async (key, value) => {
    if (!canEdit) { flash('err', 'Alleen gradatie ≤ 1 mag dit aanpassen'); return; }
    setBusy(true);
    try {
      await saveOne(key, value);
      setCfg(c => ({ ...c, [key.replace(/^login_/, '').replace(/^corner_glow_/, 'corner_').replace(/^dots_/, 'dots_')]: value }));
      flash('ok', 'Opgeslagen');
    } catch (e) {
      flash('err', e.message);
    } finally {
      setBusy(false);
    }
  };

  const uploadLogo = async (file) => {
    if (!canEdit) { flash('err', 'Alleen gradatie ≤ 1 mag Spark-logo uploaden'); return; }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('viewer_id', userId);
      fd.append('file', file);
      const r = await fetch(`${API}/api/settings/system/spark-logo`, { method: 'POST', body: fd });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || `HTTP ${r.status}`);
      setCfg(c => ({ ...c, spark_logo_url: d.url }));
      flash('ok', `Logo geupload (${(d.size_bytes/1024).toFixed(1)} KB)`);
    } catch (e) {
      flash('err', e.message);
    } finally {
      setUploading(false);
    }
  };

  const deleteLogo = async () => {
    if (!canEdit) return;
    if (!window.confirm('Weet je zeker dat je het Spark-logo wilt verwijderen? Terug naar het standaard-icoon.')) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/settings/system/spark-logo?viewer_id=${encodeURIComponent(userId)}`, { method: 'DELETE' });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || `HTTP ${r.status}`);
      }
      setCfg(c => ({ ...c, spark_logo_url: null }));
      flash('ok', 'Logo verwijderd — fallback op standaard-icoon');
    } catch (e) {
      flash('err', e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Spark Logo Upload */}
      <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-14 h-14 flex-shrink-0 rounded-lg overflow-hidden border border-slate-700 bg-slate-800 flex items-center justify-center">
            {cfg.spark_logo_url ? (
              <img
                data-testid="admin-spark-logo-preview"
                src={`${API}${cfg.spark_logo_url}`}
                alt="Spark logo"
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-[10px] text-slate-500">geen logo</span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white">Spark Logo</p>
            <p className="text-[10px] text-slate-500">
              PNG/JPG/WEBP/SVG · max 5 MB · aanbevolen 512×512. Verschijnt op login-scherm
              en in de header wanneer je bent ingelogd.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex-1">
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp,image/svg+xml"
              onChange={e => e.target.files?.[0] && uploadLogo(e.target.files[0])}
              disabled={!canEdit || uploading}
              className="hidden"
              data-testid="admin-spark-logo-file-input"
            />
            <span
              data-testid="admin-spark-logo-upload-btn"
              className={`inline-flex w-full items-center justify-center gap-2 px-3 py-2 text-xs rounded-lg font-medium text-white transition-all ${canEdit && !uploading ? 'hover:brightness-110 cursor-pointer' : 'opacity-40 cursor-not-allowed'}`}
              style={{
                background: canEdit && !uploading ? 'linear-gradient(135deg, #a855f7, #7c3aed)' : '#334155',
                boxShadow: canEdit && !uploading ? '0 6px 18px -14px #a855f788' : 'none',
              }}
            >
              {uploading ? 'Bezig met uploaden…' : (cfg.spark_logo_url ? 'Vervang logo' : 'Kies bestand')}
            </span>
          </label>
          {cfg.spark_logo_url && (
            <button
              onClick={deleteLogo}
              disabled={!canEdit || busy}
              className="px-3 py-2 text-xs rounded-lg border border-red-500/40 text-red-300 hover:bg-red-500/10 disabled:opacity-40"
              data-testid="admin-spark-logo-delete-btn"
            >
              Verwijder
            </button>
          )}
        </div>
      </div>

      {/* Corner Glow */}
      <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-white">Hoek-glow (corner glow)</p>
            <p className="text-[10px] text-slate-500">Twee grote wazige gloed-vlekken in de hoeken van het login-scherm.</p>
          </div>
          <button
            data-testid="admin-corner-glow-toggle"
            onClick={() => update('login_corner_glow_enabled', !cfg.corner_enabled)}
            disabled={!canEdit || busy}
            className="relative w-10 h-5 rounded-full transition-colors flex-shrink-0 disabled:opacity-40"
            style={{ background: cfg.corner_enabled ? '#a855f7' : '#334155' }}
          >
            <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow ${cfg.corner_enabled ? 'left-[22px]' : 'left-[2px]'}`} />
          </button>
        </div>
        {/* v13_corner_glow_follow_scheme_001 (sessie 53) — losse hoek-pickers
            verwijderd. Hoeken volgen nu automatisch Primary (linksboven) +
            Secondary (rechtsonder) uit "App Kleurenschema" hierboven.
            Willem: "veel makkelijker" — 1 plek voor kleur, hoeken doen mee. */}
        <div className={`text-[11px] text-slate-400 bg-slate-900/60 border border-slate-800 rounded p-2 space-y-0.5 ${!cfg.corner_enabled ? 'opacity-40' : ''}`}>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border border-slate-700" style={{ backgroundColor: cfg.primary || '#f59e0b' }} />
            <span>Linksboven — volgt <span className="text-slate-200 font-medium">Primary</span> ({cfg.primary || '#f59e0b'})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full border border-slate-700" style={{ backgroundColor: cfg.secondary || '#06b6d4' }} />
            <span>Rechtsonder — volgt <span className="text-slate-200 font-medium">Secondary</span> ({cfg.secondary || '#06b6d4'})</span>
          </div>
          <p className="text-[10px] text-slate-500 pt-1 italic">
            Wijzig via {'"App Kleurenschema"'} bovenaan deze pagina.
          </p>
        </div>
      </div>

      {/* Glow Dots */}
      <div className="p-3 bg-slate-900/40 rounded-lg border border-slate-800 space-y-3">
        <p className="text-sm font-medium text-white">Glow-puntjes</p>

        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Aantal puntjes</span>
            <span className="font-mono">{cfg.dots_count}</span>
          </div>
          <input
            data-testid="admin-dots-count-slider"
            type="range" min="4" max="24" step="1"
            value={cfg.dots_count}
            onChange={e => setCfg(c => ({ ...c, dots_count: Number(e.target.value) }))}
            onMouseUp={e => update('login_dots_count', Number(e.target.value))}
            onTouchEnd={e => update('login_dots_count', Number(e.target.value))}
            disabled={!canEdit || busy}
            className="w-full mt-1 accent-purple-500"
          />
          <div className="flex justify-between text-[9px] text-slate-500"><span>4</span><span>24</span></div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Contrast (opacity)</span>
            <span className="font-mono">{Math.round(cfg.dots_contrast * 100)}%</span>
          </div>
          <input
            data-testid="admin-dots-contrast-slider"
            type="range" min="0.1" max="1.0" step="0.05"
            value={cfg.dots_contrast}
            onChange={e => setCfg(c => ({ ...c, dots_contrast: Number(e.target.value) }))}
            onMouseUp={e => update('login_dots_contrast', Number(e.target.value))}
            onTouchEnd={e => update('login_dots_contrast', Number(e.target.value))}
            disabled={!canEdit || busy}
            className="w-full mt-1 accent-purple-500"
          />
          <div className="flex justify-between text-[9px] text-slate-500"><span>zacht</span><span>fel</span></div>
        </div>

        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Grootte-multiplier</span>
            <span className="font-mono">×{cfg.dots_size.toFixed(1)}</span>
          </div>
          <input
            data-testid="admin-dots-size-slider"
            type="range" min="0.5" max="3.0" step="0.1"
            value={cfg.dots_size}
            onChange={e => setCfg(c => ({ ...c, dots_size: Number(e.target.value) }))}
            onMouseUp={e => update('login_dots_size', Number(e.target.value))}
            onTouchEnd={e => update('login_dots_size', Number(e.target.value))}
            disabled={!canEdit || busy}
            className="w-full mt-1 accent-purple-500"
          />
          <div className="flex justify-between text-[9px] text-slate-500"><span>klein</span><span>groot</span></div>
        </div>

        {/* v13s_login_glow_extras_002 (sessie 53) — Fade-slider: radial-mask sterkte
            zodat de buitenring dots zachter fade in plaats van even hard te blijven
            als het midden. 0 = uniform, 1 = sterk midden→buiten. */}
        <div>
          <div className="flex items-center justify-between text-[11px] text-slate-400">
            <span>Rand-fade (buiten zachter)</span>
            <span className="font-mono">{Math.round((cfg.dots_fade || 0) * 100)}%</span>
          </div>
          <input
            data-testid="admin-dots-fade-slider"
            type="range" min="0" max="1" step="0.05"
            value={cfg.dots_fade || 0}
            onChange={e => setCfg(c => ({ ...c, dots_fade: Number(e.target.value) }))}
            onMouseUp={e => update('login_dots_fade', Number(e.target.value))}
            onTouchEnd={e => update('login_dots_fade', Number(e.target.value))}
            disabled={!canEdit || busy}
            className="w-full mt-1 accent-purple-500"
          />
          <div className="flex justify-between text-[9px] text-slate-500"><span>gelijkmatig</span><span>midden fel, rand zacht</span></div>
        </div>
      </div>

      {/* Live-preview hint */}
      <div className="p-2 bg-slate-800/40 rounded-lg border border-slate-700/50">
        <p className="text-[10px] text-slate-400">
          💡 Wijzigingen zijn direct actief op het login-scherm (uitloggen om te bekijken).
        </p>
      </div>

      {!canEdit && (
        <p className="text-[11px] text-amber-300/80 italic">
          Alleen gradatie 1 (beheerder) kan Login Glow &amp; Spark-logo instellen.
        </p>
      )}

      {msg && (
        <p data-testid="login-glow-msg"
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
  // v13s_admin_button_style_001 — Admin actions krijgen een eigen violet/paars gradient
  // (past bij Palette-icoon van Beeld-tab) i.p.v. amber (dat is de user/login primary).
  // Zo weet je in 1 oogopslag: dit is een admin-actie, niet een gebruikers-inlogknop.
  return (
    <button
      data-testid="save-settings-btn"
      onClick={onClick}
      disabled={saving}
      className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:brightness-110 disabled:opacity-50"
      style={{
        background: saving ? '#334155' : 'linear-gradient(135deg, #a855f7, #7c3aed)',
        boxShadow: saving ? 'none' : '0 8px 22px -14px #a855f788',
      }}
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
  const [oldPw, setOldPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [showBark, setShowBark] = useState(null);
  const [showGrantBark, setShowGrantBark] = useState(false); // v6_admin_grant_frame_001
  const [busy, setBusy] = useState(false);
  // v12_admin_type_001 — Types voor RBAC-light dropdown
  const [adminTypes, setAdminTypes] = useState([]);

  useEffect(() => {
    if (!userId) return;
    fetch(`${API}/api/admin/is-admin/${userId}`).then(r => r.json()).then(d => setIsAdmin(d.is_admin === true));
    // Types laden (public — voor de dropdown)
    fetch(`${API}/api/admin/types`).then(r => r.json()).then(d => setAdminTypes(d.types || [])).catch(() => {});
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

  const grant = async ({ targetId, grantPw, adminType }) => {
    if (!targetId || !grantPw) {
      setShowBark({ begrip: 'Toegang geweigerd', title: 'Vul beide velden in', text: 'Kies een user en typ het admin-wachtwoord.', tone: 'warn' });
      return;
    }
    setBusy(true);
    const res = await fetch(`${API}/api/admin/grant`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_user_id: targetId,
        granted_by: userId,
        password: grantPw,
        admin_type: adminType || 'full',  // v12_admin_type_001
      }),
    }).then(r => r.json());
    setBusy(false);
    if (res.success) {
      setShowGrantBark(false);
      const typeLabel = adminTypes.find(t => t.id === (res.admin_type || 'full'))?.naam || res.admin_type || 'admin';
      setShowBark({ begrip: 'Admin geactiveerd', title: `${res.naam || targetId} is nu ${typeLabel}`, text: res.message, tone: 'success' });
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
                {/* v12_admin_type_001 — Type badge (full / community / user_admin) */}
                {(() => {
                  const t = adminTypes.find(x => x.id === (a.admin_type || 'full'));
                  return (
                    <span
                      data-testid={`admin-type-badge-${a.id}`}
                      style={{ color: t?.kleur || '#f59e0b', borderColor: t?.kleur || '#f59e0b' }}
                      className="text-[9px] font-semibold px-1.5 py-0.5 rounded border bg-slate-900/40"
                      title={t?.beschrijving || ''}
                    >
                      {t?.naam || (a.admin_type || 'full')}
                    </span>
                  );
                })()}
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

      {/* Grant nieuwe admin — v6_admin_grant_frame_001 (InputBark frame popup) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 space-y-3">
        <h3 className="text-sm font-semibold text-white">Nieuwe admin toekennen</h3>
        <p className="text-[11px] text-slate-400">
          Open de ceremoniële bark om een gebruiker tot admin te benoemen. Je hebt het admin-wachtwoord nodig.
        </p>
        <button
          data-testid="admin-grant-btn"
          onClick={() => setShowGrantBark(true)}
          disabled={busy || grantableUsers.length === 0}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 disabled:opacity-40 disabled:cursor-not-allowed border border-purple-500/40"
        >
          <ShieldCheck className="w-3.5 h-3.5" /> Maak admin (in frame-bark)
        </button>
        {grantableUsers.length === 0 && (
          <p className="text-[10px] text-slate-500 italic">Geen kandidaat-gebruikers beschikbaar.</p>
        )}
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

      {/* v6_pre_deploy_reset_002 — Pre-deploy schoonmaak knop met opties */}
      <PreDeployResetPanel userId={userId} setShowBark={setShowBark} />

      {/* v6_admin_grant_frame_001 — Ornament-frame popup voor admin-grant */}
      <InputBark
        open={showGrantBark}
        onClose={() => setShowGrantBark(false)}
        title="Nieuwe admin benoemen"
        text="Kies de gebruiker en bevestig met het admin-wachtwoord."
        tone="info"
        variant="frame"
        fields={[
          {
            name: 'targetId',
            type: 'select',
            label: 'Gebruiker',
            placeholder: '— kies user —',
            options: grantableUsers.map(u => ({
              value: u.id,
              label: `${u.naam || u.id} (g${u.gradatie || '?'})`,
            })),
          },
          {
            // v12_admin_type_001 — Kies type (full / community / user_admin)
            name: 'adminType',
            type: 'select',
            label: 'Admin-type',
            placeholder: '— kies type —',
            initial: 'full',
            options: adminTypes.map(t => ({
              value: t.id,
              label: t.naam,
            })),
          },
          {
            name: 'grantPw',
            type: 'password',
            label: 'Admin-wachtwoord',
            placeholder: '•••••••',
            autoFocus: false,
          },
        ]}
        onSubmit={grant}
        submitLabel={busy ? 'Bezig…' : 'Maak admin'}
        cancelLabel="Annuleer"
      />
    </div>
  );
}


// ============================================================
// v6_pre_deploy_reset_002 — Pre-deploy schoonmaak paneel
// ============================================================
function PreDeployResetPanel({ userId, setShowBark }) {
  const [status, setStatus] = useState(null);
  const [opts, setOpts] = useState({
    disable_shadow: true,
    reset_pots: true,
    clear_baseline: true,
    clear_accounting: true,
    clear_shadow_pots: true,
    zero_all_roar: true,
    clear_bots_registry: true,
  });
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);

  const loadStatus = useCallback(() => {
    fetch(`${API}/api/admin/system/health-status`)
      .then(r => r.json()).then(setStatus).catch(() => {});
  }, []);
  useEffect(() => { loadStatus(); }, [loadStatus]);

  const run = async () => {
    setBusy(true);
    try {
      const r = await fetch(`${API}/api/admin/system/pre-deploy-reset`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ by_user: userId, ...opts }),
      });
      const d = await r.json();
      if (r.ok) {
        setShowBark({
          begrip: 'Admin geactiveerd',
          title: 'Schone lei',
          text: `Reset uitgevoerd. ROAR: ${Object.keys(d.balances?.new || {}).length} users, pots: ${Object.keys(d.pots_reset || {}).length} users, accounting tx gewist: ${d.accounting_cleared?.previous_tx_count ?? 0}`,
          tone: 'success',
        });
        loadStatus();
      } else {
        setShowBark({ begrip: 'Toegang geweigerd', title: 'Reset mislukt', text: d.detail || 'Onbekende fout', tone: 'error' });
      }
    } finally {
      setBusy(false);
      setConfirm(false);
    }
  };

  const flagLabels = {
    disable_shadow: 'Shadow-cascade UIT',
    reset_pots: '12 lege potjes per user (capital €10, geen positie)',
    clear_baseline: 'Geen base (capital_baseline leeg)',
    clear_accounting: 'Boekhouding wissen (transactions = [])',
    clear_shadow_pots: 'Shadow-pots wissen',
    zero_all_roar: 'Alle ROAR balances → 0',
    clear_bots_registry: 'Bots-registry leeg (verwijder stale user-bots)',
  };

  return (
    <div data-testid="pre-deploy-panel" className="bg-slate-900/60 border border-rose-900/50 rounded-xl p-4 space-y-3">
      <div className="flex items-start gap-2">
        <div className="w-7 h-7 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-300 text-sm">!</div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-white">Pre-Deploy Schoonmaak</h3>
          <p className="text-[11px] text-slate-400">Maakt alles klaar voor een schone redeploy. Voer dit pas uit nadat je alle posities verkocht hebt op Bitvavo.</p>
        </div>
      </div>

      {/* Huidige status */}
      {status && (
        <div className="bg-slate-950/40 border border-slate-800 rounded-lg px-3 py-2 text-[10px] text-slate-300 font-mono space-y-0.5">
          <div>shadow: <span className={status.shadow_enabled ? 'text-rose-300' : 'text-emerald-300'}>{status.shadow_enabled ? 'AAN' : 'UIT'}</span></div>
          <div>baseline_users: {status.baseline_users?.length || 0}</div>
          <div>accounting tx: {status.accounting_tx_count}</div>
          <div>pots per user: {Object.entries(status.pots_per_user || {}).map(([u, p]) => `${u.slice(-6)}=${p.count}(${p.open_positions}open)`).join(', ') || '—'}</div>
          <div>ROAR totaal: {Object.values(status.roar_balances || {}).reduce((a, b) => a + b, 0)}</div>
        </div>
      )}

      {/* Vlaggen */}
      <div className="space-y-1.5">
        {Object.entries(flagLabels).map(([k, lbl]) => (
          <label key={k} className="flex items-start gap-2 text-[11px] text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              data-testid={`pre-deploy-${k}`}
              checked={opts[k]}
              onChange={e => setOpts({ ...opts, [k]: e.target.checked })}
              className="mt-0.5 accent-rose-500"
            />
            <span>{lbl}</span>
          </label>
        ))}
      </div>

      {/* Confirm flow */}
      {!confirm ? (
        <button
          data-testid="pre-deploy-trigger-btn"
          onClick={() => setConfirm(true)}
          disabled={busy}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-medium bg-rose-500/20 text-rose-200 hover:bg-rose-500/30 border border-rose-500/40 disabled:opacity-40"
        >
          <RefreshCw className="w-3.5 h-3.5" /> Voer pre-deploy reset uit
        </button>
      ) : (
        <div className="flex gap-2">
          <button
            data-testid="pre-deploy-confirm-btn"
            onClick={run}
            disabled={busy}
            className="flex-1 px-3 py-2 rounded-lg text-xs font-bold bg-rose-600 text-white hover:bg-rose-500 disabled:opacity-40"
          >
            {busy ? 'Bezig…' : 'JA, schone lei'}
          </button>
          <button
            onClick={() => setConfirm(false)}
            disabled={busy}
            className="px-3 py-2 rounded-lg text-xs text-slate-300 bg-slate-800 hover:bg-slate-700"
          >
            Annuleer
          </button>
        </div>
      )}
    </div>
  );
}


// v7_achievement_agents_001 — Placeholder-panel: toont sub-agent blueprints (read-only)
// Toekomst: velden editable maken via PATCH /api/achievements/admin/blueprint/{name}
function AchievementBlueprintPanel() {
  const [blueprints, setBlueprints] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/achievements/admin/blueprints`)
      .then(r => r.json())
      .then(d => { setBlueprints(d.blueprints || {}); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-slate-500 p-3">Achievement blueprints laden…</div>;
  if (!blueprints) return null;

  return (
    <div data-testid="achievement-blueprint-panel"
      className="p-5 rounded-xl border border-amber-500/20"
      style={{ background: 'linear-gradient(135deg, rgba(245,158,11,0.05), rgba(168,85,247,0.04))' }}>
      <div className="flex items-center gap-3 mb-3">
        <Trophy className="w-5 h-5 text-amber-400" />
        <h2 className="text-lg font-bold text-white">Achievement Config</h2>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40">
          Placeholder v7 — read-only
        </span>
      </div>
      <p className="text-xs text-slate-400 mb-4">
        Elke achievement-agent leest zijn config uit een blueprint-JSON.<br/>
        <span className="text-amber-300">Later editable</span> — XP-waarden, banner-teksten, thresholds — zonder code-wijziging.
        <span className="text-slate-500"> (Willem-regel: &ldquo;alles kunnen aanpassen behalve script zelf&rdquo;)</span>
      </p>

      <div className="space-y-2">
        {Object.entries(blueprints).map(([name, info]) => (
          <div key={name}
            className="rounded-lg border border-slate-700/60 bg-slate-900/40 overflow-hidden">
            <button
              data-testid={`ach-bp-toggle-${name}`}
              onClick={() => setExpanded(expanded === name ? null : name)}
              className="w-full px-3 py-2.5 flex items-center justify-between hover:bg-slate-800/50">
              <div className="flex items-center gap-3">
                <ChevronRight className={`w-3.5 h-3.5 text-slate-500 transition-transform ${expanded === name ? 'rotate-90' : ''}`} />
                <span className="text-sm font-semibold text-slate-200">{info.agent_class}</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {(info.handles_types || []).join(', ')}
                </span>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">{name}.json</span>
            </button>
            {expanded === name && (
              <div className="border-t border-slate-800 p-3 bg-black/30">
                <pre className="text-[10px] text-slate-300 overflow-x-auto font-mono whitespace-pre max-h-96">
{JSON.stringify(info.blueprint, null, 2)}
                </pre>
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-800">
                  <span className="text-[10px] text-slate-500">
                    Bewerken via UI komt in de volgende iteratie.
                  </span>
                  <button
                    disabled
                    data-testid={`ach-bp-edit-${name}`}
                    className="px-3 py-1.5 text-xs rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 opacity-40 cursor-not-allowed flex items-center gap-1.5">
                    <Edit3 className="w-3 h-3" /> Bewerken (soon)
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}


// v10_finance_hub_001 — Boekhouder Finance Hub admin panel
function FinanceHubPanel() {
  const [snapshot, setSnapshot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);
  const [mintN, setMintN] = useState(3);
  const [busy, setBusy] = useState(false);
  const [lastAction, setLastAction] = useState(null);

  const reload = () => {
    setLoading(true);
    fetch(`${API}/api/boekhouder/snapshot/user-001`)
      .then(r => r.json())
      .then(d => { setSnapshot(d); setLoading(false); })
      .catch(() => setLoading(false));
  };
  useEffect(() => { reload(); }, []);

  const doSync = async (dryRun) => {
    setBusy(true);
    const r = await fetch(`${API}/api/boekhouder/admin/sync-wallet-mirror`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ dry_run: dryRun, viewer_id: 'user-001' })
    }).then(r => r.json());
    setLastAction({ type: 'sync', dryRun, ...r });
    setBusy(false);
    if (!dryRun) reload();
  };

  const doMint = async (dryRun) => {
    setBusy(true);
    const r = await fetch(`${API}/api/boekhouder/admin/mint`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ user_id: 'user-001', n_tokens: mintN, source: 'admin_test', dry_run: dryRun, viewer_id: 'user-001' })
    }).then(r => r.json());
    setLastAction({ type: 'mint', dryRun, ...r });
    setBusy(false);
    if (!dryRun) reload();
  };

  if (loading) return <div className="text-xs text-slate-500 p-3">Finance Hub laden…</div>;
  if (!snapshot) return null;

  const t = snapshot.token || {};
  const p = snapshot.price || {};
  const w = snapshot.wallet || {};
  const pj = snapshot.potjes || {};
  const bv = snapshot.bitvavo || {};
  const rc = snapshot.recon || {};

  return (
    <div data-testid="finance-hub-panel"
      className="p-5 rounded-xl border border-emerald-500/20"
      style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.05), rgba(6,95,70,0.04))' }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <Wallet className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg font-bold text-white">Boekhouder Finance Hub</h2>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">v10 dispatcher</span>
        </div>
        <button onClick={reload} data-testid="fh-reload"
          className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300">🔄 refresh</button>
      </div>

      {/* Live snapshot grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-500 mb-1">EUR-saldo</div>
          <div className="text-lg font-bold text-white">€{w.balance_eur?.toFixed(2)}</div>
          <div className="text-[10px] text-slate-500">gestort: €{w.total_deposited_eur?.toFixed(2)}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-500 mb-1">ROAR tokens</div>
          <div className="text-lg font-bold text-white">{t.user_tokens_roar_authoritative}</div>
          {t.drift_detected && <div className="text-[10px] text-amber-400">⚠️ mirror: {t.user_tokens_wallet_mirror}</div>}
        </div>
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-500 mb-1">Token-prijs</div>
          <div className="text-lg font-bold text-white">€{p.current_price_eur?.toFixed(2)}</div>
          <div className="text-[10px] text-slate-500">{p.at_floor ? '(floor)' : `${p.formula?.split(',')[0]?.replace('max(','')}...`}</div>
        </div>
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-[10px] text-slate-500 mb-1">Potjes</div>
          <div className="text-lg font-bold text-white">{pj.potjes_count} × €{p.current_price_eur?.toFixed(2)}</div>
          <div className="text-[10px] text-slate-500">totaal: €{pj.total_capital_dynamic_eur}</div>
        </div>
      </div>

      {/* Ruis + drift status */}
      <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-semibold text-slate-300">🍖 Ruis (bitvavo - som potjes)</span>
          <span className={`text-sm font-bold ${(rc.system_wide?.ruis_eur||0) >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            €{rc.system_wide?.ruis_eur >= 0 ? '+' : ''}{rc.system_wide?.ruis_eur?.toFixed(2)}
          </span>
        </div>
        <div className="text-[10px] text-slate-500">
          Bitvavo: €{bv.bitvavo_free_eur?.toFixed(2)} • potjes-totaal: €{rc.system_wide?.total_potjes_capital_eur?.toFixed(2)}
        </div>
        {rc.warnings?.length > 0 && (
          <div className="mt-2 text-[10px] text-amber-400">
            {rc.warnings.map((wn, i) => <div key={i}>⚠️ {wn}</div>)}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="space-y-2 mb-3">
        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-xs font-semibold text-slate-200 mb-2">🔧 Sync wallet mirror (fix drift)</div>
          <div className="flex gap-2">
            <button onClick={() => doSync(true)} disabled={busy} data-testid="fh-sync-dry"
              className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300">Dry-run</button>
            <button onClick={() => doSync(false)} disabled={busy} data-testid="fh-sync-real"
              className="px-3 py-1.5 text-xs rounded bg-emerald-600 hover:bg-emerald-500 text-white">Uitvoeren</button>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
          <div className="text-xs font-semibold text-slate-200 mb-2">🪙 Test-mint tokens (1 token = 1 pot @ €{p.current_price_eur?.toFixed(2)})</div>
          <div className="flex gap-2 items-center">
            <input type="number" min="1" max="20" value={mintN} onChange={e => setMintN(Number(e.target.value))}
              data-testid="fh-mint-n" className="w-16 px-2 py-1 text-xs rounded bg-slate-950 border border-slate-700 text-white" />
            <span className="text-xs text-slate-400">tokens = €{(mintN * (p.current_price_eur||0)).toFixed(2)}</span>
            <button onClick={() => doMint(true)} disabled={busy} data-testid="fh-mint-dry"
              className="px-3 py-1.5 text-xs rounded bg-slate-800 hover:bg-slate-700 text-slate-300">Preview</button>
            <button onClick={() => doMint(false)} disabled={busy} data-testid="fh-mint-real"
              className="px-3 py-1.5 text-xs rounded bg-amber-600 hover:bg-amber-500 text-white">Mint</button>
          </div>
        </div>
      </div>

      {/* Last action result */}
      {lastAction && (
        <div className="p-3 rounded-lg bg-black/40 border border-emerald-500/20 mb-3">
          <div className="text-[10px] text-emerald-400 mb-1">
            Laatste actie: <b>{lastAction.type}</b> {lastAction.dryRun ? '(dry-run)' : '(uitgevoerd)'}
          </div>
          <pre className="text-[10px] text-slate-300 overflow-x-auto max-h-40">
{JSON.stringify(lastAction, null, 2)}
          </pre>
        </div>
      )}

      {/* Sub-agents overview */}
      <button onClick={() => setExpanded(expanded === 'agents' ? null : 'agents')} data-testid="fh-toggle-agents"
        className="w-full px-3 py-2 text-xs rounded bg-slate-900/50 hover:bg-slate-800/50 text-slate-300 flex items-center justify-between">
        <span>🤖 8 sub-agents (dispatcher-pattern)</span>
        <ChevronRight className={`w-3 h-3 transition-transform ${expanded === 'agents' ? 'rotate-90' : ''}`} />
      </button>
      {expanded === 'agents' && (
        <div className="mt-2 p-3 bg-black/30 rounded-lg border border-slate-800">
          <pre className="text-[10px] text-slate-300 overflow-x-auto max-h-96 font-mono">
{JSON.stringify(snapshot, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

