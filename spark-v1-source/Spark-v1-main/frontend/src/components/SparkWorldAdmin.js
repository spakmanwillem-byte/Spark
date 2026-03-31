import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SparkWorldAdmin() {
  const [actors, setActors] = useState([]);
  const [factions, setFactions] = useState([]);
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [actorsRes, factionsRes, gameRes] = await Promise.all([
        axios.get(`${API}/actors/list`),
        axios.get(`${API}/factions/list`),
        axios.get(`${API}/game/state`)
      ]);
      
      setActors(actorsRes.data.actors || []);
      setFactions(factionsRes.data.factions || []);
      setGameState(gameRes.data.state || null);
      setLoading(false);
    } catch (err) {
      console.error('Error loading data:', err);
      setLoading(false);
    }
  };

  const updateActorStats = async (actorId, stats) => {
    try {
      await axios.put(`${API}/actors/${actorId}/stats`, stats);
      loadData();
      alert('Actor updated!');
    } catch (err) {
      alert('Error updating actor');
    }
  };

  if (loading) return <div style={{padding: '40px'}}>Loading Spark World...</div>;

  return (
    <div style={{padding: '40px'}}>
      <h2>🎮 Spark World Admin</h2>

      {/* Actors */}
      <div style={{marginBottom: '30px'}}>
        <h3>🤖 Actors ({actors.length})</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px'}}>
          {actors.map(actor => (
            <div key={actor.id} style={{
              background: 'rgba(30, 30, 30, 0.8)',
              padding: '20px',
              borderRadius: '12px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <h4>{actor.icon} {actor.name}</h4>
              <p style={{fontSize: '13px', color: 'rgba(255,255,255,0.7)'}}>{actor.personality}</p>
              
              <div style={{marginTop: '15px'}}>
                <strong>Stats:</strong>
                <div style={{marginTop: '8px', fontSize: '13px'}}>
                  <div>🪵 Hout: {actor.stats.wood}</div>
                  <div>🪨 Steen: {actor.stats.stone}</div>
                  <div>🐟 Vis: {actor.stats.fish}</div>
                </div>
              </div>

              <div style={{marginTop: '15px'}}>
                <span style={{
                  padding: '4px 12px',
                  background: actor.active ? 'rgba(76, 175, 80, 0.2)' : 'rgba(244, 67, 54, 0.2)',
                  borderRadius: '12px',
                  fontSize: '12px'
                }}>
                  {actor.active ? '✅ Actief' : '❌ Inactief'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Monumenten */}
      <div style={{marginBottom: '30px'}}>
        <h3>🏛️ Monumenten ({gameState?.monuments?.length || 0})</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px'}}>
          {gameState?.monuments?.map(monument => (
            <div key={monument.id} style={{
              background: 'rgba(30, 30, 30, 0.8)',
              padding: '15px',
              borderRadius: '8px',
              border: `2px solid ${monument.color}`
            }}>
              <h4>{monument.icon} {monument.name}</h4>
              <div style={{fontSize: '13px', marginTop: '10px'}}>
                <div>Progress: {monument.progress.toFixed(1)}%</div>
                <div>🪵 {monument.wood_contributed} / {monument.wood_needed}</div>
                <div>🪨 {monument.stone_contributed} / {monument.stone_needed}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fracties */}
      <div>
        <h3>⚔️ Fracties ({factions.length})</h3>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px'}}>
          {factions.map(faction => (
            <div key={faction.id} style={{
              background: 'rgba(30, 30, 30, 0.8)',
              padding: '15px',
              borderRadius: '8px',
              border: '1px solid rgba(255, 255, 255, 0.1)'
            }}>
              <h4>{faction.icon} {faction.name}</h4>
              <p style={{fontSize: '12px', color: 'rgba(255,255,255,0.6)'}}>{faction.description}</p>
              <div style={{marginTop: '10px', fontSize: '13px'}}>
                <div>Element: {faction.element}</div>
                <div>Members: {faction.members}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <button 
        onClick={loadData}
        style={{
          marginTop: '30px',
          padding: '12px 30px',
          background: '#4CAF50',
          border: 'none',
          borderRadius: '8px',
          color: 'white',
          fontSize: '16px',
          cursor: 'pointer'
        }}
      >
        🔄 Refresh Data
      </button>
    </div>
  );
}

export default SparkWorldAdmin;
