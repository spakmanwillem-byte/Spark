/**
 * PriveCallBark — Lokale UI-shell voor bel/beeld-oproep in privé-chat.
 *
 * Puur visueel. Geen echte verbinding (WebRTC/socket) — dat is een aparte
 * sessie voor de lokale-socket-laag op Odroid. Deze component:
 *   - Toont bark-modal wanneer gebruiker op Phone/Video-icoon klikt
 *   - Laat avatar van gebelde persoon zien tijdens "verbinden" of pauze
 *   - Zwart video-blok als VLC-placeholder (later: local media stream)
 *   - Mute / Camera-toggle / Hangup knoppen (lokale UI-state)
 *   - Glow-rand met --glow-base CSS variabele (kleurschema uit profiel)
 */
import React, { useEffect, useRef, useState } from 'react';
import { UserAvatar } from '../common/UserAvatar';
import { Phone, Video, VideoOff, Mic, MicOff, PhoneOff, Camera } from 'lucide-react';

export function PriveCallBark({ open, mode = 'audio', contact, onClose }) {
  const [muted, setMuted] = useState(false);
  const [videoPaused, setVideoPaused] = useState(false);
  const [callState, setCallState] = useState('connecting'); // connecting | ringing | active | no_answer
  const onCloseRef = useRef(onClose);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);

  useEffect(() => {
    if (!open) return;
    setMuted(false);
    setVideoPaused(false);
    setCallState('connecting');
    const isOnline = contact?.online === true;
    const timers = [];
    // Fake state-progressie zodat de shell "leeft" — echt bellen komt later
    timers.push(setTimeout(() => setCallState('ringing'), 800));
    if (isOnline) {
      timers.push(setTimeout(() => setCallState('active'), 3200));
    } else {
      // Offline: laat 'm 4s overgaan, dan "geen gehoor"
      timers.push(setTimeout(() => setCallState('no_answer'), 4800));
      // Auto-hangup 15s na "no_answer"
      timers.push(setTimeout(() => onCloseRef.current && onCloseRef.current(), 4800 + 15000));
    }
    return () => timers.forEach(clearTimeout);
  }, [open, contact?.id, contact?.online, mode]);

  if (!open || !contact) return null;

  const isVideo = mode === 'video';
  const stateLabel = {
    connecting: 'Verbinden…',
    ringing: 'Overgaan…',
    active: isVideo ? 'In beeld' : 'In gesprek',
    no_answer: 'Geen gehoor',
  }[callState];
  const isNoAnswer = callState === 'no_answer';

  return (
    <div
      data-testid="prive-call-overlay"
      className="fixed inset-0 z-[110] flex items-center justify-center bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        data-testid="prive-call-bark"
        onClick={(e) => e.stopPropagation()}
        className="relative bg-slate-950 border-2 rounded-2xl w-[92vw] max-w-2xl shadow-2xl overflow-hidden"
        style={{
          borderColor: 'var(--glow-base, #f59e0b)',
          boxShadow: '0 0 40px color-mix(in srgb, var(--glow-base, #f59e0b) 45%, transparent)',
        }}
      >
        {/* Header */}
        <div className="h-12 px-4 flex items-center justify-between border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2">
            {isVideo
              ? <Video className="w-4 h-4" style={{ color: 'var(--glow-base, #f59e0b)' }} />
              : <Phone className="w-4 h-4" style={{ color: 'var(--glow-base, #f59e0b)' }} />}
            <span className="text-sm font-semibold text-white">
              {isVideo ? 'Beeldbellen' : 'Bellen'} · {contact.naam}
            </span>
          </div>
          <span
            data-testid="prive-call-state"
            className="text-[11px] px-2 py-0.5 rounded-full"
            style={
              isNoAnswer
                ? { backgroundColor: 'rgba(239,68,68,0.15)', color: '#fca5a5' }
                : {
                    backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 15%, transparent)',
                    color: 'var(--glow-base, #f59e0b)',
                  }
            }
          >
            {stateLabel}
          </span>
        </div>

        {/* Beeld-vlak (VLC placeholder) */}
        <div
          data-testid="prive-call-stage"
          className="relative w-full aspect-video bg-black flex items-center justify-center"
        >
          {/* Avatar tijdens verbinden / paused / audio-only / geen-gehoor */}
          {(!isVideo || videoPaused || callState !== 'active') && (
            <div
              data-testid="prive-call-avatar"
              className={`flex flex-col items-center gap-3 ${isNoAnswer ? 'opacity-60' : 'animate-pulse-slow'}`}
            >
              <div
                className="rounded-2xl p-1"
                style={
                  isNoAnswer
                    ? {
                        backgroundColor: 'rgba(239,68,68,0.15)',
                        boxShadow: '0 0 30px rgba(239,68,68,0.35)',
                        filter: 'grayscale(0.6)',
                      }
                    : {
                        backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 25%, transparent)',
                        boxShadow: '0 0 30px color-mix(in srgb, var(--glow-base, #f59e0b) 60%, transparent)',
                      }
                }
              >
                <UserAvatar
                  user={{
                    id: contact.id,
                    naam: contact.naam,
                    avatar: contact.avatar_ref,
                    gradatie: contact.gradatie,
                  }}
                  size="xl"
                  rounded="rounded-2xl"
                />
              </div>
              <p className="text-slate-300 text-sm font-medium">{contact.naam}</p>
              <p className={`text-xs ${isNoAnswer ? 'text-red-300' : 'text-slate-500'}`}>
                {isNoAnswer
                  ? `${contact.naam} is offline — probeer later opnieuw`
                  : stateLabel}
              </p>
            </div>
          )}

          {/* Actieve video "feed" placeholder (VLC-plek). Geen echte stream. */}
          {isVideo && callState === 'active' && !videoPaused && (
            <div
              data-testid="prive-call-video-placeholder"
              className="absolute inset-0 flex items-center justify-center"
              style={{
                background:
                  'radial-gradient(circle at 30% 30%, rgba(30,30,40,0.9), rgba(0,0,0,1) 70%)',
              }}
            >
              <div className="text-center">
                <Camera className="w-10 h-10 mx-auto mb-2 text-slate-700" />
                <p className="text-slate-600 text-xs">
                  Video-feed placeholder (VLC / lokale cam-koppeling)
                </p>
              </div>
              {/* Eigen zelfbeeld picture-in-picture (leeg blok) */}
              <div
                data-testid="prive-call-self-pip"
                className="absolute bottom-3 right-3 w-28 h-20 rounded-lg border border-slate-700 bg-slate-900/80 flex items-center justify-center"
              >
                <span className="text-[10px] text-slate-500">jij</span>
              </div>
            </div>
          )}

          {/* LIVE-badge wanneer actief */}
          {callState === 'active' && (
            <div className="absolute top-3 left-3 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-red-500/20 border border-red-500/40">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[10px] font-semibold text-red-300">LIVE</span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="h-16 flex items-center justify-center gap-3 bg-slate-900/60 border-t border-slate-800">
          <button
            data-testid="prive-call-mute-btn"
            onClick={() => setMuted((v) => !v)}
            className={`w-11 h-11 rounded-full flex items-center justify-center border transition-colors ${
              muted
                ? 'bg-red-500/20 border-red-500/40 text-red-300'
                : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
            }`}
            title={muted ? 'Microfoon uit' : 'Microfoon aan'}
          >
            {muted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          {isVideo && (
            <button
              data-testid="prive-call-video-toggle-btn"
              onClick={() => setVideoPaused((v) => !v)}
              className={`w-11 h-11 rounded-full flex items-center justify-center border transition-colors ${
                videoPaused
                  ? 'bg-red-500/20 border-red-500/40 text-red-300'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title={videoPaused ? 'Camera aan' : 'Camera uit'}
            >
              {videoPaused ? <VideoOff className="w-4 h-4" /> : <Video className="w-4 h-4" />}
            </button>
          )}

          <button
            data-testid="prive-call-hangup-btn"
            onClick={onClose}
            className="w-12 h-12 rounded-full flex items-center justify-center bg-red-600 hover:bg-red-500 text-white shadow-lg"
            title="Ophangen"
          >
            <PhoneOff className="w-5 h-5" />
          </button>
        </div>

        {/* Footer info */}
        <div className="px-4 py-2 border-t border-slate-800 bg-slate-950">
          <p className="text-[10px] text-slate-500 text-center">
            UI-shell · lokale verbinding volgt in aparte sessie (geen cloud)
          </p>
        </div>
      </div>
    </div>
  );
}
