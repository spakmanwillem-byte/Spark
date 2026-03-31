import React from 'react';
import './TopHeader.css';

function TopHeader({ userData }) {
  // Get name from userData - prioritize 'name' field
  const userName = userData?.name || userData?.username || 'Gast';
  const isOnline = true; // Later kunnen we dit dynamisch maken

  return (
    <div className="top-header">
      {/* Left: Username */}
      <div className="header-left">
        <span className="user-name">{userName}</span>
      </div>

      {/* Center: Empty (for future banners/graphs) */}
      <div className="header-center">
        {/* Ruimte voor banners, grafieken, etc. */}
      </div>

      {/* Right: Status */}
      <div className="header-right">
        <div className="status-indicator">
          <span className={`status-dot ${isOnline ? 'online' : 'offline'}`}></span>
          <span className="status-text">Online</span>
        </div>
      </div>
    </div>
  );
}

export default TopHeader;
