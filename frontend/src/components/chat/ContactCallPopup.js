/**
 * v12_contact_call_001 — WhatsApp/tel deep-link popup.
 *
 * Toont zodra chat-response type='contact_call' terugkomt. User kan:
 *  - WhatsApp openen (deep link)
 *  - Bellen (tel: link)
 *  - Sluiten
 *
 * Placeholder tot echte in-app calling (WebRTC) er is.
 */
import React from 'react';
import { X, MessageCircle, Phone, UserPlus } from 'lucide-react';

export function ContactCallPopup({ action, onClose }) {
  if (!action || action.type !== 'contact_call') return null;
  const found = action.found === true;
  const c = action.contact || {};

  return (
    <div
      data-testid="contact-call-overlay"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        data-testid="contact-call-modal"
        onClick={(e) => e.stopPropagation()}
        className="bg-slate-900 border border-slate-700 rounded-2xl p-6 max-w-md w-[92vw] shadow-2xl"
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-white">
              {found ? `Bel ${c.name}` : 'Contact onbekend'}
            </h3>
            {found && c.relation && (
              <p className="text-xs text-slate-400 mt-0.5">
                relatie: {c.relation} · {c.phone}
              </p>
            )}
          </div>
          <button
            data-testid="contact-call-close"
            onClick={onClose}
            className="text-slate-500 hover:text-white"
            aria-label="Sluiten"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {found ? (
          <>
            <p className="text-sm text-slate-300 mb-5">
              {action.message || `Klik om ${c.name} te bellen.`}
            </p>
            <div className="flex flex-col gap-2">
              {action.whatsapp_link && (
                <a
                  data-testid="contact-call-whatsapp"
                  href={action.whatsapp_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={onClose}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/30 font-medium"
                >
                  <MessageCircle className="w-4 h-4" />
                  Open WhatsApp
                </a>
              )}
              {action.tel_link && (
                <a
                  data-testid="contact-call-tel"
                  href={action.tel_link}
                  onClick={onClose}
                  className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 hover:bg-slate-700 font-medium"
                >
                  <Phone className="w-4 h-4" />
                  Bel direct
                </a>
              )}
              <p className="text-[10px] text-slate-500 text-center mt-2">
                Placeholder — echte in-app calling (WebRTC) komt later.
              </p>
            </div>
          </>
        ) : (
          <>
            <p className="text-sm text-slate-300 mb-4">
              {action.message || `Contact '${action.query}' niet gevonden.`}
            </p>
            <a
              data-testid="contact-call-add"
              href="/beheer"
              onClick={onClose}
              className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-amber-500/20 border border-amber-500/40 text-amber-300 hover:bg-amber-500/30 font-medium"
            >
              <UserPlus className="w-4 h-4" />
              Voeg contact toe in Beheer
            </a>
          </>
        )}
      </div>
    </div>
  );
}
