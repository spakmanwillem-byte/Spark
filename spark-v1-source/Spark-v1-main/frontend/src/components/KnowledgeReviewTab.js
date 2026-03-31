import React, { useState, useEffect } from 'react';

const KnowledgeReviewTab = () => {
  const [guestContributions, setGuestContributions] = useState([]);
  const [pendingConfirmation, setPendingConfirmation] = useState([]);
  const [loading, setLoading] = useState(true);
  const [counts, setCounts] = useState({ guest: 0, pending: 0, total: 0 });

  const API = process.env.REACT_APP_BACKEND_URL;

  // Load pending knowledge
  const loadPendingKnowledge = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API}/api/admin/knowledge/review/pending`);
      const data = await response.json();
      
      setGuestContributions(data.guest_contributions || []);
      setPendingConfirmation(data.pending_confirmation || []);
      setCounts(data.counts || { guest: 0, pending: 0, total: 0 });
    } catch (error) {
      console.error('Failed to load pending knowledge:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPendingKnowledge();
  }, []);

  // Approve entry
  const handleApprove = async (id, begrip) => {
    try {
      const response = await fetch(`${API}/api/admin/knowledge/${id}/approve`, {
        method: 'PUT'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`✅ "${begrip}" goedgekeurd!`);
        loadPendingKnowledge(); // Reload
      }
    } catch (error) {
      console.error('Failed to approve:', error);
      alert('❌ Fout bij goedkeuren');
    }
  };

  // Reject entry
  const handleReject = async (id, begrip) => {
    if (!window.confirm(`Weet je zeker dat je "${begrip}" wilt verwijderen?`)) {
      return;
    }
    
    try {
      const response = await fetch(`${API}/api/admin/knowledge/${id}/reject`, {
        method: 'PUT'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`🗑️ "${begrip}" verwijderd`);
        loadPendingKnowledge(); // Reload
      }
    } catch (error) {
      console.error('Failed to reject:', error);
      alert('❌ Fout bij verwijderen');
    }
  };

  // Confirm different (for pending confirmation)
  const handleConfirmDifferent = async (id, begrip) => {
    try {
      const response = await fetch(`${API}/api/admin/knowledge/${id}/confirm-different`, {
        method: 'PUT'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`✅ "${begrip}" is anders - goedgekeurd!`);
        loadPendingKnowledge(); // Reload
      }
    } catch (error) {
      console.error('Failed to confirm different:', error);
      alert('❌ Fout');
    }
  };

  // Confirm same (for pending confirmation)
  const handleConfirmSame = async (id, begrip) => {
    try {
      const response = await fetch(`${API}/api/admin/knowledge/${id}/confirm-same`, {
        method: 'PUT'
      });
      const result = await response.json();
      
      if (result.success) {
        alert(`🗑️ "${begrip}" is hetzelfde - verwijderd`);
        loadPendingKnowledge(); // Reload
      }
    } catch (error) {
      console.error('Failed to confirm same:', error);
      alert('❌ Fout');
    }
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-400">Laden...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">📝 Review Nieuwe Input</h2>
          <p className="text-gray-400 text-sm mt-1">
            {counts.total} {counts.total === 1 ? 'item' : 'items'} wacht op review
          </p>
        </div>
        <button
          onClick={loadPendingKnowledge}
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg text-sm"
        >
          🔄 Ververs
        </button>
      </div>

      {/* Guest Contributions */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-semibold text-white">
            👤 Guest Contributions
          </h3>
          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-sm">
            {counts.guest}
          </span>
        </div>

        {guestContributions.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
            Geen guest contributions
          </div>
        ) : (
          <div className="space-y-3">
            {guestContributions.map((entry) => (
              <div
                key={entry.id}
                className="bg-gray-800 rounded-lg p-4 border border-gray-700"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-lg font-medium text-white">
                        {entry.begrip}
                      </span>
                      {entry.metadata?.is_sentence && (
                        <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">
                          ZIN
                        </span>
                      )}
                    </div>
                    
                    {entry.snap_context && (
                      <p className="text-sm text-gray-400 mb-2">
                        Context: "{entry.snap_context}"
                      </p>
                    )}
                    
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>👤 {entry.detected_by}</span>
                      <span>
                        📅 {new Date(entry.metadata?.created_at).toLocaleDateString('nl-NL')}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleApprove(entry.id, entry.begrip)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium"
                    >
                      ✓ Approve
                    </button>
                    <button
                      onClick={() => handleReject(entry.id, entry.begrip)}
                      className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium"
                    >
                      ✕ Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pending Confirmation */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <h3 className="text-xl font-semibold text-white">
            ⚠️ Mogelijk Duplicaten
          </h3>
          <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-sm">
            {counts.pending}
          </span>
        </div>

        {pendingConfirmation.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-6 text-center text-gray-400">
            Geen duplicaten om te checken
          </div>
        ) : (
          <div className="space-y-3">
            {pendingConfirmation.map((entry) => {
              const confirmation = entry.confirmation_needed || {};
              const similarTo = confirmation.similar_to || 'onbekend';
              const similarDesc = confirmation.similar_description || '';

              return (
                <div
                  key={entry.id}
                  className="bg-gray-800 rounded-lg p-4 border border-yellow-500/30"
                >
                  <div className="space-y-4">
                    {/* New Entry */}
                    <div>
                      <div className="text-xs text-gray-500 mb-1">NIEUW:</div>
                      <div className="text-lg font-medium text-white">
                        {entry.begrip}
                      </div>
                      {entry.snap_context && (
                        <p className="text-sm text-gray-400 mt-1">
                          "{entry.snap_context}"
                        </p>
                      )}
                      <div className="flex items-center gap-4 text-xs text-gray-500 mt-2">
                        <span>👤 {entry.detected_by}</span>
                        <span>
                          📅 {new Date(entry.metadata?.created_at).toLocaleDateString('nl-NL')}
                        </span>
                      </div>
                    </div>

                    {/* Similar Entry */}
                    <div className="border-t border-gray-700 pt-3">
                      <div className="text-xs text-gray-500 mb-1">LIJKT OP:</div>
                      <div className="text-white font-medium">{similarTo}</div>
                      {similarDesc && (
                        <p className="text-sm text-gray-400 mt-1">
                          {similarDesc}
                        </p>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 pt-2">
                      <button
                        onClick={() => handleConfirmDifferent(entry.id, entry.begrip)}
                        className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-sm font-medium"
                      >
                        Dit is ANDERS
                      </button>
                      <button
                        onClick={() => handleConfirmSame(entry.id, entry.begrip)}
                        className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded-lg text-sm font-medium"
                      >
                        Dit is HETZELFDE
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeReviewTab;
