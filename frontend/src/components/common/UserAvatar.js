// v4_user_avatar_helper_001 — Centrale avatar render
// Toont avatar-image uit users.json `avatar` field met fallback:
//   1. gallery:xxx → /api/avatar/gallery/xxx/image
//   2. user        → /api/avatar/user/{id}/image
//   3. emoji:🎩   → emoji char
//   4. niets       → Vraagteken-avatar (gallery id 31c6dc04a2fd)
//   5. img-load-error → eerste letter van naam in gradient bg
import React, { useState, useEffect } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;
const QUESTION_AVATAR = `${API}/api/avatar/gallery/31c6dc04a2fd/image`;

// Resolve avatar info uit user object
export function resolveAvatar(user) {
  if (!user) return { kind: 'letter', letter: '?' };
  const av = user.avatar || user.avatar_ref;
  if (typeof av === 'string') {
    if (av.startsWith('gallery:')) {
      const gid = av.split(':', 2)[1];
      return { kind: 'image', url: `${API}/api/avatar/gallery/${gid}/image` };
    }
    if (av === 'user' || av.startsWith('upload:')) {
      return { kind: 'image', url: `${API}/api/avatar/user/${user.id}/image` };
    }
    if (av.startsWith('emoji:')) {
      return { kind: 'emoji', emoji: av.split(':', 2)[1] };
    }
  }
  // Geen avatar set → vraagteken-avatar fallback
  return { kind: 'fallback', url: QUESTION_AVATAR, letter: (user.naam || '?').charAt(0).toUpperCase() };
}

const SIZE_CLASSES = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-16 h-16 text-xl',
  xl: 'w-20 h-20 text-2xl',
};

export function UserAvatar({ user, size = 'md', className = '', rounded = 'rounded-xl', showRing = false }) {
  const [errored, setErrored] = useState(false);
  // v6_avatar_live_refresh — cache-buster die wijzigt bij avatar-changed event
  const [bust, setBust] = useState(0);
  const info = resolveAvatar(user);
  const sizeCls = SIZE_CLASSES[size] || SIZE_CLASSES.md;

  // Reset error on user change
  useEffect(() => { setErrored(false); }, [user?.id, user?.avatar]);

  // Listen for global avatar-changed event (dispatched from AvatarPickerPanel)
  useEffect(() => {
    const handler = (e) => {
      // Alleen busten als event van dezelfde user is (of geen user-specificatie heeft)
      if (!e?.detail?.userId || e.detail.userId === user?.id) {
        setBust(Date.now());
        setErrored(false);
      }
    };
    window.addEventListener('avatar-changed', handler);
    return () => window.removeEventListener('avatar-changed', handler);
  }, [user?.id]);

  // Gradient bg per gradatie (zelfde palet als voorheen)
  const grad = user?.gradatie;
  const bgGradient =
    grad === 1 ? 'bg-gradient-to-br from-amber-500 to-orange-600' :
    grad === 2 ? 'bg-gradient-to-br from-amber-500 to-orange-600' :
    grad <= 4 ? 'bg-gradient-to-br from-amber-500 to-orange-600' :
    'bg-gradient-to-br from-slate-600 to-slate-700';

  const baseCls = `${sizeCls} ${rounded} ${className} overflow-hidden flex items-center justify-center font-bold text-white flex-shrink-0 ${showRing ? 'ring-2 ring-slate-700' : ''}`;

  // Render image (gallery/user/fallback)
  if ((info.kind === 'image' || info.kind === 'fallback') && !errored) {
    const src = bust ? `${info.url}${info.url.includes('?') ? '&' : '?'}t=${bust}` : info.url;
    return (
      <div className={baseCls} data-testid={`avatar-${user?.id || 'anon'}`}>
        <img
          src={src}
          alt={user?.naam || ''}
          className={`w-full h-full object-cover`}
          onError={() => setErrored(true)}
        />
      </div>
    );
  }

  if (info.kind === 'emoji') {
    return (
      <div className={`${baseCls} bg-slate-800`} data-testid={`avatar-${user?.id || 'anon'}`}>
        <span className="leading-none">{info.emoji}</span>
      </div>
    );
  }

  // Final fallback: gradient + letter
  const letter = info.letter || (user?.naam || '?').charAt(0).toUpperCase();
  return (
    <div className={`${baseCls} ${bgGradient}`} data-testid={`avatar-${user?.id || 'anon'}-letter`}>
      <span>{letter}</span>
    </div>
  );
}

export default UserAvatar;
