import React, { useState, useEffect } from 'react';
import './BlueprintEditorTab.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Fractie kleuren
const FACTION_COLORS = {
  spark: '#FFD700',
  terra: '#8B4513',
  aqua: '#2196F3',
  ignis: '#F44336',
  ventus: '#9E9E9E'
};

function BlueprintEditorTab() {
  const [activeTab, setActiveTab] = useState('buildings'); // buildings, resources, actions, bots
  const [buildings, setBuildings] = useState([]);
  const [resources, setResources] = useState([]);
  const [actions, setActions] = useState([]);
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'buildings') {
        const res = await fetch(`${API_URL}/api/blueprints/buildings`);
        const data = await res.json();
        setBuildings(data.buildings || []);
      } else if (activeTab === 'resources') {
        const res = await fetch(`${API_URL}/api/blueprints/resources`);
        const data = await res.json();
        setResources(data.resources || []);
      } else if (activeTab === 'actions') {
        const res = await fetch(`${API_URL}/api/blueprints/actions`);
        const data = await res.json();
        setActions(data.actions || []);
      } else if (activeTab === 'bots') {
        const res = await fetch(`${API_URL}/api/blueprints/bots`);
        const data = await res.json();
        setBots(data.bots || []);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
    setLoading(false);
  };

  const handleDelete = async (type, id) => {
    if (!window.confirm('Weet je zeker dat je dit wilt verwijderen?')) return;
    
    try {
      await fetch(`${API_URL}/api/blueprints/${type}/${id}`, {
        method: 'DELETE'
      });
      loadData();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  };

  return (
    <div className="blueprint-editor">
      <div className="blueprint-header">
        <h1>🛠️ Blueprint Editor</h1>
        <p>Maak custom gebouwen, resources en acties</p>
      </div>

      {/* Tab Navigation */}
      <div className="blueprint-tabs">
        <button 
          className={activeTab === 'buildings' ? 'active' : ''}
          onClick={() => setActiveTab('buildings')}
        >
          🏗️ Gebouwen ({buildings.length})
        </button>
        <button 
          className={activeTab === 'resources' ? 'active' : ''}
          onClick={() => setActiveTab('resources')}
        >
          📦 Resources ({resources.length})
        </button>
        <button 
          className={activeTab === 'actions' ? 'active' : ''}
          onClick={() => setActiveTab('actions')}
        >
          ⚡ Acties ({actions.length})
        </button>
        <button 
          className={activeTab === 'bots' ? 'active' : ''}
          onClick={() => setActiveTab('bots')}
        >
          🤖 Bots ({bots.length})
        </button>
      </div>

      {/* Content */}
      <div className="blueprint-content">
        {loading ? (
          <div className="loading">⏳ Laden...</div>
        ) : (
          <>
            {activeTab === 'buildings' && (
              <BuildingsPanel 
                buildings={buildings}
                onEdit={setEditingItem}
                onDelete={(id) => handleDelete('buildings', id)}
                onCreate={() => setShowCreateModal(true)}
              />
            )}
            {activeTab === 'resources' && (
              <ResourcesPanel 
                resources={resources}
                onEdit={setEditingItem}
                onDelete={(id) => handleDelete('resources', id)}
                onCreate={() => setShowCreateModal(true)}
              />
            )}
            {activeTab === 'actions' && (
              <ActionsPanel 
                actions={actions}
                onCreate={() => setShowCreateModal(true)}
              />
            )}
            {activeTab === 'bots' && (
              <BotsPanel 
                bots={bots}
                onEdit={setEditingItem}
                onDelete={(id) => handleDelete('bots', id)}
                onCreate={() => setShowCreateModal(true)}
              />
            )}
          </>
        )}
      </div>

      {/* Create/Edit Modal */}
      {(showCreateModal || editingItem) && (
        <EditorModal
          type={activeTab}
          item={editingItem}
          resources={resources}
          onClose={() => {
            setShowCreateModal(false);
            setEditingItem(null);
          }}
          onSave={() => {
            loadData();
            setShowCreateModal(false);
            setEditingItem(null);
          }}
        />
      )}
    </div>
  );
}

