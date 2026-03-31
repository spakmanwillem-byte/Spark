import React, { useState, useEffect } from 'react';
import './SparkInfoBanner.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function SparkInfoBanner() {
  const [activeTab, setActiveTab] = useState('missie');
  const [sparkBalance, setSparkBalance] = useState(null);
  const [bchPrice, setBchPrice] = useState(null);
  const [monitorStatus, setMonitorStatus] = useState(null);

  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  // Fetch Spark vermogen
  useEffect(() => {
    const fetchBalance = async () => {
      try {
        // Use overview API instead (more reliable)
        const response = await fetch(`${BACKEND_URL}/api/wallet/overview?user_id=user-001`);
        const data = await response.json();
        if (data.success && data.total_eur) {
          setSparkBalance(data.total_eur);
        }
      } catch (error) {
        console.error('Failed to fetch Spark balance:', error);
      }
    };
    fetchBalance();
  }, [BACKEND_URL]);

  // Fetch BCH live data + monitor status
  useEffect(() => {
    const fetchLiveData = async () => {
      try {
        // BCH prijs
        const priceRes = await fetch(`${BACKEND_URL}/api/bitvavo/ticker/BCH-EUR`);
        const priceData = await priceRes.json();
        if (priceData.success) {
          setBchPrice(priceData.ticker);
        }

        // Monitor status
        const monitorRes = await fetch(`${BACKEND_URL}/api/monitoring/status`);
        const monitorData = await monitorRes.json();
        if (monitorData.success) {
          setMonitorStatus(monitorData.status);
        }
      } catch (error) {
        console.error('Failed to fetch live data:', error);
      }
    };

    fetchLiveData();
    const interval = setInterval(fetchLiveData, 60000); // Update elk minuut
    return () => clearInterval(interval);
  }, [BACKEND_URL]);

  return (
    <div className="spark-info-banner">
      <div className="banner-header">
        <div className="spark-logo">✨ SPARK CORE 4.1</div>
        <div className="banner-tagline">"Technologie die versterkt, niet vervangt"</div>
      </div>

      {/* Tab Navigation */}
      <div className="banner-tabs">
        <button
          onClick={() => setActiveTab('missie')}
          className={`banner-tab ${activeTab === 'missie' ? 'active' : ''}`}
        >
          🎯 Missie & Visie
        </button>
        <button
          onClick={() => setActiveTab('oorsprong')}
          className={`banner-tab ${activeTab === 'oorsprong' ? 'active' : ''}`}
        >
          🌱 Oorsprong
        </button>
        <button
          onClick={() => setActiveTab('filosofie')}
          className={`banner-tab ${activeTab === 'filosofie' ? 'active' : ''}`}
        >
          💎 Filosofie
        </button>
        <button
          onClick={() => setActiveTab('waarden')}
          className={`banner-tab ${activeTab === 'waarden' ? 'active' : ''}`}
        >
          ⚡ Kernwaarden
        </button>
        <button
          onClick={() => setActiveTab('trading')}
          className={`banner-tab ${activeTab === 'trading' ? 'active' : ''}`}
        >
          💰 Live Trading
        </button>
      </div>

      {/* Tab Content */}
      <div className="banner-content">
        {activeTab === 'missie' && (
          <div className="content-section">
            <h3>🎯 Missie</h3>
            <p>
              Mensen ondersteunen in hun persoonlijke ontwikkeling door technologie te bouwen 
              die <strong>autonomie versterkt</strong> in plaats van afhankelijkheid creëert.
            </p>
            <p>
              Spark wil laten zien dat technologie:
            </p>
            <ul>
              <li>✓ Begrijpelijk mag zijn</li>
              <li>✓ Lokaal mag draaien</li>
              <li>✓ Controleerbaar moet blijven</li>
              <li>✓ In dienst staat van menselijke groei</li>
            </ul>
            
            <h3>🔮 Visie</h3>
            <p>
              Een ecosysteem waarin mensen eigenaar blijven van hun data, 
              AI ondersteunend werkt, en groei voortkomt uit bewust bouwen.
            </p>
            <div className="vision-box">
              <strong>Lange termijn:</strong> Transparante, lokale AI zonder verborgen datastromen 
              of verslavingsmodellen.
            </div>
          </div>
        )}

        {activeTab === 'oorsprong' && (
          <div className="content-section">
            <h3>🌱 Het Begin</h3>
            <blockquote className="origin-quote">
              "Kan ik een Iron Man-bril maken?"
            </blockquote>
            <p>
              Het antwoord was: <strong>ja</strong>, maar niet via een bestaande AI. 
              Dus moest er een eigen systeem gebouwd worden.
            </p>
            <p>
              Vanuit <em>scepsis</em>, <em>nieuwsgierigheid</em> en <em>doorzettingsvermogen</em> ontstond Spark.
            </p>
            <div className="founder-box">
              <strong>🛠️ Gebouwd door:</strong> Willem Spakman
              <br />
              <strong>💪 Zonder:</strong> Programmeerachtergrond
              <br />
              <strong>✨ Met:</strong> Visie en vastberadenheid
            </div>
            <p className="spark-quote">
              "Spark is geen product. <strong>Spark is een bouwwerk.</strong>"
            </p>
          </div>
        )}

        {activeTab === 'filosofie' && (
          <div className="content-section">
            <h3>💎 Fundamentele Principes</h3>
            <div className="principle-grid">
              <div className="principle">Fundament vóór uitbreiding</div>
              <div className="principle">Structuur vóór snelheid</div>
              <div className="principle">Begrijpelijkheid vóór complexiteit</div>
              <div className="principle">Autonomie vóór schaal</div>
              <div className="principle">Stabiliteit vóór hype</div>
            </div>
            
            <h3>🤝 Symbiose Mens & AI</h3>
            <p>
              AI is een <strong>versterker</strong> van menselijke capaciteit. 
              Geen vervanger. Geen bestuurder. Geen manipulator.
            </p>
            
            <div className="ethics-box">
              <strong>Spark AI:</strong>
              <ul>
                <li>✗ Heeft geen eigen wil</li>
                <li>✗ Heeft geen verborgen agenda</li>
                <li>✓ Ondersteunt de mens</li>
                <li>✓ De mens beslist</li>
              </ul>
            </div>

            <h3>🌳 Levend Organisme</h3>
            <p>Spark is bewust opgebouwd als levend systeem:</p>
            <ul className="organism-list">
              <li>🦴 Mappenstructuur = skelet</li>
              <li>🩸 Datastromen = bloedbaan</li>
              <li>🫀 Generators = organen</li>
              <li>⚡ Footnotes = synapsen</li>
              <li>🧬 Kernwaarden = DNA</li>
            </ul>
          </div>
        )}

        {activeTab === 'waarden' && (
          <div className="content-section">
            <h3>⚡ Kernwaarden</h3>
            <div className="values-grid">
              <div className="value-card">
                <div className="value-icon">🔓</div>
                <div className="value-name">Autonomie</div>
                <div className="value-desc">Eigenaarschap over data en keuzes</div>
              </div>
              <div className="value-card">
                <div className="value-icon">👁️</div>
                <div className="value-name">Transparantie</div>
                <div className="value-desc">Geen verborgen systemen of agenda's</div>
              </div>
              <div className="value-card">
                <div className="value-icon">🎯</div>
                <div className="value-name">Verantwoordelijkheid</div>
                <div className="value-desc">Bewust bouwen en groeien</div>
              </div>
              <div className="value-card">
                <div className="value-icon">🧘</div>
                <div className="value-name">Rust boven snelheid</div>
                <div className="value-desc">Groei zonder geforceerde deadlines</div>
              </div>
              <div className="value-card">
                <div className="value-icon">🏗️</div>
                <div className="value-name">Structuur boven chaos</div>
                <div className="value-desc">Fundament eerst, uitbreiding later</div>
              </div>
              <div className="value-card">
                <div className="value-icon">❤️</div>
                <div className="value-name">Menselijkheid</div>
                <div className="value-desc">Technologie in dienst van mensen</div>
              </div>
            </div>

            <div className="growth-principle">
              <strong>Groeiprincipe:</strong>
              <p>Spark groeit zonder deadlines. Uitbreiding gebeurt alleen wanneer het fundament stabiel is.</p>
              <p className="highlight">"Groei volgt ruimte."</p>
            </div>
          </div>
        )}

        {activeTab === 'trading' && (
          <div className="content-section">
            <h3>💰 Live Trading Status</h3>
            
            {/* BCH Prijs */}
            {bchPrice && (
              <div style={{
                background: 'rgba(76, 175, 80, 0.1)',
                border: '1px solid rgba(76, 175, 80, 0.3)',
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '14px', color: '#aaa' }}>BCH/EUR</div>
                    <div style={{ fontSize: '32px', fontWeight: 'bold', color: '#fff' }}>
                      €{parseFloat(bchPrice.last).toFixed(2)}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '18px', color: bchPrice.percentageChange >= 0 ? '#4CAF50' : '#f44336' }}>
                      {bchPrice.percentageChange >= 0 ? '↑' : '↓'} {Math.abs(parseFloat(bchPrice.percentageChange)).toFixed(2)}%
                    </div>
                    <div style={{ fontSize: '12px', color: '#888' }}>24h change</div>
                  </div>
                </div>
              </div>
            )}

            {/* Monitor Status */}
            {monitorStatus && (
              <div style={{
                background: monitorStatus.running ? 'rgba(76, 175, 80, 0.1)' : 'rgba(158, 158, 158, 0.1)',
                border: `1px solid ${monitorStatus.running ? 'rgba(76, 175, 80, 0.3)' : 'rgba(158, 158, 158, 0.3)'}`,
                borderRadius: '8px',
                padding: '16px',
                marginBottom: '16px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '24px' }}>{monitorStatus.running ? '🟢' : '⚪'}</span>
                  <div>
                    <div style={{ fontWeight: 'bold', color: '#fff' }}>
                      Monitor: {monitorStatus.running ? 'ACTIEF' : 'GESTOPT'}
                    </div>
                    <div style={{ fontSize: '12px', color: '#aaa' }}>
                      {monitorStatus.running ? `Interval: ${monitorStatus.interval_label}` : 'Niet actief'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Wallet Info */}
            {sparkBalance !== null && (
              <div style={{
                background: 'rgba(33, 150, 243, 0.1)',
                border: '1px solid rgba(33, 150, 243, 0.3)',
                borderRadius: '8px',
                padding: '16px'
              }}>
                <div style={{ fontSize: '14px', color: '#aaa', marginBottom: '4px' }}>Spark Vermogen</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2196F3' }}>
                  €{sparkBalance.toFixed(2)}
                </div>
                <div style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>
                  Groeit door trading + donaties · Alles traceerbaar
                </div>
              </div>
            )}

            <p style={{ marginTop: '16px', fontSize: '13px', color: '#aaa' }}>
              📊 Voor gedetailleerde monitoring: <strong>KERN → Admin → Monitor</strong>
            </p>
          </div>
        )}
      </div>

      <div className="banner-footer">
        <span className="core-version">SPARK CORE 4.0 / 4.1</span>
        <span className="footer-text">Gebouwd met intentie · Transparant · Autonoom</span>
      </div>
    </div>
  );
}

export default SparkInfoBanner;
