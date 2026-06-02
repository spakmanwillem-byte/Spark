/**
 * v6_admin_role_001 — Herbruikbare bark-popup modal.
 *
 * Toont een KB-kaart-afbeelding ("bark image") + titel + tekst eronder.
 * Vervangt droge text-alerts door visuele Spark-respons.
 *
 * Props:
 *   open      — boolean
 *   onClose   — () => void
 *   begrip    — string: KB-kaart begrip om afbeelding voor te zoeken (optioneel)
 *   imageUrl  — string: directe image URL (overrules begrip lookup, optioneel)
 *   title     — string: titel boven de tekst
 *   text      — string: hoofdtekst onder de afbeelding
 *   tone      — 'info' | 'success' | 'warn' | 'error' (kleurtoon)
 *   children  — React node (extra content/inputs, b.v. password-input)
 *   primary   — { label, onClick, testId } primaire actie-knop
 *   secondary — { label, onClick, testId } secundaire knop (optioneel)
 */
import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const TONE_STYLES = {
  info:    { ring: 'ring-cyan-500/40',    title: 'text-cyan-200' },
  success: { ring: 'ring-emerald-500/40', title: 'text-emerald-200' },
  warn:    { ring: 'ring-amber-500/40',   title: 'text-amber-200' },
  error:   { ring: 'ring-rose-500/40',    title: 'text-rose-200' },
};

// v6_bark_frame_001 — Leeg ornament-frame als achtergrond (Willem upload)
const FRAME_URL = '/api/system-archive/file/33f6faadf2a6';

export function BarkModal({
  open, onClose, begrip, imageUrl, title, text, tone = 'info', children,
  primary, secondary, variant = 'plain', // 'plain' (default) | 'frame'
}) {
  const [resolvedImg, setResolvedImg] = useState(imageUrl || null);

  useEffect(() => {
    if (!open) return;
    if (imageUrl) { setResolvedImg(imageUrl); return; }
    if (!begrip) { setResolvedImg(null); return; }
    fetch(`${API}/api/admin/bark-image?begrip=${encodeURIComponent(begrip)}`)
      .then(r => r.json())
      .then(d => setResolvedImg(d.image_url || null))
      .catch(() => setResolvedImg(null));
  }, [open, begrip, imageUrl]);

  if (!open) return null;
  const t = TONE_STYLES[tone] || TONE_STYLES.info;

  // v6_bark_frame_001 — Frame variant: ornament-achtergrond + tekst-laag erboven
  if (variant === 'frame') {
    return (
      <div
        data-testid="bark-modal"
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
        onClick={onClose}
      >
        <div
          className="relative aspect-square w-full max-w-lg"
          onClick={e => e.stopPropagation()}
          style={{
            backgroundImage: `url(${API}${FRAME_URL})`,
            backgroundSize: 'contain',
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'center',
          }}
        >
          <button
            data-testid="bark-modal-close"
            onClick={onClose}
            className="absolute right-[10%] top-[8%] z-10 text-amber-300 hover:text-amber-200 p-1.5 rounded-full bg-black/40 backdrop-blur-sm"
          >
            <X className="w-4 h-4" />
          </button>

          {/* Content-layer in het midden van het ornament (waar het donker/leeg is) */}
          <div className="absolute inset-0 flex items-center justify-center px-[18%] py-[20%]">
            <div className="w-full max-h-full overflow-y-auto text-center space-y-3 text-amber-50">
              {resolvedImg && (
                <img
                  data-testid="bark-modal-image"
                  src={`${API}${resolvedImg}`}
                  alt={title || begrip || ''}
                  className="mx-auto max-h-20 w-auto rounded-lg object-contain mb-2 ring-1 ring-amber-500/40"
                />
              )}
              {title && (
                <h3 data-testid="bark-modal-title" className="text-base font-bold text-amber-200 drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
                  {title}
                </h3>
              )}
              {text && (
                <p data-testid="bark-modal-text" className="text-[11px] text-amber-100/90 leading-relaxed whitespace-pre-line drop-shadow-[0_1px_2px_rgba(0,0,0,0.8)]">
                  {text}
                </p>
              )}
              {children && <div className="pt-1">{children}</div>}
              {(primary || secondary) && (
                <div className="flex flex-wrap gap-2 pt-2 justify-center">
                  {secondary && (
                    <button
                      data-testid={secondary.testId || 'bark-modal-secondary'}
                      onClick={secondary.onClick}
                      className="px-3 py-1.5 rounded text-[11px] font-medium bg-slate-900/70 text-amber-200 hover:bg-slate-800 border border-amber-700/40"
                    >
                      {secondary.label}
                    </button>
                  )}
                  {primary && (
                    <button
                      data-testid={primary.testId || 'bark-modal-primary'}
                      onClick={primary.onClick}
                      className="px-3 py-1.5 rounded text-[11px] font-bold bg-amber-500/30 text-amber-100 hover:bg-amber-500/40 border border-amber-400/60 shadow-lg shadow-amber-500/30"
                    >
                      {primary.label}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Default 'plain' variant — bestaande popup
  return (
    <div
      data-testid="bark-modal"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={onClose}
    >
      <div
        className={`relative max-w-md w-full bg-slate-900 border border-slate-700 rounded-2xl ring-2 ${t.ring} shadow-2xl overflow-hidden`}
        onClick={e => e.stopPropagation()}
      >
        <button
          data-testid="bark-modal-close"
          onClick={onClose}
          className="absolute right-3 top-3 z-10 text-slate-400 hover:text-white p-1 rounded-full bg-slate-800/80"
        >
          <X className="w-4 h-4" />
        </button>

        {resolvedImg && (
          <div className="w-full bg-gradient-to-b from-slate-800 to-slate-900 flex items-center justify-center p-6">
            <img
              data-testid="bark-modal-image"
              src={`${API}${resolvedImg}`}
              alt={title || begrip || ''}
              className="max-h-48 w-auto rounded-lg object-contain"
            />
          </div>
        )}

        <div className="p-5 space-y-3">
          {title && (
            <h3 data-testid="bark-modal-title" className={`text-base font-semibold ${t.title}`}>
              {title}
            </h3>
          )}
          {text && (
            <p data-testid="bark-modal-text" className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
              {text}
            </p>
          )}
          {children && <div className="pt-2">{children}</div>}

          {(primary || secondary) && (
            <div className="flex flex-wrap gap-2 pt-3 justify-end">
              {secondary && (
                <button
                  data-testid={secondary.testId || 'bark-modal-secondary'}
                  onClick={secondary.onClick}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                >
                  {secondary.label}
                </button>
              )}
              {primary && (
                <button
                  data-testid={primary.testId || 'bark-modal-primary'}
                  onClick={primary.onClick}
                  className="px-4 py-2 rounded-lg text-xs font-medium bg-purple-500/20 text-purple-200 hover:bg-purple-500/30 border border-purple-500/40"
                >
                  {primary.label}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default BarkModal;
