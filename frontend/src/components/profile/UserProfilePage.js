import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { useAuth } from '../../context/AuthContext';
import { 
  User, Edit3, Save, X, Heart, Target, AlertTriangle,
  Eye, Ear, Brain, Smile, Globe, MessageCircle, 
  ChevronRight, Star, Award, Settings, Camera, MapPin, Phone, Mail
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function UserProfilePage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [editMode, setEditMode] = useState(false);
  const [activeTab, setActiveTab] = useState('algemeen');
  const [saving, setSaving] = useState(false);
  const [extProfile, setExtProfile] = useState({});

  // Load extended profile from API
  useEffect(() => {
    fetch(`${API}/api/profile/extended/${userId}`)
      .then(r => r.json())
      .then(d => { if (d.profile) setExtProfile(d.profile); })
      .catch(() => {});
  }, [userId]);

  const saveProfile = async () => {
    setSaving(true);
    await fetch(`${API}/api/profile/extended/${userId}`, {
      method: 'PUT', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(extProfile),
    });
    setSaving(false);
  };

  const updateField = (key, val) => setExtProfile(prev => ({ ...prev, [key]: val }));

  // User persona data (will be stored per user later)
  const [personaData, setPersonaData] = useState({
    // Algemeen
    geslacht: 'man',
    leeftijd: '',
    locatie: '',
    beroep: '',
    opleiding: '',
    
    // Persoonlijkheid sliders (0-100)
    introvert_extravert: 65,
    analytisch_creatief: 45,
    planmatig_spontaan: 70,
    rationeel_emotioneel: 50,
    traditioneel_vernieuwend: 80,
    zelfstandig_teamspeler: 55,
    
    // Doelen & Behoeften
    doelen: [],
    behoeften: [],
    verlangens: [],
    winsten: [],
    
    // Pijn & Frustraties
    pijn: [],
    angst: [],
    frustraties: [],
    belemmeringen: [],
    
    // Zintuigen
    hoort: [],
    ziet: [],
    denkt: [],
    voelt: [],
    
    // Media & Communicatie
    mediagedrag: [],
    communicatie: [],
  });

  const tabs = [
    { id: 'algemeen', label: 'ALGEMEEN' },
    { id: 'achtergrond', label: 'ACHTERGRONDINFORMATIE' },
    { id: 'persoonlijkheid', label: 'PERSOONLIJKHEID / OVERIGE' },
  ];

  return (
    <MainLayout activePage="profiel" onNavigate={onNavigate}>
      <div className="p-6 min-h-full">
        {/* Header Tabs */}
        <div className="bg-gradient-to-r from-amber-500 to-orange-600 rounded-t-2xl">
          <div className="flex">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-4 px-6 text-sm font-bold uppercase tracking-wider transition-all ${
                  activeTab === tab.id 
                    ? 'bg-slate-900 text-white rounded-t-xl' 
                    : 'text-white/80 hover:text-white hover:bg-white/10'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="bg-slate-900 border border-slate-800 border-t-0 rounded-b-2xl">
          <div className="p-6">
            {/* Top Section - 3 Columns */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">
              {/* Column 1: Avatar & Basic Info */}
              <div className="bg-slate-800/50 rounded-xl p-6">
                {/* Avatar */}
                <div className="relative mb-4">
                  <div className="w-32 h-32 mx-auto bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center overflow-hidden">
                    <User className="w-16 h-16 text-white" />
                  </div>
                  <button className="absolute bottom-0 right-1/2 translate-x-1/2 translate-y-2 p-2 bg-amber-500 rounded-full hover:bg-amber-400 transition-colors">
                    <Camera className="w-4 h-4 text-white" />
                  </button>
                </div>

                {/* Gender Selection */}
                <div className="flex justify-center gap-4 mb-4">
                  <button 
                    onClick={() => setPersonaData({...personaData, geslacht: 'man'})}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      personaData.geslacht === 'man' 
                        ? 'border-cyan-500 bg-cyan-500/20' 
                        : 'border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <span className="text-xl">♂</span>
                  </button>
                  <button 
                    onClick={() => setPersonaData({...personaData, geslacht: 'vrouw'})}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      personaData.geslacht === 'vrouw' 
                        ? 'border-pink-500 bg-pink-500/20' 
                        : 'border-slate-700 hover:border-slate-600'
                    }`}
                  >
                    <span className="text-xl">♀</span>
                  </button>
                </div>

                {/* Basic Fields */}
                <div className="space-y-3">
                  <InputField label="Naam" value={user?.naam || ''} disabled />
                  <InputField label="Leeftijd" value={personaData.leeftijd} placeholder="Bijv. 35" />
                  <InputField label="Locatie" value={personaData.locatie} placeholder="Stad, Land" />
                </div>
              </div>

              {/* Column 2: Achtergrond Info */}
              <div className="bg-slate-800/50 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-amber-400 mb-4 flex items-center gap-2">
                  <Award className="w-4 h-4" />
                  ACHTERGROND
                </h3>
                <div className="space-y-3">
                  <InputField label="Volledige Naam" value={extProfile.volledige_naam || ''} placeholder="Voor- en achternaam" onChange={v => updateField('volledige_naam', v)} />
                  <InputField label="Email" value={extProfile.email || ''} placeholder="email@voorbeeld.nl" onChange={v => updateField('email', v)} />
                  <InputField label="Telefoon" value={extProfile.telefoon || ''} placeholder="+31 6 ..." onChange={v => updateField('telefoon', v)} />
                  <InputField label="Geboortedatum" value={extProfile.geboortedatum || ''} placeholder="DD-MM-JJJJ" onChange={v => updateField('geboortedatum', v)} />
                  <InputField label="Nationaliteit" value={extProfile.nationaliteit || ''} placeholder="Nederlands" onChange={v => updateField('nationaliteit', v)} />
                </div>
              </div>

              {/* Column 3: Adres & Noodcontact */}
              <div className="bg-slate-800/50 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-amber-400 mb-4 flex items-center gap-2">
                  <MapPin className="w-4 h-4" /> ADRES & CONTACT
                </h3>
                <div className="space-y-3">
                  <InputField label="Straat + Nr" value={extProfile.straat || ''} placeholder="Straatnaam 1" onChange={v => updateField('straat', v)} />
                  <InputField label="Postcode" value={extProfile.postcode || ''} placeholder="1234 AB" onChange={v => updateField('postcode', v)} />
                  <InputField label="Plaats" value={extProfile.plaats || ''} placeholder="Amsterdam" onChange={v => updateField('plaats', v)} />
                  <InputField label="Land" value={extProfile.land || ''} placeholder="Nederland" onChange={v => updateField('land', v)} />
                  <div className="pt-3 border-t border-slate-700">
                    <p className="text-[10px] text-red-400/60 uppercase tracking-wider mb-2">Noodcontact</p>
                    <InputField label="Naam" value={extProfile.noodcontact_naam || ''} placeholder="Contact naam" onChange={v => updateField('noodcontact_naam', v)} />
                    <InputField label="Telefoon" value={extProfile.noodcontact_telefoon || ''} placeholder="+31 6 ..." onChange={v => updateField('noodcontact_telefoon', v)} />
                  </div>
                  <div className="pt-3 border-t border-slate-700">
                    <p className="text-[10px] text-green-400/60 uppercase tracking-wider mb-2">Bankrekening</p>
                    <InputField label="IBAN" value={extProfile.iban || ''} placeholder="NL00 BANK 0000 0000 00" onChange={v => updateField('iban', v)} />
                    <InputField label="Bank" value={extProfile.bank_provider || ''} placeholder="ING, Rabobank, ABN..." onChange={v => updateField('bank_provider', v)} />
                  </div>
                </div>
              </div>

              {/* Column 4: Personality Sliders */}
              <div className="bg-slate-800/50 rounded-xl p-6">
                <h3 className="text-sm font-semibold text-amber-400 mb-4">PERSOONLIJKHEID</h3>
                <div className="space-y-4">
                  <PersonalitySlider 
                    left="Introvert" 
                    right="Extravert" 
                    value={personaData.introvert_extravert}
                    onChange={(v) => setPersonaData({...personaData, introvert_extravert: v})}
                  />
                  <PersonalitySlider 
                    left="Analytisch" 
                    right="Creatief" 
                    value={personaData.analytisch_creatief}
                    onChange={(v) => setPersonaData({...personaData, analytisch_creatief: v})}
                  />
                  <PersonalitySlider 
                    left="Planmatig" 
                    right="Spontaan" 
                    value={personaData.planmatig_spontaan}
                    onChange={(v) => setPersonaData({...personaData, planmatig_spontaan: v})}
                  />
                  <PersonalitySlider 
                    left="Rationeel" 
                    right="Emotioneel" 
                    value={personaData.rationeel_emotioneel}
                    onChange={(v) => setPersonaData({...personaData, rationeel_emotioneel: v})}
                  />
                  <PersonalitySlider 
                    left="Traditioneel" 
                    right="Vernieuwend" 
                    value={personaData.traditioneel_vernieuwend}
                    onChange={(v) => setPersonaData({...personaData, traditioneel_vernieuwend: v})}
                  />
                  <PersonalitySlider 
                    left="Zelfstandig" 
                    right="Teamspeler" 
                    value={personaData.zelfstandig_teamspeler}
                    onChange={(v) => setPersonaData({...personaData, zelfstandig_teamspeler: v})}
                  />
                </div>
              </div>
            </div>

            {/* Bottom Section Header */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-600 rounded-t-xl">
              <div className="grid grid-cols-4">
                <div className="py-3 px-4 text-center">
                  <h4 className="text-xs font-bold text-white uppercase">Doelen/Behoeften/Verlangens/Winsten</h4>
                </div>
                <div className="py-3 px-4 text-center border-l border-white/20">
                  <h4 className="text-xs font-bold text-white uppercase">Pijn, Angst, Frustraties & Belemmeringen</h4>
                </div>
                <div className="py-3 px-4 text-center border-l border-white/20">
                  <h4 className="text-xs font-bold text-white uppercase">Laat zich leiden door: Hoort, Ziet, Denkt, Voelt</h4>
                </div>
                <div className="py-3 px-4 text-center border-l border-white/20">
                  <h4 className="text-xs font-bold text-white uppercase">(Online) Mediagedrag & Communicatie</h4>
                </div>
              </div>
            </div>

            {/* Bottom Section Content */}
            <div className="grid grid-cols-4 gap-0 bg-slate-800/30 rounded-b-xl">
              {/* Column 1: Doelen */}
              <div className="p-4 border-r border-slate-700">
                <ListSection 
                  icon={Target} 
                  items={[
                    { label: 'Doelen', placeholder: 'Wat wil je bereiken?' },
                    { label: 'Behoeften', placeholder: 'Wat heb je nodig?' },
                    { label: 'Verlangens', placeholder: 'Waar verlang je naar?' },
                    { label: 'Winsten', placeholder: 'Wat zijn je successen?' },
                  ]}
                />
              </div>

              {/* Column 2: Pijn */}
              <div className="p-4 border-r border-slate-700">
                <ListSection 
                  icon={AlertTriangle}
                  color="red"
                  items={[
                    { label: 'Pijn', placeholder: 'Wat doet pijn?' },
                    { label: 'Angst', placeholder: 'Waar ben je bang voor?' },
                    { label: 'Frustraties', placeholder: 'Wat frustreert je?' },
                    { label: 'Belemmeringen', placeholder: 'Wat houdt je tegen?' },
                  ]}
                />
              </div>

              {/* Column 3: Zintuigen */}
              <div className="p-4 border-r border-slate-700">
                <ListSection 
                  icon={Brain}
                  color="purple"
                  items={[
                    { label: 'Hoort', placeholder: 'Wat hoor je vaak?', icon: Ear },
                    { label: 'Ziet', placeholder: 'Wat zie je?', icon: Eye },
                    { label: 'Denkt', placeholder: 'Wat denk je?', icon: Brain },
                    { label: 'Voelt', placeholder: 'Wat voel je?', icon: Heart },
                  ]}
                />
              </div>

              {/* Column 4: Media */}
              <div className="p-4">
                <ListSection 
                  icon={Globe}
                  color="cyan"
                  items={[
                    { label: 'Sociale Media', placeholder: 'Welke platforms?' },
                    { label: 'Communicatie', placeholder: 'Hoe communiceer je?' },
                    { label: 'Content', placeholder: 'Wat consumeer je?' },
                    { label: 'Invloeden', placeholder: 'Wie volg je?' },
                  ]}
                />
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="px-6 py-4 border-t border-slate-800 flex justify-between items-center">
            <div className="text-sm text-slate-500">
              Laatst bijgewerkt: {new Date().toLocaleDateString('nl-NL')}
            </div>
            <div className="flex gap-3">
              <button className="px-6 py-2 bg-slate-800 text-slate-300 rounded-xl hover:bg-slate-700 transition-colors">
                Annuleren
              </button>
              <button data-testid="profile-save" onClick={saveProfile} disabled={saving}
                className="px-6 py-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-medium rounded-xl hover:from-amber-400 hover:to-orange-500 transition-all flex items-center gap-2 disabled:opacity-50">
                <Save className="w-4 h-4" />
                {saving ? 'Opslaan...' : 'Opslaan'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// Input Field Component
function InputField({ label, value, placeholder, disabled, onChange }) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      <input 
        type="text"
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.value)}
        className={`w-full px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-sm text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none ${
          disabled ? 'opacity-60 cursor-not-allowed' : ''
        }`}
      />
    </div>
  );
}

// Personality Slider Component
function PersonalitySlider({ left, right, value, onChange }) {
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-500 mb-1">
        <span>{left}</span>
        <span>{right}</span>
      </div>
      <div className="relative">
        <div className="h-2 bg-slate-700 rounded-full">
          <div 
            className="absolute h-2 bg-gradient-to-r from-cyan-500 to-cyan-400 rounded-full"
            style={{ width: `${value}%` }}
          />
        </div>
        <input
          type="range"
          min="0"
          max="100"
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
        />
        <div 
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white rounded-full shadow-lg border-2 border-cyan-500 flex items-center justify-center"
          style={{ left: `calc(${value}% - 8px)` }}
        >
          <X className="w-2 h-2 text-cyan-500" />
        </div>
      </div>
    </div>
  );
}

// List Section Component
function ListSection({ icon: Icon, color = 'amber', items }) {
  const colorClasses = {
    amber: 'text-amber-400',
    red: 'text-red-400',
    purple: 'text-purple-400',
    cyan: 'text-cyan-400',
  };

  return (
    <div className="space-y-4">
      {items.map((item, idx) => (
        <div key={idx}>
          <div className={`flex items-center gap-2 mb-2 ${colorClasses[color]}`}>
            {item.icon ? <item.icon className="w-3 h-3" /> : <Icon className="w-3 h-3" />}
            <span className="text-xs font-medium uppercase">{item.label}</span>
          </div>
          <div className="space-y-1">
            {[1, 2, 3].map(i => (
              <input
                key={i}
                type="text"
                placeholder={item.placeholder}
                className="w-full px-3 py-1.5 bg-slate-700/30 border-none rounded text-sm text-slate-300 placeholder-slate-600 focus:ring-1 focus:ring-amber-500 focus:outline-none"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export default UserProfilePage;
