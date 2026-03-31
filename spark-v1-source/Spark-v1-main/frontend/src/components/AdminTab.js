import React, { useState, useEffect } from "react";
import axios from "axios";
import "./AdminPanel.css";
import ProfielenTab from "./ProfielenTab";
import DebugTab from "./DebugTab";
import SparkWorldAdmin from "./SparkWorldAdmin";
import UserManagement from "./UserManagement";
import FileBrowserTab from "./FileBrowserTab";
import StatusTabNew from "./StatusTabNew";
import TriggerManagerTab from "./TriggerManagerTab";
import SettingsTabNew from "./SettingsTabNew";
import EmotionStatsTab from "./EmotionStatsTab";
import WalletTab from "./WalletTab";
import LogsTab from "./LogsTab";
import BuildingBlueprintTab from "./BuildingBlueprintTab";
import BuildingsOverviewTab from "./BuildingsOverviewTab";
import BlueprintEditorTab from "./BlueprintEditorTab";
import KnowledgeReviewTab from "./KnowledgeReviewTab";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AdminTab({ currentUser }) {
  const [activeSection, setActiveSection] = useState("norms");
  const [profielenSubTab, setProfielenSubTab] = useState("overzicht");
  const [sparkWorldSubTab, setSparkWorldSubTab] = useState("overview");
  const [norms, setNorms] = useState([]);
  const [values, setValues] = useState([]);
  const [knowledge, setKnowledge] = useState([]);
  const [snaps, setSnaps] = useState([]);
  const [bijbelItems, setBijbelItems] = useState([]);
  const [emotions, setEmotions] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Knowledge Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterTags, setFilterTags] = useState([]);
  const [selectedLetter, setSelectedLetter] = useState(null);
  
  // Edit states
  const [editingNorm, setEditingNorm] = useState(null);
  const [editingValue, setEditingValue] = useState(null);
  const [editingBijbel, setEditingBijbel] = useState(null);
  
  // View modal state
  const [viewingItem, setViewingItem] = useState(null);
  
  // Form states
  const [newNorm, setNewNorm] = useState({ norm: "", beschrijving: "", belangrijkheid: 3 });
  const [newValue, setNewValue] = useState({ waarde: "", beschrijving: "", belangrijkheid: 3 });
  const [newBijbelItem, setNewBijbelItem] = useState({ naam: "", beschrijving: "" });
  const [newKnowledge, setNewKnowledge] = useState({
    onderwerp: "",
    kort_antwoord: "",
    voorwoord: "",
    omschrijving: "",
    tags: "",
    belangrijkheid: 3,
    ws5: {
      who: "",
      what: "",
      when: "",
      where: "",
      why: "",
      how: ""
    }
  });
  const [editingKnowledge, setEditingKnowledge] = useState(null);

  useEffect(() => {
    fetchData();
  }, [activeSection]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeSection === "norms") {
        const response = await axios.get(`${API}/admin/personality/norms`);
        setNorms(response.data.norms || []);
      } else if (activeSection === "values") {
        const response = await axios.get(`${API}/admin/personality/values`);
        setValues(response.data.values || []);
      } else if (activeSection === "bijbel") {
        const response = await axios.get(`${API}/admin/personality/bijbel`);
        setBijbelItems(response.data.items || []);
      } else if (activeSection === "emotions") {
        const response = await axios.get(`${API}/emotions/stats`);
        setEmotions(response.data.stats || null);
      } else if (activeSection === "knowledge") {
        const response = await axios.get(`${API}/knowledge/all`);
        // Filter out trash and draft items from Admin tab view
        const activeKnowledge = (response.data.entries || []).filter(item => 
          item.status !== "trash" && item.status !== "draft"
        );
        setKnowledge(activeKnowledge);
      } else if (activeSection === "snaps") {
        const response = await axios.get(`${API}/knowledge/all`);
        // Show only draft/snap items
        const draftItems = (response.data.entries || []).filter(item => 
          item.status === "draft" || item.tags?.includes("knowledge-snap")
        );
        setSnaps(draftItems);
      }
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const addNorm = async () => {
    if (!newNorm.norm.trim()) return;
    try {
      await axios.post(`${API}/admin/personality/norms`, newNorm);
      setNewNorm({ norm: "", beschrijving: "", belangrijkheid: 3 });
      fetchData();
    } catch (error) {
      alert("Kon norm niet toevoegen");
    }
  };

  const addValue = async () => {
    if (!newValue.waarde.trim()) return;
    try {
      await axios.post(`${API}/admin/personality/values`, newValue);
      setNewValue({ waarde: "", beschrijving: "", belangrijkheid: 3 });
      fetchData();
    } catch (error) {
      alert("Kon waarde niet toevoegen");
    }
  };

  const addBijbelItem = async () => {
    if (!newBijbelItem.naam.trim()) return;
    try {
      await axios.post(`${API}/admin/personality/bijbel`, newBijbelItem);
      setNewBijbelItem({ naam: "", beschrijving: "" });
      fetchData();
    } catch (error) {
      alert("Kon bijbel item niet toevoegen");
    }
  };

  const deleteNorm = async (normId) => {
    if (!window.confirm("Weet je zeker dat je deze norm wilt verwijderen?")) return;
    try {
      await axios.delete(`${API}/admin/personality/norms/${normId}`);
      fetchData();
    } catch (error) {
      alert("Kon norm niet verwijderen");
    }
  };

  const deleteValue = async (valueId) => {
    if (!window.confirm("Weet je zeker dat je deze waarde wilt verwijderen?")) return;
    try {
      await axios.delete(`${API}/admin/personality/values/${valueId}`);
      fetchData();
    } catch (error) {
      alert("Kon waarde niet verwijderen");
    }
  };

  const deleteBijbelItem = async (itemId) => {
    if (!window.confirm("Weet je zeker dat je dit bijbel item wilt verwijderen?")) return;
    try {
      await axios.delete(`${API}/admin/personality/bijbel/${itemId}`);
      fetchData();
    } catch (error) {
      alert("Kon bijbel item niet verwijderen");
    }
  };
  
  // UPDATE FUNCTIONS
  const updateNorm = async () => {
    if (!editingNorm || !editingNorm.norm.trim()) return;
    try {
      await axios.put(`${API}/admin/personality/norms/${editingNorm.id}`, editingNorm);
      setEditingNorm(null);
      fetchData();
      alert("✅ Norm bijgewerkt!");
    } catch (error) {
      alert("Kon norm niet bijwerken");
    }
  };
  
  const updateValue = async () => {
    if (!editingValue || !editingValue.waarde.trim()) return;
    try {
      await axios.put(`${API}/admin/personality/values/${editingValue.id}`, editingValue);
      setEditingValue(null);
      fetchData();
      alert("✅ Waarde bijgewerkt!");
    } catch (error) {
      alert("Kon waarde niet bijwerken");
    }
  };
  
  const updateBijbelItem = async () => {
    if (!editingBijbel || !editingBijbel.naam.trim()) return;
    try {
      await axios.put(`${API}/admin/personality/bijbel/${editingBijbel.id}`, editingBijbel);
      setEditingBijbel(null);
      fetchData();
      alert("✅ Bijbel item bijgewerkt!");
    } catch (error) {
      alert("Kon bijbel item niet bijwerken");
    }
  };

  const addKnowledge = async () => {
    if (!newKnowledge.onderwerp.trim() || !newKnowledge.kort_antwoord.trim()) {
      alert("⚠️ Onderwerp en kort antwoord zijn verplicht!");
      return;
    }
    
    try {
      const payload = {
        begrip: newKnowledge.onderwerp,
        lagen: {
          laag1: newKnowledge.kort_antwoord,
          laag2: newKnowledge.voorwoord,
          laag3: newKnowledge.omschrijving,
          laag4: newKnowledge.verdieping  // ✨ LAAG 4
        },
        tags: newKnowledge.tags.split(',').map(t => t.trim()).filter(t => t),
        topic: newKnowledge.topic || "algemeen",  // ✨ TOPIC
        belangrijkheid: newKnowledge.belangrijkheid,
        ws5: newKnowledge.ws5,
        status: "active",
        // Send current user info
        admin_user_naam: currentUser?.naam || 'Unknown',
        admin_user_id: currentUser?.id || null
      };
      
      if (editingKnowledge) {
        // Update existing
        console.log('[UPDATE] Updating knowledge:', editingKnowledge.id, payload);
        const response = await axios.put(`${API}/admin/knowledge/${editingKnowledge.id}`, payload);
        console.log('[UPDATE] Response:', response.data);
        
        // Check if XP was awarded
        if (response.data.xp_awarded) {
          alert(`✅ Knowledge bijgewerkt!\n\n🎉 ${response.data.xp_awarded.message}\nLevel: ${response.data.xp_awarded.level}`);
        } else {
          alert("✅ Knowledge bijgewerkt!");
        }
        
        setEditingKnowledge(null);
      } else {
        // Create new
        console.log('[CREATE] Creating new knowledge:', payload);
        await axios.post(`${API}/admin/knowledge`, payload);
        alert("✅ Nieuwe knowledge aangemaakt!");
      }
      
      setNewKnowledge({ 
        onderwerp: "", 
        kort_antwoord: "", 
        voorwoord: "", 
        omschrijving: "",
        verdieping: "",  // ✨ LAAG 4
        topic: "",       // ✨ TOPIC
        tags: "",
        belangrijkheid: 3,
        ws5: { who: "", what: "", when: "", where: "", why: "", how: "" }
      });
      
      await fetchData();
      
    } catch (error) {
      console.error("[SAVE ERROR]", error);
      console.error("[SAVE ERROR] Response:", error.response?.data);
      alert("❌ Kon knowledge niet opslaan: " + (error.response?.data?.detail || error.message));
    }
  };

  const editKnowledge = (item) => {
    setEditingKnowledge(item);
    setNewKnowledge({
      onderwerp: item.begrip,
      kort_antwoord: item.lagen?.laag1 || "",
      voorwoord: item.lagen?.laag2 || "",
      omschrijving: item.lagen?.laag3 || "",
      verdieping: item.lagen?.laag4 || "",  // ✨ LAAG 4
      topic: item.topic || "algemeen",      // ✨ TOPIC
      tags: item.tags?.join(", ") || "",
      belangrijkheid: item.belangrijkheid || 3,
      ws5: item.ws5 || { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
    
    // Switch to knowledge section so form is visible
    setActiveSection("knowledge");
    
    // Scroll to top so user sees the edit form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const cancelEdit = () => {
    const wasSnap = editingKnowledge?.status === 'draft' || editingKnowledge?.id?.includes('snap-');
    
    setEditingKnowledge(null);
    setNewKnowledge({ 
      onderwerp: "", 
      kort_antwoord: "", 
      voorwoord: "", 
      omschrijving: "",
      verdieping: "",  // ✨ LAAG 4
      topic: "",       // ✨ TOPIC
      tags: "",
      belangrijkheid: 3,
      ws5: { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
    
    // Switch back to snaps if it was a snap
    if (wasSnap) {
      setActiveSection("snaps");
    }
  };

  const deleteItem = async (id, type) => {
    console.log('[DELETE] Called with:', { id, type });
    
    if (!window.confirm("Weet je zeker dat je dit permanent wilt verwijderen?")) {
      console.log('[DELETE] User cancelled');
      return;
    }
    
    try {
      console.log('[DELETE] Sending request...');
      const url = `${API}/admin/${type === "knowledge" ? "knowledge" : `personality/${type}`}/${id}`;
      console.log('[DELETE] URL:', url);
      
      const response = await axios.delete(url);
      
      console.log('[DELETE] Success:', response.data);
      alert('✅ Succesvol verwijderd!');
      
      // Refresh the data
      await fetchData();
      
    } catch (error) {
      console.error("[DELETE] Error:", error);
      console.error("[DELETE] Error response:", error.response?.data);
      alert("❌ Kon niet verwijderen: " + (error.response?.data?.detail || error.message));
    }
  };

  const importanceColors = {
    1: "bg-gray-500/20 text-gray-300",
    2: "bg-blue-500/20 text-blue-300",
    3: "bg-yellow-500/20 text-yellow-300",
    4: "bg-orange-500/20 text-orange-300",
    5: "bg-red-500/20 text-red-300"
  };

  return (
    <div className="space-y-6">
      {/* Section Selector - Gegroepeerd */}
      <div className="space-y-4">
        
        {/* SPARK BRAIN */}
        <div>
          <div className="text-xs font-semibold text-purple-400 mb-2 px-2">🧠 SPARK BRAIN</div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setActiveSection("knowledge")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "knowledge"
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🧠 Knowledge
            </button>
            <button
              onClick={() => setActiveSection("snaps")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "snaps"
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📸 Snaps
            </button>
            <button
              onClick={() => setActiveSection("review")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "review"
                  ? "bg-gradient-to-r from-blue-500 to-cyan-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📝 Review
            </button>
            <button
              onClick={() => setActiveSection("triggers")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "triggers"
                  ? "bg-gradient-to-r from-pink-500 to-red-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🎯 Triggers
            </button>
          </div>
        </div>

        {/* PERSOONLIJKHEID */}
        <div>
          <div className="text-xs font-semibold text-pink-400 mb-2 px-2">💎 PERSOONLIJKHEID</div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setActiveSection("norms")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "norms"
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📜 Normen
            </button>
            <button
              onClick={() => setActiveSection("values")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "values"
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              💎 Waarden
            </button>
            <button
              onClick={() => setActiveSection("emotions")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "emotions"
                  ? "bg-gradient-to-r from-pink-500 to-purple-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              😊 Emoties
            </button>
            <button
              onClick={() => setActiveSection("bijbel")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "bijbel"
                  ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📖 Bijbel
            </button>
          </div>
        </div>

        {/* SYSTEEM */}
        <div>
          <div className="text-xs font-semibold text-cyan-400 mb-2 px-2">⚙️ SYSTEEM</div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setActiveSection("gebruikers")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "gebruikers"
                  ? "bg-gradient-to-r from-red-500 to-orange-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              👥 Gebruikers
            </button>
            <button
              onClick={() => setActiveSection("files")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "files"
                  ? "bg-gradient-to-r from-cyan-500 to-blue-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📂 Bestanden
            </button>
            <button
              onClick={() => setActiveSection("status")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "status"
                  ? "bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              ⚡ Status
            </button>
            <button
              onClick={() => setActiveSection("logs")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "logs"
                  ? "bg-gradient-to-r from-gray-500 to-slate-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📜 Logs
            </button>
            <button
              onClick={() => setActiveSection("settings")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "settings"
                  ? "bg-gradient-to-r from-indigo-500 to-purple-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              ⚙️ Settings
            </button>
            <button
              onClick={() => setActiveSection("wallet")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "wallet"
                  ? "bg-gradient-to-r from-yellow-500 to-orange-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              💰 Wallet
            </button>
          </div>
        </div>

        {/* GAME & DEBUG */}
        <div>
          <div className="text-xs font-semibold text-green-400 mb-2 px-2">🎮 GAME & DEBUG</div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setActiveSection("sparkworld")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "sparkworld"
                  ? "bg-gradient-to-r from-green-500 to-blue-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🎮 Spark World
            </button>
            <button
              onClick={() => setActiveSection("debug")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                activeSection === "debug"
                  ? "bg-gradient-to-r from-red-500 to-orange-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🐛 Debug
            </button>
          </div>
        </div>

      </div>

      {/* Add Form */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">
          ➕ {editingKnowledge ? "Bewerk Knowledge" : 
               activeSection === "norms" ? "Nieuwe Norm" : 
               activeSection === "values" ? "Nieuwe Waarde" :
               activeSection === "bijbel" ? "Nieuw Bijbel Item" : 
               "Nieuwe Waarde"}
        </h3>
        {editingKnowledge && (
          <div className="mb-3 p-3 bg-blue-500/10 border border-blue-500/30 rounded flex items-center justify-between">
            <span className="text-blue-300 text-sm">✏️ Bezig met bewerken: {editingKnowledge.begrip}</span>
            <button onClick={cancelEdit} className="text-blue-400 hover:text-blue-300 text-sm">Annuleren</button>
          </div>
        )}
        {activeSection === "norms" ? (
          <div className="space-y-3">
            <input
              type="text"
              value={newNorm.norm}
              onChange={(e) => setNewNorm({...newNorm, norm: e.target.value})}
              placeholder="Norm naam"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
            />
            <textarea
              value={newNorm.beschrijving}
              onChange={(e) => setNewNorm({...newNorm, beschrijving: e.target.value})}
              placeholder="Beschrijving"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
              rows="2"
            />
            <div className="flex items-center gap-3">
              <label className="text-gray-300 text-sm">Belangrijkheid:</label>
              {[1,2,3,4,5].map(val => (
                <button
                  key={val}
                  onClick={() => setNewNorm({...newNorm, belangrijkheid: val})}
                  className={`px-3 py-1 rounded ${
                    newNorm.belangrijkheid === val 
                      ? importanceColors[val]
                      : "bg-slate-700/30 text-gray-500"
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
            <button
              onClick={addNorm}
              disabled={!newNorm.norm.trim()}
              className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Toevoegen
            </button>
          </div>
        ) : activeSection === "values" ? (
          <div className="space-y-3">
            <input
              type="text"
              value={newValue.waarde}
              onChange={(e) => setNewValue({...newValue, waarde: e.target.value})}
              placeholder="Waarde naam"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
            />
            <textarea
              value={newValue.beschrijving}
              onChange={(e) => setNewValue({...newValue, beschrijving: e.target.value})}
              placeholder="Beschrijving"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
              rows="2"
            />
            <div className="flex items-center gap-3">
              <label className="text-gray-300 text-sm">Belangrijkheid:</label>
              {[1,2,3,4,5].map(val => (
                <button
                  key={val}
                  onClick={() => setNewValue({...newValue, belangrijkheid: val})}
                  className={`px-3 py-1 rounded ${
                    newValue.belangrijkheid === val 
                      ? importanceColors[val]
                      : "bg-slate-700/30 text-gray-500"
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
            <button
              onClick={addValue}
              disabled={!newValue.waarde.trim()}
              className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Toevoegen
            </button>
          </div>
        ) : activeSection === "bijbel" ? (
          <div className="space-y-3">
            <input
              type="text"
              value={newBijbelItem.naam}
              onChange={(e) => setNewBijbelItem({...newBijbelItem, naam: e.target.value})}
              placeholder="Item naam"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
            />
            <textarea
              value={newBijbelItem.beschrijving}
              onChange={(e) => setNewBijbelItem({...newBijbelItem, beschrijving: e.target.value})}
              placeholder="Beschrijving"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
              rows="3"
            />
            <button
              onClick={addBijbelItem}
              disabled={!newBijbelItem.naam.trim()}
              className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium disabled:opacity-50"
            >
              Toevoegen
            </button>
          </div>
        ) : activeSection === "snaps" ? (
          <div className="p-4 bg-slate-700/30 rounded-lg text-gray-300 text-center">
            💡 Knowledge snaps worden automatisch aangemaakt. Klik op "✏️ Invullen" om een snap om te zetten naar volledige knowledge.
          </div>
        ) : activeSection === "emotions" ? (
          <div className="p-4 bg-slate-700/30 rounded-lg text-gray-300 text-center">
            💡 Emoties zijn read-only. Huidige emotie wordt getoond in de lijst hieronder.
          </div>
        ) : activeSection === "profielen" ? (
          <div className="p-4 bg-slate-700/30 rounded-lg text-gray-300 text-center">
            💡 Gebruik de sub-tabs hierboven om gebruikers te bekijken of beheren
          </div>
        ) : activeSection === "knowledge" ? (
          <div className="space-y-3">
            <input
              type="text"
              value={newKnowledge.onderwerp}
              onChange={(e) => setNewKnowledge({...newKnowledge, onderwerp: e.target.value})}
              placeholder="Onderwerp (bijv. Appel)"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
            />
            <div className="grid grid-cols-1 gap-3">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Laag 1: Kort antwoord</label>
                <input
                  type="text"
                  value={newKnowledge.kort_antwoord}
                  onChange={(e) => setNewKnowledge({...newKnowledge, kort_antwoord: e.target.value})}
                  placeholder="Appel is een fruit"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Laag 2: + Voorwoord (optioneel)</label>
                <input
                  type="text"
                  value={newKnowledge.voorwoord}
                  onChange={(e) => setNewKnowledge({...newKnowledge, voorwoord: e.target.value})}
                  placeholder="Je kunt het eten, gezond"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Laag 3: + Omschrijving (optioneel)</label>
                <textarea
                  value={newKnowledge.omschrijving}
                  onChange={(e) => setNewKnowledge({...newKnowledge, omschrijving: e.target.value})}
                  placeholder="Bevat vitamines, vele soorten, geschiedenis..."
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500 resize-none"
                  rows="3"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Laag 4: Verdieping (optioneel)</label>
                <textarea
                  value={newKnowledge.verdieping}
                  onChange={(e) => setNewKnowledge({...newKnowledge, verdieping: e.target.value})}
                  placeholder="Extra verdieping, voorbeelden, context..."
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500 resize-none"
                  rows="3"
                />
              </div>
              
              {/* Topic & Tags */}
              <div className="border-t border-slate-700 pt-4 mt-2">
                <label className="text-gray-300 text-sm font-medium block mb-3">📂 Categorisatie</label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">Topic/Categorie</label>
                    <input
                      type="text"
                      value={newKnowledge.topic}
                      onChange={(e) => setNewKnowledge({...newKnowledge, topic: e.target.value})}
                      placeholder="bijv. technologie, natuur, wetenschap"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">Tags (komma gescheiden)</label>
                    <input
                      type="text"
                      value={newKnowledge.tags}
                      onChange={(e) => setNewKnowledge({...newKnowledge, tags: e.target.value})}
                      placeholder="fruit, voedsel, gezond"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                </div>
              </div>
              
              {/* Belangrijkheid Rating */}
              <div className="border-t border-slate-700 pt-4 mt-2">
                <label className="text-gray-300 text-sm font-medium block mb-2">⭐ Belangrijkheid</label>
                <div className="flex gap-2">
                  {[1,2,3,4,5].map(val => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setNewKnowledge({...newKnowledge, belangrijkheid: val})}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        newKnowledge.belangrijkheid === val 
                          ? importanceColors[val] + " border-2 border-current"
                          : "bg-slate-700/30 text-gray-500"
                      }`}
                    >
                      {val}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  1 = Lage prioriteit, 5 = Zeer belangrijk
                </p>
              </div>
              
              {/* 5 W's Framework */}
              <div className="border-t border-slate-700 pt-4 mt-2">
                <label className="text-gray-300 text-sm font-medium block mb-3">📋 5 W's Framework (optioneel)</label>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">👤 Wie (Who)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.who}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, who: e.target.value}})}
                      placeholder="Betrokken personen/organisaties"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📌 Wat (What)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.what}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, what: e.target.value}})}
                      placeholder="Kern van het onderwerp"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📅 Wanneer (When)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.when}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, when: e.target.value}})}
                      placeholder="Tijdscontext"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">📍 Waar (Where)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.where}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, where: e.target.value}})}
                      placeholder="Locatie/context"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">❓ Waarom (Why)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.why}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, why: e.target.value}})}
                      placeholder="Reden/doel/betekenis"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                  <div>
                    <label className="text-gray-400 text-xs block mb-1">⚙️ Hoe (How)</label>
                    <input
                      type="text"
                      value={newKnowledge.ws5.how}
                      onChange={(e) => setNewKnowledge({...newKnowledge, ws5: {...newKnowledge.ws5, how: e.target.value}})}
                      placeholder="Werking/proces"
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm placeholder-gray-500"
                    />
                  </div>
                </div>
              </div>
            </div>
            <button
              onClick={addKnowledge}
              disabled={!newKnowledge.onderwerp.trim() || !newKnowledge.kort_antwoord.trim()}
              className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium disabled:opacity-50"
            >
              {editingKnowledge ? "Opslaan" : "Toevoegen"}
            </button>
            {editingKnowledge && (
              <button
                onClick={cancelEdit}
                className="ml-2 px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
              >
                Annuleren
              </button>
            )}
          </div>
        ) : null}
      </div>

      {/* List */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-white">
          {activeSection === "norms" ? "📜 Normen Lijst" : 
           activeSection === "values" ? "💎 Waarden Lijst" :
           activeSection === "bijbel" ? "📖 Bijbel Items" :
           activeSection === "emotions" ? "😊 Emotie Status" :
           activeSection === "profielen" ? "👥 Gebruikersprofielen" :
           "🧠 Knowledge Lijst"}
        </h3>
        {loading ? (
          <p className="text-gray-400">Laden...</p>
        ) : activeSection === "norms" ? (
          norms.length > 0 ? (
            norms.map(norm => (
              <div key={norm.id || norm.norm} className="bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-white font-medium text-lg">{norm.norm}</h4>
                      <span className={`text-xs px-2 py-1 rounded ${importanceColors[norm.belangrijkheid || 3]}`}>
                        Niveau {norm.niveau || norm.belangrijkheid || 3}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{norm.beschrijving}</p>
                  </div>
                  {norm.id && (
                    <div className="flex gap-2 ml-3">
                      <button
                        onClick={() => setViewingItem({type: 'norm', data: norm})}
                        className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30"
                        title="Bekijken"
                      >
                        👁️
                      </button>
                      <button
                        onClick={() => {
                          setEditingNorm(norm);
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30"
                        title="Bewerken"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteNorm(norm.id)}
                        className="px-3 py-1 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30"
                        title="Verwijderen"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">Nog geen normen</p>
          )
        ) : activeSection === "values" ? (
          values.length > 0 ? (
            values.map(value => (
              <div key={value.id || value.waarde} className="bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-white font-medium text-lg">💎 {value.waarde}</h4>
                      <span className={`text-xs px-2 py-1 rounded ${importanceColors[value.belangrijkheid || 3]}`}>
                        Niveau {value.niveau || value.belangrijkheid || 3}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">{value.beschrijving}</p>
                  </div>
                  {value.id && (
                    <div className="flex gap-2 ml-3">
                      <button
                        onClick={() => setViewingItem({type: 'value', data: value})}
                        className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30"
                        title="Bekijken"
                      >
                        👁️
                      </button>
                      <button
                        onClick={() => {
                          setEditingValue(value);
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30"
                        title="Bewerken"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteValue(value.id)}
                        className="px-3 py-1 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30"
                        title="Verwijderen"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">Nog geen waarden</p>
          )
        ) : activeSection === "knowledge" ? (
          <>
            {/* KNOWLEDGE SEARCH & FILTER TOOLBOX */}
            <div className="mb-6 space-y-4 bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg">
              {/* Search Bar */}
              <div>
                <input
                  type="text"
                  placeholder="🔍 Zoek in knowledge base (titel, inhoud, tags)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-3 bg-slate-700 text-white rounded-lg border border-slate-600 focus:border-purple-500 focus:outline-none"
                />
              </div>

              {/* Filters Row */}
              <div className="flex flex-wrap gap-3">
                {/* Type Filter */}
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="px-3 py-2 bg-slate-700 text-white rounded-lg border border-slate-600 text-sm"
                >
                  <option value="all">Alle types</option>
                  <option value="knowledge">Knowledge</option>
                  <option value="unknown">Context/Unknown</option>
                  <option value="snap">Snaps</option>
                </select>

                {/* A-Z Index */}
                <div className="flex items-center gap-1 flex-wrap">
                  <span className="text-gray-400 text-xs mr-2">A-Z:</span>
                  {['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'].map(letter => (
                    <button
                      key={letter}
                      onClick={() => setSelectedLetter(selectedLetter === letter ? null : letter)}
                      className={`w-7 h-7 rounded text-xs font-semibold transition-all ${
                        selectedLetter === letter
                          ? 'bg-purple-500 text-white'
                          : 'bg-slate-700 text-gray-400 hover:bg-slate-600 hover:text-white'
                      }`}
                    >
                      {letter}
                    </button>
                  ))}
                  {selectedLetter && (
                    <button
                      onClick={() => setSelectedLetter(null)}
                      className="ml-2 px-2 py-1 bg-red-500/20 text-red-300 rounded text-xs"
                    >
                      ✕ Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Results Count */}
              <div className="text-sm text-gray-400">
                {(() => {
                  const filtered = knowledge.filter(item => {
                    // Search filter
                    const matchesSearch = !searchQuery || 
                      item.begrip?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      item.lagen?.laag1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      item.lagen?.laag2?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      item.lagen?.laag3?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                      item.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

                    // Type filter
                    const matchesType = filterType === 'all' ||
                      (filterType === 'snap' && item.tags?.includes('knowledge-snap')) ||
                      (filterType === 'knowledge' && item.type === 'knowledge') ||
                      (filterType === 'unknown' && item.type === 'unknown');

                    // Letter filter
                    const matchesLetter = !selectedLetter ||
                      item.begrip?.charAt(0).toUpperCase() === selectedLetter;

                    return matchesSearch && matchesType && matchesLetter;
                  });

                  return `${filtered.length} van ${knowledge.length} items`;
                })()}
              </div>
            </div>

            {/* Knowledge List (filtered) */}
            {knowledge.filter(item => {
              const matchesSearch = !searchQuery || 
                item.begrip?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.lagen?.laag1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.lagen?.laag2?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.lagen?.laag3?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                item.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

              const matchesType = filterType === 'all' ||
                (filterType === 'snap' && item.tags?.includes('knowledge-snap')) ||
                (filterType === 'knowledge' && item.type === 'knowledge') ||
                (filterType === 'unknown' && item.type === 'unknown');

              const matchesLetter = !selectedLetter ||
                item.begrip?.charAt(0).toUpperCase() === selectedLetter;

              return matchesSearch && matchesType && matchesLetter;
            }).length > 0 ? (
              knowledge.filter(item => {
                const matchesSearch = !searchQuery || 
                  item.begrip?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  item.lagen?.laag1?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  item.lagen?.laag2?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  item.lagen?.laag3?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                  item.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

                const matchesType = filterType === 'all' ||
                  (filterType === 'snap' && item.tags?.includes('knowledge-snap')) ||
                  (filterType === 'knowledge' && item.type === 'knowledge') ||
                  (filterType === 'unknown' && item.type === 'unknown');

                const matchesLetter = !selectedLetter ||
                  item.begrip?.charAt(0).toUpperCase() === selectedLetter;

                return matchesSearch && matchesType && matchesLetter;
              }).map(item => (
              <div key={item.id || item.begrip} className="bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg">
                <div className="flex flex-col sm:flex-row items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h4 className="text-white font-medium text-lg">🧠 {item.begrip}</h4>
                      {item.type && (
                        <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                          {item.type}
                        </span>
                      )}
                      {(!item.lagen?.laag1 || item.lagen.laag1 === "") && (
                        <span className="text-xs px-2 py-1 bg-orange-500/20 text-orange-300 rounded">
                          ⚠️ Onbeantwoord
                        </span>
                      )}
                      {item.tags?.includes("user-vraag") && (
                        <span className="text-xs px-2 py-1 bg-blue-500/20 text-blue-300 rounded">
                          👤 User vraag
                        </span>
                      )}
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-400">Preview:</span>
                        <p className="text-gray-200 mt-1 line-clamp-2">
                          {item.lagen?.laag1?.substring(0, 150) || item.betekenis?.substring(0, 150) || <span className="text-gray-500 italic">Nog geen antwoord</span>}
                          {(item.lagen?.laag1?.length > 150 || item.betekenis?.length > 150) && '...'}
                        </p>
                      </div>
                      {item.tags && item.tags.length > 0 && (
                        <div className="flex gap-2 mt-2 flex-wrap">
                          {item.tags.slice(0, 5).map((tag, idx) => (
                            <span key={idx} className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded">
                              #{tag}
                            </span>
                          ))}
                          {item.tags.length > 5 && (
                            <span className="text-xs text-gray-500">+{item.tags.length - 5} meer</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0 w-full sm:w-auto">
                    <button
                      onClick={() => editKnowledge(item)}
                      className="flex-1 sm:flex-none px-3 py-2 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30 transition-all"
                    >
                      ✏️ Bewerk
                    </button>
                    <button
                      onClick={() => deleteItem(item.id || item.begrip, "knowledge")}
                      className="flex-1 sm:flex-none px-3 py-2 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30 transition-all"
                    >
                      🗑️ Verwijder
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">Geen results voor je zoekopdracht</p>
          )}
        </>
        ) : activeSection === "snaps" ? (
          snaps.length > 0 ? (
            snaps.map(snap => (
              <div key={snap.id} className="bg-slate-800/50 border border-orange-500/20 p-4 rounded-lg">
                <div className="flex flex-col sm:flex-row items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                      <h4 className="text-white font-medium text-lg">📸 {snap.begrip}</h4>
                      <span className="text-xs px-2 py-1 bg-orange-500/20 text-orange-300 rounded">
                        Draft
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-gray-400">Context:</span>
                        <p className="text-white mt-1">{snap.lagen?.laag2 || "Geen context"}</p>
                      </div>
                      <div className="flex gap-4 text-xs text-gray-500 flex-wrap">
                        <span>👤 Detected by: {snap.detected_by || "Unknown"}</span>
                        <span>📅 {new Date(snap.detected_at).toLocaleDateString('nl-NL')}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2 flex-shrink-0 w-full sm:w-auto">
                    <button
                      onClick={() => editKnowledge(snap)}
                      className="flex-1 sm:flex-none px-3 py-2 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30 transition-all"
                    >
                      ✏️ Invullen
                    </button>
                    <button
                      onClick={() => deleteItem(snap.id, "knowledge")}
                      className="flex-1 sm:flex-none px-3 py-2 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30 transition-all"
                    >
                      🗑️ Verwijder
                    </button>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">
              💡 Geen knowledge snaps. Deze worden automatisch aangemaakt wanneer Spark nieuwe concepten tegenkomt in gesprekken.
            </p>
          )
        ) : activeSection === "bijbel" ? (
          bijbelItems.length > 0 ? (
            bijbelItems.map((item, idx) => (
              <div key={item.id || idx} className="bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="text-white font-medium text-lg mb-2">📖 {item.naam}</h4>
                    <p className="text-sm text-gray-400">{item.beschrijving}</p>
                  </div>
                  {item.id && (
                    <div className="flex gap-2 ml-3">
                      <button
                        onClick={() => setViewingItem({type: 'bijbel', data: item})}
                        className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30"
                        title="Bekijken"
                      >
                        👁️
                      </button>
                      <button
                        onClick={() => {
                          setEditingBijbel(item);
                          window.scrollTo({ top: 0, behavior: 'smooth' });
                        }}
                        className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30"
                        title="Bewerken"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteBijbelItem(item.id)}
                        className="px-3 py-1 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30"
                        title="Verwijderen"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))
          ) : (
            <p className="text-gray-500 text-center py-8">Nog geen bijbel items</p>
          )
        ) : activeSection === "emotions" ? (
          emotions ? (
            <div className="space-y-4">
              <div className="bg-slate-800/50 border border-purple-500/20 p-6 rounded-lg">
                <h4 className="text-white font-medium mb-4">😊 Huidige Emotie</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-gray-400 text-sm">State:</span>
                    <p className="text-white font-medium capitalize">{emotions.current_emotion?.state || "neutral"}</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Sub-state:</span>
                    <p className="text-white font-medium capitalize">{emotions.current_emotion?.sub_state || "Geen"}</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Intensity:</span>
                    <p className="text-white font-medium">{(emotions.current_emotion?.intensity * 100).toFixed(0)}%</p>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">XP Modifier:</span>
                    <p className="text-white font-medium">{emotions.xp_modifier}x</p>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-400 text-sm">Triggered by:</span>
                    <p className="text-white">{emotions.current_emotion?.triggered_by || "system"}</p>
                  </div>
                </div>
              </div>
              <div className="bg-slate-800/50 border border-purple-500/20 p-6 rounded-lg">
                <h4 className="text-white font-medium mb-3">📊 Statistieken</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-400">Totaal Emoties:</span>
                    <p className="text-white">{emotions.total_emotions}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Sub-emoties:</span>
                    <p className="text-white">{emotions.total_sub_emotions}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">XP Groei Levels:</span>
                    <p className="text-white">{emotions.xp_growth_levels}</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">Geen emotie data beschikbaar</p>
          )
        ) : activeSection === "debug" ? (
          <DebugTab />
        ) : null}
      </div>

      {/* EDIT MODALS */}
      {editingNorm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setEditingNorm(null)}>
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 border border-purple-500/30" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white mb-4">✏️ Norm Bewerken</h3>
            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Norm</label>
                <input
                  type="text"
                  value={editingNorm.norm}
                  onChange={(e) => setEditingNorm({...editingNorm, norm: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Beschrijving</label>
                <textarea
                  value={editingNorm.beschrijving}
                  onChange={(e) => setEditingNorm({...editingNorm, beschrijving: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
                  rows="4"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-2">Niveau (1-5)</label>
                <div className="flex gap-2">
                  {[1,2,3,4,5].map(n => (
                    <button
                      key={n}
                      onClick={() => setEditingNorm({...editingNorm, niveau: n})}
                      className={`px-4 py-2 rounded ${(editingNorm.niveau || editingNorm.belangrijkheid) === n ? 'bg-purple-500 text-white' : 'bg-slate-700 text-gray-400'}`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={updateNorm}
                  className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium"
                >
                  Opslaan
                </button>
                <button
                  onClick={() => setEditingNorm(null)}
                  className="px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
                >
                  Annuleren
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingValue && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setEditingValue(null)}>
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 border border-purple-500/30" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white mb-4">✏️ Waarde Bewerken</h3>
            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Waarde</label>
                <input
                  type="text"
                  value={editingValue.waarde}
                  onChange={(e) => setEditingValue({...editingValue, waarde: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Beschrijving</label>
                <textarea
                  value={editingValue.beschrijving}
                  onChange={(e) => setEditingValue({...editingValue, beschrijving: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
                  rows="4"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-2">Niveau (1-5)</label>
                <div className="flex gap-2">
                  {[1,2,3,4,5].map(n => (
                    <button
                      key={n}
                      onClick={() => setEditingValue({...editingValue, niveau: n})}
                      className={`px-4 py-2 rounded ${(editingValue.niveau || editingValue.belangrijkheid) === n ? 'bg-purple-500 text-white' : 'bg-slate-700 text-gray-400'}`}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={updateValue}
                  className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium"
                >
                  Opslaan
                </button>
                <button
                  onClick={() => setEditingValue(null)}
                  className="px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
                >
                  Annuleren
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {editingBijbel && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setEditingBijbel(null)}>
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 border border-purple-500/30" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white mb-4">✏️ Bijbel Item Bewerken</h3>
            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">Naam</label>
                <input
                  type="text"
                  value={editingBijbel.naam}
                  onChange={(e) => setEditingBijbel({...editingBijbel, naam: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
                />
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Beschrijving</label>
                <textarea
                  value={editingBijbel.beschrijving}
                  onChange={(e) => setEditingBijbel({...editingBijbel, beschrijving: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
                  rows="4"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  onClick={updateBijbelItem}
                  className="px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium"
                >
                  Opslaan
                </button>
                <button
                  onClick={() => setEditingBijbel(null)}
                  className="px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
                >
                  Annuleren
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODAL */}
      {viewingItem && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setViewingItem(null)}>
          <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full mx-4 border border-purple-500/30" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white mb-4">
              👁️ {viewingItem.type === 'norm' ? 'Norm' : viewingItem.type === 'value' ? 'Waarde' : 'Bijbel Item'}
            </h3>
            <div className="space-y-4">
              <div>
                <label className="text-gray-400 text-sm block mb-1">
                  {viewingItem.type === 'norm' ? 'Norm' : viewingItem.type === 'value' ? 'Waarde' : 'Naam'}
                </label>
                <p className="text-white text-lg font-medium">
                  {viewingItem.data.norm || viewingItem.data.waarde || viewingItem.data.naam}
                </p>
              </div>
              <div>
                <label className="text-gray-400 text-sm block mb-1">Beschrijving</label>
                <p className="text-white whitespace-pre-wrap">{viewingItem.data.beschrijving}</p>
              </div>
              {(viewingItem.type === 'norm' || viewingItem.type === 'value') && (
                <div>
                  <label className="text-gray-400 text-sm block mb-1">Niveau</label>
                  <div className="flex gap-1">
                    {[1,2,3,4,5].map(n => (
                      <span
                        key={n}
                        className={`w-8 h-8 flex items-center justify-center rounded ${
                          n <= (viewingItem.data.niveau || viewingItem.data.belangrijkheid || 3) 
                            ? 'bg-purple-500 text-white' 
                            : 'bg-slate-700 text-gray-500'
                        }`}
                      >
                        {n}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <button
                onClick={() => setViewingItem(null)}
                className="px-6 py-2 bg-slate-600 text-white rounded-lg font-medium"
              >
                Sluiten
              </button>
            </div>
          </div>
        </div>
      )}


      {/* Profielen Section */}
      {activeSection === "gebruikers" && (
        <div>
          <div className="mb-4 flex gap-3 border-b border-slate-700/50 pb-3">
            <button
              onClick={() => setProfielenSubTab("overzicht")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                profielenSubTab === "overzicht"
                  ? "bg-purple-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              📊 Overzicht
            </button>
            {(currentUser?.gradatie === 1 || currentUser?.gradatie === 2) && (
              <button
                onClick={() => setProfielenSubTab("beheer")}
                className={`px-4 py-2 rounded-lg font-medium transition-all ${
                  profielenSubTab === "beheer"
                    ? "bg-purple-500 text-white"
                    : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                ⚙️ Beheer
              </button>
            )}
          </div>

          {profielenSubTab === "overzicht" && (
            <ProfielenTab currentUserId={currentUser?.id || "user-001"} isAdmin={true} />
          )}

          {profielenSubTab === "beheer" && (currentUser?.gradatie === 1 || currentUser?.gradatie === 2) && (
            <UserManagement adminUserId={currentUser?.id || "user-001"} />
          )}
        </div>
      )}

      {activeSection === "sparkworld" && (
        <div>
          <div className="mb-4 flex gap-3 border-b border-slate-700/50 pb-3">
            <button
              onClick={() => setSparkWorldSubTab("overview")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                sparkWorldSubTab === "overview"
                  ? "bg-green-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🎮 Overview
            </button>
            <button
              onClick={() => setSparkWorldSubTab("buildings")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                sparkWorldSubTab === "buildings"
                  ? "bg-green-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🏘️ Buildings
            </button>
            <button
              onClick={() => setSparkWorldSubTab("blueprints")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                sparkWorldSubTab === "blueprints"
                  ? "bg-green-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🏗️ Blueprints
            </button>
            <button
              onClick={() => setSparkWorldSubTab("editor")}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                sparkWorldSubTab === "editor"
                  ? "bg-green-500 text-white"
                  : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🛠️ Blueprint Editor
            </button>
          </div>

          {sparkWorldSubTab === "overview" && <SparkWorldAdmin />}
          {sparkWorldSubTab === "buildings" && <BuildingsOverviewTab />}
          {sparkWorldSubTab === "blueprints" && <BuildingBlueprintTab />}
          {sparkWorldSubTab === "editor" && <BlueprintEditorTab />}
        </div>
      )}

      {activeSection === "files" && (
        <div>
          <FileBrowserTab userData={currentUser} />
        </div>
      )}
      
      {activeSection === "settings" && (
        <div>
          <SettingsTabNew userData={currentUser} />
        </div>
      )}
      
      {activeSection === "status" && (
        <div>
          <StatusTabNew userData={currentUser} />
        </div>
      )}
      
      {activeSection === "triggers" && (
        <div>
          <TriggerManagerTab />
        </div>
      )}

      {activeSection === "wallet" && (
        <div>
          <WalletTab userData={currentUser} />
        </div>
      )}

      {activeSection === "logs" && (
        <div>
          <LogsTab userData={currentUser} />
        </div>
      )}

      {activeSection === "review" && (
        <KnowledgeReviewTab />
      )}
    </div>
  );
}

export default AdminTab;
