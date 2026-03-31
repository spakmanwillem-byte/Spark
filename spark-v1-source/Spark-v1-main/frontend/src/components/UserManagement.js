import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './UserManagement.css';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

function UserManagement({ adminUserId }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [deleteInput, setDeleteInput] = useState('');
  
  // Warn modal
  const [warnUser, setWarnUser] = useState(null);
  const [warnText, setWarnText] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/users/list`, {
        params: { admin_user_id: adminUserId }
      });
      
      if (res.data.success) {
        setUsers(res.data.users);
      }
    } catch (error) {
      console.error('Error loading users:', error);
      alert('Failed to load users');
    }
    setLoading(false);
  };

  const handleBlock = async (userId, naam, reason) => {
    if (!reason) {
      reason = prompt(`Reden voor blokkeren van ${naam}:`);
      if (!reason) return;
    }

    setActionLoading(true);
    try {
      const res = await axios.post(`${API}/admin/users/block`, {}, {
        params: {
          admin_user_id: adminUserId,
          target_user_id: userId,
          reason: reason
        }
      });

      if (res.data.success) {
        alert(`✅ ${naam} is geblokkeerd`);
        loadUsers();
      }
    } catch (error) {
      alert('❌ Fout bij blokkeren');
    }
    setActionLoading(false);
  };

  const handleUnblock = async (userId, naam) => {
    if (!window.confirm(`${naam} deblokkeren?`)) return;

    setActionLoading(true);
    try {
      const res = await axios.post(`${API}/admin/users/unblock`, {}, {
        params: {
          admin_user_id: adminUserId,
          target_user_id: userId
        }
      });

      if (res.data.success) {
        alert(`✅ ${naam} is gedeblokkeerd`);
        loadUsers();
      }
    } catch (error) {
      alert('❌ Fout bij deblokkeren');
    }
    setActionLoading(false);
  };

  const handleWarn = async () => {
    if (!warnText.trim()) return;

    setActionLoading(true);
    try {
      const res = await axios.post(`${API}/admin/users/warn`, {}, {
        params: {
          admin_user_id: adminUserId,
          target_user_id: warnUser.id,
          warning: warnText
        }
      });

      if (res.data.success) {
        alert(`✅ Waarschuwing toegevoegd (${res.data.total_warnings} totaal)`);
        setWarnUser(null);
        setWarnText('');
        loadUsers();
      }
    } catch (error) {
      alert('❌ Fout bij waarschuwing');
    }
    setActionLoading(false);
  };

  const handleDelete = async () => {
    if (deleteInput !== deleteConfirm.naam) {
      alert('❌ Naam komt niet overeen!');
      return;
    }

    setActionLoading(true);
    try {
      const res = await axios.delete(`${API}/admin/users/delete`, {
        params: {
          admin_user_id: adminUserId,
          target_user_id: deleteConfirm.id,
          confirmation: deleteInput
        }
      });

      if (res.data.success) {
        alert(`✅ ${deleteConfirm.naam} permanent verwijderd`);
        setDeleteConfirm(null);
        setDeleteInput('');
        loadUsers();
      }
    } catch (error) {
      alert(error.response?.data?.detail || '❌ Fout bij verwijderen');
    }
    setActionLoading(false);
  };

  if (loading) {
    return <div className="user-mgmt-loading">Laden...</div>;
  }

  return (
    <div className="user-management">
      <div className="user-mgmt-header">
        <h2>👥 Gebruikersbeheer</h2>
        <button onClick={loadUsers} className="btn-refresh">🔄 Ververs</button>
      </div>

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>Naam</th>
              <th>Gradatie</th>
              <th>Gesprekken</th>
              <th>Laatste Actief</th>
              <th>Status</th>
              <th>Acties</th>
            </tr>
          </thead>
          <tbody>
            {users.map(user => (
              <tr key={user.id} className={user.blocked ? 'blocked-user' : ''}>
                <td>
                  <div className="user-name">{user.naam}</div>
                  <div className="user-fullname">{user.volledige_naam}</div>
                </td>
                <td>
                  <span className={`gradatie gradatie-${user.gradatie}`}>
                    {user.gradatie === 1 ? '👑' : ''} Gradatie {user.gradatie}
                  </span>
                </td>
                <td>{user.gesprekken_count}</td>
                <td className="last-active">
                  {user.last_active ? new Date(user.last_active).toLocaleDateString('nl-NL') : '-'}
                </td>
                <td>
                  {user.blocked ? (
                    <span className="status-blocked">🔒 Geblokkeerd</span>
                  ) : (
                    <span className="status-active">✅ Actief</span>
                  )}
                  {user.warnings && user.warnings.length > 0 && (
                    <span className="warnings-badge">⚠️ {user.warnings.length}</span>
                  )}
                </td>
                <td className="actions">
                  {user.gradatie !== 1 && (
                    <>
                      {!user.blocked ? (
                        <button
                          onClick={() => handleBlock(user.id, user.naam)}
                          className="btn-block"
                          disabled={actionLoading}
                        >
                          🔒 Blokkeer
                        </button>
                      ) : (
                        <button
                          onClick={() => handleUnblock(user.id, user.naam)}
                          className="btn-unblock"
                          disabled={actionLoading}
                        >
                          🔓 Deblokkeer
                        </button>
                      )}
                      
                      <button
                        onClick={() => setWarnUser(user)}
                        className="btn-warn"
                        disabled={actionLoading}
                      >
                        ⚠️ Waarschuw
                      </button>
                      
                      <button
                        onClick={() => setDeleteConfirm(user)}
                        className="btn-delete"
                        disabled={actionLoading}
                      >
                        🗑️ Verwijder
                      </button>
                    </>
                  )}
                  {user.gradatie === 1 && (
                    <span className="admin-protected">Admin (beveiligd)</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>⚠️ Gebruiker Permanent Verwijderen</h3>
            <p><strong>{deleteConfirm.naam}</strong> ({deleteConfirm.volledige_naam})</p>
            <p className="warning-text">
              Dit kan NIET ongedaan gemaakt worden!<br />
              Alle data van deze gebruiker wordt verwijderd.
            </p>
            <div className="form-group">
              <label>Typ de naam "{deleteConfirm.naam}" om te bevestigen:</label>
              <input
                type="text"
                value={deleteInput}
                onChange={(e) => setDeleteInput(e.target.value)}
                placeholder={deleteConfirm.naam}
                className="confirm-input"
              />
            </div>
            <div className="modal-actions">
              <button
                onClick={handleDelete}
                disabled={deleteInput !== deleteConfirm.naam || actionLoading}
                className="btn-confirm-delete"
              >
                {actionLoading ? 'Verwijderen...' : '🗑️ Permanent Verwijderen'}
              </button>
              <button
                onClick={() => {
                  setDeleteConfirm(null);
                  setDeleteInput('');
                }}
                className="btn-cancel"
              >
                Annuleren
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Warn Modal */}
      {warnUser && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>⚠️ Waarschuwing Geven</h3>
            <p><strong>{warnUser.naam}</strong></p>
            <div className="form-group">
              <label>Reden:</label>
              <textarea
                value={warnText}
                onChange={(e) => setWarnText(e.target.value)}
                placeholder="Waarom wordt deze user gewaarschuwd?"
                rows={4}
                className="warn-textarea"
              />
            </div>
            <div className="modal-actions">
              <button
                onClick={handleWarn}
                disabled={!warnText.trim() || actionLoading}
                className="btn-confirm-warn"
              >
                {actionLoading ? 'Toevoegen...' : '⚠️ Waarschuwing Toevoegen'}
              </button>
              <button
                onClick={() => {
                  setWarnUser(null);
                  setWarnText('');
                }}
                className="btn-cancel"
              >
                Annuleren
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
