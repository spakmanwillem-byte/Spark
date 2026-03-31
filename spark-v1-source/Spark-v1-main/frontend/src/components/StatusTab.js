import React from "react";

function StatusTab({ systemStatus, userData }) {
  return (
    <div className="space-y-6">
      {/* Placeholder voor toekomstige Status Monitoring */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-8 rounded-lg text-center">
        <div className="text-6xl mb-4">🚧</div>
        <h2 className="text-2xl font-bold text-white mb-2">Status Monitoring - In Ontwikkeling</h2>
        <p className="text-gray-400 mb-4">
          Deze functie is bedoeld voor production deployment met live users.
        </p>
        <div className="bg-slate-700/30 p-4 rounded-lg text-left max-w-2xl mx-auto">
          <p className="text-sm text-gray-300 mb-3">
            <strong>Huidige Fase:</strong> Standalone Development op Odroid
          </p>
          <p className="text-sm text-gray-300 mb-3">
            <strong>Focus Nu:</strong>
          </p>
          <ul className="text-sm text-gray-400 space-y-1 ml-4">
            <li>✅ Chat functionaliteit</li>
            <li>✅ Knowledge Graph</li>
            <li>✅ Voice Interface (TTS/STT)</li>
            <li>✅ Lokaal leren en testen</li>
          </ul>
          <p className="text-sm text-gray-300 mt-3">
            <strong>Later (Deploy Fase):</strong>
          </p>
          <ul className="text-sm text-gray-400 space-y-1 ml-4">
            <li>🔮 Live status monitoring</li>
            <li>🔮 Multi-user management</li>
            <li>🔮 System health checks</li>
            <li>🔮 Performance metrics</li>
          </ul>
        </div>
      </div>

      {/* Basis Info (altijd beschikbaar) */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">📊 Lokale Installatie Info</h3>
        <div className="space-y-2 text-sm">
          <div>
            <span className="text-gray-400">Versie:</span>
            <span className="text-white ml-2">v0.1 (Standalone)</span>
          </div>
          <div>
            <span className="text-gray-400">Platform:</span>
            <span className="text-white ml-2">Odroid Development</span>
          </div>
          <div>
            <span className="text-gray-400">Maker:</span>
            <span className="text-white ml-2">Willem Spakman (Roadkill)</span>
          </div>
          <div>
            <span className="text-gray-400">Je rol:</span>
            <span className="text-white ml-2">{userData?.rol || 'User'}</span>
          </div>
          <div>
            <span className="text-gray-400">Je gradatie:</span>
            <span className="text-purple-300 ml-2">Gradatie {userData?.gradatie || '?'}</span>
          </div>
        </div>
        {userData?.gradatie === 1 && (
          <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/30 rounded">
            <p className="text-purple-300 text-sm">
              👑 <strong>Admin (Gradatie 1):</strong> Status monitoring wordt actief bij production deployment.
            </p>
          </div>
        )}
      </div>

      {/* Snelle Links naar Belangrijke Tabs */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">🚀 Belangrijke Functies</h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-700/30 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">💬</div>
            <div className="text-sm text-white">Chat met Spark</div>
            <div className="text-xs text-gray-400 mt-1">Test conversaties</div>
          </div>
          <div className="bg-slate-700/30 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">🎤</div>
            <div className="text-sm text-white">Voice Interface</div>
            <div className="text-xs text-gray-400 mt-1">TTS/STT testen</div>
          </div>
          <div className="bg-slate-700/30 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">🕸️</div>
            <div className="text-sm text-white">Knowledge Graph</div>
            <div className="text-xs text-gray-400 mt-1">Bekijk verbindingen</div>
          </div>
          <div className="bg-slate-700/30 p-4 rounded-lg text-center">
            <div className="text-2xl mb-2">⚙️</div>
            <div className="text-sm text-white">Settings</div>
            <div className="text-xs text-gray-400 mt-1">Configureer systeem</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StatusTab;
