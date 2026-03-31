import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BestandenTab = ({ userData }) => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userData?.id) {
      loadFiles();
    }
  }, [userData]);

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API}/user/files/list`, {
        params: { 
          user_id: userData?.id,
          requesting_user_id: userData?.id
        }
      });
      setFiles(response.data.files || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading files:', error);
      setLoading(false);
    }
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
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
        <h3 className="text-2xl font-bold text-white mb-2">📁 Mijn Bestanden</h3>
        <p className="text-gray-400 text-sm">
          Persoonlijk archief - Coming Soon
        </p>
      </div>

      {/* Files List */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
        {files.length > 0 ? (
          <div className="space-y-3">
            <h4 className="text-lg font-semibold text-white mb-4">
              📋 Bestanden ({files.length})
            </h4>
            {files.map((file) => (
              <div key={file.id} className="p-4 bg-slate-700/50 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <div className="text-white font-medium">{file.original_name}</div>
                    <div className="text-sm text-gray-400">
                      {(file.size / 1024).toFixed(1)} KB • {new Date(file.uploaded_at).toLocaleDateString('nl-NL')}
                    </div>
                  </div>
                  <button
                    onClick={() => window.open(`${API}/user/files/download/${file.id}?user_id=${userData?.id}`, '_blank')}
                    className="px-4 py-2 bg-blue-500/20 text-blue-300 rounded hover:bg-blue-500/30"
                  >
                    ⬇️ Download
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">📂</div>
            <h4 className="text-xl font-semibold text-white mb-2">Nog geen bestanden</h4>
            <p className="text-gray-400 mb-6">
              Upload functionaliteit komt binnenkort
            </p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-slate-800 border border-slate-700 p-6 rounded-lg">
        <h4 className="text-lg font-semibold text-white mb-3">ℹ️ Binnenkort beschikbaar:</h4>
        <ul className="text-gray-400 space-y-2">
          <li>• 📤 Upload foto's, video's, audio en documenten</li>
          <li>• 📁 Persoonlijke opslag per categorie</li>
          <li>• 🖼️ Profielfoto instellen</li>
          <li>• 🔒 Alles privé en veilig opgeslagen</li>
        </ul>
      </div>
    </div>
  );
};

export default BestandenTab;
