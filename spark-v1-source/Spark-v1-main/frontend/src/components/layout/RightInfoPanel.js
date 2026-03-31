import React, { useState, useRef, useEffect } from 'react';

const RightInfoPanel = ({ userData }) => {
  const [panelWidth, setPanelWidth] = useState(() => {
    const saved = localStorage.getItem('spark_right_panel_width');
    return saved ? parseInt(saved) : 220; // Smaller default: 220px instead of 280px
  });
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const handleMouseDown = (e) => {
    setIsDragging(true);
    startX.current = e.clientX;
    startWidth.current = panelWidth;
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      // Calculate delta (inverted because we're dragging from the left edge)
      const deltaX = startX.current - e.clientX;
      const newWidth = Math.max(150, Math.min(600, startWidth.current + deltaX)); // Min 150px, Max 600px
      setPanelWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isDragging) {
        setIsDragging(false);
        localStorage.setItem('spark_right_panel_width', panelWidth.toString());
      }
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, panelWidth]);

  return (
    <div className="right-info-panel" style={{ width: `${panelWidth}px` }}>
      {/* Resize Handle - LEFT SIDE - LARGER & MORE VISIBLE */}
      <div 
        className={`panel-resize-handle-left ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
        style={{
          position: 'absolute',
          left: '-5px',  // Moved outside panel for easier grabbing
          top: 0,
          bottom: 0,
          width: '12px',  // Wider for easier clicking
          cursor: 'ew-resize',
          backgroundColor: isDragging ? 'rgba(168, 85, 247, 0.5)' : 'rgba(168, 85, 247, 0.15)',
          transition: isDragging ? 'none' : 'background-color 0.2s',
          zIndex: 1000,  // Higher z-index to be above everything
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderLeft: '2px solid rgba(168, 85, 247, 0.3)',
          borderRight: '2px solid rgba(168, 85, 247, 0.3)'
        }}
        title="Sleep om grootte aan te passen"
      >
        <div style={{
          width: '3px',
          height: '60px',
          backgroundColor: 'rgba(255, 255, 255, 0.5)',
          borderRadius: '3px'
        }}></div>
      </div>

      {/* Quick Stats Widget - COMPACT */}
      {userData && (
        <div className="info-widget stats-widget">
          <h3 className="widget-title text-sm">📈 Quick Stats</h3>
          <div className="widget-content">
            <div className="stat-item">
              <span className="stat-label text-xs">XP</span>
              <span className="stat-value text-sm">{userData.xp || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label text-xs">Achievements</span>
              <span className="stat-value text-sm">
                {userData.achievements?.unlocked?.length || 0}
              </span>
            </div>
            <div className="stat-item">
              <span className="stat-label text-xs">Gesprekken</span>
              <span className="stat-value text-sm">{userData.gesprekken_count || 0}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label text-xs">Gradatie</span>
              <span className="stat-value text-sm">{userData.gradatie}</span>
            </div>
          </div>
        </div>
      )}

      {/* System Health Widget - COMPACT */}
      <div className="info-widget health-widget">
        <h3 className="widget-title text-sm">💚 System Health</h3>
        <div className="widget-content">
          <div className="health-item text-xs">
            <span className="health-icon">🟢</span>
            <span className="health-label">Backend</span>
            <span className="health-status">Online</span>
          </div>
          <div className="health-item text-xs">
            <span className="health-icon">🟢</span>
            <span className="health-label">Database</span>
            <span className="health-status">Connected</span>
          </div>
          <div className="health-item text-xs">
            <span className="health-icon">🟢</span>
            <span className="health-label">Session</span>
            <span className="health-status">Active</span>
          </div>
        </div>
      </div>

      {/* Tips Widget - COMPACT */}
      <div className="info-widget tips-widget">
        <h3 className="widget-title text-sm">💡 Tips</h3>
        <div className="widget-content">
          <p className="tip-text text-xs">
            Gebruik natuurlijke taal! Probeer "bekijk mijn achievements".
          </p>
        </div>
      </div>
    </div>
  );
};

export default RightInfoPanel;
