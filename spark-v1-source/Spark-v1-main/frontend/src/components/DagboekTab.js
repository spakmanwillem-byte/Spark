import React, { useState, useEffect } from 'react';
import axios from 'axios';
import MoodSelector from './MoodSelector';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function DagboekTab({ userId }) {
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newEntry, setNewEntry] = useState('');
  const [mood, setMood] = useState('');
  const [tags, setTags] = useState('');
  const [saving, setSaving] = useState(false);

  // Filter state
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Edit state
  const [editingId, setEditingId] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [editMood, setEditMood] = useState('');
  const [editTags, setEditTags] = useState('');

  useEffect(() => {
    fetchEntries();
  }, [userId, startDate, endDate]);

  const fetchEntries = async () => {
    try {
      const params = { 
        start_date: startDate || undefined, 
        end_date: endDate || undefined 
      };
      const response = await axios.get(`${API}/personal/dagboek/${userId}`, { params });
      setEntries(response.data?.entries || []);
      setStats(response.data?.stats || {});
    } catch (error) {
      console.error('Error fetching dagboek:', error);
    } finally {
      setLoading(false);
    }
  };

  const addEntry = async () => {
    if (!newEntry.trim()) return;

    setSaving(true);
    try {
      const tagsList = tags.trim() ? tags.split(',').map(t => t.trim()).filter(Boolean) : [];
      
      await axios.post(`${API}/personal/dagboek`, {
        user_id: userId,
        content: newEntry,
        mood: mood || null,
        tags: tagsList
      });

      // Clear form
      setNewEntry('');
      setMood('');
      setTags('');

      // Reload entries
      await fetchEntries();
    } catch (error) {
      console.error('Error adding entry:', error);
      alert('Kon entry niet opslaan');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (entry) => {
    setEditingId(entry.id);
    setEditContent(entry.content);
    setEditMood(entry.mood || '');
    setEditTags((entry.tags || []).join(', '));
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditContent('');
    setEditMood('');
    setEditTags('');
  };

  const saveEdit = async (entryId) => {
    if (!editContent.trim()) return;

    try {
      const tagsList = editTags.trim() ? editTags.split(',').map(t => t.trim()).filter(Boolean) : [];
      
      await axios.put(
        `${API}/personal/dagboek/${entryId}`,
        {
          content: editContent,
          mood: editMood || null,
          tags: tagsList
        },
        {
          params: { user_id: userId }
        }
      );

      setEditingId(null);
      await fetchEntries();
    } catch (error) {
      console.error('Error updating entry:', error);
      alert('Kon entry niet bijwerken');
    }
  };

  const deleteEntry = async (entryId) => {
    if (!window.confirm('Weet je zeker dat je deze entry wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API}/personal/dagboek/${entryId}`, {
        params: { user_id: userId }
      });
      await fetchEntries();
    } catch (error) {
      console.error('Error deleting entry:', error);
      alert('Kon entry niet verwijderen');
    }
  };

  const exportDagboek = async (format = 'txt') => {
    try {
      const params = {
        format,
        start_date: startDate || undefined,
        end_date: endDate || undefined
      };
      
      const response = await axios.get(`${API}/personal/dagboek/${userId}/export`, { params });
      
      if (response.data.success) {
        // Create download
        const blob = new Blob([response.data.content], { type: 'text/plain;charset=utf-8' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `dagboek_export_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Kon export niet genereren');
    }
  };

  const moodEmojis = {
    blij: '😊',
    gespannen: '😰',
    verdrietig: '😢',
    boos: '😠',
    enthousiast: '🤩',
    moe: '😴',
    neutraal: '😐',
    energiek: '⚡'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-purple-400">Dagboek laden...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">📔 Dagboek</h2>
          <p className="text-sm text-gray-400 mt-1">Privé reflecties en emoties</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            data-testid="dagboek-filter-toggle"
          >
            🔍 {showFilters ? 'Verberg' : 'Filter'}
          </button>
          <button
            onClick={() => exportDagboek('txt')}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            data-testid="dagboek-export-btn"
          >
            📥 Export
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-4 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-300 mb-2">Van datum</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full bg-slate-900/50 border border-purple-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-purple-500/50"
                data-testid="dagboek-start-date"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-2">Tot datum</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full bg-slate-900/50 border border-purple-500/20 rounded px-3 py-2 text-white focus:outline-none focus:border-purple-500/50"
                data-testid="dagboek-end-date"
              />
            </div>
          </div>
          {(startDate || endDate) && (
            <button
              onClick={() => { setStartDate(''); setEndDate(''); }}
              className="mt-3 text-sm text-purple-400 hover:text-purple-300"
            >
              ✕ Wis filters
            </button>
          )}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{stats.total_entries || 0}</div>
              <div className="text-xs text-gray-400">Entries</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{stats.total_words || 0}</div>
              <div className="text-xs text-gray-400">Woorden</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-pink-400">{stats.avg_words_per_entry || 0}</div>
              <div className="text-xs text-gray-400">Gemiddeld/entry</div>
            </div>
          </div>
        </div>
      )}

      {/* New Entry Form */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">✍️ Nieuwe Entry</h3>
        <textarea
          value={newEntry}
          onChange={(e) => setNewEntry(e.target.value)}
          placeholder="Schrijf hier je gedachten..."
          className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50 resize-none"
          rows="4"
          data-testid="dagboek-new-entry-textarea"
        />

        {/* Tags Input */}
        <div className="mt-3">
          <input
            type="text"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            placeholder="Tags (komma gescheiden, bijv: reflectie, werk, emotie)"
            className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:border-purple-500/50"
            data-testid="dagboek-tags-input"
          />
        </div>

        {/* Mood Selector */}
        <div className="mt-4">
          <MoodSelector selectedMood={mood} onMoodChange={setMood} />
        </div>

        <button
          onClick={addEntry}
          disabled={saving || !newEntry.trim()}
          className="mt-4 w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          data-testid="dagboek-add-entry-btn"
        >
          {saving ? 'Opslaan...' : '✍️ Entry Toevoegen'}
        </button>
      </div>

      {/* Entries List */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-white">📚 Entries ({entries.length})</h3>
        {entries.length > 0 ? (
          entries.map((entry) => (
            <div key={entry.id} className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
              {editingId === entry.id ? (
                // Edit mode
                <div className="space-y-3">
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white resize-none focus:outline-none focus:border-purple-500/50"
                    rows="4"
                  />
                  <input
                    type="text"
                    value={editTags}
                    onChange={(e) => setEditTags(e.target.value)}
                    placeholder="Tags (komma gescheiden)"
                    className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500/50"
                  />
                  <MoodSelector selectedMood={editMood} onMoodChange={setEditMood} />
                  <div className="flex gap-2">
                    <button
                      onClick={() => saveEdit(entry.id)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                    >
                      💾 Opslaan
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
                    >
                      ✕ Annuleren
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      {entry.mood && moodEmojis[entry.mood] && (
                        <span className="text-2xl">{moodEmojis[entry.mood]}</span>
                      )}
                      <span className="text-sm text-gray-400">
                        {new Date(entry.created_at).toLocaleString('nl-NL', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">{entry.word_count} woorden</span>
                      <button
                        onClick={() => startEdit(entry)}
                        className="text-blue-400 hover:text-blue-300 transition-colors"
                        title="Bewerken"
                        data-testid={`dagboek-edit-btn-${entry.id}`}
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => deleteEntry(entry.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                        style={{ 
                          pointerEvents: 'auto',
                          zIndex: 9999,
                          cursor: 'pointer'
                        }}
                        type="button"
                        title="Verwijderen"
                        data-testid={`dagboek-delete-btn-${entry.id}`}
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                  <p className="text-gray-200 whitespace-pre-wrap">{entry.content}</p>
                  {entry.tags && entry.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {entry.tags.map((tag, idx) => (
                        <span key={idx} className="text-xs px-2 py-1 bg-purple-500/20 text-purple-300 rounded">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                  {entry.updated_at && (
                    <div className="text-xs text-gray-500 mt-2">
                      Laatst bewerkt: {new Date(entry.updated_at).toLocaleString('nl-NL')}
                    </div>
                  )}
                </>
              )}
            </div>
          ))
        ) : (
          <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-8 rounded-lg text-center">
            <p className="text-gray-400">
              {(startDate || endDate) ? 'Geen entries gevonden in deze periode' : 'Nog geen entries. Schrijf je eerste gedachte! ✍️'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default DagboekTab;
