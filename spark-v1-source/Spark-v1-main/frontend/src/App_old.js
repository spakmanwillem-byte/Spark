import React, { useState, useEffect, useRef } from "react";
import "@/App.css";
import axios from "axios";

// Import all tab components
import AdminTab from "./components/AdminTab";
import AchievementsTab from "./components/AchievementsTab";
import StatusTab from "./components/StatusTab";
import BestandenTab from "./components/BestandenTab";
import AgendaTab from "./components/AgendaTab";
import DagboekTab from "./components/DagboekTab";
import RoadmapTab from "./components/RoadmapTab";
import NotitiesTab from "./components/NotitiesTab";
import ProfielenTab from "./components/ProfielenTab";
import KnowledgeBaseTab from "./components/KnowledgeBaseTab";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [userData, setUserData] = useState(() => {
    try {
      const saved = localStorage.getItem('spark_user_data');
      console.log('[INIT] Loading userData from localStorage:', saved ? 'found' : 'not found');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      console.error('[INIT] Error loading userData:', e);
      return null;
    }
  });
  const [sessionId] = useState(() => {
    // Create persistent session ID for anonymous users
    let sid = localStorage.getItem('spark_session_id');
    if (!sid) {
      sid = 'anon_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('spark_session_id', sid);
    }
    return sid;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");
  const [awaitingPassword, setAwaitingPassword] = useState(null);
  const [forceRender, setForceRender] = useState(0);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  useEffect(() => {
    if (userData) {
      localStorage.setItem('spark_user_data', JSON.stringify(userData));
    } else {
      localStorage.removeItem('spark_user_data');
    }
  }, [userData]);

  // Session heartbeat - keep session alive every 30 seconds
  useEffect(() => {
    if (!userData) return;

    console.log('[HEARTBEAT] Starting session heartbeat for', userData.naam);

    const heartbeatInterval = setInterval(async () => {
      try {
        const response = await axios.post(`${API}/session/heartbeat`, null, {
          params: { user_id: userData.id }
        });
        
        console.log('[HEARTBEAT] Session active, expires in', response.data.expires_in, 'seconds');
      } catch (error) {
        console.error('[HEARTBEAT] Session expired or error:', error);
        
        // Session expired - logout user
        if (error.response?.status === 401) {
          console.log('[HEARTBEAT] Auto-logout due to session expiry');
          
          // Add system message about session expiry
          setMessages(prev => [...prev, {
            content: "⏱️ Je sessie is verlopen na 5 minuten inactiviteit.",
            isUser: false,
            timestamp: new Date().toISOString()
          }]);
          
          // Logout after 1 second
          setTimeout(() => {
            handleLogout();
          }, 1000);
        }
      }
    }, 30000); // Every 30 seconds

    // Cleanup on unmount or logout
    return () => {
      console.log('[HEARTBEAT] Stopping session heartbeat');
      clearInterval(heartbeatInterval);
    };
  }, [userData]);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get(`${API}/system/status`);
      setSystemStatus(response.data);
    } catch (error) {
      console.error("Error fetching system status:", error);
    }
  };

  const handleLogout = () => {
    setUserData(null);
    setMessages([]);
    setAwaitingPassword(null);
    setActiveTab("chat");
    localStorage.removeItem('spark_user_data');
  };

  const sendMessage = async () => {
    console.log('[DEBUG] sendMessage called, inputMessage:', inputMessage);
    if (!inputMessage.trim()) return;

    const userMessage = {
      content: inputMessage,
      isUser: true,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage("");
    setIsLoading(true);

    try {
      console.log('[SEND] Sending message:', currentInput.substring(0, 50));
      console.log('[SEND] Current userData:', userData);
      
      if (awaitingPassword) {
        const password = currentInput.trim();
        let loginMessage = "";
        
        if (awaitingPassword.type === "masterkey") {
          loginMessage = `Ik ben ${awaitingPassword.naam} mijn Masterkey is ${password}`;
        } else {
          loginMessage = `Ik ben ${awaitingPassword.naam} en mijn sleutelwoord is ${password}`;
        }
        
        const response = await axios.post(`${API}/chat`, {
          message: loginMessage,
          user_id: userData?.id || sessionId,
        });

        const sparkMessage = {
          content: response.data.response,
          isUser: false,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, sparkMessage]);

        if (response.data.context) {
          console.log('[LOGIN] Setting userData:', response.data.context);
          setUserData(response.data.context);
          setForceRender(prev => prev + 1);
          setAwaitingPassword(null);
        } else {
          setAwaitingPassword(null);
        }
      } else {
        console.log('[SEND] Calling /api/chat endpoint');
        const response = await axios.post(`${API}/chat`, {
          message: currentInput,
          user_id: userData?.id || sessionId,
        });

        console.log('[SEND] Response received:', {
          hasContext: !!response.data.context,
          response: response.data.response?.substring(0, 50)
        });

        const sparkMessage = {
          content: response.data.response,
          isUser: false,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, sparkMessage]);

        if (response.data.response.includes("Tot ziens") || 
            response.data.response.includes("👋") && currentInput.toLowerCase().includes("afmeld")) {
          setTimeout(() => {
            handleLogout();
          }, 1500);
        }

        if (response.data.response.includes("Wat is je sleutelwoord")) {
          const nameMatch = currentInput.match(/(?:ik ben|mijn naam is)\s+(\w+)/i);
          if (nameMatch) {
            setAwaitingPassword({ naam: nameMatch[1], type: "sleutelwoord" });
          }
        }

        if (response.data.context) {
          console.log('[CHAT] Setting userData:', response.data.context);
          setUserData(response.data.context);
          setForceRender(prev => prev + 1);
          setAwaitingPassword(null);
        }
      }
    } catch (error) {
      console.error("[SEND] Error sending message:", error);
      console.error("[SEND] Error details:", error.response?.data || error.message);
      const errorMessage = {
        content: "Sorry, er ging iets mis. Probeer het opnieuw.",
        isUser: false,
        isError: true,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* Sidebar */}
      <div className="w-64 bg-slate-800/80 backdrop-blur-lg border-r border-slate-700 p-4 flex flex-col">
        <div className="mb-8">
          <div className="relative w-32 h-32 mx-auto mb-4 bg-gradient-to-br from-purple-900/50 to-pink-900/50 rounded-lg p-1">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-lg animate-pulse opacity-50" />
            <div className="absolute inset-1 bg-slate-900 rounded-lg flex items-center justify-center">
              <div className="heartbeat-container">
                <svg viewBox="0 0 100 100" className="w-20 h-20">
                  <g className="heartbeat-line">
                    <polyline
                      points="0,50 20,50 25,30 30,70 35,40 40,60 45,50 100,50"
                      fill="none"
                      stroke="url(#gradient)"
                      strokeWidth="2"
                    />
                  </g>
                  <defs>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#3b82f6" />
                      <stop offset="50%" stopColor="#a855f7" />
                      <stop offset="100%" stopColor="#ec4899" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-center bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            Spark AI
          </h1>
          <p className="text-xs text-center text-gray-400 mt-1">v0.1</p>
        </div>

        <nav className="space-y-2">
          <button
            onClick={() => setActiveTab("chat")}
            className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
              activeTab === "chat"
                ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                : "text-gray-400 hover:bg-slate-700/50"
            }`}
          >
            💬 Chat
          </button>

          {userData && (
            <>
              <button
                onClick={() => setActiveTab("dagboek")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "dagboek"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                📖 Dagboek
              </button>
              <button
                onClick={() => setActiveTab("agenda")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "agenda"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                📅 Agenda
              </button>
              <button
                onClick={() => setActiveTab("bestanden")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "bestanden"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                📁 Bestanden
              </button>
            </>
          )}

          {userData && (
            <button
              onClick={() => setActiveTab("roadmap")}
              className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                activeTab === "roadmap"
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                  : "text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🗺️ Roadmap
            </button>
          )}

          {userData && (
            <button
              onClick={() => setActiveTab("achievements")}
              className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                activeTab === "achievements"
                  ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                  : "text-gray-400 hover:bg-slate-700/50"
              }`}
            >
              🏆 Achievements
            </button>
          )}

          {userData && userData.gradatie === 1 && (
            <>
              <button
                onClick={() => setActiveTab("knowledge")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "knowledge"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                🧠 Knowledge Base
              </button>
              
              <button
                onClick={() => setActiveTab("notities")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "notities"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                📝 Notities
              </button>
              
              <button
                onClick={() => setActiveTab("status")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "status"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                ⚡ Status
              </button>
              <button
                onClick={() => setActiveTab("admin")}
                className={`w-full text-left px-4 py-2 rounded-lg transition-all ${
                  activeTab === "admin"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/50"
                    : "text-gray-400 hover:bg-slate-700/50"
                }`}
              >
                👑 Admin
              </button>
            </>
          )}
        </nav>

        {userData && (
          <div className="mt-auto p-4 bg-slate-700/30 rounded-lg border border-purple-500/20">
            <p className="text-sm text-gray-300 font-medium">{userData.naam}</p>
            <p className="text-xs text-gray-500 mt-1">Ingelogd ✓</p>
            <button
              onClick={handleLogout}
              className="mt-3 w-full px-3 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm rounded-lg border border-red-500/30 transition-all"
            >
              🚪 Afmelden
            </button>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-slate-900">
        {activeTab === "chat" && (
          <>
            <div className="bg-slate-800/80 backdrop-blur-lg border-b border-slate-700 p-4">
              <h2 className="text-xl font-semibold text-white">Chat met Spark</h2>
              <p className="text-sm text-gray-400">
                {userData
                  ? `Ingelogd als ${userData.naam}`
                  : "Niet ingelogd - stel jezelf voor"}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900">
              {messages.length === 0 && (
                <div className="text-center text-gray-400 mt-20">
                  <p className="text-lg mb-2">👋 Welkom bij Spark AI</p>
                  <p className="text-sm">Begin met typen om te starten...</p>
                  <p className="text-xs mt-4 text-gray-500">
                    Tip: Stel jezelf voor met "Ik ben [naam] en mijn sleutelwoord is [woord]"
                  </p>
                </div>
              )}

              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${
                    msg.isUser ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-2xl px-4 py-3 rounded-lg ${
                      msg.isUser
                        ? "bg-purple-500/20 border border-purple-500/50 text-white"
                        : msg.isError
                        ? "bg-red-500/20 border border-red-500/50 text-red-300"
                        : "bg-slate-700/50 border border-slate-600/50 text-gray-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-700/50 border border-slate-600/50 px-4 py-3 rounded-lg">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-100" />
                      <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce delay-200" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="bg-slate-800/50 backdrop-blur-lg border-t border-purple-500/20 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type een bericht..."
                  className="flex-1 px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50"
                />
                <button
                  onClick={sendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  Verzend
                </button>
              </div>
            </div>
          </>
        )}

        {activeTab === "status" && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">⚡ Status</h2>
            {systemStatus && userData ? (
              <StatusTab systemStatus={systemStatus} userData={userData} />
            ) : (
              <p className="text-gray-400">Systeem status laden...</p>
            )}
          </div>
        )}

        {activeTab === "admin" && userData && userData.gradatie === 1 && (
          <div className="p-8 bg-slate-900 min-h-screen">
            <h2 className="text-2xl font-bold text-white mb-6">👑 Admin Panel</h2>
            <AdminTab currentUser={userData} />
          </div>
        )}

        {activeTab === "achievements" && userData && (
          <div className="p-8 bg-slate-900 min-h-screen">
            <AchievementsTab userId={userData.id} isAdmin={userData.gradatie === 1} userName={userData.naam} />
          </div>
        )}

        {activeTab === "dagboek" && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">📖 Dagboek</h2>
            {userData ? (
              <DagboekTab userId={userData.id} />
            ) : (
              <p className="text-gray-400">Je moet ingelogd zijn om je dagboek te bekijken.</p>
            )}
          </div>
        )}

        {activeTab === "agenda" && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">📅 Agenda</h2>
            {userData ? (
              <AgendaTab userId={userData.id} />
            ) : (
              <p className="text-gray-400">Je moet ingelogd zijn om je agenda te bekijken.</p>
            )}
          </div>
        )}

        {activeTab === "roadmap" && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">🗺️ Development Roadmap</h2>
            {userData ? (
              <RoadmapTab />
            ) : (
              <p className="text-gray-400">Je moet ingelogd zijn om de roadmap te bekijken.</p>
            )}
          </div>
        )}

        {activeTab === "bestanden" && (
          <div className="p-8">
            <h2 className="text-2xl font-bold text-white mb-6">📁 Bestanden</h2>
            {userData ? (
              <BestandenTab userId={userData.id} userName={userData.naam} />
            ) : (
              <p className="text-gray-400">Je moet ingelogd zijn om bestanden te bekijken.</p>
            )}
          </div>
        )}

        {activeTab === "knowledge" && userData && userData.gradatie === 1 && (
          <div className="p-8 bg-slate-900 min-h-screen">
            <KnowledgeBaseTab userId={userData.id} isAdmin={userData.gradatie === 1} />
          </div>
        )}

        {activeTab === "notities" && userData && userData.gradatie === 1 && (
          <div className="p-8 bg-slate-900 min-h-screen">
            <NotitiesTab userId={userData.id} userName={userData.naam} />
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
