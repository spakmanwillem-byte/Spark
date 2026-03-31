import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function KnowledgeBaseTab({ userId, isAdmin }) {
  const [knowledge, setKnowledge] = useState([]);
  const [filteredKnowledge, setFilteredKnowledge] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all, unanswered, answered, te-herzien
  const [isEditing, setIsEditing] = useState(false);
  
  // NEW: Search, Sort, Filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("recent"); // recent, alpha-asc, alpha-desc, importance-high, importance-low
  const [filterImportance, setFilterImportance] = useState("all"); // all, 1-5, 6-10
  const [filterTags, setFilterTags] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(50);
  
  const [editForm, setEditForm] = useState({
    begrip: "",
    laag1: "",
    laag2: "",
    laag3: "",
    laag4: "",
    topic: "",
    tags: "",
    belangrijkheid: 3,
    ws5: { who: "", what: "", when: "", where: "", why: "", how: "" }
  });

  // Helper: Check of card audit attention nodig heeft + geef REDEN
  const needsAuditAttention = (entry) => {
    // 🔴 Placeholder action (HIGH)
    if (entry.type === 'action' && entry.action?.type === 'placeholder') {
      return { 
        level: 'high', 
        label: '🔴 [TE HERZIEN]',
        reason: 'Placeholder action',
        detail: `Nog te bouwen: ${entry.action.future_module || 'Unknown module'}`
      };
    }
    
    // 🔴 Weak trigger (MEDIUM -> ook rood tonen)
    const triggerTypes = ['greeting', 'farewell', 'action'];
    if (triggerTypes.includes(entry.type)) {
      const response = entry.response;
      
      // Geen response
      if (!response || !response.text) {
        return { 
          level: 'high', 
          label: '🔴 [TE HERZIEN]',
          reason: 'Weak trigger',
          detail: 'Geen response field - voeg response toe'
        };
      }
      
      // Response te kort
      if (response.text) {
        const text = Array.isArray(response.text) ? response.text[0] : response.text;
        if (text && text.length < 10) {
          return { 
            level: 'high', 
            label: '🔴 [TE HERZIEN]',
            reason: 'Weak trigger',
            detail: `Response te kort: "${text}" - maak uitgebreider`
          };
        }
      }
    }
    
    return null;
  };

  useEffect(() => {
    fetchKnowledge();
  }, []);

  useEffect(() => {
    // Apply search, sort, filter whenever knowledge or filters change
    applyFiltersAndSort();
  }, [knowledge, searchQuery, sortBy, filterImportance, filterTags, filter]);

  const applyFiltersAndSort = () => {
    let filtered = [...knowledge];

    // Status filter
    if (filter === "unanswered") {
      // Onbeantwoord = laag1 is leeg
      filtered = filtered.filter(entry => !entry.lagen?.laag1 || entry.lagen.laag1 === "");
    } else if (filter === "answered") {
      // Beantwoord = laag1 is ingevuld
      filtered = filtered.filter(entry => entry.lagen?.laag1 && entry.lagen.laag1 !== "");
    } else if (filter === "te-herzien") {
      // TE HERZIEN = cards die audit attention nodig hebben
      filtered = filtered.filter(entry => needsAuditAttention(entry) !== null);
      
      // SORTEER OP STERREN (belangrijkheid hoog → laag)
      // Als sterren gelijk: Eerst placeholder actions, dan weak triggers
      filtered.sort((a, b) => {
        const belangA = a.belangrijkheid || 0;
        const belangB = b.belangrijkheid || 0;
        
        // Eerst op sterren
        if (belangA !== belangB) {
          return belangB - belangA; // Descending (hoogste eerst)
        }
        
        // Als sterren gelijk: sorteer op type
        const typeA = needsAuditAttention(a);
        const typeB = needsAuditAttention(b);
        
        // Placeholder actions eerst (echte ontbrekende features)
        if (typeA?.reason === 'Placeholder action' && typeB?.reason !== 'Placeholder action') {
          return -1; // A komt voor B
        }
        if (typeA?.reason !== 'Placeholder action' && typeB?.reason === 'Placeholder action') {
          return 1; // B komt voor A
        }
        
        // Anders: behoud volgorde
        return 0;
      });
    }
    // "all" = geen filter

    // Search query (begrip + definitie)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(entry => 
        entry.begrip.toLowerCase().includes(query) ||
        entry.lagen?.laag1?.toLowerCase().includes(query) ||
        entry.lagen?.laag2?.toLowerCase().includes(query) ||
        entry.lagen?.laag3?.toLowerCase().includes(query)
      );
    }

    // Filter by importance (sterren)
    if (filterImportance !== "all") {
      if (filterImportance === "low") {
        filtered = filtered.filter(entry => (entry.belangrijkheid || 0) >= 1 && (entry.belangrijkheid || 0) <= 5);
      } else if (filterImportance === "high") {
        filtered = filtered.filter(entry => (entry.belangrijkheid || 0) >= 6 && (entry.belangrijkheid || 0) <= 10);
      }
    }

    // Filter by tags
    if (filterTags.length > 0) {
      filtered = filtered.filter(entry => 
        entry.tags && entry.tags.some(tag => filterTags.includes(tag))
      );
    }

    // Sort
    switch (sortBy) {
      case "alpha-asc":
        filtered.sort((a, b) => a.begrip.localeCompare(b.begrip));
        break;
      case "alpha-desc":
        filtered.sort((a, b) => b.begrip.localeCompare(a.begrip));
        break;
      case "importance-high":
        filtered.sort((a, b) => (b.belangrijkheid || 0) - (a.belangrijkheid || 0));
        break;
      case "importance-low":
        filtered.sort((a, b) => (a.belangrijkheid || 0) - (b.belangrijkheid || 0));
        break;
      case "recent":
      default:
        // Keep original order (most recent first, assuming backend returns that way)
        break;
    }

    setFilteredKnowledge(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const getAllTags = () => {
    const tagsSet = new Set();
    knowledge.forEach(entry => {
      if (entry.tags) {
        entry.tags.forEach(tag => tagsSet.add(tag));
      }
    });
    return Array.from(tagsSet).sort();
  };

  // Pagination
  const totalPages = Math.ceil(filteredKnowledge.length / itemsPerPage);
  const paginatedKnowledge = filteredKnowledge.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const fetchKnowledge = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/knowledge/all`);
      setKnowledge(response.data.entries || []);
    } catch (error) {
      console.error("Error fetching knowledge:", error);
    } finally {
      setLoading(false);
    }
  };

  const deleteEntry = async (id, begrip) => {
    console.log(`[DELETE] Starting hard delete for: ${begrip} (ID: ${id})`);
    
    if (!window.confirm(`"${begrip}" permanent verwijderen?\n\nDit kan NIET ongedaan worden gemaakt!`)) {
      console.log(`[DELETE] User cancelled`);
      return;
    }
    
    try {
      console.log(`[DELETE] Sending DELETE request to /api/admin/knowledge/${id}`);
      const response = await axios.delete(`${API}/admin/knowledge/${id}`);
      console.log(`[DELETE] Success!`, response.data);
      
      alert("✅ Knowledge verwijderd");
      
      // Reload data
      console.log(`[DELETE] Reloading knowledge...`);
      await fetchKnowledge();
      setSelectedEntry(null);
      console.log(`[DELETE] Done!`);
    } catch (error) {
      console.error(`[DELETE] Error:`, error);
      alert("Kon niet verwijderen: " + (error.response?.data?.detail || error.message));
    }
  };

  // TRASH/RESTORE REMOVED - using simple hard delete only

  const startEdit = (entry) => {
    setIsEditing(true);
    setEditForm({
      begrip: entry.begrip,
      laag1: entry.lagen?.laag1 || "",
      laag2: entry.lagen?.laag2 || "",
      laag3: entry.lagen?.laag3 || "",
      laag4: entry.lagen?.laag4 || "",
      topic: entry.topic || "",
      tags: entry.tags?.join(", ") || "",
      belangrijkheid: entry.belangrijkheid || 3,
      ws5: entry.ws5 || { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
    
    // Scroll modal to top when opening edit mode
    setTimeout(() => {
      const modal = document.querySelector('.fixed.inset-0 > div');
      if (modal) {
        modal.scrollTop = 0;
      }
    }, 100);
  };

  const saveEdit = async () => {
    if (!selectedEntry) return;
    
    try {
      await axios.put(`${API}/admin/knowledge/${selectedEntry.id}`, {
        begrip: editForm.begrip,
        lagen: {
          laag1: editForm.laag1,
          laag2: editForm.laag2,
          laag3: editForm.laag3,
          laag4: editForm.laag4
        },
        topic: editForm.topic,
        tags: editForm.tags.split(',').map(t => t.trim()).filter(t => t),
        belangrijkheid: editForm.belangrijkheid,
        ws5: editForm.ws5
      });
      
      setIsEditing(false);
      setSelectedEntry(null);
      fetchKnowledge();
    } catch (error) {
      alert("Kon niet opslaan: " + (error.response?.data?.detail || error.message));
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setEditForm({
      begrip: "",
      laag1: "",
      laag2: "",
      laag3: "",
      laag4: "",
      topic: "",
      tags: "",
      belangrijkheid: 3,
      ws5: { who: "", what: "", when: "", where: "", why: "", how: "" }
    });
  };

  // OLD filteredKnowledge removed - now using state variable from line 9

  const stats = {
    total: knowledge.length,
    unanswered: knowledge.filter(k => !k.lagen?.laag1 || k.lagen.laag1 === "").length,
    answered: knowledge.filter(k => k.lagen?.laag1 && k.lagen.laag1 !== "").length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">🧠 Knowledge Base</h2>
          <p className="text-sm text-gray-400 mt-1">Beheer alle kennis van Spark</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-4 rounded-lg">
          <p className="text-sm text-gray-400">Totaal</p>
          <p className="text-2xl font-bold text-white">{stats.total}</p>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-lg border border-orange-500/20 p-4 rounded-lg">
          <p className="text-sm text-gray-400">Onbeantwoord</p>
          <p className="text-2xl font-bold text-orange-400">{stats.unanswered}</p>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-lg border border-green-500/20 p-4 rounded-lg">
          <p className="text-sm text-gray-400">Beantwoord</p>
          <p className="text-2xl font-bold text-green-400">{stats.answered}</p>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-lg border border-red-500/20 p-4 rounded-lg">
          <p className="text-sm text-gray-400">Te Herzien</p>
          <p className="text-2xl font-bold text-red-400">{knowledge.filter(e => needsAuditAttention(e)).length}</p>
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setFilter("all")}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            filter === "all"
              ? "bg-purple-500 text-white"
              : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
          }`}
        >
          Alles ({stats.total})
        </button>
        <button
          onClick={() => setFilter("unanswered")}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            filter === "unanswered"
              ? "bg-orange-500 text-white"
              : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
          }`}
        >
          ⚠️ Onbeantwoord ({stats.unanswered})
        </button>
        <button
          onClick={() => setFilter("answered")}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            filter === "answered"
              ? "bg-green-500 text-white"
              : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
          }`}
        >
          ✅ Beantwoord ({stats.answered})
        </button>
        <button
          onClick={() => setFilter("te-herzien")}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            filter === "te-herzien"
              ? "bg-red-500 text-white"
              : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
          }`}
        >
          🔴 Te Herzien ({knowledge.filter(e => needsAuditAttention(e)).length})
        </button>
      </div>

      {/* Knowledge List */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        {loading ? (
          <p className="text-gray-400">Laden...</p>
        ) : paginatedKnowledge.length > 0 ? (
          <div className="space-y-3">
            {paginatedKnowledge.map((item, idx) => (
              <div
                key={idx}
                className="bg-slate-700/30 p-4 rounded-lg border border-slate-600/30 hover:border-purple-500/50 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <div 
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                    onClick={() => setSelectedEntry(item)}
                  >
                    <span className="text-lg">🧠</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-white font-medium">{item.begrip}</h4>
                        
                        {/* 🔴 AUDIT TAG + REASON */}
                        {(() => {
                          const auditStatus = needsAuditAttention(item);
                          if (auditStatus) {
                            return (
                              <div className="flex flex-col gap-1">
                                <span className="text-xs font-bold px-2 py-1 bg-red-500/20 text-red-400 rounded">
                                  {auditStatus.label}
                                </span>
                                <span className="text-xs text-orange-400">
                                  ⚠️ {auditStatus.reason}: {auditStatus.detail}
                                </span>
                              </div>
                            );
                          }
                          return null;
                        })()}
                        
                        {(!item.lagen?.laag1 || item.lagen.laag1 === "") && !needsAuditAttention(item) && (
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
                      <p className="text-sm text-gray-400 mt-1">
                        {item.lagen?.laag1 ? 
                          item.lagen.laag1.substring(0, 80) + (item.lagen.laag1.length > 80 ? "..." : "") 
                          : "Nog geen antwoord - klik om toe te voegen"}
                      </p>
                      {item.gevraagd_door && (
                        <p className="text-xs text-gray-500 mt-1">
                          Gevraagd door: {item.gevraagd_door}
                        </p>
                      )}
                    </div>
                  </div>
                  {isAdmin && (
                    <div className="flex gap-2 ml-3 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedEntry(item);
                          startEdit(item);
                        }}
                        className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30"
                        title="Bewerken"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteEntry(item.id, item.begrip);
                        }}
                        className="px-3 py-1 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30"
                        style={{ 
                          pointerEvents: 'auto',
                          zIndex: 9999,
                          cursor: 'pointer'
                        }}
                        type="button"
                        title="Verwijderen"
                      >
                        🗑️
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <span className="text-4xl mb-4 block">🤔</span>
            <p className="text-gray-400">
              {filter === "unanswered" ? "Geen onbeantwoorde vragen" :
               filter === "answered" ? "Nog geen beantwoorde vragen" :
               "Nog geen knowledge entries"}
            </p>
          </div>
        )}
      </div>

      {/* Detail Modal - DIRECT EDITABLE */}
      {selectedEntry && !isEditing && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" 
          onClick={() => setSelectedEntry(null)}
        >
          <div 
            className="bg-slate-800 border border-purple-500/30 rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto" 
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">🧠 {selectedEntry.begrip}</h3>
                {selectedEntry.gevraagd_door && (
                  <p className="text-sm text-gray-400">
                    Gevraagd door: {selectedEntry.gevraagd_door} 
                    {selectedEntry.gevraagd_op && ` op ${new Date(selectedEntry.gevraagd_op).toLocaleDateString('nl-NL')}`}
                  </p>
                )}
              </div>
              <button
                onClick={() => setSelectedEntry(null)}
                className="text-gray-400 hover:text-white text-3xl leading-none"
                style={{ 
                  pointerEvents: 'auto',
                  zIndex: 99999,
                  cursor: 'pointer'
                }}
                type="button"
              >
                ×
              </button>
            </div>

            <div className="space-y-6">
              {/* Layer 1 */}
              <div className="bg-slate-700/30 p-4 rounded-lg">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🍎</span>
                  <div>
                    <span className="text-sm text-gray-400 font-medium">Laag 1: Kort antwoord</span>
                    <p className="text-xs text-gray-500">Directe, korte uitleg</p>
                  </div>
                </div>
                <p className="text-gray-200">
                  {selectedEntry.lagen?.laag1 || (
                    <span className="text-gray-500 italic">
                      Nog geen antwoord - klik op bewerken om toe te voegen
                    </span>
                  )}
                </p>
              </div>

              {/* Layer 2 */}
              <div className={`bg-slate-700/30 p-4 rounded-lg ${!selectedEntry.lagen?.laag2 ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🍏</span>
                  <div>
                    <span className="text-sm text-gray-400 font-medium">Laag 2: + Context</span>
                    <p className="text-xs text-gray-500">Waarom belangrijk, context</p>
                  </div>
                </div>
                <p className="text-gray-200">
                  {selectedEntry.lagen?.laag2 || (
                    <span className="text-gray-500 italic">Nog niet ingevuld</span>
                  )}
                </p>
              </div>

              {/* Layer 3 */}
              <div className={`bg-slate-700/30 p-4 rounded-lg ${!selectedEntry.lagen?.laag3 ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">🌳</span>
                  <div>
                    <span className="text-sm text-gray-400 font-medium">Laag 3: Volledig</span>
                    <p className="text-xs text-gray-500">Diepgaande uitleg, alle details</p>
                  </div>
                </div>
                <p className="text-gray-200">
                  {selectedEntry.lagen?.laag3 || (
                    <span className="text-gray-500 italic">Nog niet ingevuld</span>
                  )}
                </p>
              </div>

              {/* Layer 4 - ESSENTIE/GEDRAG */}
              <div className={`bg-slate-700/30 p-4 rounded-lg ${!selectedEntry.lagen?.laag4 ? 'opacity-50' : ''}`}>
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-2xl">💡</span>
                  <div>
                    <span className="text-sm text-gray-400 font-medium">Laag 4: Essentie</span>
                    <p className="text-xs text-gray-500">Wat Spark hiermee doet in communicatie</p>
                  </div>
                </div>
                <p className="text-gray-200">
                  {selectedEntry.lagen?.laag4 || (
                    <span className="text-orange-400 italic">⚠️ Verplicht - nog niet ingevuld</span>
                  )}
                </p>
              </div>

              {/* Topic */}
              <div>
                <p className="text-sm text-gray-400 mb-2">📂 Topic:</p>
                <p className="text-gray-200">
                  {selectedEntry.topic || (
                    <span className="text-orange-400 italic">⚠️ Nog geen topic (gebruik betekenisvolle clustering)</span>
                  )}
                </p>
              </div>

              {/* Tags */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Tags:</p>
                {selectedEntry.tags && selectedEntry.tags.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.tags.map((tag, idx) => (
                      <span key={idx} className="text-xs px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full">
                        #{tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-gray-500 italic text-sm">Nog geen tags</span>
                )}
              </div>
              
              {/* Belangrijkheid */}
              <div>
                <p className="text-sm text-gray-400 mb-2">⭐ Belangrijkheid:</p>
                <div className="flex gap-1">
                  {[...Array(5)].map((_, i) => (
                    <span key={i} className={`text-lg ${i < (selectedEntry.belangrijkheid || 0) ? 'text-yellow-400' : 'text-gray-600'}`}>
                      ⭐
                    </span>
                  ))}
                  <span className="text-sm text-gray-400 ml-2">({selectedEntry.belangrijkheid || 0}/5)</span>
                </div>
              </div>
              
              {/* 5 W's Framework */}
              <div className="border-t border-slate-700 pt-4 mt-4">
                <p className="text-sm text-gray-300 font-medium mb-3">📋 5 W's Framework</p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">👤 Wie:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.who || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">📌 Wat:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.what || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">📅 Wanneer:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.when || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">📍 Waar:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.where || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">❓ Waarom:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.why || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">⚙️ Hoe:</span>
                    <p className="text-gray-200 mt-1">{selectedEntry.ws5?.how || <span className="text-gray-600 italic">-</span>}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-6 border-t border-slate-700 mt-6">
              <button
                onClick={() => startEdit(selectedEntry)}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 transition-all font-medium"
              >
                ✏️ Bewerken
              </button>
              {isAdmin && (
                <button
                  onClick={() => deleteEntry(selectedEntry.id, selectedEntry.begrip)}
                  className="px-4 py-3 bg-red-500/20 text-red-300 rounded-lg hover:bg-red-500/30 transition-all font-medium"
                  style={{ 
                    pointerEvents: 'auto',
                    zIndex: 9999,
                    cursor: 'pointer'
                  }}
                  type="button"
                >
                  🗑️
                </button>
              )}
              <button
                onClick={() => setSelectedEntry(null)}
                className="px-6 py-3 bg-slate-600 text-white rounded-lg hover:bg-slate-700 transition-all font-medium"
              >
                Sluiten
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {isEditing && selectedEntry && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800/95 border border-purple-500/30 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800/95 border-b border-slate-700 p-6 flex items-center justify-between">
              <h3 className="text-2xl font-bold text-white">✏️ Bewerk: {selectedEntry.begrip}</h3>
              <button
                onClick={() => { setIsEditing(false); setSelectedEntry(null); }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Begrip */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">Begrip</label>
                <input
                  type="text"
                  value={editForm.begrip}
                  onChange={(e) => setEditForm({...editForm, begrip: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
                />
              </div>

              {/* 3 Lagen */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">🍎 Laag 1: Kort Antwoord</label>
                <textarea
                  value={editForm.laag1}
                  onChange={(e) => setEditForm({...editForm, laag1: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
                  rows="2"
                />
              </div>

              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">🍏 Laag 2: + Context</label>
                <textarea
                  value={editForm.laag2}
                  onChange={(e) => setEditForm({...editForm, laag2: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none"
                  rows="3"
                />
              </div>

              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">🌳 Laag 3: Volledig</label>
                <textarea
                  value={editForm.laag3}
                  onChange={(e) => setEditForm({...editForm, laag3: e.target.value})}
                  placeholder="Diepgaande uitleg, alle details"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none placeholder-gray-500"
                  rows="4"
                />
              </div>

              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">
                  💡 Laag 4: Essentie <span className="text-orange-400">*</span>
                </label>
                <p className="text-xs text-gray-500 mb-2">Wat Spark hiermee doet in communicatie (verplicht)</p>
                <textarea
                  value={editForm.laag4}
                  onChange={(e) => setEditForm({...editForm, laag4: e.target.value})}
                  placeholder="Bijvoorbeeld: Geeft een duidelijk signaal van afsluiting en helpt verwachtingen te managen"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none placeholder-gray-500"
                  rows="3"
                />
              </div>

              {/* Topic */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">
                  📂 Topic <span className="text-orange-400">*</span>
                </label>
                <p className="text-xs text-gray-500 mb-2">Betekenisvol voor clustering (niet "algemeen")</p>
                <input
                  type="text"
                  value={editForm.topic}
                  onChange={(e) => setEditForm({...editForm, topic: e.target.value})}
                  placeholder="bijv: communicatie, communicatie: afsluiting"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>

              {/* Tags */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">Tags (komma gescheiden)</label>
                <input
                  type="text"
                  value={editForm.tags}
                  onChange={(e) => setEditForm({...editForm, tags: e.target.value})}
                  placeholder="bijv: fruit, gezond, voedsel"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>

              {/* Belangrijkheid */}
              <div>
                <label className="text-sm text-gray-300 font-medium block mb-2">⭐ Belangrijkheid</label>
                <div className="flex gap-2">
                  {[1,2,3,4,5].map(val => (
                    <button
                      key={val}
                      type="button"
                      onClick={() => setEditForm({...editForm, belangrijkheid: val})}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        editForm.belangrijkheid === val 
                          ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                          : "bg-slate-700/30 text-gray-500"
                      }`}
                    >
                      {val}
                    </button>
                  ))}
                </div>
              </div>

              {/* 5 W's Framework */}
              <div className="border-t border-slate-700 pt-4">
                <p className="text-sm text-gray-300 font-medium mb-3">📋 5 W's Framework (optioneel)</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">👤 Wie</label>
                    <input
                      type="text"
                      value={editForm.ws5.who}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, who: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Wie is betrokken?"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">📌 Wat</label>
                    <input
                      type="text"
                      value={editForm.ws5.what}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, what: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Wat is het?"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">📅 Wanneer</label>
                    <input
                      type="text"
                      value={editForm.ws5.when}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, when: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Wanneer relevant?"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">📍 Waar</label>
                    <input
                      type="text"
                      value={editForm.ws5.where}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, where: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Waar speelt het?"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">❓ Waarom</label>
                    <input
                      type="text"
                      value={editForm.ws5.why}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, why: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Waarom belangrijk?"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-gray-500 block mb-1">⚙️ Hoe</label>
                    <input
                      type="text"
                      value={editForm.ws5.how}
                      onChange={(e) => setEditForm({...editForm, ws5: {...editForm.ws5, how: e.target.value}})}
                      className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded text-white text-sm"
                      placeholder="Hoe werkt het?"
                    />
                  </div>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-4 border-t border-slate-700">
                <button
                  onClick={saveEdit}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:opacity-90"
                >
                  💾 Opslaan
                </button>
                <button
                  onClick={cancelEdit}
                  className="px-6 py-3 bg-slate-600 text-white rounded-lg font-medium hover:bg-slate-500"
                >
                  Annuleren
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default KnowledgeBaseTab;