// ============= BUILDINGS PANEL =============
function BuildingsPanel({ buildings, onEdit, onDelete, onCreate }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Gebouwen</h2>
        <button className="btn-primary" onClick={onCreate}>
          ➕ Nieuw Gebouw
        </button>
      </div>

      <div className="cards-grid">
        {buildings.map(building => (
          <div 
            key={building.id} 
            className="building-card"
            style={{ borderColor: FACTION_COLORS[building.faction] }}
          >
            <div className="card-header">
              <span className="card-icon" style={{ 
                border: `3px solid ${FACTION_COLORS[building.faction]}`
              }}>
                {building.icon}
              </span>
              <div>
                <h3>{building.name}</h3>
                <span className="badge" style={{ 
                  background: FACTION_COLORS[building.faction] 
                }}>
                  {building.faction}
                </span>
              </div>
            </div>

            <p className="card-description">{building.description}</p>

            <div className="card-section">
              <strong>💰 Bouw Kosten:</strong>
              <div className="resource-list">
                {Object.entries(building.build_cost || {}).map(([res, amount]) => (
                  <span key={res} className="resource-badge">
                    {res}: {amount}
                  </span>
                ))}
              </div>
            </div>

            {building.input_resources?.length > 0 && (
              <div className="card-section">
                <strong>📥 Input:</strong>
                <div className="resource-list">
                  {building.input_resources.map((r, i) => (
                    <span key={i} className="resource-badge">
                      {r.resource}: {r.amount}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {building.output_resources?.length > 0 && (
              <div className="card-section">
                <strong>📤 Output:</strong>
                <div className="resource-list">
                  {building.output_resources.map((r, i) => (
                    <span key={i} className="resource-badge">
                      {r.resource}: {r.amount}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="card-actions">
              <button onClick={() => onEdit(building)}>✏️ Bewerk</button>
              <button onClick={() => onDelete(building.id)} className="btn-danger">
                🗑️ Verwijder
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============= RESOURCES PANEL =============
function ResourcesPanel({ resources, onEdit, onDelete, onCreate }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Resources</h2>
        <button className="btn-primary" onClick={onCreate}>
          ➕ Nieuwe Resource
        </button>
      </div>

      <table className="resources-table">
        <thead>
          <tr>
            <th>Icoon</th>
            <th>Naam</th>
            <th>Gewicht (kg)</th>
            <th>Volume</th>
            <th>Beschrijving</th>
            <th>Acties</th>
          </tr>
        </thead>
        <tbody>
          {resources.map(resource => (
            <tr key={resource.id}>
              <td className="icon-cell">{resource.icon}</td>
              <td>
                {resource.name}
                {resource.is_default && <span className="badge-small">default</span>}
              </td>
              <td>{resource.weight}</td>
              <td>{resource.volume}</td>
              <td>{resource.description}</td>
              <td>
                <button onClick={() => onEdit(resource)} className="btn-small">
                  ✏️
                </button>
                {!resource.is_default && (
                  <button 
                    onClick={() => onDelete(resource.id)} 
                    className="btn-small btn-danger"
                  >
                    🗑️
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ============= ACTIONS PANEL =============
function ActionsPanel({ actions, onCreate }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Task Acties</h2>
        <button className="btn-primary" onClick={onCreate}>
          ➕ Nieuwe Actie
        </button>
      </div>

      <div className="actions-grid">
        {actions.map(action => (
          <div key={action.id} className="action-card">
            <span className="action-icon">{action.icon}</span>
            <h3>{action.name}</h3>
            <p>{action.description}</p>
            <code>ID: {action.id}</code>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============= EDITOR MODAL =============
function EditorModal({ type, item, resources, onClose, onSave }) {
  const [formData, setFormData] = useState(item || {
    name: '',
    icon: '🏗️',
    description: '',
    faction: 'spark',
    type: 'production',
    build_cost: { wood: 10, stone: 5 },
    input_resources: [],
    output_resources: [],
    weight: 1,
    volume: 1
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      const url = item 
        ? `${API_URL}/api/blueprints/${type}/${item.id}`
        : `${API_URL}/api/blueprints/${type}`;
      
      const method = item ? 'PUT' : 'POST';
      
      await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      onSave();
    } catch (error) {
      console.error('Save failed:', error);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{item ? 'Bewerken' : 'Nieuw'} {type === 'buildings' ? 'Gebouw' : type === 'resources' ? 'Resource' : 'Actie'}</h2>
          <button onClick={onClose} className="btn-close">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form">
          {/* Basic Fields */}
          <div className="form-group">
            <label>Naam:</label>
            <input 
              type="text"
              value={formData.name || ''}
              onChange={e => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>

          <div className="form-group">
            <label>Icoon (emoji of URL):</label>
            <input 
              type="text"
              value={formData.icon || ''}
              onChange={e => setFormData({...formData, icon: e.target.value})}
              placeholder="🏗️"
            />
          </div>

          <div className="form-group">
            <label>Beschrijving:</label>
            <textarea 
              value={formData.description || ''}
              onChange={e => setFormData({...formData, description: e.target.value})}
            />
          </div>

          {/* Building Specific */}
          {type === 'buildings' && (
            <>
              <div className="form-row">
                <div className="form-group">
                  <label>Type:</label>
                  <select 
                    value={formData.type || 'production'}
                    onChange={e => setFormData({...formData, type: e.target.value})}
                  >
                    <option value="production">Production</option>
                    <option value="storage">Storage</option>
                    <option value="housing">Housing</option>
                    <option value="defense">Defense</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Fractie:</label>
                  <select 
                    value={formData.faction || 'spark'}
                    onChange={e => setFormData({...formData, faction: e.target.value})}
                    style={{ borderColor: FACTION_COLORS[formData.faction || 'spark'] }}
                  >
                    <option value="spark">⚡ Spark</option>
                    <option value="terra">🌍 Terra</option>
                    <option value="aqua">💧 Aqua</option>
                    <option value="ignis">🔥 Ignis</option>
                    <option value="ventus">💨 Ventus</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Bouw Kosten (JSON):</label>
                <textarea 
                  value={JSON.stringify(formData.build_cost || {}, null, 2)}
                  onChange={e => {
                    try {
                      setFormData({...formData, build_cost: JSON.parse(e.target.value)});
                    } catch {}
                  }}
                  placeholder='{"wood": 10, "stone": 5}'
                />
              </div>
            </>
          )}

          {/* Resource Specific */}
          {type === 'resources' && (
            <div className="form-row">
              <div className="form-group">
                <label>Gewicht (kg):</label>
                <input 
                  type="number"
                  step="0.1"
                  value={formData.weight || 1}
                  onChange={e => setFormData({...formData, weight: parseFloat(e.target.value)})}
                />
              </div>

              <div className="form-group">
                <label>Volume:</label>
                <input 
                  type="number"
                  step="0.1"
                  value={formData.volume || 1}
                  onChange={e => setFormData({...formData, volume: parseFloat(e.target.value)})}
                />
              </div>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" onClick={onClose} className="btn-secondary">
              Annuleren
            </button>
            <button type="submit" className="btn-primary">
              💾 Opslaan
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ============= BOTS PANEL =============

function BotsPanel({ bots, onEdit, onDelete, onCreate }) {
  return (
    <div className="panel-container">
      <div className="panel-header">
        <h2>🤖 Bot Blueprints ({bots.length})</h2>
        <button className="btn-create" onClick={onCreate}>
          ➕ Nieuwe Bot
        </button>
      </div>

      <div className="items-grid">
        {bots.length === 0 ? (
          <div className="empty-state">
            <p>Geen bots gedefinieerd</p>
            <p style={{fontSize: '12px', color: '#666'}}>Maak custom bots met unieke gedrag, stats en rollen</p>
          </div>
        ) : (
          bots.map(bot => (
            <div key={bot.id} className="item-card">
              <div className="item-header">
                <span className="item-icon">{bot.icon}</span>
                <div className="item-info">
                  <h3>{bot.name}</h3>
                  <div className="item-meta">
                    <span className={`badge badge-${bot.faction}`}>{bot.faction}</span>
                    <span className="badge">{bot.type}</span>
                    {bot.role && <span className="badge badge-role">{bot.role}</span>}
                  </div>
                </div>
              </div>

              <div className="item-details">
                <div className="detail-row">
                  <span className="label">Gedrag:</span>
                  <span>{bot.behavior}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Combat Type:</span>
                  <span>{bot.combat_type}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Stats:</span>
                  <span>
                    ❤️ {bot.health} | ⚔️ {bot.power} | 👁️ {bot.vision_radius} | 🏃 {bot.speed}x
                  </span>
                </div>
                {bot.carry_capacity > 0 && (
                  <div className="detail-row">
                    <span className="label">Draagcapaciteit:</span>
                    <span>📦 {bot.carry_capacity}</span>
                  </div>
                )}
                {bot.linked_building && (
                  <div className="detail-row">
                    <span className="label">Gekoppeld aan:</span>
                    <span>🏗️ {bot.linked_building}</span>
                  </div>
                )}
                {bot.drop_resource && (
                  <div className="detail-row">
                    <span className="label">Drops:</span>
                    <span>{bot.drop_resource.type} ({bot.drop_resource.amount_min}-{bot.drop_resource.amount_max})</span>
                  </div>
                )}
                <div className="detail-row">
                  <span className="label">Agressief:</span>
                  <span>{bot.is_aggressive ? '⚔️ Ja' : '🕊️ Nee'}</span>
                </div>
              </div>

              <div className="item-actions">
                <button onClick={() => onEdit(bot)} className="btn-edit">
                  ✏️ Bewerken
                </button>
                <button onClick={() => onDelete(bot.id)} className="btn-delete">
                  🗑️ Verwijderen
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default BlueprintEditorTab;
