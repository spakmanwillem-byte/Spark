/**
 * IncomingCallBark — Accept/Decline modal wanneer een lokaal signaal
 * een inkomende oproep meldt. Toont beller-avatar met alert-glow puls.
 */
import React from 'react';
import { UserAvatar } from '../common/UserAvatar';
import { Phone, PhoneOff, Video } from 'lucide-react';

export function IncomingCallBark({ call, caller, onAccept, onDecline }) {
  if (!call) return null;
  const isVideo = call.mode === 'video';
  const name = caller?.naam || 'Onbekende beller';

  return (
    <div
      data-testid="incoming-call-overlay"
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/85 backdrop-blur-sm"
    >
      <div
        data-testid="incoming-call-bark"
        className="relative bg-slate-950 border-2 rounded-2xl w-[92vw] max-w-md shadow-2xl overflow-hidden"
        style={{
          borderColor: 'var(--glow-base, #f59e0b)',
          boxShadow: '0 0 60px color-mix(in srgb, var(--glow-base, #f59e0b) 70%, transparent)',
          animation: 'incomingRing 1.4s ease-in-out infinite',
        }}
      >
        <div className="p-6 flex flex-col items-center gap-4">
          <p className="text-slate-400 text-xs uppercase tracking-widest">Inkomende oproep</p>
          <div
            className="rounded-2xl p-1"
            style={{
              backgroundColor: 'color-mix(in srgb, var(--glow-base, #f59e0b) 30%, transparent)',
              boxShadow: '0 0 40px color-mix(in srgb, var(--glow-base, #f59e0b) 70%, transparent)',
              animation: 'incomingAvatarPulse 1.2s ease-in-out infinite',
            }}
          >
            <UserAvatar
              user={{
                id: caller?.id,
                naam: name,
                avatar: caller?.avatar_ref,
                gradatie: caller?.gradatie,
              }}
              size="xl"
              rounded="rounded-2xl"
            />
          </div>
          <div className="text-center">
            <p className="text-white font-semibold">{name}</p>
            <p className="text-slate-400 text-xs mt-1 flex items-center justify-center gap-1">
              {isVideo ? <Video className="w-3 h-3" /> : <Phone className="w-3 h-3" />}
              {isVideo ? 'wil beeldbellen' : 'belt je'}
            </p>
          </div>
          <div className="flex items-center gap-4 mt-2">
            <button
              data-testid="incoming-call-decline"
              onClick={onDecline}
              className="w-14 h-14 rounded-full flex items-center justify-center bg-red-600 hover:bg-red-500 text-white shadow-lg"
              title="Weigeren"
            >
              <PhoneOff className="w-5 h-5" />
            </button>
            <button
              data-testid="incoming-call-accept"
              onClick={onAccept}
              className="w-14 h-14 rounded-full flex items-center justify-center bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg"
              title="Opnemen"
              style={{ animation: 'incomingAcceptPulse 1s ease-in-out infinite' }}
            >
              {isVideo ? <Video className="w-5 h-5" /> : <Phone className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
      <style>{`
        @keyframes incomingRing {
          0%, 100% { box-shadow: 0 0 60px color-mix(in srgb, var(--glow-base, #f59e0b) 70%, transparent); }
          50% { box-shadow: 0 0 90px color-mix(in srgb, var(--glow-base, #f59e0b) 100%, transparent); }
        }
        @keyframes incomingAvatarPulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes incomingAcceptPulse {
          0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(16,185,129,0.5); }
          50% { transform: scale(1.08); box-shadow: 0 0 0 12px rgba(16,185,129,0); }
        }
      `}</style>
    </div>
  );
}
