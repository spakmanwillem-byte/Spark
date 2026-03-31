import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './BuildingsOverviewTab.css';

const API = process.env.REACT_APP_BACKEND_URL;

function BuildingsOverviewTab() {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('spark');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBuildingsData();
    const interval = setInterval(fetchBuildingsData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchBuildingsData = async () => {
    try {
      const response = await axios.get(`${API}/api/game/buildings-overview`);
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching buildings data:', error);
      setLoading(false);
    }
  };

  if (loading || !data) {
    return <div className="buildings-overview-loading">Loading...</div>;
  }

  const tabs = [
    { id: 'spark', name: '⚡ Spark', color: '#FFD700' },
    { id: 'terra', name: '🌍 Terra', color: '#8B4513' },
    { id: 'aqua', name: '💧 Aqua', color: '#2196F3' },
    { id: 'ignis', name: '🔥 Ignis', color: '#F44336' },
    { id: 'ventus', name: '💨 Ventus', color: '#9E9E9E' }
  ];

  const currentTabData = data.overview[activeTab] || [];

  return (
    <div className="buildings-overview-container">
      <h2>🏗️ Buildings Overview</h2>
      
      {/* Tabs */}
      <div className="faction-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`faction-tab ${activeTab === tab.id ? 'active' : ''}`}
            style={{
              borderColor: activeTab === tab.id ? tab.color : 'transparent',
              color: activeTab === tab.id ? tab.color : '#ccc'
            }}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="tab-content">
        
        {/* Spark Inventory (only for spark tab) */}
        {activeTab === 'spark' && (
          <div className="inventory-section">
            <h3>🎒 Spark Inventory</h3>
            <div className="resource-grid">
              <div className="resource-item">
                <span className="resource-icon">🪵</span>
                <span className="resource-value">{data.spark_inventory.wood}</span>
              </div>
              <div className="resource-item">
                <span className="resource-icon">🪨</span>
                <span className="resource-value">{data.spark_inventory.stone}</span>
              </div>
              <div className="resource-item">
                <span className="resource-icon">🐟</span>
                <span className="resource-value">{data.spark_inventory.fish}</span>
              </div>
              <div className="resource-item">
                <span className="resource-icon">💧</span>
                <span className="resource-value">{data.spark_inventory.water_bottle}</span>
              </div>
            </div>
          </div>
        )}

        {/* Total Storage */}
        <div className="storage-section">
          <h3>📦 Total Storage (All Buildings)</h3>
          <div className="resource-grid">
            <div className="resource-item">
              <span className="resource-label">Wood</span>
              <span className="resource-value">{data.total_storage.wood}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Stone</span>
              <span className="resource-value">{data.total_storage.stone}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Fish</span>
              <span className="resource-value">{data.total_storage.fish}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Grain</span>
              <span className="resource-value">{data.total_storage.grain}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Flour</span>
              <span className="resource-value">{data.total_storage.flour}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Bread</span>
              <span className="resource-value">{data.total_storage.bread}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Planks</span>
              <span className="resource-value">{data.total_storage.plank}</span>
            </div>
            <div className="resource-item">
              <span className="resource-label">Water</span>
              <span className="resource-value">{data.total_storage.water}</span>
            </div>
          </div>
        </div>

        {/* Buildings List */}
        <div className="buildings-section">
          <h3>🏗️ Buildings ({currentTabData.length})</h3>
          {currentTabData.length === 0 ? (
            <p className="no-buildings">No buildings yet</p>
          ) : (
            <div className="buildings-list">
              {currentTabData.map((building, index) => (
                <div key={index} className="building-card">
                  <span className="building-icon">{building.icon}</span>
                  <div className="building-info">
                    <div className="building-name">{building.name}</div>
                    <div className="building-coords">({building.x}, {building.y})</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default BuildingsOverviewTab;
