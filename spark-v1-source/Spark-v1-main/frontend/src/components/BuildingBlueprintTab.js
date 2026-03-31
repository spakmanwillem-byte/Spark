import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './BuildingBlueprintTab.css';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

function BuildingBlueprintTab() {
  const [tree, setTree] = useState(null);
  const [selectedBuilding, setSelectedBuilding] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedData, setEditedData] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBuildingsTree();
  }, []);

  const fetchBuildingsTree = async () => {
    try {
      const response = await axios.get(`${API}/buildings/tree`);
      if (response.data.success) {
        setTree(response.data.tree);
        // Expand all categories by default
        const expanded = {};
        response.data.tree.children?.forEach((cat, idx) => {
          expanded[idx] = true;
        });
        setExpandedCategories(expanded);
      }
    } catch (err) {
      console.error('Error loading buildings:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleCategory = (index) => {
    setExpandedCategories(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const selectBuilding = (building) => {
    setSelectedBuilding(building);
    setEditedData(JSON.parse(JSON.stringify(building))); // Deep copy
    setEditMode(false);
  };

  const handleEdit = (field, value) => {
    setEditedData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleCostEdit = (resource, value) => {
    setEditedData(prev => ({
      ...prev,
      cost: {
        ...prev.cost,
        [resource]: parseInt(value) || 0
      }
    }));
  };

  const saveChanges = async () => {
    try {
      const updates = {
        name: editedData.name,
        icon: editedData.icon,
        cost: editedData.cost,
        ...editedData.properties
      };

      await axios.post(`${API}/buildings/update`, {
        item_type: selectedBuilding.id,
        updates: updates
      });

      alert('✅ Building updated! (Restart backend for persistence)');
      fetchBuildingsTree();
      setEditMode(false);
    } catch (err) {
      alert('❌ Error updating building: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="blueprint-tab">
        <div className="loading">Loading blueprints...</div>
      </div>
    );
  }

  return (
    <div className="blueprint-tab">
      <div className="blueprint-header">
        <h1>🏗️ Building Blueprints</h1>
        <p>View and configure all buildings</p>
      </div>

      <div className="blueprint-container">
        {/* LEFT: Tree View */}
        <div className="blueprint-tree">
          <h2>📋 All Buildings</h2>
          
          {tree?.children?.map((category, catIdx) => (
            <div key={catIdx} className="category">
              <div 
                className="category-header"
                onClick={() => toggleCategory(catIdx)}
              >
                <span className="expand-icon">
                  {expandedCategories[catIdx] ? '▼' : '▶'}
                </span>
                <span>{category.name}</span>
                <span className="count">({category.children.length})</span>
              </div>

              {expandedCategories[catIdx] && (
                <div className="category-children">
                  {category.children.map((building, buildIdx) => (
                    <div
                      key={buildIdx}
                      className={`building-item ${selectedBuilding?.id === building.id ? 'selected' : ''}`}
                      onClick={() => selectBuilding(building)}
                    >
                      <span className="building-icon">{building.icon}</span>
                      <span className="building-name">{building.name}</span>
                      {building.cost && Object.keys(building.cost).length > 0 && (
                        <span className="building-cost">
                          {Object.entries(building.cost).map(([res, amt]) => (
                            <span key={res} className="cost-item">
                              {amt} {res === 'wood' ? '🪵' : '🪨'}
                            </span>
                          ))}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* RIGHT: Details Panel */}
        <div className="blueprint-details">
          {selectedBuilding ? (
            <>
              <div className="details-header">
                <h2>
                  <span className="big-icon">{selectedBuilding.icon}</span>
                  {selectedBuilding.name}
                </h2>
                <button 
                  className="edit-btn"
                  onClick={() => setEditMode(!editMode)}
                >
                  {editMode ? '❌ Cancel' : '✏️ Edit'}
                </button>
              </div>

              {editMode ? (
                // EDIT MODE
                <div className="edit-form">
                  <div className="form-group">
                    <label>Name:</label>
                    <input
                      type="text"
                      value={editedData.name}
                      onChange={(e) => handleEdit('name', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Icon (emoji):</label>
                    <input
                      type="text"
                      value={editedData.icon}
                      onChange={(e) => handleEdit('icon', e.target.value)}
                    />
                  </div>

                  <div className="form-group">
                    <label>Cost:</label>
                    <div className="cost-inputs">
                      <div>
                        <label>Wood 🪵:</label>
                        <input
                          type="number"
                          value={editedData.cost?.wood || 0}
                          onChange={(e) => handleCostEdit('wood', e.target.value)}
                        />
                      </div>
                      <div>
                        <label>Stone 🪨:</label>
                        <input
                          type="number"
                          value={editedData.cost?.stone || 0}
                          onChange={(e) => handleCostEdit('stone', e.target.value)}
                        />
                      </div>
                    </div>
                  </div>

                  <button className="save-btn" onClick={saveChanges}>
                    💾 Save Changes
                  </button>
                </div>
              ) : (
                // VIEW MODE
                <div className="details-content">
                  <div className="detail-section">
                    <h3>💰 Cost</h3>
                    {selectedBuilding.cost && Object.keys(selectedBuilding.cost).length > 0 ? (
                      <div className="cost-display">
                        {Object.entries(selectedBuilding.cost).map(([resource, amount]) => (
                          <div key={resource} className="cost-row">
                            <span className="resource-icon">
                              {resource === 'wood' ? '🪵' : '🪨'}
                            </span>
                            <span className="resource-name">{resource}</span>
                            <span className="resource-amount">{amount}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="no-data">Free to build</p>
                    )}
                  </div>

                  {selectedBuilding.properties?.process && (
                    <div className="detail-section">
                      <h3>⚙️ Production</h3>
                      <div className="production-display">
                        <p>
                          <strong>Input:</strong> {JSON.stringify(selectedBuilding.properties.process.input)}
                        </p>
                        <p>
                          <strong>Output:</strong> {selectedBuilding.properties.process.output}
                        </p>
                        <p>
                          <strong>Rate:</strong> {selectedBuilding.properties.process.rate}
                        </p>
                      </div>
                    </div>
                  )}

                  {selectedBuilding.properties && Object.keys(selectedBuilding.properties).length > 0 && (
                    <div className="detail-section">
                      <h3>📊 Properties</h3>
                      <div className="properties-display">
                        {Object.entries(selectedBuilding.properties).map(([key, value]) => (
                          <div key={key} className="property-row">
                            <span className="prop-key">{key}:</span>
                            <span className="prop-value">{JSON.stringify(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="detail-section">
                    <h3>🔧 Type</h3>
                    <p className="type-badge">{selectedBuilding.type}</p>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <p>👈 Select a building from the tree to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BuildingBlueprintTab;
