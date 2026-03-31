import React from 'react';

const MainContentArea = ({ activeTab, userData, children }) => {
  return (
    <div className="main-content-area">
      <div className="content-header">
        <h2 className="content-title">
          {getTabTitle(activeTab, userData)}
        </h2>
      </div>
      
      <div className="content-body">
        {children}
      </div>
    </div>
  );
};

const getTabTitle = (tab, userData) => {
  const titles = {
    profiel: `👤 Mijn Profiel${userData ? ` - ${userData.naam}` : ''}`,
    voortgang: '📊 Mijn Voortgang',
    chat: '💬 Chat met Spark',
    dagboek: '📖 Dagboek',
    agenda: '📅 Agenda',
    bestanden: '📁 Bestanden',
    roadmap: '🗺️ Roadmap',
    achievements: '🏆 Achievements',
    knowledge: '🧠 Knowledge Base',
    emotions: '😊 Emotie Statistieken',
    leaderboard: '🏆 Leaderboard',
    notities: '📝 Notities',
    status: '⚡ System Status',
    settings: '⚙️ Settings',
    logs: '📊 System Logs',
    admin: '👑 Admin Panel',
    uitgaven: '💸 Uitgaven',
    inkomsten: '💰 Inkomsten',
    dashboard: '📊 Dashboard',
    wallet: '💰 Wallet',
  };
  
  return titles[tab] || 'Spark';
};

export default MainContentArea;
