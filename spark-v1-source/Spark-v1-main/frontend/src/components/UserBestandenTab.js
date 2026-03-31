import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const UserBestandenTab = ({ userData }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [viewMode, setViewMode] = useState('uploads'); // 'uploads' or 'datacluster'
  const [uploadForm, setUploadForm] = useState({
    file: null,
    category: 'document',
    visibility: 'private',
    description: ''
  });
  const [isDragging, setIsDragging] = useState(false);
  const [dataCluster, setDataCluster] = useState({
    audio: [],
    conversations: { count: 0, size: 0 },
    personal: []
  });

  const categories = {
    all: { icon: '📁', label: 'Alles', color: 'gray' },
    photo: { icon: '🖼️', label: 'Foto\'s', color: 'purple' },
    video: { icon: '🎥', label: 'Video\'s', color: 'red' },
    audio: { icon: '🎵', label: 'Audio', color: 'blue' },
    document: { icon: '📄', label: 'Documenten', color: 'green' },
    other: { icon: '📦', label: 'Overig', color: 'yellow' }
  };

  useEffect(() => {
    if (userData?.id) {
      loadFiles();
      loadDataCluster();
    }
  }, [userData]);

  const loadFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/user/files/list`, {
        params: { 
          user_id: userData?.id,
          requesting_user_id: userData?.id
        }
      });
      setFiles(response.data.files || []);
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDataCluster = async () => {
    try {
      // Load audio sounds
      const audioRes = await axios.get(`${API}/sounds/mappings`, {
        params: { user_id: userData?.id }
      });
      const userAudio = audioRes.data.mappings.filter(m => 
        m.user_id === userData?.id && m.visibility === 'private'
      );

      // Load conversations
      const convRes = await axios.get(`${API}/conversations/user/${userData?.id}`).catch(() => ({ data: { conversations: [] } }));
      const conversations = convRes.data.conversations || [];
      
      setDataCluster({
        audio: userAudio,
        conversations: {
          count: conversations.length,
          size: JSON.stringify(conversations).length
        },
        personal: [
          { name: 'dagboek.json', icon: '📔', type: 'Dagboek', size: '4.7 KB' },
          { name: 'agenda.json', icon: '📅', type: 'Agenda', size: '753 B' },
          { name: 'relationships.json', icon: '🤝', type: 'Relaties (Spark)', size: '525 B' },
          { name: 'expenses.json', icon: '💰', type: 'Uitgaven', size: '181 B' },
          { name: 'income.json', icon: '💵', type: 'Inkomsten', size: '186 B' },
          { name: 'achievements.json', icon: '🏆', type: 'Achievements', size: '28 B' },
          { name: 'settings.json', icon: '⚙️', type: 'Instellingen', size: '349 B' },
        ]
      });
    } catch (error) {
      console.error('Error loading data cluster:', error);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setUploadForm({ ...uploadForm, file });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      setUploadForm({ ...uploadForm, file });
    }
  };

  const handleUpload = async () => {
    if (!uploadForm.file) {
      alert('⚠️ Selecteer eerst een bestand');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('user_id', userData.id);
      formData.append('category', uploadForm.category);
      formData.append('visibility', uploadForm.visibility);
      if (uploadForm.description) {
        formData.append('description', uploadForm.description);
      }

      await axios.post(`${API}/user/files/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      alert('✅ Bestand geüpload!');
      setUploadForm({ file: null, category: 'document', visibility: 'private', description: '' });
      loadFiles();
    } catch (error) {
      console.error('Upload error:', error);
      alert('❌ Upload mislukt: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId) => {
    if (!window.confirm('Weet je zeker dat je dit bestand wilt verwijderen?')) {
      return;
    }

    try {
      await axios.delete(`${API}/user/files/delete/${fileId}`, {
        params: { user_id: userData.id }
      });
      alert('✅ Bestand verwijderd');
      loadFiles();
    } catch (error) {
      console.error('Delete error:', error);
      alert('❌ Verwijderen mislukt');
    }
  };

  const handleDownload = (file) => {
    window.open(`${API}/user/files/download/${file.id}?user_id=${userData?.id}`, '_blank');
  };

  const handleDownloadPersonalData = (filename) => {
    // Download JSON from backend
    window.open(`${API}/user/data/download/${userData.id}/${filename}`, '_blank');
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getCategoryIcon = (category) => {
    return categories[category]?.icon || '📄';
  };

  const filteredFiles = selectedCategory === 'all' 
    ? files 
    : files.filter(f => f.category === selectedCategory);

  const fileCounts = {
    all: files.length,
    photo: files.filter(f => f.category === 'photo').length,
    video: files.filter(f => f.category === 'video').length,
    audio: files.filter(f => f.category === 'audio').length,
    document: files.filter(f => f.category === 'document').length,
    other: files.filter(f => f.category === 'other').length,
  };

  if (loading) {
    return (
      <div className="bg-slate-800 border border-slate-700 p-12 rounded-lg text-center">
        <div className="text-5xl mb-4">⏳</div>
        <p className="text-gray-400">Bestanden laden...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Mode Toggle */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-2xl font-bold text-white mb-2">📁 Mijn Bestanden</h3>
            <p className="text-gray-400 text-sm">
              Jouw persoonlijke data vault - alles user_id gebonden met metadata
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('uploads')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'uploads'
                  ? 'bg-blue-500 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              📤 Uploads
            </button>
            <button
              onClick={() => setViewMode('datacluster')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                viewMode === 'datacluster'
                  ? 'bg-purple-500 text-white'
                  : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
              }`}
            >
              🗂️ Data Cluster
            </button>
          </div>
        </div>
      </div>

      {/* UPLOADS MODE */}
      {viewMode === 'uploads' && (
        <>
          {/* Upload Section */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">📤 Bestand Uploaden</h4>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Categorie</label>
                  <select
                    value={uploadForm.category}
                    onChange={(e) => setUploadForm({ ...uploadForm, category: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  >
                    <option value="photo">🖼️ Foto</option>
                    <option value="video">🎥 Video</option>
                    <option value="audio">🎵 Audio</option>
                    <option value="document">📄 Document</option>
                    <option value="other">📦 Overig</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Zichtbaarheid</label>
                  <select
                    value={uploadForm.visibility}
                    onChange={(e) => setUploadForm({ ...uploadForm, visibility: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  >
                    <option value="private">🔒 Privé (alleen jij)</option>
                    <option value="shared">👥 Gedeeld</option>
                    <option value="public">🌍 Publiek</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Beschrijving (optioneel)</label>
                <input
                  type="text"
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  placeholder="Bijv: Vakantie foto's 2024"
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                />
              </div>

              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  isDragging ? 'border-blue-500 bg-blue-500/10' : 'border-slate-600'
                }`}
              >
                <input
                  type="file"
                  onChange={handleFileSelect}
                  className="hidden"
                  id="file-upload"
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <div className="text-4xl mb-2">📁</div>
                  <p className="text-gray-300 mb-1">
                    {uploadForm.file ? uploadForm.file.name : 'Sleep een bestand hierheen'}
                  </p>
                  <p className="text-sm text-gray-500">of klik om te selecteren</p>
                </label>
              </div>

              <button
                onClick={handleUpload}
                disabled={uploading || !uploadForm.file}
                className="w-full px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium"
              >
                {uploading ? '⏳ Uploaden...' : '📤 Upload Bestand'}
              </button>
            </div>
          </div>

          {/* Category Filters */}
          <div className="bg-slate-800 border border-slate-700 p-4 rounded-lg">
            <div className="flex flex-wrap gap-2">
              {Object.entries(categories).map(([key, cat]) => (
                <button
                  key={key}
                  onClick={() => setSelectedCategory(key)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedCategory === key
                      ? 'bg-blue-500 text-white'
                      : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }`}
                >
                  {cat.icon} {cat.label} ({fileCounts[key]})
                </button>
              ))}
            </div>
          </div>

          {/* Files List */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">
              {categories[selectedCategory].icon} {categories[selectedCategory].label}
              {selectedCategory !== 'all' && ` (${filteredFiles.length})`}
            </h4>

            {filteredFiles.length > 0 ? (
              <div className="space-y-3">
                {filteredFiles.map((file) => (
                  <div key={file.id} className="p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <div className="text-3xl">{getCategoryIcon(file.category)}</div>
                        <div className="flex-1">
                          <div className="text-white font-medium">{file.original_name}</div>
                          <div className="text-sm text-gray-400">
                            {formatFileSize(file.size)} • {new Date(file.uploaded_at).toLocaleDateString('nl-NL')}
                            {file.description && ` • ${file.description}`}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {file.visibility === 'private' && '🔒 Privé'}
                            {file.visibility === 'shared' && '👥 Gedeeld'}
                            {file.visibility === 'public' && '🌍 Publiek'}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleDownload(file)}
                          className="px-3 py-2 bg-blue-500/20 text-blue-300 rounded hover:bg-blue-500/30 text-sm"
                        >
                          ⬇️ Download
                        </button>
                        <button
                          onClick={() => handleDelete(file.id)}
                          className="px-3 py-2 bg-red-500/20 text-red-300 rounded hover:bg-red-500/30 text-sm"
                        >
                          🗑️
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">{categories[selectedCategory].icon}</div>
                <h4 className="text-xl font-semibold text-white mb-2">Geen bestanden</h4>
                <p className="text-gray-400">
                  Upload je eerste bestand!
                </p>
              </div>
            )}
          </div>
        </>
      )}

      {/* DATA CLUSTER MODE */}
      {viewMode === 'datacluster' && (
        <>
          {/* Audio Bestanden */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">🎵 Audio Bestanden ({dataCluster.audio.length})</h4>
            <p className="text-sm text-gray-400 mb-4">Jouw privé geluiden (ook in Geluiden tab)</p>
            
            {dataCluster.audio.length > 0 ? (
              <div className="space-y-2">
                {dataCluster.audio.map((sound) => (
                  <div key={sound.id} className="p-3 bg-slate-700/50 rounded-lg flex items-center justify-between">
                    <div>
                      <div className="text-white font-medium">{sound.word}</div>
                      <div className="text-sm text-gray-400">{sound.file} • user_id: {sound.user_id}</div>
                    </div>
                    <div className="text-xs text-purple-400 px-2 py-1 bg-purple-500/20 rounded">
                      visibility: {sound.visibility}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">Nog geen audio geüpload</p>
            )}
          </div>

          {/* Conversaties */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">💬 Gespreksgeschiedenis</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 p-4 rounded-lg text-center">
                <div className="text-3xl font-bold text-blue-400">{dataCluster.conversations.count}</div>
                <div className="text-sm text-gray-400">Conversaties</div>
              </div>
              <div className="bg-slate-700/50 p-4 rounded-lg text-center">
                <div className="text-3xl font-bold text-purple-400">
                  {(dataCluster.conversations.size / 1024).toFixed(0)} KB
                </div>
                <div className="text-sm text-gray-400">Totale grootte</div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              📍 Locatie: /data/conversations/user-{userData.id}_conversations.json
            </p>
          </div>

          {/* Persoonlijke Data */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-4">📊 Persoonlijke Data ({dataCluster.personal.length})</h4>
            <p className="text-sm text-gray-400 mb-4">JSON bestanden met metadata - user_id gebonden</p>
            
            <div className="space-y-2">
              {dataCluster.personal.map((item) => (
                <div key={item.name} className="p-3 bg-slate-700/50 rounded-lg flex items-center justify-between hover:bg-slate-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="text-2xl">{item.icon}</div>
                    <div>
                      <div className="text-white font-medium">{item.type}</div>
                      <div className="text-sm text-gray-400">{item.name} • {item.size}</div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadPersonalData(item.name)}
                    className="px-3 py-1 bg-green-500/20 text-green-300 rounded hover:bg-green-500/30 text-sm"
                  >
                    ⬇️ Download JSON
                  </button>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
              <p className="text-sm text-blue-300">
                💡 <strong>Tip:</strong> Al deze data is gekoppeld aan jouw user_id met metadata en footnotes voor Spark's learning systeem
              </p>
            </div>
          </div>

          {/* Storage Info */}
          <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
            <h4 className="text-lg font-semibold text-white mb-3">💾 Data Overzicht</h4>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-slate-700/50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-400">{dataCluster.audio.length}</div>
                <div className="text-sm text-gray-400">Audio</div>
              </div>
              <div className="bg-slate-700/50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-400">{dataCluster.conversations.count}</div>
                <div className="text-sm text-gray-400">Chats</div>
              </div>
              <div className="bg-slate-700/50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-400">{dataCluster.personal.length}</div>
                <div className="text-sm text-gray-400">JSON Files</div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default UserBestandenTab;
