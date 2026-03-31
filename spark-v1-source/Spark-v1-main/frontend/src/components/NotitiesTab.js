import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CATEGORIES = ["Algemeen", "Inzicht", "Patroon", "Observatie", "TODO"];

const CATEGORY_COLORS = {
  "Algemeen": "bg-slate-700/30 text-gray-300",
  "Inzicht": "bg-purple-500/20 text-purple-300",
  "Patroon": "bg-blue-500/20 text-blue-300",
  "Observatie": "bg-green-500/20 text-green-300",
  "TODO": "bg-orange-500/20 text-orange-300"
};

const CATEGORY_ICONS = {
  "Algemeen": "📝",
  "Inzicht": "💡",
  "Patroon": "📊",
  "Observatie": "👁️",
  "TODO": "✅"
};

function NotitiesTab({ userId, userName }) {
  const [notes, setNotes] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [selectedNote, setSelectedNote] = useState(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  const [formData, setFormData] = useState({
    titel: "",
    inhoud: "",
    categorie: "Algemeen",
    tags: ""
  });

  useEffect(() => {
    fetchNotes();
  }, []);

  const fetchNotes = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/notes/notes`, {
        params: { user_id: userId }
      });
      setNotes(response.data.notes || []);
      setStats(response.data.stats || {});
    } catch (error) {
      console.error("Error fetching notes:", error);
    } finally {
      setLoading(false);
    }
  };

  const addNote = async () => {
    if (!formData.titel.trim() || !formData.inhoud.trim()) {
      alert("Titel en inhoud zijn verplicht");
      return;
    }

    try {
      await axios.post(
        `${API}/notes/notes`,
        {
          titel: formData.titel,
          inhoud: formData.inhoud,
          categorie: formData.categorie,
          tags: formData.tags.split(',').map(t => t.trim()).filter(t => t),
          created_by: userName || "User"
        },
        {
          params: { user_id: userId }
        }
      );
      
      resetForm();
      fetchNotes();
    } catch (error) {
      console.error("Error adding note:", error);
      alert("Kon notitie niet toevoegen");
    }
  };

  const updateNote = async () => {
    if (!selectedNote) return;

    try {
      await axios.put(
        `${API}/notes/notes/${selectedNote.id}`,
        {
          titel: formData.titel,
          inhoud: formData.inhoud,
          categorie: formData.categorie,
          tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
        },
        {
          params: { user_id: userId }
        }
      );
      
      resetForm();
      fetchNotes();
    } catch (error) {
      console.error("Error updating note:", error);
      alert("Kon notitie niet bijwerken");
    }
  };

  const deleteNote = async (noteId, titel) => {
    if (!window.confirm(`"${titel}" verwijderen?`)) return;

    try {
      await axios.delete(`${API}/notes/notes/${noteId}`, {
        params: { user_id: userId }
      });
      setSelectedNote(null);
      fetchNotes();
    } catch (error) {
      console.error("Error deleting note:", error);
      alert("Kon notitie niet verwijderen");
    }
  };

  const createTaskFromNote = async (note) => {
    try {
      // Create task linked to this note
      await axios.post(`${BACKEND_URL}/api/tasks`, {
        task: note.titel,
        priority: note.categorie === "TODO" ? "high" : "medium",
        note_id: note.id  // Link to note
      });
      
      alert(`✅ Taak aangemaakt: "${note.titel}"\n\nJe kunt de taak vinden in de Taken tab.`);
    } catch (error) {
      console.error("Error creating task:", error);
      alert("Kon taak niet aanmaken");
    }
  };

  const startEdit = (note) => {
    setSelectedNote(note);
    setIsEditing(true);
    setIsAdding(true);
    setFormData({
      titel: note.titel,
      inhoud: note.inhoud,
      categorie: note.categorie,
      tags: note.tags?.join(", ") || ""
    });
  };

  const resetForm = () => {
    setFormData({ titel: "", inhoud: "", categorie: "Algemeen", tags: "" });
    setIsAdding(false);
    setIsEditing(false);
    setSelectedNote(null);
  };

  const filteredNotes = filter === "all" 
    ? notes 
    : notes.filter(n => n.categorie === filter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">📝 Notities & Brainfarts</h2>
          <p className="text-sm text-gray-400 mt-1">Spark's inzichten, patronen en observaties</p>
        </div>
        {!isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:opacity-90 transition-all"
          >
            ➕ Nieuwe Notitie
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-5 gap-3">
        {CATEGORIES.map(cat => (
          <div key={cat} className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xl">{CATEGORY_ICONS[cat]}</span>
              <p className="text-sm text-gray-400">{cat}</p>
            </div>
            <p className="text-2xl font-bold text-white">{stats[cat] || 0}</p>
          </div>
        ))}
      </div>

      {/* Add/Edit Form */}
      {isAdding && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">
            {isEditing ? "✏️ Bewerk Notitie" : "➕ Nieuwe Notitie"}
          </h3>
          
          <div className="space-y-3">
            <input
              type="text"
              value={formData.titel}
              onChange={(e) => setFormData({...formData, titel: e.target.value})}
              placeholder="Titel"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
            />
            
            <textarea
              value={formData.inhoud}
              onChange={(e) => setFormData({...formData, inhoud: e.target.value})}
              placeholder="Inhoud"
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500 resize-none"
              rows="4"
            />
            
            <div className="flex gap-3">
              <div className="flex-1">
                <label className="text-sm text-gray-400 mb-1 block">Categorie</label>
                <select
                  value={formData.categorie}
                  onChange={(e) => setFormData({...formData, categorie: e.target.value})}
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat} value={cat}>{CATEGORY_ICONS[cat]} {cat}</option>
                  ))}
                </select>
              </div>
              
              <div className="flex-1">
                <label className="text-sm text-gray-400 mb-1 block">Tags (komma gescheiden)</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({...formData, tags: e.target.value})}
                  placeholder="belangrijk, persoonlijk, idee"
                  className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-500"
                />
              </div>
            </div>
            
            <div className="flex gap-3 pt-2">
              <button
                onClick={isEditing ? updateNote : addNote}
                className="flex-1 px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium"
              >
                {isEditing ? "💾 Opslaan" : "➕ Toevoegen"}
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
          Alles ({notes.length})
        </button>
        {CATEGORIES.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              filter === cat
                ? "bg-purple-500 text-white"
                : "bg-slate-700/30 text-gray-400 hover:bg-slate-700/50"
            }`}
          >
            {CATEGORY_ICONS[cat]} {cat} ({stats[cat] || 0})
          </button>
        ))}
      </div>

      {/* Notes List */}
      <div className="space-y-3">
        {loading ? (
          <p className="text-gray-400 text-center py-8">Laden...</p>
        ) : filteredNotes.length > 0 ? (
          filteredNotes.map(note => (
            <div
              key={note.id}
              className="bg-slate-800/50 border border-purple-500/20 p-4 rounded-lg hover:border-purple-500/40 transition-all"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-xl">{CATEGORY_ICONS[note.categorie]}</span>
                    <h4 className="text-white font-medium">{note.titel}</h4>
                    <span className={`text-xs px-2 py-1 rounded ${CATEGORY_COLORS[note.categorie]}`}>
                      {note.categorie}
                    </span>
                  </div>
                  
                  <p className="text-gray-300 text-sm mb-2">{note.inhoud}</p>
                  
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    <span>📅 {new Date(note.datum).toLocaleDateString('nl-NL')}</span>
                    <span>👤 {note.created_by}</span>
                    {note.tags && note.tags.length > 0 && (
                      <div className="flex gap-1">
                        {note.tags.map((tag, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded">
                            #{tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2 ml-4">
                  <button
                    onClick={() => createTaskFromNote(note)}
                    className="px-3 py-1 bg-green-500/20 text-green-300 rounded text-sm hover:bg-green-500/30"
                    title="Maak taak van deze notitie"
                  >
                    ✅ Taak
                  </button>
                  <button
                    onClick={() => startEdit(note)}
                    className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded text-sm hover:bg-blue-500/30"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => deleteNote(note.id, note.titel)}
                    className="px-3 py-1 bg-red-500/20 text-red-300 rounded text-sm hover:bg-red-500/30"
                    style={{ 
                      pointerEvents: 'auto',
                      zIndex: 9999,
                      cursor: 'pointer'
                    }}
                    type="button"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-12 bg-slate-800/30 rounded-lg">
            <span className="text-4xl mb-4 block">📝</span>
            <p className="text-gray-400">
              Nog geen notities in deze categorie.
            </p>
            <p className="text-gray-500 text-sm mt-2">
              💡 Tip: Type "note: [jouw tekst]" in de chat om snel een notitie toe te voegen!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default NotitiesTab;
