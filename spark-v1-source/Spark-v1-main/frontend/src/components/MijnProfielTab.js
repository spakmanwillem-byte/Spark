import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MijnProfielTab = ({ userData, setUserData }) => {
  const [activeSection, setActiveSection] = useState('gegevens');
  const [isEditing, setIsEditing] = useState(false);
  const [editedData, setEditedData] = useState({});
  const [achievements, setAchievements] = useState([]);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [deleteConfirm, setDeleteConfirm] = useState('');

  useEffect(() => {
    if (userData) {
      setEditedData({
        naam: userData.naam || '',
        volledige_naam: userData.volledige_naam || '',
        email: userData.persoonlijke_info?.email || '',
        telefoon: userData.persoonlijke_info?.telefoon || '',
        geboortedatum: userData.persoonlijke_info?.geboortedatum || '',
        adres: userData.persoonlijke_info?.adres || '',
        postcode: userData.persoonlijke_info?.postcode || '',
        plaats: userData.persoonlijke_info?.plaats || '',
        // Nieuwe velden
        beroep: userData.persoonlijke_info?.beroep || '',
        opleiding: userData.persoonlijke_info?.opleiding || '',
        hobbies: userData.persoonlijke_info?.hobbies || '',
        muziek_voorkeur: userData.persoonlijke_info?.muziek_voorkeur || '',
        film_voorkeur: userData.persoonlijke_info?.film_voorkeur || '',
        game_voorkeur: userData.persoonlijke_info?.game_voorkeur || '',
        over_mij: userData.persoonlijke_info?.over_mij || '',
      });
      fetchAchievements();
    }
  }, [userData]);

  const fetchAchievements = async () => {
    try {
      const response = await axios.get(`${API}/admin/achievements`);
      setAchievements(response.data.achievements || []);
    } catch (error) {
      console.error('Error fetching achievements:', error);
    }
  };

  const getRank = (xp) => {
    if (xp >= 50000) return { name: 'Master', icon: '👑', color: '#FFD700', level: 7 };
    if (xp >= 20000) return { name: 'Expert', icon: '🎓', color: '#9C27B0', level: 6 };
    if (xp >= 10000) return { name: 'Scholar', icon: '📚', color: '#2196F3', level: 5 };
    if (xp >= 5000) return { name: 'Explorer', icon: '🗺️', color: '#4CAF50', level: 4 };
    if (xp >= 2000) return { name: 'Learner', icon: '🌱', color: '#8BC34A', level: 3 };
    if (xp >= 500) return { name: 'Beginner', icon: '✨', color: '#FFC107', level: 2 };
    return { name: 'Novice', icon: '🔰', color: '#9E9E9E', level: 1 };
  };

  const getNextRankXP = (xp) => {
    if (xp < 500) return 500;
    if (xp < 2000) return 2000;
    if (xp < 5000) return 5000;
    if (xp < 10000) return 10000;
    if (xp < 20000) return 20000;
    if (xp < 50000) return 50000;
    return 100000;
  };

  const handleSaveProfile = async () => {
    try {
      // Use correct endpoint with user_id in URL
      await axios.put(`${API}/profile/extended/${userData.id}`, editedData);
      
      // Update local userData
      setUserData({
        ...userData,
        naam: editedData.naam,
        volledige_naam: editedData.volledige_naam,
        persoonlijke_info: {
          ...userData.persoonlijke_info,
          email: editedData.email,
          telefoon: editedData.telefoon,
          geboortedatum: editedData.geboortedatum,
          adres: editedData.adres,
          postcode: editedData.postcode,
          plaats: editedData.plaats,
          beroep: editedData.beroep,
          opleiding: editedData.opleiding,
          hobbies: editedData.hobbies,
          muziek_voorkeur: editedData.muziek_voorkeur,
          film_voorkeur: editedData.film_voorkeur,
          game_voorkeur: editedData.game_voorkeur,
          over_mij: editedData.over_mij,
        }
      });
      
      setIsEditing(false);
      alert('✅ Profiel opgeslagen!');
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('❌ Fout bij opslaan. Probeer opnieuw.');
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      alert('❌ Sleutelwoorden komen niet overeen!');
      return;
    }
    
    if (newPassword.length < 3) {
      alert('❌ Sleutelwoord moet minimaal 3 tekens zijn!');
      return;
    }

    try {
      await axios.put(`${API}/profile/change-password`, {
        user_id: userData.id,
        new_password: newPassword
      });
      
      setNewPassword('');
      setConfirmPassword('');
      alert('✅ Sleutelwoord gewijzigd! Gebruik dit bij je volgende login.');
    } catch (error) {
      console.error('Error changing password:', error);
      alert('❌ Fout bij wijzigen sleutelwoord.');
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirm !== userData.sleutelwoord) {
      alert('❌ Sleutelwoord incorrect!');
      return;
    }

    if (!window.confirm('⚠️ Weet je zeker dat je je account wilt verwijderen? Je kan niet meer inloggen, maar je bijdragen blijven bewaard voor Spark.')) {
      return;
    }

    try {
      await axios.delete(`${API}/profile/delete-account`, {
        params: {
          user_id: userData.id,
          sleutelwoord: deleteConfirm
        }
      });
      
      alert('✅ Account verwijderd. Je bijdragen blijven bewaard voor Spark.');
      // Logout
      setUserData(null);
      window.location.reload();
    } catch (error) {
      console.error('Error deleting account:', error);
      alert('❌ Fout bij verwijderen account.');
    }
  };

  if (!userData) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <h2>Log in om je profiel te zien</h2>
        <p>Stel jezelf voor aan Spark in de chat.</p>
      </div>
    );
  }

  const rank = getRank(userData.xp || 0);
  const nextRankXP = getNextRankXP(userData.xp || 0);
  const progress = ((userData.xp || 0) / nextRankXP) * 100;
  const unlocked = userData.achievements?.unlocked || [];

  return (
    <div className="mijn-profiel-container">
      {/* Section Navigation */}
      <div className="profiel-nav">
        <button
          className={`profiel-nav-btn ${activeSection === 'gegevens' ? 'active' : ''}`}
          onClick={() => setActiveSection('gegevens')}
        >
          📝 Persoonlijke Gegevens
        </button>
        <button
          className={`profiel-nav-btn ${activeSection === 'voortgang' ? 'active' : ''}`}
          onClick={() => setActiveSection('voortgang')}
        >
          🏆 Mijn Voortgang
        </button>
        <button
          className={`profiel-nav-btn ${activeSection === 'wallet' ? 'active' : ''}`}
          onClick={() => setActiveSection('wallet')}
        >
          💰 Wallet & Credits
        </button>
        <button
          className={`profiel-nav-btn ${activeSection === 'instellingen' ? 'active' : ''}`}
          onClick={() => setActiveSection('instellingen')}
        >
          ⚙️ Account Instellingen
        </button>
      </div>

      {/* Section Content */}
      <div className="profiel-content">
        
        {/* PERSOONLIJKE GEGEVENS */}
        {activeSection === 'gegevens' && (
          <div className="profiel-section">
            <div className="section-header">
              <h2>📝 Persoonlijke Gegevens</h2>
              {!isEditing && (
                <button className="edit-btn" onClick={() => setIsEditing(true)}>
                  ✏️ Bewerken
                </button>
              )}
            </div>

            <div className="form-grid">
              <div className="form-group">
                <label>Voornaam</label>
                <input
                  type="text"
                  value={editedData.naam}
                  onChange={(e) => setEditedData({...editedData, naam: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Volledige Naam</label>
                <input
                  type="text"
                  value={editedData.volledige_naam}
                  onChange={(e) => setEditedData({...editedData, volledige_naam: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={editedData.email}
                  onChange={(e) => setEditedData({...editedData, email: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="naam@voorbeeld.nl"
                />
              </div>

              <div className="form-group">
                <label>Telefoon</label>
                <input
                  type="tel"
                  value={editedData.telefoon}
                  onChange={(e) => setEditedData({...editedData, telefoon: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="06-12345678"
                />
              </div>

              <div className="form-group">
                <label>Geboortedatum</label>
                <input
                  type="date"
                  value={editedData.geboortedatum}
                  onChange={(e) => setEditedData({...editedData, geboortedatum: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                />
              </div>

              <div className="form-group">
                <label>Gradatie</label>
                <input
                  type="text"
                  value={`Gradatie ${userData.gradatie}`}
                  disabled
                  className="form-input"
                  style={{ background: 'rgba(76, 175, 80, 0.1)', color: '#4CAF50' }}
                />
              </div>

              <div className="form-group full-width">
                <label>Adres</label>
                <input
                  type="text"
                  value={editedData.adres}
                  onChange={(e) => setEditedData({...editedData, adres: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Straatnaam 123"
                />
              </div>

              <div className="form-group">
                <label>Postcode</label>
                <input
                  type="text"
                  value={editedData.postcode}
                  onChange={(e) => setEditedData({...editedData, postcode: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="1234 AB"
                />
              </div>

              <div className="form-group">
                <label>Plaats</label>
                <input
                  type="text"
                  value={editedData.plaats}
                  onChange={(e) => setEditedData({...editedData, plaats: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Amsterdam"
                />
              </div>

              {/* NIEUWE VELDEN - Werk & Opleiding */}
              <div className="form-group full-width" style={{ marginTop: '30px', paddingTop: '30px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <h4 style={{ marginBottom: '20px', fontSize: '16px', color: 'rgba(255,255,255,0.9)' }}>💼 Werk & Opleiding</h4>
              </div>

              <div className="form-group">
                <label>Beroep</label>
                <input
                  type="text"
                  value={editedData.beroep}
                  onChange={(e) => setEditedData({...editedData, beroep: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. Software Developer"
                />
              </div>

              <div className="form-group">
                <label>Opleiding</label>
                <input
                  type="text"
                  value={editedData.opleiding}
                  onChange={(e) => setEditedData({...editedData, opleiding: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. HBO Informatica"
                />
              </div>

              {/* Interesses & Voorkeuren */}
              <div className="form-group full-width" style={{ marginTop: '30px', paddingTop: '30px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <h4 style={{ marginBottom: '20px', fontSize: '16px', color: 'rgba(255,255,255,0.9)' }}>🎨 Interesses & Voorkeuren</h4>
              </div>

              <div className="form-group full-width">
                <label>Hobby's</label>
                <textarea
                  value={editedData.hobbies}
                  onChange={(e) => setEditedData({...editedData, hobbies: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. Gaming, Lezen, Fotografie..."
                  rows={2}
                  style={{ resize: 'vertical' }}
                />
              </div>

              <div className="form-group">
                <label>🎵 Muziek Voorkeur</label>
                <input
                  type="text"
                  value={editedData.muziek_voorkeur}
                  onChange={(e) => setEditedData({...editedData, muziek_voorkeur: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. Rock, Pop, Jazz..."
                />
              </div>

              <div className="form-group">
                <label>🎬 Film Voorkeur</label>
                <input
                  type="text"
                  value={editedData.film_voorkeur}
                  onChange={(e) => setEditedData({...editedData, film_voorkeur: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. Sci-Fi, Action, Drama..."
                />
              </div>

              <div className="form-group full-width">
                <label>🎮 Game Voorkeur</label>
                <input
                  type="text"
                  value={editedData.game_voorkeur}
                  onChange={(e) => setEditedData({...editedData, game_voorkeur: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Bijv. FPS, RPG, Strategy..."
                />
              </div>

              {/* Over Mij */}
              <div className="form-group full-width" style={{ marginTop: '30px', paddingTop: '30px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <h4 style={{ marginBottom: '20px', fontSize: '16px', color: 'rgba(255,255,255,0.9)' }}>📝 Over Mij</h4>
              </div>

              <div className="form-group full-width">
                <label>Korte Bio</label>
                <textarea
                  value={editedData.over_mij}
                  onChange={(e) => setEditedData({...editedData, over_mij: e.target.value})}
                  disabled={!isEditing}
                  className="form-input"
                  placeholder="Vertel iets over jezelf..."
                  rows={4}
                  style={{ resize: 'vertical' }}
                />
              </div>
            </div>

            {isEditing && (
              <div className="form-actions">
                <button className="btn-save" onClick={handleSaveProfile}>
                  ✅ Opslaan
                </button>
                <button className="btn-cancel" onClick={() => setIsEditing(false)}>
                  ❌ Annuleren
                </button>
              </div>
            )}
          </div>
        )}

        {/* MIJN VOORTGANG */}
        {activeSection === 'voortgang' && (
          <div className="profiel-section">
            <h2>🏆 Mijn Voortgang</h2>

            {/* Rank Display */}
            <div className="rank-card">
              <div className="rank-icon" style={{ fontSize: '64px' }}>{rank.icon}</div>
              <div className="rank-info">
                <h3 style={{ color: rank.color }}>Rank: {rank.name}</h3>
                <p>Level {rank.level} / 7</p>
                <div className="xp-display">
                  <span className="xp-current">{userData.xp || 0} XP</span>
                  <span className="xp-next">→ {nextRankXP} XP voor volgende rank</span>
                </div>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${progress}%`, background: rank.color }}></div>
                </div>
              </div>
            </div>

            {/* Achievements */}
            <div className="achievements-grid">
              <h3>🎯 Achievements ({unlocked.length} unlocked)</h3>
              {achievements.length > 0 ? (
                achievements.map(ach => {
                  // Support both old format (array of IDs) and new format (array of objects)
                  const isUnlocked = Array.isArray(unlocked) && 
                    (unlocked.some(u => typeof u === 'object' ? u.id === ach.id : u === ach.id));
                  return (
                    <div
                      key={ach.id}
                      className={`achievement-card ${isUnlocked ? 'unlocked' : 'locked'}`}
                    >
                      <div className="achievement-icon">{ach.icon}</div>
                      <div className="achievement-info">
                        <h4>{ach.name}</h4>
                        <p>{ach.description}</p>
                        {isUnlocked ? (
                          <span className="achievement-badge">✅ Unlocked</span>
                        ) : (
                          <span className="achievement-progress">
                            {userData.achievements?.progress?.word_count || 0} / {ach.requirement} woorden
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <p>Geen achievements beschikbaar</p>
              )}
            </div>
          </div>
        )}

        {/* WALLET & CREDITS */}
        {activeSection === 'wallet' && (
          <div className="profiel-section">
            <h2>💰 Wallet & Credits</h2>
            
            <div className="wallet-card">
              <div className="wallet-icon">💳</div>
              <div className="wallet-info">
                <h3>Credits Balance</h3>
                <p className="credits-amount">{userData.credits || 0} Credits</p>
              </div>
            </div>

            <div className="info-box">
              <h3>🎮 Verdien Credits</h3>
              <ul>
                <li>Speel games (binnenkort beschikbaar)</li>
                <li>Voltooi daily challenges</li>
                <li>Maak knowledge cards</li>
                <li>Dagelijkse login bonus</li>
              </ul>
            </div>

            <div className="info-box">
              <h3>🛒 Besteed Credits</h3>
              <ul>
                <li>Koop items in de Winkel</li>
                <li>Unlock premium features</li>
                <li>Customize je profiel</li>
              </ul>
            </div>

            <p style={{ textAlign: 'center', opacity: 0.7, marginTop: '30px' }}>
              ⚡ Credits systeem in ontwikkeling - binnenkort beschikbaar!
            </p>
          </div>
        )}

        {/* ACCOUNT INSTELLINGEN */}
        {activeSection === 'instellingen' && (
          <div className="profiel-section">
            <h2>⚙️ Account Instellingen</h2>

            {/* Change Password */}
            <div className="settings-card">
              <h3>🔑 Sleutelwoord Wijzigen</h3>
              <div className="form-group">
                <label>Nieuw Sleutelwoord</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="form-input"
                  placeholder="Minimaal 3 tekens"
                />
              </div>
              <div className="form-group">
                <label>Bevestig Sleutelwoord</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="form-input"
                  placeholder="Herhaal sleutelwoord"
                />
              </div>
              <button className="btn-primary" onClick={handleChangePassword}>
                ✅ Sleutelwoord Wijzigen
              </button>
            </div>

            {/* Delete Account */}
            <div className="settings-card danger-zone">
              <h3>🗑️ Vergeet Mij</h3>
              <p>⚠️ Deze actie verwijdert je account en login toegang.</p>
              <p style={{ marginTop: '10px' }}>
                <strong>Wat wordt verwijderd:</strong><br/>
                ✓ Jouw profiel en login<br/>
                ✓ Persoonlijke gegevens
              </p>
              <p style={{ marginTop: '10px' }}>
                <strong>Wat blijft bewaard:</strong><br/>
                ✓ Jouw knowledge cards (anoniem)<br/>
                ✓ Bijdragen aan Spark's kennis
              </p>
              
              <div className="form-group" style={{ marginTop: '20px' }}>
                <label>Bevestig met je sleutelwoord:</label>
                <input
                  type="password"
                  value={deleteConfirm}
                  onChange={(e) => setDeleteConfirm(e.target.value)}
                  className="form-input"
                  placeholder="Typ je huidige sleutelwoord"
                />
              </div>
              
              <button className="btn-danger" onClick={handleDeleteAccount}>
                🗑️ Vergeet Mij
              </button>
            </div>
          </div>
        )}

      </div>

      <style jsx>{`
        .mijn-profiel-container {
          padding: 0;
        }

        .profiel-nav {
          display: flex;
          gap: 10px;
          padding: 20px;
          background: rgba(20, 20, 20, 0.5);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          overflow-x: auto;
        }

        .profiel-nav-btn {
          padding: 12px 20px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: transparent;
          color: rgb(200, 200, 200);
          cursor: pointer;
          transition: all 0.2s ease;
          white-space: nowrap;
          font-size: 14px;
        }

        .profiel-nav-btn:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .profiel-nav-btn.active {
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.3) 0%, rgba(76, 175, 80, 0.2) 100%);
          border-color: rgba(76, 175, 80, 0.4);
          color: #4CAF50;
          font-weight: 600;
        }

        .profiel-content {
          padding: 30px;
        }

        .profiel-section {
          max-width: 900px;
          margin: 0 auto;
        }

        .section-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 30px;
        }

        .section-header h2 {
          margin: 0;
        }

        .edit-btn {
          padding: 10px 20px;
          border-radius: 8px;
          border: 1px solid rgba(76, 175, 80, 0.4);
          background: rgba(76, 175, 80, 0.1);
          color: #4CAF50;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .edit-btn:hover {
          background: rgba(76, 175, 80, 0.2);
        }

        .form-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }

        .form-group.full-width {
          grid-column: 1 / -1;
        }

        .form-group label {
          display: block;
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 8px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .form-input {
          width: 100%;
          padding: 12px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(40, 40, 40, 0.8);
          color: rgb(255, 255, 255);
          font-size: 14px;
          font-family: inherit;
          transition: all 0.2s ease;
        }

        .form-input:focus {
          border-color: rgba(76, 175, 80, 0.4);
          background: rgba(40, 40, 40, 1);
          outline: none;
          box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
        }

        .form-input:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .form-input::placeholder {
          color: rgba(255, 255, 255, 0.3);
        }

        textarea.form-input {
          min-height: 80px;
          resize: vertical;
        }

        .form-actions {
          display: flex;
          gap: 15px;
          margin-top: 30px;
        }

        .btn-save, .btn-primary {
          padding: 12px 30px;
          border-radius: 8px;
          border: none;
          background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-save:hover, .btn-primary:hover {
          background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%);
          transform: translateY(-1px);
        }

        .btn-cancel {
          padding: 12px 30px;
          border-radius: 8px;
          border: 1px solid rgba(255, 255, 255, 0.2);
          background: transparent;
          color: rgb(200, 200, 200);
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-cancel:hover {
          background: rgba(255, 255, 255, 0.05);
        }

        .rank-card {
          display: flex;
          align-items: center;
          gap: 30px;
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 30px;
          margin-bottom: 30px;
        }

        .rank-info {
          flex: 1;
        }

        .rank-info h3 {
          margin: 0 0 5px 0;
          font-size: 24px;
        }

        .rank-info p {
          margin: 0;
          color: rgba(255, 255, 255, 0.6);
          font-size: 14px;
        }

        .xp-display {
          display: flex;
          gap: 15px;
          margin: 15px 0;
          font-size: 14px;
        }

        .xp-current {
          color: #4CAF50;
          font-weight: 600;
          font-size: 18px;
        }

        .xp-next {
          color: rgba(255, 255, 255, 0.5);
        }

        .progress-bar {
          height: 12px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 6px;
          overflow: hidden;
          margin-top: 10px;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.5s ease;
        }

        .achievements-grid {
          margin-top: 30px;
        }

        .achievements-grid h3 {
          margin-bottom: 20px;
        }

        .achievement-card {
          display: flex;
          gap: 15px;
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 15px;
          transition: all 0.2s ease;
        }

        .achievement-card.locked {
          opacity: 0.4;
          filter: grayscale(70%);
        }

        .achievement-card.unlocked {
          border-color: rgba(76, 175, 80, 0.5);
          background: linear-gradient(135deg, rgba(76, 175, 80, 0.15) 0%, rgba(76, 175, 80, 0.05) 100%);
          box-shadow: 0 0 20px rgba(76, 175, 80, 0.3);
          animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
          from {
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.2);
          }
          to {
            box-shadow: 0 0 25px rgba(76, 175, 80, 0.4);
          }
        }

        .achievement-icon {
          font-size: 32px;
          min-width: 40px;
          text-align: center;
        }

        .achievement-info h4 {
          margin: 0 0 5px 0;
          font-size: 16px;
        }

        .achievement-info p {
          margin: 0 0 10px 0;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
        }

        .achievement-badge {
          display: inline-block;
          padding: 4px 10px;
          background: rgba(76, 175, 80, 0.2);
          color: #4CAF50;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 600;
        }

        .achievement-progress {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.5);
        }

        .wallet-card {
          display: flex;
          align-items: center;
          gap: 30px;
          background: linear-gradient(135deg, rgba(255, 193, 7, 0.2) 0%, rgba(255, 152, 0, 0.1) 100%);
          border: 1px solid rgba(255, 193, 7, 0.3);
          border-radius: 12px;
          padding: 30px;
          margin-bottom: 30px;
        }

        .wallet-icon {
          font-size: 64px;
        }

        .wallet-info h3 {
          margin: 0 0 10px 0;
          color: rgba(255, 255, 255, 0.8);
        }

        .credits-amount {
          font-size: 32px;
          font-weight: 700;
          color: #FFC107;
          margin: 0;
        }

        .info-box {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          margin-bottom: 20px;
        }

        .info-box h3 {
          margin: 0 0 15px 0;
          font-size: 16px;
        }

        .info-box ul {
          margin: 0;
          padding-left: 20px;
          color: rgba(255, 255, 255, 0.7);
        }

        .info-box li {
          margin-bottom: 8px;
        }

        .settings-card {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 25px;
          margin-bottom: 25px;
        }

        .settings-card h3 {
          margin: 0 0 20px 0;
        }

        .settings-card.danger-zone {
          border-color: rgba(244, 67, 54, 0.3);
          background: rgba(244, 67, 54, 0.05);
        }

        .btn-danger {
          padding: 12px 30px;
          border-radius: 8px;
          border: none;
          background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          margin-top: 15px;
        }

        .btn-danger:hover {
          background: linear-gradient(135deg, #d32f2f 0%, #c62828 100%);
          transform: translateY(-1px);
        }
      `}</style>
    </div>
  );
};

export default MijnProfielTab;
