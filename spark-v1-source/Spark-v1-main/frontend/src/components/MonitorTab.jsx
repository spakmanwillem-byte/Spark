import React, { useState, useEffect, useRef } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/monitoring`;

function MonitorTab() {
  const [status, setStatus] = useState({
    running: false,
    paused: false,
    cycles_completed: 0,
    uptime_seconds: null,
    thread_alive: false,
    interval_seconds: 10,
    interval_label: null
  });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [selectedInterval, setSelectedInterval] = useState(3600); // Default 1 uur
  const [renderKey, setRenderKey] = useState(0); // Force re-render key
  
  // Use ref to prevent polling after stop
  const pollingEnabled = useRef(true);
  const justStopped = useRef(false);
  
  const [trades, setTrades] = useState([]);
  const [tradesLoading, setTradesLoading] = useState(false);
  const [tradePeriod, setTradePeriod] = useState('today'); // today, week, month
  const [lastTradeId, setLastTradeId] = useState(null); // Track nieuwe trades
  
  // Decision feed state
  const [decisions, setDecisions] = useState([]);
  const [decisionsLoading, setDecisionsLoading] = useState(false);
  const [lastDecisionId, setLastDecisionId] = useState(null);
  const [showOnlySignals, setShowOnlySignals] = useState(false); // Filter: alleen BUY/SELL
  
  // Candle countdown state
  const [countdown, setCountdown] = useState({ minutes: 0, seconds: 0, percentage: 0 });

  // Interval options (voor trading candles)
  const intervalOptions = [
    { value: 60, label: "1 min candle" },
    { value: 300, label: "5 min candle" },
    { value: 900, label: "15 min candle" },
    { value: 3600, label: "1 uur candle" },
    { value: 14400, label: "4 uur candle" },
    { value: 86400, label: "1 dag candle" }
  ];

  useEffect(() => {
    fetchStatus();
    fetchTrades();
    fetchDecisions(); // Initial fetch
    
    // Auto-refresh elke 10 seconden (rustiger)
    const interval = setInterval(() => {
      if (pollingEnabled.current && !justStopped.current) {
        fetchStatus();
        // Decisions altijd updaten (ook als niet running)
        fetchDecisions();
        // Trades alleen als monitor draait
        if (status.running) {
          fetchTrades();
        }
      }
    }, 10000); // 10 seconden
    return () => clearInterval(interval);
  }, [tradePeriod, status.running]);
  
  // Auto-restart wanneer interval verandert tijdens running
  useEffect(() => {
    if (status.running && status.interval_seconds !== selectedInterval) {
      console.log(`⚠️ Interval mismatch: Running op ${status.interval_seconds}s maar ${selectedInterval}s geselecteerd`);
    }
  }, [selectedInterval, status.running, status.interval_seconds]);
  
  // Candle countdown timer - gebaseerd op real-time klok
  useEffect(() => {
    const timer = setInterval(() => {
      if (status.running && !status.paused && status.interval_seconds) {
        const now = Math.floor(Date.now() / 1000);
        const intervalSec = status.interval_seconds;
        
        // Bereken wanneer de huidige candle sluit (gebaseerd op epoch time)
        // Candles sluiten op vaste intervallen (bijv. 00:00, 00:15, 00:30 voor 15 min)
        const secondsSinceEpoch = now;
        const currentCandleStart = Math.floor(secondsSinceEpoch / intervalSec) * intervalSec;
        const nextCandleStart = currentCandleStart + intervalSec;
        const secondsUntilNext = nextCandleStart - secondsSinceEpoch;
        
        const minutes = Math.floor(secondsUntilNext / 60);
        const seconds = secondsUntilNext % 60;
        const percentage = ((intervalSec - secondsUntilNext) / intervalSec) * 100;
        
        setCountdown({ minutes, seconds, percentage });
      } else {
        setCountdown({ minutes: 0, seconds: 0, percentage: 0 });
      }
    }, 1000);
    
    return () => clearInterval(timer);
  }, [status.running, status.paused, status.interval_seconds]);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API}/status`);
      setStatus(response.data.status);
    } catch (error) {
      console.error("Error fetching monitor status:", error);
    } finally {
      setLoading(false);
    }
  };


  const fetchTrades = async () => {
    try {
      setTradesLoading(true);
      const response = await axios.get(`${API}/trades`, {
        params: {
          period: tradePeriod,
          limit: 20
        }
      });
      
      if (response.data.success) {
        const newTrades = response.data.trades || [];
        
        // Detect nieuwe trade
        if (newTrades.length > 0) {
          const newestTrade = newTrades[0];
          const tradeId = `${newestTrade.timestamp}-${newestTrade.type}`;
          
          if (lastTradeId && lastTradeId !== tradeId) {
            console.log("🆕 NIEUWE TRADE:", newestTrade.type, newestTrade.amount);
          }
          
          setLastTradeId(tradeId);
        }
        
        setTrades(newTrades);
      }
    } catch (error) {
      console.error("Error fetching trades:", error);
    } finally {
      setTradesLoading(false);
    }
  };

  const fetchDecisions = async () => {
    try {
      setDecisionsLoading(true);
      const response = await axios.get(`${API}/decisions`, {
        params: { limit: 30 }
      });
      
      if (response.data.success) {
        const newDecisions = response.data.decisions || [];
        
        // Detect nieuwe decision
        if (newDecisions.length > 0) {
          const newestDecision = newDecisions[0];
          const decisionId = newestDecision.timestamp;
          
          if (lastDecisionId && lastDecisionId !== decisionId) {
            console.log(`🆕 NIEUWE DECISION: ${newestDecision.action} @ €${newestDecision.price}`);
          }
          
          setLastDecisionId(decisionId);
        }
        
        setDecisions(newDecisions);
      }
    } catch (error) {
      console.error("Error fetching decisions:", error);
    } finally {
      setDecisionsLoading(false);
    }
  };

  const startMonitor = async () => {
    setActionLoading(true);
    justStopped.current = false;
    pollingEnabled.current = true;
    
    try {
      // Als monitor al draait, stop het eerst
      if (status.running) {
        console.log("Monitor draait al, stoppen eerst...");
        await axios.post(`${API}/stop`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Nu starten met nieuw interval
      const response = await axios.post(`${API}/start`, {
        interval: selectedInterval
      });
      
      if (response.data.success) {
        setStatus(response.data.status);
        console.log("✅ Monitor gestart:", response.data.message);
        setTimeout(() => fetchStatus(), 1000);
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      console.error("Error starting monitor:", error);
      alert("Kon monitor niet starten");
    } finally {
      setActionLoading(false);
    }
  };

  const stopMonitor = async () => {
    if (!window.confirm("Weet je zeker dat je de monitor wilt stoppen?")) return;
    
    setActionLoading(true);
    
    // STOP POLLING IMMEDIATELY
    justStopped.current = true;
    pollingEnabled.current = false;
    
    // HARD RESET STATE FIRST (instant UI update)
    const resetState = {
      running: false,
      paused: false,
      cycles_completed: 0,
      uptime_seconds: null,
      thread_alive: false,
      interval_seconds: 3600,
      interval_label: null
    };
    
    setStatus(resetState);
    setCountdown({ minutes: 0, seconds: 0, percentage: 0 });
    
    // FORCE RE-RENDER by changing key
    setRenderKey(prev => prev + 1);
    
    console.log("🛑 Monitor gestopt - UI reset + force re-render");
    
    // Then call backend
    try {
      const response = await axios.post(`${API}/stop`);
      console.log("✅ Backend stop:", response.data.message);
      
      // Re-enable polling after 3 seconds (for future start)
      setTimeout(() => {
        justStopped.current = false;
        pollingEnabled.current = true;
      }, 3000);
      
    } catch (error) {
      console.error("❌ Error stopping monitor:", error);
      
      // Still re-enable polling
      setTimeout(() => {
        justStopped.current = false;
        pollingEnabled.current = true;
      }, 3000);
    } finally {
      setActionLoading(false);
    }
  };

  const pauseMonitor = async () => {
    setActionLoading(true);
    try {
      const response = await axios.post(`${API}/pause`);
      if (response.data.success) {
        setStatus(response.data.status);
        // Force refresh after 1 second
        setTimeout(() => fetchStatus(), 1000);
      }
    } catch (error) {
      console.error("Error pausing monitor:", error);
      alert("Kon monitor niet pauzeren");
    } finally {
      setActionLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    if (!seconds) return "N/A";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const getStatusColor = () => {
    if (!status.running) return "#64748b"; // Gray
    if (status.paused) return "#f59e0b"; // Orange
    return "#10b981"; // Green
  };

  const getStatusText = () => {
    if (!status.running) return "Inactief";
    if (status.paused) return "Gepauzeerd";
    return "Actief";
  };

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#fff" }}>
        <p>Monitor status laden...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px", maxWidth: "800px", margin: "0 auto" }}>
      <h2 style={{ color: "#fff", marginBottom: "10px" }}>📡 Monitor Service</h2>
      <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "30px" }}>
        Spark draait autonoom in de background (blijft actief na UI sluiten)
      </p>

      {/* Status Card */}
      <div style={{
        backgroundColor: "#1e293b",
        padding: "30px",
        borderRadius: "12px",
        border: `2px solid ${getStatusColor()}`,
        marginBottom: "30px"
      }}>
        {/* Status Indicator */}
        <div style={{ 
          display: "flex", 
          alignItems: "center", 
          gap: "15px",
          marginBottom: "25px"
        }}>
          <div style={{
            width: "20px",
            height: "20px",
            borderRadius: "50%",
            backgroundColor: getStatusColor(),
            boxShadow: `0 0 15px ${getStatusColor()}`,
            animation: status.running && !status.paused ? "pulse 2s infinite" : "none"
          }} />
          <div>
            <div style={{ color: "#fff", fontSize: "24px", fontWeight: "bold" }}>
              {getStatusText()}
            </div>
            <div style={{ color: "#94a3b8", fontSize: "12px" }}>
              {status.thread_alive ? "Thread actief" : "Thread inactief"}
            </div>
          </div>
        </div>

        {/* Stats */}
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: "15px",
          marginBottom: "25px"
        }}>
          <div style={{
            backgroundColor: "#0f172a",
            padding: "15px",
            borderRadius: "8px"
          }}>
            <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
              Cycles
            </div>
            <div style={{ color: "#fff", fontSize: "24px", fontWeight: "bold" }}>
              {status.cycles_completed}
            </div>
          </div>
          
          <div style={{
            backgroundColor: "#0f172a",
            padding: "15px",
            borderRadius: "8px"
          }}>
            <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
              Uptime
            </div>
            <div style={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}>
              {formatUptime(status.uptime_seconds)}
            </div>
          </div>
          
          <div style={{
            backgroundColor: "#0f172a",
            padding: "15px",
            borderRadius: "8px"
          }}>
            <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
              Interval
            </div>
            <div style={{ color: "#fff", fontSize: "14px", fontWeight: "bold" }}>
              {status.interval_label || `${status.interval_seconds}s`}
            </div>
          </div>
        </div>

        {/* Candle Countdown */}
        {status.running && !status.paused && (
          <div style={{
            marginTop: "20px",
            padding: "15px",
            backgroundColor: "#0f172a",
            borderRadius: "8px",
            border: "1px solid #3b82f6"
          }}>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px"
            }}>
              <div style={{ color: "#94a3b8", fontSize: "14px" }}>
                ⏱️ Volgende candle check
              </div>
              <div style={{ 
                color: "#3b82f6",
                fontSize: "24px",
                fontWeight: "bold",
                fontFamily: "monospace"
              }}>
                {String(countdown.minutes).padStart(2, '0')}:{String(countdown.seconds).padStart(2, '0')}
              </div>
            </div>
            
            {/* Progress bar */}
            <div style={{
              width: "100%",
              height: "8px",
              backgroundColor: "#1e293b",
              borderRadius: "4px",
              overflow: "hidden"
            }}>
              <div style={{
                width: `${countdown.percentage}%`,
                height: "100%",
                backgroundColor: "#3b82f6",
                transition: "width 1s linear"
              }} />
            </div>
            
            <div style={{
              marginTop: "8px",
              textAlign: "center",
              color: "#64748b",
              fontSize: "12px"
            }}>
              {Math.round(countdown.percentage)}% voltooid • {status.interval_label}
            </div>
          </div>
        )}

        {/* Interval Selector - ALTIJD ENABLED, NOOIT DISABLED */}
        <div style={{ marginBottom: "25px" }}>
          <label style={{ 
            color: "#94a3b8", 
            fontSize: "14px", 
            marginBottom: "10px",
            display: "block"
          }}>
            Tijdschaal (voor candle trading):
          </label>
          <select
            value={selectedInterval}
            onChange={(e) => setSelectedInterval(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "12px",
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "14px",
              cursor: "pointer"
            }}
          >
            {intervalOptions.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          
          {/* Waarschuwing als interval niet matcht met running interval */}
          {status.running && status.interval_seconds !== selectedInterval && (
            <div>
              <p style={{ 
                color: "#f59e0b", 
                fontSize: "12px", 
                marginTop: "8px",
                padding: "8px",
                backgroundColor: "#f59e0b20",
                borderRadius: "6px",
                border: "1px solid #f59e0b40"
              }}>
                ⚠️ Monitor draait op <strong>{status.interval_label}</strong>. 
                Klik hieronder om te switchen naar <strong>{intervalOptions.find(o => o.value === selectedInterval)?.label}</strong>.
              </p>
              <button
                onClick={async () => {
                  await stopMonitor();
                  setTimeout(async () => {
                    await startMonitor();
                  }, 2000);
                }}
                disabled={actionLoading}
                style={{
                  width: "100%",
                  marginTop: "8px",
                  padding: "10px",
                  backgroundColor: "#3b82f6",
                  color: "#fff",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "14px",
                  fontWeight: "600",
                  cursor: actionLoading ? "not-allowed" : "pointer",
                  opacity: actionLoading ? 0.6 : 1
                }}
              >
                🔄 Stop & Herstart met {intervalOptions.find(o => o.value === selectedInterval)?.label}
              </button>
            </div>
          )}
        </div>

        {/* Controls - SMART BUTTON (Start/Pause/Stop) */}
        <div style={{ 
          display: "flex", 
          gap: "10px",
          flexWrap: "wrap"
        }}>
          <button
            onClick={async () => {
              if (!status.running) {
                // Start monitor
                await startMonitor();
              } else if (status.paused) {
                // Resume (unpause)
                await pauseMonitor();
              } else {
                // Pause
                await pauseMonitor();
              }
            }}
            disabled={actionLoading}
            style={{
              width: "100%",
              padding: "18px 25px",
              backgroundColor: !status.running ? "#10b981" : (status.paused ? "#10b981" : "#f59e0b"),
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              fontSize: "18px",
              fontWeight: "600",
              cursor: actionLoading ? "not-allowed" : "pointer",
              opacity: actionLoading ? 0.6 : 1,
              pointerEvents: 'auto',
              zIndex: 9999
            }}
            type="button"
          >
            {!status.running ? "▶️ Start Monitor" : 
             status.paused ? "▶️ Hervatten" : 
             "⏸️ Pauzeren"}
          </button>
        </div>
      </div>

      {/* Info */}
      <div style={{
        backgroundColor: "#1e293b",
        padding: "20px",
        borderRadius: "8px",
        border: "1px solid #334155"
      }}>
        <h3 style={{ color: "#fff", fontSize: "16px", marginBottom: "15px" }}>
          💡 Chat Commands
        </h3>
        <div style={{ color: "#94a3b8", fontSize: "14px", lineHeight: "1.8" }}>
          <div style={{ marginBottom: "8px" }}>
            <code style={{ 
              backgroundColor: "#0f172a", 
              padding: "4px 8px", 
              borderRadius: "4px",
              color: "#10b981"
            }}>
              run monitor
            </code>
            {" "}- Start de monitor
          </div>
          <div style={{ marginBottom: "8px" }}>
            <code style={{ 
              backgroundColor: "#0f172a", 
              padding: "4px 8px", 
              borderRadius: "4px",
              color: "#f59e0b"
            }}>
              pause monitor
            </code>
            {" "}- Pauzeer/hervat de monitor
          </div>
          <div>
            <code style={{ 
              backgroundColor: "#0f172a", 
              padding: "4px 8px", 
              borderRadius: "4px",
              color: "#ef4444"
            }}>
              stop monitor
            </code>
            {" "}- Stop de monitor
          </div>
        </div>
      </div>


      {/* 🎯 Decision Feed - Bot Beslissingen */}
      <div style={{
        backgroundColor: "#1e293b",
        padding: "25px",
        borderRadius: "12px",
        border: "2px solid #10b981",
        marginTop: "30px"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px"
        }}>
          <h3 style={{ color: "#fff", fontSize: "18px", margin: 0 }}>
            🎯 Bot Beslissingen (Live Feed)
          </h3>
          
          {/* Filter toggle */}
          <button
            onClick={() => setShowOnlySignals(!showOnlySignals)}
            style={{
              padding: "8px 15px",
              backgroundColor: showOnlySignals ? "#10b981" : "#334155",
              color: "#fff",
              border: "none",
              borderRadius: "6px",
              fontSize: "12px",
              cursor: "pointer"
            }}
          >
            {showOnlySignals ? "Toon Alles" : "Alleen Signalen"}
          </button>
        </div>

        <div style={{
          maxHeight: "400px",
          overflowY: "auto",
          paddingRight: "10px"
        }}>
          {decisionsLoading && decisions.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>
              Beslissingen laden...
            </div>
          ) : decisions.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px", color: "#64748b" }}>
              Nog geen beslissingen. Start de monitor om te beginnen.
            </div>
          ) : (
            decisions
              .filter(d => !showOnlySignals || (d.action === 'BUY' || d.action === 'SELL'))
              .map((decision, idx) => {
                const isBuy = decision.action === 'BUY';
                const isSell = decision.action === 'SELL';
                const isHold = decision.action === 'HOLD';
                const isNewest = idx === 0;
                
                const timestamp = new Date(decision.timestamp);
                const timeStr = timestamp.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                
                let bgColor = "#0f172a";
                let borderColor = "#334155";
                let icon = "⏸️";
                let actionColor = "#94a3b8";
                
                if (isBuy) {
                  bgColor = isNewest && decision.executed ? '#10b98130' : '#10b98110';
                  borderColor = '#10b981';
                  icon = decision.executed ? '🟢 ✅' : '🟢';
                  actionColor = '#10b981';
                } else if (isSell) {
                  bgColor = isNewest && decision.executed ? '#ef444430' : '#ef444410';
                  borderColor = '#ef4444';
                  icon = decision.executed ? '🔴 ✅' : '🔴';
                  actionColor = '#ef4444';
                }
                
                return (
                  <div
                    key={decision.timestamp}
                    style={{
                      padding: "15px",
                      marginBottom: "10px",
                      backgroundColor: bgColor,
                      borderRadius: "8px",
                      borderLeft: `4px solid ${borderColor}`,
                      border: isNewest ? `2px solid ${borderColor}` : `1px solid ${borderColor}30`
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                          <span style={{ fontSize: "20px" }}>{icon}</span>
                          <div>
                            <span style={{ 
                              color: actionColor,
                              fontWeight: "bold",
                              fontSize: "16px"
                            }}>
                              {decision.action}
                              {isNewest && <span style={{fontSize: "10px", color: "#f59e0b", marginLeft: "8px"}}>🆕</span>}
                            </span>
                            <span style={{ color: "#64748b", fontSize: "12px", marginLeft: "10px" }}>
                              Cycle #{decision.cycle}
                            </span>
                          </div>
                        </div>
                        
                        <div style={{ color: "#94a3b8", fontSize: "13px", lineHeight: "1.6", marginLeft: "30px" }}>
                          {/* Als in positie: toon entry price en current price */}
                          {decision.position && decision.position.entry_price ? (
                            <>
                              <div style={{ marginBottom: "4px" }}>
                                🔵 Inkoop: <strong style={{color: "#3b82f6"}}>€{decision.position.entry_price.toFixed(2)}</strong>
                              </div>
                              <div style={{ marginBottom: "4px" }}>
                                💰 Huidig: <strong style={{color: "#fff"}}>€{decision.price.toFixed(2)}</strong>
                              </div>
                            </>
                          ) : (
                            <div style={{ marginBottom: "4px" }}>
                              💰 Prijs: <strong style={{color: "#fff"}}>€{decision.price.toFixed(2)}</strong>
                            </div>
                          )}
                          <div style={{ marginBottom: "4px" }}>
                            💡 Reden: <em>{decision.reason}</em>
                          </div>
                          {decision.pnl !== null && decision.pnl !== undefined && typeof decision.pnl === 'number' && (
                            <div style={{ color: decision.pnl >= 0 ? '#10b981' : '#ef4444', fontWeight: "bold" }}>
                              📈 P&L: {decision.pnl >= 0 ? '+' : ''}{decision.pnl.toFixed(2)}%
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div style={{ textAlign: "right", minWidth: "80px" }}>
                        <div style={{ color: "#64748b", fontSize: "11px" }}>
                          {timeStr}
                        </div>
                        {decision.executed && (
                          <div style={{ 
                            color: "#10b981", 
                            fontSize: "10px",
                            marginTop: "4px",
                            fontWeight: "bold"
                          }}>
                            UITGEVOERD
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
          )}
        </div>
      </div>

      {/* 📊 Trade Logs Kader */}
      <div style={{
        backgroundColor: "#1e293b",
        padding: "30px",
        borderRadius: "12px",
        border: "2px solid #3b82f6",
        marginTop: "30px"
      }}>
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px"
        }}>
          <h3 style={{ color: "#fff", fontSize: "18px", fontWeight: "bold" }}>
            📊 Trade Logs
          </h3>
          
          {/* Period Filter */}
          <div style={{ display: "flex", gap: "10px" }}>
            {['today', 'week', 'month'].map(period => (
              <button
                key={period}
                onClick={() => setTradePeriod(period)}
                style={{
                  padding: "8px 16px",
                  backgroundColor: tradePeriod === period ? "#3b82f6" : "#0f172a",
                  color: tradePeriod === period ? "#fff" : "#94a3b8",
                  border: "none",
                  borderRadius: "6px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: "500",
                  transition: "all 0.2s"
                }}
                onMouseEnter={(e) => {
                  if (tradePeriod !== period) {
                    e.target.style.backgroundColor = "#1e293b";
                  }
                }}
                onMouseLeave={(e) => {
                  if (tradePeriod !== period) {
                    e.target.style.backgroundColor = "#0f172a";
                  }
                }}
              >
                {period === 'today' ? 'Vandaag' : period === 'week' ? 'Week' : 'Maand'}
              </button>
            ))}
          </div>
        </div>

        {/* Trade List */}
        {tradesLoading ? (
          <div style={{ textAlign: "center", color: "#94a3b8", padding: "20px" }}>
            Laden...
          </div>
        ) : trades.length === 0 ? (
          <div style={{ textAlign: "center", color: "#64748b", padding: "40px" }}>
            <div style={{ fontSize: "48px", marginBottom: "10px" }}>📭</div>
            <div>Geen trades gevonden voor deze periode</div>
          </div>
        ) : (
          <div style={{
            maxHeight: "400px",
            overflowY: "auto",
            backgroundColor: "#0f172a",
            borderRadius: "8px",
            padding: "15px"
          }}>
            {trades.map((trade, idx) => {
              const isBuy = trade.action === 'BUY';
              const timestamp = new Date(trade.timestamp);
              const timeStr = timestamp.toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
              const dateStr = timestamp.toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' });
              const tradeId = `${trade.timestamp}-${trade.type}`;
              const isNewest = idx === 0; // Eerste trade is altijd de nieuwste
              
              return (
                <div
                  key={idx}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 15px",
                    marginBottom: "8px",
                    backgroundColor: isNewest ? (isBuy ? '#10b98120' : '#ef444420') : "#1e293b",
                    borderRadius: "6px",
                    borderLeft: `4px solid ${isBuy ? '#10b981' : '#ef4444'}`,
                    border: isNewest ? `2px solid ${isBuy ? '#10b981' : '#ef4444'}` : 'none',
                    animation: isNewest ? 'pulse 2s ease-in-out' : 'none'
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
                    <span style={{ fontSize: "24px" }}>
                      {isBuy ? '🟢' : '🔴'}
                    </span>
                    <div>
                      <div style={{ 
                        color: isBuy ? '#10b981' : '#ef4444',
                        fontWeight: "bold",
                        fontSize: "14px"
                      }}>
                        {trade.action} {isNewest && <span style={{fontSize: "10px", color: "#f59e0b"}}>🆕 NIEUW</span>}
                      </div>
                      <div style={{ color: "#64748b", fontSize: "12px" }}>
                        {dateStr} • {timeStr}
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ textAlign: "right" }}>
                    <div style={{ color: "#fff", fontWeight: "bold", fontSize: "16px" }}>
                      €{parseFloat(trade.price || 0).toFixed(2)}
                    </div>
                    {trade.status && (
                      <div style={{ 
                        color: trade.status === 'filled' ? '#10b981' : '#64748b',
                        fontSize: "12px"
                      }}>
                        {trade.status}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        
        {/* Stats Summary */}
        {trades.length > 0 && (
          <div style={{
            marginTop: "20px",
            padding: "15px",
            backgroundColor: "#0f172a",
            borderRadius: "8px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
            gap: "15px"
          }}>
            <div>
              <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
                Totaal Trades
              </div>
              <div style={{ color: "#fff", fontSize: "20px", fontWeight: "bold" }}>
                {trades.length}
              </div>
            </div>
            <div>
              <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
                Buys
              </div>
              <div style={{ color: "#10b981", fontSize: "20px", fontWeight: "bold" }}>
                {trades.filter(t => t.action === 'BUY').length}
              </div>
            </div>
            <div>
              <div style={{ color: "#64748b", fontSize: "12px", marginBottom: "5px" }}>
                Sells
              </div>
              <div style={{ color: "#ef4444", fontSize: "20px", fontWeight: "bold" }}>
                {trades.filter(t => t.action === 'SELL').length}
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}

export default MonitorTab;
