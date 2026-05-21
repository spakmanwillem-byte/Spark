/**
 * v5_event_overlay_001 — Event Overlay Renderer
 *
 * Polt elke 2 sec /api/events/active?target=X en toont actieve events
 * als transparante overlay over het kanaal.
 *
 * Usage: <EventOverlay target="community" />
 */
import React, { useEffect, useRef, useState } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function EventOverlay({ target = 'community' }) {
  const [events, setEvents] = useState([]);
  const audioRefs = useRef({});

  // Polling
  useEffect(() => {
    let mounted = true;
    const tick = async () => {
      try {
        const r = await fetch(`${API}/api/events/active?target=${target}`).then(x => x.json());
        if (!mounted) return;
        const now = r.now_ms || Date.now();
        const live = (r.events || []).filter(e => (e.expires_at_ms || 0) > now);
        setEvents(live);
      } catch (e) { /* silent */ }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => { mounted = false; clearInterval(id); };
  }, [target]);

  // Stop audio van events die niet meer in lijst staan
  useEffect(() => {
    const liveIds = new Set(events.map(e => e.id));
    Object.keys(audioRefs.current).forEach(id => {
      if (!liveIds.has(id)) {
        try { audioRefs.current[id].pause(); audioRefs.current[id].src = ''; } catch (e) { /* ignore */ }
        delete audioRefs.current[id];
      }
    });
  }, [events]);

  if (events.length === 0) return null;

  return (
    <div data-testid="event-overlay-stack" className="fixed inset-0 pointer-events-none z-40 flex items-center justify-center">
      {events.map(evt => <SingleOverlay key={evt.id} evt={evt} audioRefs={audioRefs} />)}
    </div>
  );
}

function SingleOverlay({ evt, audioRefs }) {
  const [phase, setPhase] = useState('in'); // 'in' | 'hold' | 'out'
  const fade = evt.fade_ms || 600;
  const duration = evt.duration_ms || 8000;
  const media = evt.media || {};

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('hold'), fade);
    const t2 = setTimeout(() => setPhase('out'), duration - fade);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [fade, duration]);

  // Audio handling
  useEffect(() => {
    if (!media.sound_url) return;
    const url = media.sound_url.startsWith('http') ? media.sound_url : `${API}${media.sound_url}`;
    const a = new Audio(url);
    a.loop = !!media.sound_loop;
    a.volume = 0.4;
    a.play().catch(() => { /* autoplay block — skip */ });
    audioRefs.current[evt.id] = a;
    return () => {
      try { a.pause(); a.src = ''; } catch (e) { /* ignore */ }
    };
  }, [evt.id, media.sound_url, media.sound_loop, audioRefs]);

  const opacity = phase === 'hold' ? 1 : 0;
  const imgUrl = media.image_url
    ? (media.image_url.startsWith('http') ? media.image_url : `${API}${media.image_url}`)
    : null;

  return (
    <div data-testid={`event-overlay-${evt.id}`}
      className="absolute inset-0 flex items-center justify-center transition-opacity"
      style={{ opacity, transitionDuration: `${fade}ms` }}>
      <div className="pointer-events-auto bg-slate-950/85 backdrop-blur-md border border-amber-500/40 rounded-2xl shadow-2xl shadow-amber-500/20 max-w-md w-full mx-4 p-6 text-center">
        {imgUrl && (
          <img src={imgUrl} alt={media.image_alt || evt.begrip}
            className="w-32 h-32 mx-auto rounded-xl object-cover mb-4 border border-amber-500/30 shadow-lg" />
        )}
        <h3 className="text-xl font-bold text-amber-400 mb-2">{evt.begrip}</h3>
        {evt.lagen_preview && (
          <p className="text-sm text-slate-300 italic leading-relaxed">{evt.lagen_preview}</p>
        )}
        {evt.triggered_by && (
          <p className="text-[10px] text-slate-600 mt-3">→ {evt.triggered_by}</p>
        )}
      </div>
    </div>
  );
}
