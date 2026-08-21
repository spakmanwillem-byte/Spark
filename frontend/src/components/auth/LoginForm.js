import React, { useState, useEffect, useMemo } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Zap, User, Key, Shield, LogIn, AlertCircle, UserPlus, CheckCircle } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// v13s_login_glow_config_001 — DEFAULTS (fallback als backend niet reageert of nog geen setting).
// Willem beheert deze via Beheer → Instellingen → Beeld → "Login Glow & Spark-logo".
const LOGIN_GLOW_DEFAULTS = {
  primary: '#f59e0b',
  secondary: '#06b6d4',
  bg_tint: '#0f172a',
  dots_count: 8,
  dots_contrast: 0.6,
  dots_size: 1.0,
  corner_enabled: true,
  corner_a: '#f59e0b',
  corner_b: '#f97316',
  spark_logo_url: null,
};

// Kleuren palet voor de dots (rotatie door de primaire + secundaire tint + accenten)
const DOT_PALETTE = ['#f59e0b', '#06b6d4', '#a855f7', '#10b981', '#ec4899', '#f97316', '#3b82f6', '#22c55e'];

export function LoginForm() {
  const { login, error } = useAuth();
  const [naam, setNaam] = useState('');
  const [sleutelwoord, setSleutelwoord] = useState('');
  const [masterkey, setMasterkey] = useState('');
  const [showMasterkey, setShowMasterkey] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  // v13s_login_glow_config_001 — glow-config uit /api/settings/system (publiek, geen auth)
  const [glow, setGlow] = useState(LOGIN_GLOW_DEFAULTS);
  useEffect(() => {
    fetch(`${API}/api/settings/system`)
      .then(r => r.json())
      .then(d => {
        const s = d.settings || {};
        setGlow({
          primary: s.app_primary_accent || LOGIN_GLOW_DEFAULTS.primary,
          secondary: s.app_secondary_accent || LOGIN_GLOW_DEFAULTS.secondary,
          bg_tint: s.app_background_tint || LOGIN_GLOW_DEFAULTS.bg_tint,
          dots_count: Number.isFinite(s.login_dots_count) ? s.login_dots_count : LOGIN_GLOW_DEFAULTS.dots_count,
          dots_contrast: Number.isFinite(s.login_dots_contrast) ? s.login_dots_contrast : LOGIN_GLOW_DEFAULTS.dots_contrast,
          dots_size: Number.isFinite(s.login_dots_size) ? s.login_dots_size : LOGIN_GLOW_DEFAULTS.dots_size,
          corner_enabled: s.login_corner_glow_enabled !== false,
          corner_a: s.login_corner_glow_color_a || LOGIN_GLOW_DEFAULTS.corner_a,
          corner_b: s.login_corner_glow_color_b || LOGIN_GLOW_DEFAULTS.corner_b,
          spark_logo_url: s.spark_logo_url || null,
        });
      })
      .catch(() => {/* fallback op defaults */});
  }, []);

  // Genereer stabiele random dot posities op basis van count
  const dots = useMemo(() => {
    const seed = (i) => {
      // deterministisch pseudo-random per index zodat re-renders niet flikkeren
      const x = Math.sin(i * 12.9898) * 43758.5453;
      return x - Math.floor(x);
    };
    const arr = [];
    for (let i = 0; i < glow.dots_count; i++) {
      arr.push({
        top: `${5 + seed(i) * 90}%`,
        left: `${5 + seed(i + 100) * 90}%`,
        color: DOT_PALETTE[i % DOT_PALETTE.length],
        size: Math.round(3 + seed(i + 200) * 4) * glow.dots_size,
        delay: `${(seed(i + 300) * 2).toFixed(2)}s`,
      });
    }
    return arr;
  }, [glow.dots_count, glow.dots_size]);

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
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: `linear-gradient(135deg, ${glow.bg_tint}, #0f1728, ${glow.bg_tint})`,
      }}
    >
      {/* v13s_login_glow_config_001 — Animated background: 2 corner glows + N dots
          Beheer: Beheer → Instellingen → Beeld → "Login Glow & Spark-logo" */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none" data-testid="login-glow-dots">
        {glow.corner_enabled && (
          <>
            <div
              className="absolute w-96 h-96 -top-48 -left-48 rounded-full blur-3xl animate-pulse"
              style={{ backgroundColor: glow.corner_a + '1a' /* ~10% opacity */ }}
              data-testid="login-corner-glow-a"
            />
            <div
              className="absolute w-96 h-96 -bottom-48 -right-48 rounded-full blur-3xl animate-pulse"
              style={{ backgroundColor: glow.corner_b + '1a', animationDelay: '1s' }}
              data-testid="login-corner-glow-b"
            />
          </>
        )}
        {dots.map((d, i) => (
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
              opacity: glow.dots_contrast,
            }}
          />
        ))}
        <style>{`
          @keyframes heartbeatDot {
            0%, 40%, 100% { transform: scale(1); opacity: ${(glow.dots_contrast * 0.66).toFixed(2)}; }
            15% { transform: scale(1.6); opacity: ${(glow.dots_contrast * 1.5).toFixed(2)}; }
            25% { transform: scale(1.2); opacity: ${(glow.dots_contrast * 1.15).toFixed(2)}; }
            30% { transform: scale(1.5); opacity: ${(glow.dots_contrast * 1.4).toFixed(2)}; }
          }
        `}</style>
      </div>

      <div className="relative w-full max-w-md">
        {/* v13s_login_glow_config_001 — Spark Logo (systeem-branding uit /api/settings/system) */}
        <div className="text-center mb-8">
          {glow.spark_logo_url ? (
            <img
              src={`${API}${glow.spark_logo_url}`}
              alt="Spark logo"
              data-testid="login-spark-logo"
              className="inline-block w-16 h-16 rounded-2xl mb-4 shadow-lg object-cover"
              style={{ boxShadow: `0 10px 40px -10px ${glow.primary}66` }}
            />
          ) : (
            <div
              data-testid="login-spark-logo-fallback"
              className="inline-flex items-center justify-center w-16 h-16 rounded-2xl shadow-lg mb-4"
              style={{
                background: `linear-gradient(135deg, ${glow.primary}, ${glow.corner_b})`,
                boxShadow: `0 10px 30px -10px ${glow.primary}66`,
              }}
            >
              <Zap className="w-8 h-8 text-white" />
            </div>
          )}
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

            {/* Submit Button — v13s_login_glow_config_001 primary kleur uit systeem */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 text-white font-semibold rounded-xl shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 hover:brightness-110"
              style={{
                background: `linear-gradient(90deg, ${glow.primary}, ${glow.corner_b})`,
                boxShadow: `0 10px 24px -12px ${glow.primary}88`,
              }}
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

            {/* Register Button — v13s_login_glow_config_001 secondary kleur (contrast met primary) */}
            <button
              type="button"
              disabled={isLoading}
              onClick={handleRegister}
              className="w-full py-3 font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 hover:brightness-125"
              style={{
                backgroundColor: `${glow.secondary}20`,
                color: glow.secondary,
                border: `1px solid ${glow.secondary}55`,
                boxShadow: `0 6px 20px -14px ${glow.secondary}88`,
              }}
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
