import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Zap, User, Key, Shield, LogIn, AlertCircle, UserPlus, CheckCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export function LoginForm() {
  const { login, error } = useAuth();
  const [naam, setNaam] = useState('');
  const [sleutelwoord, setSleutelwoord] = useState('');
  const [masterkey, setMasterkey] = useState('');
  const [showMasterkey, setShowMasterkey] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  // v4_self_delete_001: toon alert na account-delete redirect
  const [deletedAlert, setDeletedAlert] = useState(() => {
    if (typeof window === 'undefined') return false;
    return new URLSearchParams(window.location.search).has('deleted');
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setSuccessMsg('');
    
    if (!naam.trim() || !sleutelwoord.trim()) {
      setLocalError('Vul je naam en sleutelwoord in');
      return;
    }

    setIsLoading(true);
    const result = await login(naam, sleutelwoord, masterkey || null);
    setIsLoading(false);

    if (!result.success) {
      setLocalError(result.message);
    }
  };

  // v4_025: Nieuwe gebruiker registratie. Maakt user aan + logt direct in.
  const handleRegister = async () => {
    setLocalError('');
    setSuccessMsg('');
    if (!naam.trim() || !sleutelwoord.trim()) {
      setLocalError('Vul je naam en sleutelwoord in om een account te maken');
      return;
    }
    if (sleutelwoord.length < 4) {
      setLocalError('Sleutelwoord moet minstens 4 tekens zijn');
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch(`${API}/api/auth/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ naam: naam.trim(), sleutelwoord }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        setLocalError(data.detail || data.message || 'Account aanmaken mislukt');
        setIsLoading(false);
        return;
      }
      // Account aangemaakt → meteen inloggen
      setSuccessMsg(`Welkom ${naam}! Je account is aangemaakt (gradatie 7).`);
      const loginResult = await login(naam, sleutelwoord, null);
      if (!loginResult.success) {
        setLocalError('Account is aangemaakt — log nu in.');
      }
    } catch (err) {
      setLocalError('Verbinding mislukt: ' + err.message);
    }
    setIsLoading(false);
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4">
      {/* Animated background — v13 hartslag-dots in primaire kleuren, random posities */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" data-testid="login-glow-dots">
        <div className="absolute w-96 h-96 -top-48 -left-48 bg-amber-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute w-96 h-96 -bottom-48 -right-48 bg-orange-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        {[
          { top: '12%', left: '8%',  color: '#f59e0b', size: 6,  delay: '0s'   },
          { top: '22%', left: '82%', color: '#06b6d4', size: 4,  delay: '0.3s' },
          { top: '68%', left: '18%', color: '#a855f7', size: 5,  delay: '0.6s' },
          { top: '82%', left: '72%', color: '#10b981', size: 4,  delay: '0.9s' },
          { top: '45%', left: '90%', color: '#ec4899', size: 3,  delay: '1.2s' },
          { top: '55%', left: '4%',  color: '#f59e0b', size: 5,  delay: '1.5s' },
          { top: '35%', left: '50%', color: '#3b82f6', size: 3,  delay: '0.4s' },
          { top: '90%', left: '35%', color: '#f97316', size: 6,  delay: '0.7s' },
        ].map((d, i) => (
          <div
            key={i}
            className="absolute rounded-full"
            style={{
              top: d.top, left: d.left,
              width: `${d.size}px`, height: `${d.size}px`,
              backgroundColor: d.color,
              boxShadow: `0 0 ${d.size * 4}px ${d.color}`,
              animation: `heartbeatDot 2.4s ease-in-out infinite`,
              animationDelay: d.delay,
              opacity: 0.6,
            }}
          />
        ))}
        <style>{`
          @keyframes heartbeatDot {
            0%, 40%, 100% { transform: scale(1); opacity: 0.4; }
            15% { transform: scale(1.6); opacity: 0.9; }
            25% { transform: scale(1.2); opacity: 0.7; }
            30% { transform: scale(1.5); opacity: 0.85; }
          }
        `}</style>
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl shadow-lg shadow-amber-500/25 mb-4">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Spark Core</h1>
          <p className="text-slate-400 mt-2">Modulaire AI Assistent</p>
        </div>

        {/* Login Card */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* v4_self_delete_001 — Account verwijderd melding */}
            {deletedAlert && (
              <div className="flex items-start gap-3 p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300" data-testid="account-deleted-alert">
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Account verwijderd</p>
                  <p className="text-xs text-amber-300/80 mt-1">
                    Je account is gewist. Een backup blijft 30 dagen bewaard — neem contact op met de beheerder als je dit wilt terugdraaien.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setDeletedAlert(false);
                    window.history.replaceState({}, '', window.location.pathname);
                  }}
                  className="text-amber-400 hover:text-amber-200 text-lg leading-none"
                >×</button>
              </div>
            )}
            {/* Error Message */}
            {displayError && (
              <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{displayError}</span>
              </div>
            )}
            {/* Success Message */}
            {successMsg && (
              <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400">
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
                <span className="text-sm">{successMsg}</span>
              </div>
            )}

            {/* Naam Input */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">Naam</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="text"
                  value={naam}
                  onChange={(e) => setNaam(e.target.value)}
                  placeholder="Voornaam of volledige naam"
                  className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20 transition-all"
                  data-testid="login-naam-input"
                />
              </div>
            </div>

            {/* Sleutelwoord Input */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">Sleutelwoord</label>
              <div className="relative">
                <Key className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="password"
                  value={sleutelwoord}
                  onChange={(e) => setSleutelwoord(e.target.value)}
                  placeholder="Je persoonlijke sleutelwoord"
                  className="w-full pl-12 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20 transition-all"
                  data-testid="login-sleutelwoord-input"
                />
              </div>
            </div>

            {/* Masterkey Toggle */}
            <div>
              <button
                type="button"
                onClick={() => setShowMasterkey(!showMasterkey)}
                className="text-sm text-slate-500 hover:text-amber-400 transition-colors flex items-center gap-2"
              >
                <Shield className="w-4 h-4" />
                {showMasterkey ? 'Verberg masterkey' : 'Admin toegang'}
              </button>
              
              {showMasterkey && (
                <div className="relative mt-3">
                  <Shield className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-amber-500/50" />
                  <input
                    type="password"
                    value={masterkey}
                    onChange={(e) => setMasterkey(e.target.value)}
                    placeholder="Masterkey"
                    className="w-full pl-12 pr-4 py-3 bg-amber-500/5 border border-amber-500/20 rounded-xl text-amber-400 placeholder-amber-500/30 focus:outline-none focus:border-amber-500/50 focus:ring-2 focus:ring-amber-500/20 transition-all"
                    data-testid="login-masterkey-input"
                  />
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500 text-white font-semibold rounded-xl shadow-lg shadow-amber-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              data-testid="login-submit-btn"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-5 h-5" />
                  Inloggen
                </>
              )}
            </button>

            {/* Register Button (v4_025) */}
            <button
              type="button"
              disabled={isLoading}
              onClick={handleRegister}
              className="w-full py-3 bg-slate-800/60 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
              data-testid="register-btn"
            >
              <UserPlus className="w-4 h-4" />
              Nieuwe gebruiker — start als gast
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 pt-6 border-t border-slate-800 text-center">
            <p className="text-sm text-slate-500">
              Spark Core 2.0 — Modulaire Architectuur
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginForm;
