import React, { useState, useRef, useEffect } from 'react';

const LeftNavigation = ({ activeTab, setActiveTab, userData, handleLogout }) => {
  const [navWidth, setNavWidth] = useState(() => {
    const saved = localStorage.getItem('spark_nav_width');
    return saved ? parseInt(saved) : 200;
  });
  const [isDragging, setIsDragging] = useState(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  // Dragable tabs - Load from localStorage or use default order
  const [tabOrder, setTabOrder] = useState(() => {
    const saved = localStorage.getItem('spark_tab_order');
    return saved ? JSON.parse(saved) : {};
  });

  const [draggedTab, setDraggedTab] = useState(null);

  const userTabs = [
    // KERN
    { id: 'profiel', icon: '👤', label: 'Mijn Profiel', requiresLogin: true, section: 'kern' },
    { id: 'chat', icon: '💬', label: 'Spark Chat', requiresLogin: false, section: 'kern' },
    
    // PRODUCTIVITEIT
    { id: 'agenda', icon: '📅', label: 'Agenda', requiresLogin: true, section: 'productiviteit' },
    { id: 'dagboek', icon: '📝', label: 'Dagboek', requiresLogin: true, section: 'productiviteit' },
    { id: 'notities', icon: '📋', label: 'Notities & Taken', requiresLogin: true, section: 'productiviteit' },
    // 'taken' tab verwijderd - functionaliteit zit nu in Notities via TODO categorie
    
    // FINANCIEEL
    { id: 'mijn_wallet', icon: '💳', label: 'Wallet', requiresLogin: true, section: 'financieel' },
    { id: 'winkel', icon: '🛒', label: 'Winkel', requiresLogin: true, section: 'financieel' },
    
    // COMMUNITY & SPEL
    { id: 'community', icon: '🌟', label: 'Community', requiresLogin: true, section: 'community' },
    { id: 'spark_world', icon: '🌍', label: 'Spark World', requiresLogin: false, section: 'community' },
    { id: 'leaderboard', icon: '🏆', label: 'Leaderboard', requiresLogin: false, section: 'community' },
    { id: 'achievements', icon: '🏅', label: 'Achievements', requiresLogin: true, section: 'community' },
    
    // INFO
    { id: 'roadmap', icon: '🗺️', label: 'Roadmap', requiresLogin: false, section: 'info' },
  ];

  const adminTabs = [
    { id: 'knowledge', icon: '🧠', label: 'Knowledge Base' },
    { id: 'graph', icon: '🗺️', label: 'Knowledge Graph' },
    // Triggers zitten IN Admin Panel tab (niet los)
    { id: 'monitor', icon: '📡', label: 'Monitor' },
    { id: 'admin', icon: '👑', label: 'Admin Panel' },
  ];

  const isAdmin = userData && userData.gradatie === 1;

  // Drag & Drop handlers
  const handleDragStart = (e, tab, section) => {
    setDraggedTab({ tab, section });
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, targetTab, targetSection) => {
    e.preventDefault();
    
    if (!draggedTab || draggedTab.section !== targetSection) return;
    
    const sectionTabs = userTabs.filter(t => t.section === targetSection);
    const draggedIndex = sectionTabs.findIndex(t => t.id === draggedTab.tab.id);
    const targetIndex = sectionTabs.findIndex(t => t.id === targetTab.id);
    
    if (draggedIndex === targetIndex) return;
    
    // Update tab order for this section
    const newOrder = { ...tabOrder };
    if (!newOrder[targetSection]) newOrder[targetSection] = sectionTabs.map(t => t.id);
    
    const [removed] = newOrder[targetSection].splice(draggedIndex, 1);
    newOrder[targetSection].splice(targetIndex, 0, removed);
    
    setTabOrder(newOrder);
    localStorage.setItem('spark_tab_order', JSON.stringify(newOrder));
    setDraggedTab(null);
  };

  // Get sorted tabs for a section
  const getSortedTabs = (section) => {
    const sectionTabs = userTabs.filter(tab => tab.section === section);
    if (!tabOrder[section]) return sectionTabs;
    
    // Sort according to saved order
    return sectionTabs.sort((a, b) => {
      const aIndex = tabOrder[section].indexOf(a.id);
      const bIndex = tabOrder[section].indexOf(b.id);
      if (aIndex === -1) return 1;
      if (bIndex === -1) return -1;
      return aIndex - bIndex;
    });
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    startX.current = e.clientX;
    startWidth.current = navWidth;
    e.preventDefault();
  };

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging) return;
      
      const deltaX = e.clientX - startX.current;
      const newWidth = Math.max(150, Math.min(400, startWidth.current + deltaX));
      setNavWidth(newWidth);
    };

    const handleMouseUp = () => {
      if (isDragging) {
        setIsDragging(false);
        localStorage.setItem('spark_nav_width', navWidth.toString());
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
  }, [isDragging, navWidth]);

  return (
    <div className="left-navigation" style={{ width: `${navWidth}px` }}>
      {/* Resize Handle */}
      <div 
        className={`nav-resize-handle ${isDragging ? 'dragging' : ''}`}
        onMouseDown={handleMouseDown}
      >
        <div className="resize-indicator-vertical"></div>
      </div>

      {/* User Tabs - Grouped by Section with Drag & Drop */}
      {['kern', 'productiviteit', 'financieel', 'community', 'info'].map(section => {
        const sectionTabs = getSortedTabs(section);
        const visibleTabs = sectionTabs.filter(tab => !tab.requiresLogin || userData);
        
        if (visibleTabs.length === 0) return null;
        
        const sectionTitles = {
          kern: 'KERN',
          productiviteit: 'PRODUCTIVITEIT',
          financieel: 'FINANCIEEL',
          community: 'COMMUNITY & SPEL',
          info: 'INFO'
        };
        
        return (
          <div key={section} className="nav-section">
            <div className="nav-section-title">{sectionTitles[section]}</div>
            {visibleTabs.map(tab => (
              <button
                key={tab.id}
                draggable={userData ? true : false}
                onDragStart={(e) => handleDragStart(e, tab, section)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, tab, section)}
                className={`nav-item ${activeTab === tab.id ? 'active' : ''} ${draggedTab?.tab.id === tab.id ? 'opacity-50' : ''}`}
                onClick={() => setActiveTab(tab.id)}
                title={userData ? 'Sleep om volgorde te wijzigen' : tab.label}
              >
                <span className="nav-icon">{tab.icon}</span>
                <span className="nav-label">{tab.label}</span>
              </button>
            ))}
          </div>
        );
      })}

      {isAdmin && (
        <div className="nav-section">
          <div className="nav-section-title">ADMIN</div>
          {adminTabs.map(tab => (
            <button
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="nav-icon">{tab.icon}</span>
              <span className="nav-label">{tab.label}</span>
            </button>
          ))}
        </div>
      )}

      {userData && (
        <div className="nav-footer">
          <button className="nav-item logout-btn" onClick={handleLogout}>
            <span className="nav-icon">🚪</span>
            <span className="nav-label">Afmelden</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default LeftNavigation;
