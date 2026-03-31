import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function ProfielenTab({ currentUserId, isAdmin }) {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  
  const [formData, setFormData] = useState({
    need: "",
    believe: "",
    interesses: "",
    context: "",
    tags: "",
    gradatie: 7,
    // Persoonlijke info
    naam: "",
    volledige_naam: "",
    geboortedatum: "",
    geslacht: "",
    email: "",
    telefoon: "",
    straat: "",
    huisnummer: "",
    postcode: "",
    plaats: "",
    land: "",
    beroep: "",
    werkgever: "",
    opleiding: "",
    studierichting: "",
    ws5: {
      who: "",
      what: "",
      when: "",
      where: "",
      why: "",
      how: ""
    }
  });

  useEffect(() => {
    fetchProfiles();
  }, []);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/profiles/profiles`);
      setProfiles(response.data.profiles || []);
    } catch (error) {
      console.error("Error fetching profiles:", error);
    } finally {
      setLoading(false);
    }
  };

  const viewProfile = (user) => {
    setSelectedUser(user);
    setIsEditing(true);
    
    const profile = user.profile || {};
    setFormData({
      need: profile.need || "",
      believe: profile.believe || "",
      interesses: profile.interesses?.join(", ") || "",
      context: profile.context || "",
      tags: profile.tags?.join(", ") || "",
      gradatie: user.gradatie || 7,
      // Persoonlijke info
      naam: user.naam || "",
      volledige_naam: user.persoonlijke_info?.volledige_naam || "",
      geboortedatum: user.persoonlijke_info?.geboortedatum || "",
      geslacht: user.persoonlijke_info?.geslacht || "",
      email: user.email || "",
      telefoon: user.contact?.telefoon || "",
      straat: user.adres?.straat || "",
      huisnummer: user.adres?.huisnummer || "",
      postcode: user.adres?.postcode || "",
      plaats: user.adres?.plaats || "",
      land: user.adres?.land || "",
      beroep: user.werk_carriere?.beroep || "",
      werkgever: user.werk_carriere?.werkgever || "",
      opleiding: user.opleiding?.opleiding || "",
      studierichting: user.opleiding?.studierichting || "",
      ws5: profile.ws5 || { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
  };

  const updateProfile = async () => {
    if (!selectedUser) return;

    try {
      // Update Spark profile (need/believe/ws5)
      await axios.put(`${API}/profiles/profiles/${selectedUser.id}`, {
        need: formData.need,
        believe: formData.believe,
        interesses: formData.interesses.split(',').map(i => i.trim()).filter(i => i),
        context: formData.context,
        tags: formData.tags.split(',').map(t => t.trim()).filter(t => t),
        gradatie: formData.gradatie,
        ws5: formData.ws5
      });
      
      // Update persoonlijke info + naam
      await axios.put(`${API}/profile/me`, {
        user_id: selectedUser.id,
        naam: formData.naam,
        volledige_naam: formData.volledige_naam,
        geboortedatum: formData.geboortedatum,
        geslacht: formData.geslacht,
        email: formData.email,
        telefoon: formData.telefoon,
        straat: formData.straat,
        huisnummer: formData.huisnummer,
        postcode: formData.postcode,
        plaats: formData.plaats,
        land: formData.land,
        beroep: formData.beroep,
        werkgever: formData.werkgever,
        opleiding: formData.opleiding,
        studierichting: formData.studierichting
      });
      
      resetForm();
      fetchProfiles();
      alert("✅ Profiel volledig bijgewerkt!");
    } catch (error) {
      console.error("Error updating profile:", error);
      alert("Kon profiel niet bijwerken: " + (error.response?.data?.detail || error.message));
    }
  };

  const resetForm = () => {
    setSelectedUser(null);
    setIsEditing(false);
    setFormData({
      need: "",
      believe: "",
      interesses: "",
      context: "",
      tags: "",
      gradatie: 7,
      ws5: { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
  };

  const getGradatieColor = (gradatie) => {
    if (gradatie === 1) return "text-yellow-400";
    if (gradatie <= 3) return "text-purple-400";
    if (gradatie <= 5) return "text-blue-400";
    return "text-gray-400";
  };

  const getGradatieLabel = (gradatie) => {
    if (gradatie === 1) return "👑 Admin";
    if (gradatie <= 3) return "⭐ Familie/Vertrouwd";
    if (gradatie <= 5) return "🤝 Bekende";
    return "👤 Onbekende";
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">👤 User Profielen & Personalia</h2>
        <p className="text-sm text-gray-400 mt-1">
          Needs, believes, interesses en context per gebruiker - helpt Spark om beter te assisteren
        </p>
      </div>

      {/* Edit Form */}
      {isEditing && selectedUser && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              ✏️ Bewerk Profiel: {selectedUser.naam}
            </h3>
            <span className={`text-sm ${getGradatieColor(selectedUser.gradatie)}`}>
              {getGradatieLabel(selectedUser.gradatie)}
            </span>
          </div>
          
          <div className="space-y-4">
            {/* Need & Believe */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">🎯 Need (Wat heeft deze persoon nodig?)</label>
                <input
                  type="text"
                  value={formData.need}
                  onChange={(e) => setFormData({...formData, need: e.target.value})}
                  placeholder="bijv. Erkenning, begrip, hulp, vrijheid"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>
              
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">💭 Believe (Waarin geloven ze?)</label>
                <input
                  type="text"
                  value={formData.believe}
                  onChange={(e) => setFormData({...formData, believe: e.target.value})}
                  placeholder="bijv. Iedereen verdient een kans, eerlijkheid boven alles"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>
            </div>

            {/* Interesses */}
            <div>
              <label className="text-sm text-gray-300 font-medium block mb-2">🏷️ Interesses (komma gescheiden)</label>
              <input
                type="text"
                value={formData.interesses}
                onChange={(e) => setFormData({...formData, interesses: e.target.value})}
                placeholder="gaming, zorgboerderij, community, coaching"
                className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
              />
            </div>

            {/* Context */}
            <div>
              <label className="text-sm text-gray-300 font-medium block mb-2">📍 Context (Waar zit deze persoon mee?)</label>
              <textarea
                value={formData.context}
                onChange={(e) => setFormData({...formData, context: e.target.value})}
                placeholder="Beschrijf de huidige situatie, uitdagingen, doelen..."
                className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500 resize-none"
                rows="3"
              />
            </div>

            {/* NIEUWE SECTIE: Persoonlijke Informatie */}
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-gray-300 font-medium mb-3">👤 Persoonlijke Informatie</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Naam (systeem)</label>
                  <input
                    type="text"
                    value={formData.naam}
                    onChange={(e) => setFormData({...formData, naam: e.target.value})}
                    placeholder="Nickname/gebruikersnaam"
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                  <p className="text-xs text-gray-500 mt-1">Dit is de naam die overal in systeem wordt gebruikt</p>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Volledige Naam</label>
                  <input
                    type="text"
                    value={formData.volledige_naam}
                    onChange={(e) => setFormData({...formData, volledige_naam: e.target.value})}
                    placeholder="Voor- en achternaam"
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Geboortedatum</label>
                  <input
                    type="date"
                    value={formData.geboortedatum}
                    onChange={(e) => setFormData({...formData, geboortedatum: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Geslacht</label>
                  <select
                    value={formData.geslacht}
                    onChange={(e) => setFormData({...formData, geslacht: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  >
                    <option value="">Selecteer...</option>
                    <option value="Man">Man</option>
                    <option value="Vrouw">Vrouw</option>
                    <option value="Anders">Anders</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Telefoon</label>
                  <input
                    type="tel"
                    value={formData.telefoon}
                    onChange={(e) => setFormData({...formData, telefoon: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Adres */}
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-gray-300 font-medium mb-3">🏠 Adres</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Straat</label>
                  <input
                    type="text"
                    value={formData.straat}
                    onChange={(e) => setFormData({...formData, straat: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Huisnummer</label>
                  <input
                    type="text"
                    value={formData.huisnummer}
                    onChange={(e) => setFormData({...formData, huisnummer: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Postcode</label>
                  <input
                    type="text"
                    value={formData.postcode}
                    onChange={(e) => setFormData({...formData, postcode: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Plaats</label>
                  <input
                    type="text"
                    value={formData.plaats}
                    onChange={(e) => setFormData({...formData, plaats: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Land</label>
                  <input
                    type="text"
                    value={formData.land}
                    onChange={(e) => setFormData({...formData, land: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Werk & Opleiding */}
            <div className="border-t border-slate-700 pt-4">
              <h4 className="text-gray-300 font-medium mb-3">💼 Werk & Opleiding</h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Beroep</label>
                  <input
                    type="text"
                    value={formData.beroep}
                    onChange={(e) => setFormData({...formData, beroep: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Werkgever</label>
                  <input
                    type="text"
                    value={formData.werkgever}
                    onChange={(e) => setFormData({...formData, werkgever: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Opleiding</label>
                  <input
                    type="text"
                    value={formData.opleiding}
                    onChange={(e) => setFormData({...formData, opleiding: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Studierichting</label>
                  <input
                    type="text"
                    value={formData.studierichting}
                    onChange={(e) => setFormData({...formData, studierichting: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                  />
                </div>
              </div>
            </div>

            {/* 5 W's Framework - ALLEEN VOOR ADMIN */}
            {isAdmin && (
              <div className="border-t border-slate-700 pt-4">
                <label className="text-gray-300 text-sm font-medium block mb-3">
                  📋 5 W's Framework (alleen voor Spark/Admin)
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">👤 Wie (Who)</label>
                    <input
                      type="text"
                      value={formData.ws5.who}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, who: e.target.value}})}
                      placeholder="Wie is deze persoon?"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📌 Wat (What)</label>
                    <input
                      type="text"
                      value={formData.ws5.what}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, what: e.target.value}})}
                      placeholder="Wat doet deze persoon?"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📅 Wanneer (When)</label>
                    <input
                      type="text"
                      value={formData.ws5.when}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, when: e.target.value}})}
                      placeholder="Wanneer/periode"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📍 Waar (Where)</label>
                    <input
                      type="text"
                      value={formData.ws5.where}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, where: e.target.value}})}
                      placeholder="Locatie/context"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">❓ Waarom (Why)</label>
                    <input
                      type="text"
                      value={formData.ws5.why}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, why: e.target.value}})}
                      placeholder="Motivatie/reden"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">⚙️ Hoe (How)</label>
                    <input
                      type="text"
                      value={formData.ws5.how}
                      onChange={(e) => setFormData({...formData, ws5: {...formData.ws5, how: e.target.value}})}
                      placeholder="Werkwijze/aanpak"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Tags */}
            <div>
              <label className="text-sm text-gray-300 font-medium block mb-2">🏷️ Tags (komma gescheiden)</label>
              <input
                type="text"
                value={formData.tags}
                onChange={(e) => setFormData({...formData, tags: e.target.value})}
                placeholder="vip, actief, belangrijk"
                className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
              />
            </div>

            {/* Gradatie (Admin only) */}
            {isAdmin && (
              <div className="border-t border-slate-700 pt-4">
                <label className="text-sm text-gray-300 font-medium block mb-2">👑 Gradatie (Toegangsniveau)</label>
                <div className="space-y-2">
                  <div className="flex gap-2 flex-wrap">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(level => (
                      <button
                        key={level}
                        type="button"
                        onClick={() => setFormData({...formData, gradatie: level})}
                        className={`px-4 py-2 rounded-lg font-medium transition-all ${
                          formData.gradatie === level
                            ? level === 1 ? "bg-yellow-500/30 text-yellow-300 border-2 border-yellow-500"
                            : level <= 3 ? "bg-purple-500/30 text-purple-300 border-2 border-purple-500"
                            : level <= 5 ? "bg-blue-500/30 text-blue-300 border-2 border-blue-500"
                            : "bg-gray-500/30 text-gray-300 border-2 border-gray-500"
                            : "bg-slate-700/30 text-gray-500 hover:bg-slate-700/50"
                        }`}
                      >
                        {level}
                      </button>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>• 1 = 👑 Admin (volledige toegang)</p>
                    <p>• 2-3 = ⭐ Familie/Vertrouwd</p>
                    <p>• 4-5 = 🤝 Bekende</p>
                    <p>• 6+ = 👤 Standaard gebruiker</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Buttons */}
            <div className="flex gap-3 pt-2">
              <button
                onClick={updateProfile}
                className="flex-1 px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium"
              >
                💾 Opslaan
              </button>
              <button
                onClick={resetForm}
                className="px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
              >
                Annuleren
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Profiles List */}
      <div className="space-y-3">
        {loading ? (
          <p className="text-gray-400 text-center py-8">Laden...</p>
        ) : profiles.length > 0 ? (
          profiles.map(user => {
            const profile = user.profile || {};
            const hasProfile = profile.need || profile.believe || profile.interesses?.length > 0;
            
            return (
              <div
                key={user.id}
                className={`bg-slate-800/50 border ${hasProfile ? 'border-purple-500/30' : 'border-slate-700'} p-4 rounded-lg hover:border-purple-500/40 transition-all`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="text-white font-medium text-lg">{user.naam}</h4>
                      <span className={`text-xs px-2 py-1 rounded ${getGradatieColor(user.gradatie)} bg-slate-700/50`}>
                        {getGradatieLabel(user.gradatie)}
                      </span>
                      {hasProfile && (
                        <span className="text-xs px-2 py-1 rounded bg-green-500/20 text-green-300">
                          ✓ Profiel ingevuld
                        </span>
                      )}
                    </div>
                    
                    {profile.need || profile.believe ? (
                      <div className="grid grid-cols-2 gap-4 mb-2">
                        {profile.need && (
                          <div>
                            <span className="text-xs text-gray-500">🎯 Need:</span>
                            <p className="text-sm text-gray-300">{profile.need}</p>
                          </div>
                        )}
                        {profile.believe && (
                          <div>
                            <span className="text-xs text-gray-500">💭 Believe:</span>
                            <p className="text-sm text-gray-300">{profile.believe}</p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-500 mb-2">Nog geen profiel informatie</p>
                    )}
                    
                    {profile.interesses && profile.interesses.length > 0 && (
                      <div className="flex gap-2 flex-wrap mb-2">
                        {profile.interesses.map((interest, idx) => (
                          <span key={idx} className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                            {interest}
                          </span>
                        ))}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-2">
                      <span>💬 {user.gesprekken_count || 0} gesprekken</span>
                      {user.last_active && (
                        <span>🕒 Laatst actief: {new Date(user.last_active).toLocaleDateString('nl-NL')}</span>
                      )}
                    </div>
                  </div>
                  
                  {isAdmin && (
                    <button
                      onClick={() => {
                        viewProfile(user);
                        setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100);
                      }}
                      className="px-4 py-2 bg-purple-500/20 text-purple-300 rounded-lg text-sm hover:bg-purple-500/30"
                    >
                      ✏️ Bewerk
                    </button>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-12 bg-slate-800/30 rounded-lg">
            <span className="text-4xl mb-4 block">👤</span>
            <p className="text-gray-400">Geen gebruikers gevonden.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default ProfielenTab;
