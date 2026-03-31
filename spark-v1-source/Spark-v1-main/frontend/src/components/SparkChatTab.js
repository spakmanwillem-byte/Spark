import React from 'react';
import SparkInfoBanner from './SparkInfoBanner';

function SparkChatTab() {
  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <SparkInfoBanner />
      
      <div style={{ 
        background: 'rgba(30, 30, 40, 0.6)', 
        border: '1px solid rgba(76, 175, 80, 0.3)',
        borderRadius: '12px',
        padding: '24px',
        textAlign: 'center',
        color: 'rgba(255, 255, 255, 0.7)'
      }}>
        <h3 style={{ color: '#4CAF50', marginBottom: '12px' }}>💬 Chat met Spark</h3>
        <p>Gebruik het chat gebied onderaan om met Spark te praten</p>
      </div>
    </div>
  );
}

export default SparkChatTab;
