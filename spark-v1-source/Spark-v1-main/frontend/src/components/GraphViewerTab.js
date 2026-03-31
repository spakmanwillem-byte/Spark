import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GraphViewerTab = () => {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [stats, setStats] = useState({});
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGraphData();
  }, []);

  const loadGraphData = async () => {
    try {
      setLoading(true);
      
      // Load stats FIRST (lightweight)
      const statsResponse = await axios.get(`${API}/graph/stats`);
      const statsData = statsResponse.data || {};
      
      setStats({
        total_nodes: statsData.total_nodes || 0,
        total_edges: statsData.total_edges || 0,
        visible: 100  // Always show 100 max
      });
      
      // Load LIMITED nodes and edges for performance
      const nodesResponse = await axios.get(`${API}/graph/nodes?limit=100`);
      const edgesResponse = await axios.get(`${API}/graph/edges?limit=200`);
      
      setGraphData({
        nodes: nodesResponse.data || [],
        edges: edgesResponse.data || []
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading graph:', error);
      setLoading(false);
    }
  };

  const searchNodes = async (term) => {
    if (!term || term.length < 2) {
      loadGraphData();
      return;
    }

    try {
      const response = await axios.get(`${API}/graph/search?query=${term}&limit=20`);
      setGraphData({
        nodes: response.data.nodes || [],
        edges: response.data.edges || []
      });
    } catch (error) {
      console.error('Error searching:', error);
    }
  };

  const handleNodeClick = async (node) => {
    setSelectedNode(node);
    
    // Load connections voor deze node
    try {
      const response = await axios.get(`${API}/graph/connections/${node.id}`);
      // Update graph om connections te tonen
      setGraphData(prev => ({
        nodes: [...prev.nodes, ...(response.data.connected_nodes || [])],
        edges: response.data.edges || []
      }));
    } catch (error) {
      console.error('Error loading connections:', error);
    }
  };

  const getNodeColor = (node) => {
    const typeColors = {
      'knowledge': '#4CAF50',
      'concept': '#2196F3',
      'notitie': '#FFC107',
      'norm': '#9C27B0',
      'waarde': '#FF5722'
    };
    return typeColors[node.type] || '#888';
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <p>⏳ Laden van knowledge graph...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: '20px' }}>
        <h2 style={{ marginBottom: '10px' }}>🗺️ Knowledge Graph Viewer</h2>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '14px' }}>
          Visualiseer verbindingen tussen concepten - Zie hoe kennis groeit!
        </p>
      </div>

      {/* Stats */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
        gap: '15px',
        marginBottom: '20px'
      }}>
        <div className="stat-card">
          <div className="stat-icon">🧩</div>
          <div className="stat-value">{stats.total_nodes || 0}</div>
          <div className="stat-label">Totaal Concepten</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔗</div>
          <div className="stat-value">{stats.total_edges || 0}</div>
          <div className="stat-label">Totaal Verbindingen</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-value">{graphData.nodes.length}</div>
          <div className="stat-label">Nu Zichtbaar</div>
        </div>
      </div>

      {/* Search */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            searchNodes(e.target.value);
          }}
          placeholder="Zoek concept... (bijv. 'appel', 'programmeren')"
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)',
            background: 'rgba(30,30,30,0.8)',
            color: 'white',
            fontSize: '14px'
          }}
        />
      </div>

      {/* Graph Area - Simple List View (Later: Canvas/D3) */}
      <div style={{
        flex: 1,
        background: 'rgba(20,20,20,0.8)',
        borderRadius: '12px',
        border: '1px solid rgba(255,255,255,0.1)',
        padding: '20px',
        overflowY: 'auto'
      }}>
        <h3 style={{ marginBottom: '15px', fontSize: '16px' }}>
          💡 Concepten ({graphData.nodes.length})
        </h3>

        {graphData.nodes.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'rgba(255,255,255,0.5)' }}>
            <p>🔍 Geen resultaten. Probeer een andere zoekterm.</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '10px' }}>
            {graphData.nodes.map((node, idx) => (
              <div
                key={idx}
                onClick={() => handleNodeClick(node)}
                style={{
                  padding: '15px',
                  background: selectedNode?.id === node.id 
                    ? 'rgba(76, 175, 80, 0.2)' 
                    : 'rgba(40,40,40,0.6)',
                  borderRadius: '8px',
                  border: `2px solid ${getNodeColor(node)}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(5px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateX(0)'}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: getNodeColor(node)
                  }}></div>
                  <strong>{node.titel}</strong>
                  <span style={{
                    marginLeft: 'auto',
                    fontSize: '12px',
                    color: 'rgba(255,255,255,0.5)',
                    textTransform: 'uppercase'
                  }}>
                    {node.type}
                  </span>
                </div>
                {node.content && (
                  <div style={{
                    marginTop: '8px',
                    fontSize: '13px',
                    color: 'rgba(255,255,255,0.7)',
                    lineHeight: '1.4'
                  }}>
                    {node.content.substring(0, 100)}
                    {node.content.length > 100 && '...'}
                  </div>
                )}
                {node.tags && node.tags.length > 0 && (
                  <div style={{ marginTop: '8px', display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                    {node.tags.slice(0, 5).map((tag, i) => (
                      <span key={i} style={{
                        padding: '2px 8px',
                        background: 'rgba(76, 175, 80, 0.2)',
                        borderRadius: '12px',
                        fontSize: '11px',
                        color: '#4CAF50'
                      }}>
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Selected Node Details */}
        {selectedNode && (
          <div style={{
            marginTop: '20px',
            padding: '20px',
            background: 'rgba(76, 175, 80, 0.1)',
            border: '2px solid rgba(76, 175, 80, 0.3)',
            borderRadius: '12px'
          }}>
            <h4 style={{ marginBottom: '10px' }}>🔍 Geselecteerd: {selectedNode.titel}</h4>
            <div style={{ fontSize: '13px', color: 'rgba(255,255,255,0.8)' }}>
              <p><strong>Type:</strong> {selectedNode.type}</p>
              <p><strong>Bron:</strong> {selectedNode.source}</p>
              {selectedNode.metadata && (
                <p><strong>Metadata:</strong> {JSON.stringify(selectedNode.metadata)}</p>
              )}
            </div>
            
            <div style={{ marginTop: '15px' }}>
              <h5 style={{ fontSize: '14px', marginBottom: '8px' }}>
                🔗 Verbindingen ({graphData.edges.filter(e => 
                  e.from === selectedNode.id || e.to === selectedNode.id
                ).length})
              </h5>
              {graphData.edges
                .filter(e => e.from === selectedNode.id || e.to === selectedNode.id)
                .slice(0, 10)
                .map((edge, i) => (
                  <div key={i} style={{
                    padding: '8px',
                    background: 'rgba(0,0,0,0.3)',
                    borderRadius: '6px',
                    marginBottom: '5px',
                    fontSize: '12px'
                  }}>
                    {edge.relation_type} → Strength: {(edge.strength * 100).toFixed(0)}%
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      <style>{`
        .stat-card {
          background: rgba(30, 30, 30, 0.8);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          padding: 20px;
          text-align: center;
        }
        
        .stat-icon {
          font-size: 32px;
          margin-bottom: 10px;
        }
        
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #4CAF50;
          margin-bottom: 5px;
        }
        
        .stat-label {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          text-transform: uppercase;
          letter-spacing: 1px;
        }
      `}</style>
    </div>
  );
};

export default GraphViewerTab;
