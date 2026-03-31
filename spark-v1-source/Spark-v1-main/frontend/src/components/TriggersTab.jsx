import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function TriggersTab() {
  const [triggers, setTriggers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all, greeting, action, farewell

  useEffect(() => {
    fetchTriggers();
  }, []);

  const fetchTriggers = async () => {
    try {
      // Fetch knowledge base (heeft 'triggers' array)
      const response = await axios.get(`${API}/knowledge-base`);  // API endpoint
      const kb = response.data;
      
      // Haal triggers uit knowledge_base.json
      let allTriggers = [];
      
      // 1. Triggers uit 'triggers' array (nieuw format)
      if (kb.triggers && Array.isArray(kb.triggers)) {
        allTriggers = [...kb.triggers];
      }
      
      // 2. Triggers uit 'knowledge_entries' (oud format)
      if (kb.knowledge_entries && Array.isArray(kb.knowledge_entries)) {
        const oldFormatTriggers = kb.knowledge_entries.filter(entry => 
          entry.response && ['greeting', 'action', 'farewell', 'response'].includes(entry.type)
        );
        allTriggers = [...allTriggers, ...oldFormatTriggers];
      }
      
      setTriggers(allTriggers);
    } catch (error) {
      console.error("Error fetching triggers:", error);
    } finally {
      setLoading(false);
    }
  };

  const getTypeInfo = (type) => {
    switch (type) {
      case 'greeting':
        return { icon: '👋', label: 'Begroeting', color: '#10b981' };
      case 'farewell':
        return { icon: '👋', label: 'Afscheid', color: '#f59e0b' };
      case 'action':
        return { icon: '⚙️', label: 'Actie', color: '#3b82f6' };
      default:
        return { icon: '❓', label: 'Onbekend', color: '#6b7280' };
    }
  };

  const filteredTriggers = filter === "all" 
    ? triggers 
    : triggers.filter(t => t.type === filter);

  // Group by type
  const groupedTriggers = {
    greeting: triggers.filter(t => t.type === 'greeting'),
    action: triggers.filter(t => t.type === 'action'),
    farewell: triggers.filter(t => t.type === 'farewell')
  };

  if (loading) {
    return (
      <div style={{ padding: "20px", textAlign: "center", color: "#fff" }}>
        <p>Triggers laden...</p>
      </div>
    );
  }

  return (
    <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      <div style={{ marginBottom: "30px" }}>
        <h2 style={{ color: "#fff", marginBottom: "10px" }}>🎯 Triggers Overzicht</h2>
        <p style={{ color: "#94a3b8", fontSize: "14px", marginBottom: "20px" }}>
          Alle triggers die Spark herkent en daarop reageert of acties uitvoert
        </p>

        {/* Stats */}
        <div style={{ 
          display: "flex", 
          gap: "15px", 
          marginBottom: "20px",
          flexWrap: "wrap"
        }}>
          <div style={{
            backgroundColor: "#1e293b",
            padding: "15px 20px",
            borderRadius: "8px",
            border: "1px solid #334155"
          }}>
            <div style={{ color: "#94a3b8", fontSize: "12px" }}>Totaal Triggers</div>
            <div style={{ color: "#fff", fontSize: "24px", fontWeight: "bold" }}>
              {triggers.length}
            </div>
          </div>
          <div style={{
            backgroundColor: "#1e293b",
            padding: "15px 20px",
            borderRadius: "8px",
            border: "1px solid #10b981"
          }}>
            <div style={{ color: "#94a3b8", fontSize: "12px" }}>👋 Begroetingen</div>
            <div style={{ color: "#10b981", fontSize: "24px", fontWeight: "bold" }}>
              {groupedTriggers.greeting.length}
            </div>
          </div>
          <div style={{
            backgroundColor: "#1e293b",
            padding: "15px 20px",
            borderRadius: "8px",
            border: "1px solid #3b82f6"
          }}>
            <div style={{ color: "#94a3b8", fontSize: "12px" }}>⚙️ Acties</div>
            <div style={{ color: "#3b82f6", fontSize: "24px", fontWeight: "bold" }}>
              {groupedTriggers.action.length}
            </div>
          </div>
          <div style={{
            backgroundColor: "#1e293b",
            padding: "15px 20px",
            borderRadius: "8px",
            border: "1px solid #f59e0b"
          }}>
            <div style={{ color: "#94a3b8", fontSize: "12px" }}>👋 Afscheid</div>
            <div style={{ color: "#f59e0b", fontSize: "24px", fontWeight: "bold" }}>
              {groupedTriggers.farewell.length}
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{ 
          display: "flex", 
          gap: "10px", 
          borderBottom: "1px solid #334155",
          paddingBottom: "10px"
        }}>
          {[
            { id: "all", label: "Alles", count: triggers.length },
            { id: "greeting", label: "👋 Begroetingen", count: groupedTriggers.greeting.length },
            { id: "action", label: "⚙️ Acties", count: groupedTriggers.action.length },
            { id: "farewell", label: "👋 Afscheid", count: groupedTriggers.farewell.length }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              style={{
                padding: "8px 16px",
                backgroundColor: filter === tab.id ? "#3b82f6" : "transparent",
                color: filter === tab.id ? "#fff" : "#94a3b8",
                border: "1px solid",
                borderColor: filter === tab.id ? "#3b82f6" : "#334155",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "14px",
                fontWeight: "500"
              }}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Triggers List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
        {filteredTriggers.map(trigger => {
          const typeInfo = getTypeInfo(trigger.type);
          const response = trigger.response || {};
          const triggerWords = response.trigger_words || [];
          const action = response.action;
          const responseText = Array.isArray(response.text) ? response.text[0] : response.text;

          return (
            <div
              key={trigger.begrip}
              style={{
                backgroundColor: "#1e293b",
                padding: "20px",
                borderRadius: "8px",
                border: `1px solid ${typeInfo.color}40`
              }}
            >
              {/* Header */}
              <div style={{ 
                display: "flex", 
                justifyContent: "space-between", 
                alignItems: "center",
                marginBottom: "15px"
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "24px" }}>{typeInfo.icon}</span>
                  <div>
                    <h3 style={{ 
                      color: "#fff", 
                      margin: 0, 
                      fontSize: "16px",
                      fontWeight: "600"
                    }}>
                      {trigger.begrip}
                    </h3>
                    <span style={{
                      padding: "2px 8px",
                      backgroundColor: typeInfo.color + "20",
                      color: typeInfo.color,
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: "500",
                      marginTop: "5px",
                      display: "inline-block"
                    }}>
                      {typeInfo.label}
                    </span>
                  </div>
                </div>
                
                {trigger.usage_count !== undefined && (
                  <div style={{ 
                    color: "#64748b", 
                    fontSize: "12px",
                    textAlign: "right"
                  }}>
                    Gebruikt: {trigger.usage_count}x
                  </div>
                )}
              </div>

              {/* Trigger Words */}
              {triggerWords.length > 0 && (
                <div style={{ marginBottom: "10px" }}>
                  <div style={{ color: "#94a3b8", fontSize: "12px", marginBottom: "5px" }}>
                    Trigger woorden:
                  </div>
                  <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                    {triggerWords.map((word, idx) => (
                      <span
                        key={idx}
                        style={{
                          padding: "4px 10px",
                          backgroundColor: "#0f172a",
                          color: "#cbd5e1",
                          borderRadius: "4px",
                          fontSize: "13px",
                          border: "1px solid #334155"
                        }}
                      >
                        "{word}"
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action or Response */}
              {trigger.type === 'action' ? (
                <div style={{ 
                  backgroundColor: "#0f172a",
                  padding: "12px",
                  borderRadius: "6px",
                  border: "1px solid #334155"
                }}>
                  <div style={{ color: "#94a3b8", fontSize: "12px", marginBottom: "5px" }}>
                    Actie:
                  </div>
                  <div style={{ color: "#3b82f6", fontSize: "14px", fontWeight: "500" }}>
                    {action || "Niet gedefinieerd"}
                  </div>
                  {response.confirmation && (
                    <div style={{ color: "#64748b", fontSize: "12px", marginTop: "5px" }}>
                      Bevestiging: {response.confirmation}
                    </div>
                  )}
                </div>
              ) : responseText && (
                <div style={{ 
                  backgroundColor: "#0f172a",
                  padding: "12px",
                  borderRadius: "6px",
                  border: "1px solid #334155"
                }}>
                  <div style={{ color: "#94a3b8", fontSize: "12px", marginBottom: "5px" }}>
                    Response:
                  </div>
                  <div style={{ color: "#cbd5e1", fontSize: "14px" }}>
                    "{responseText}"
                  </div>
                  {Array.isArray(response.text) && response.text.length > 1 && (
                    <div style={{ color: "#64748b", fontSize: "11px", marginTop: "5px" }}>
                      + {response.text.length - 1} variatie(s)
                    </div>
                  )}
                </div>
              )}

              {/* Definition (collapsed by default) */}
              {trigger.lagen?.laag1 && (
                <details style={{ marginTop: "10px" }}>
                  <summary style={{ 
                    color: "#64748b", 
                    fontSize: "12px", 
                    cursor: "pointer",
                    userSelect: "none"
                  }}>
                    Definitie
                  </summary>
                  <div style={{ 
                    color: "#94a3b8", 
                    fontSize: "13px", 
                    marginTop: "8px",
                    padding: "10px",
                    backgroundColor: "#0f172a",
                    borderRadius: "4px"
                  }}>
                    {trigger.lagen.laag1}
                  </div>
                </details>
              )}
            </div>
          );
        })}

        {filteredTriggers.length === 0 && (
          <div style={{ 
            textAlign: "center", 
            padding: "40px", 
            color: "#64748b" 
          }}>
            Geen triggers gevonden voor filter "{filter}"
          </div>
        )}
      </div>
    </div>
  );
}

export default TriggersTab;
