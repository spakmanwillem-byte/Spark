/**
 * v6_body_slots_001 — D&D-style Body Slots inventaris voor Persoonskaart
 * 8 visuele slots rondom een silhouet. Klik op een slot → bewerk-popover.
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { X, Save, Trash2 } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const SLOT_FALLBACK = {
  head:      { label: 'Hoofd',     icon: '🎩', x: 50, y: 8,  desc: 'Pet, helm, gedachten' },
  shoulders: { label: 'Schouders', icon: '🧥', x: 50, y: 22, desc: 'Jas, cape, last' },
  chest:     { label: 'Borst',     icon: '❤️', x: 50, y: 38, desc: 'Hart, drager' },
  hands:     { label: 'Handen',    icon: '🤲', x: 18, y: 50, desc: 'Tools, magie, sieraad' },
  waist:     { label: 'Heupen',    icon: '🔑', x: 50, y: 58, desc: 'Riem, sleutels' },
  feet:      { label: 'Voeten',    icon: '👟', x: 50, y: 90, desc: 'Schoenen, pad' },
  aura:      { label: 'Aura',      icon: '✨', x: 82, y: 50, desc: 'Energie, stemming' },
  pocket:    { label: 'Zak',       icon: '💼', x: 50, y: 72, desc: 'Geheim, draag-item' },
};

export function BodySlotsPanel({ userId, personId, initialSlots, onChange }) {
  const [config, setConfig] = useState(SLOT_FALLBACK);
  const [slots, setSlots] = useState(initialSlots || {});
  const [editing, setEditing] = useState(null); // slot_id of null
  const [form, setForm] = useState({ label: '', icon: '', color: '', note: '' });

  useEffect(() => {
    fetch(`${API}/api/persons/body-slots/config`)
      .then(r => r.json())
      .then(d => { if (d?.slots) setConfig(d.slots); })
      .catch(() => {});
  }, []);

  useEffect(() => { setSlots(initialSlots || {}); }, [initialSlots]);

  const openEdit = (slotId) => {
    const cur = slots[slotId] || {};
    setForm({
      label: cur.label || '',
      icon: cur.icon || config[slotId]?.icon || '',
      color: cur.color || '',
      note: cur.note || '',
    });
    setEditing(slotId);
  };

  const saveSlot = async () => {
    if (!form.label.trim()) {
      toast.error('Vul een label in');
      return;
    }
    const item = {
      label: form.label.trim(),
      icon: form.icon || null,
      color: form.color || null,
      note: form.note.trim() || null,
    };
    try {
      const r = await fetch(`${API}/api/persons/cards/${userId}/${personId}/body-slots`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slots: { [editing]: item } }),
      }).then(x => x.json());
      if (r.success) {
        setSlots(r.body_slots || {});
        onChange?.(r.body_slots || {});
        toast.success(`${config[editing]?.label || editing}: ${item.label}`);
        setEditing(null);
      } else {
        toast.error(r.message || 'Opslaan mislukt');
      }
    } catch (e) {
      toast.error('Fout: ' + e.message);
    }
  };

  const clearSlot = async () => {
    try {
      const r = await fetch(`${API}/api/persons/cards/${userId}/${personId}/body-slots/${editing}`, {
        method: 'DELETE',
      }).then(x => x.json());
      if (r.success) {
        setSlots(r.body_slots || {});
        onChange?.(r.body_slots || {});
        toast.success(`${config[editing]?.label || editing} leeggemaakt`);
        setEditing(null);
      }
    } catch (e) {
      toast.error('Fout: ' + e.message);
    }
  };

  const filled = Object.keys(slots).length;
  const total = Object.keys(config).length;

  return (
    <div data-testid="body-slots-panel" className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
          🎭 Body Slots
        </p>
        <span className="text-[10px] text-slate-500">{filled}/{total} bezet</span>
      </div>

      {/* Silhouet met slot-knoppen op absolute posities */}
      <div className="relative w-full aspect-[2/3] max-w-[260px] mx-auto bg-gradient-to-b from-slate-800/40 via-slate-800/20 to-slate-800/40 rounded-xl border border-slate-700/30 overflow-hidden">
        {/* Silhouet-shape via SVG */}
        <svg viewBox="0 0 200 300" className="absolute inset-0 w-full h-full opacity-20">
          <circle cx="100" cy="35" r="22" fill="#f59e0b" />
          <path d="M 70 60 Q 100 55 130 60 L 138 110 L 145 180 L 130 220 L 115 295 L 100 295 L 95 220 L 85 295 L 70 295 L 70 220 L 55 180 L 62 110 Z"
            fill="#f59e0b" />
        </svg>

        {Object.entries(config).map(([slotId, cfg]) => {
          const item = slots[slotId];
          const filled = !!item;
          return (
            <button
              key={slotId}
              data-testid={`body-slot-${slotId}`}
              onClick={() => openEdit(slotId)}
              title={`${cfg.label} — ${cfg.desc}`}
              className={`absolute -translate-x-1/2 -translate-y-1/2 w-10 h-10 rounded-full border-2 flex items-center justify-center text-base transition-all hover:scale-110 ${
                filled
                  ? 'bg-amber-500/30 border-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.4)]'
                  : 'bg-slate-800/80 border-slate-600/50 hover:border-amber-400/50'
              }`}
              style={{
                left: `${cfg.x}%`,
                top: `${cfg.y}%`,
                ...(item?.color ? { borderColor: item.color, boxShadow: `0 0 10px ${item.color}66` } : {}),
              }}
            >
              {item?.icon || cfg.icon}
            </button>
          );
        })}
      </div>

      {/* Inventory legend */}
      <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
        {Object.entries(slots).length === 0 ? (
          <p className="text-[10px] text-slate-500 text-center py-2">
            Klik op een slot om een item toe te voegen
          </p>
        ) : (
          Object.entries(slots).map(([slotId, item]) => (
            <button key={slotId} onClick={() => openEdit(slotId)}
              data-testid={`body-slot-row-${slotId}`}
              className="w-full flex items-center gap-2 px-2 py-1 bg-slate-800/30 hover:bg-slate-800/60 rounded text-left transition-colors">
              <span className="text-sm">{item.icon || config[slotId]?.icon || '•'}</span>
              <span className="text-[10px] text-slate-500 w-16 flex-shrink-0">{config[slotId]?.label || slotId}</span>
              <span className="text-xs text-slate-200 flex-1 truncate">{item.label}</span>
              {item.note && <span className="text-[9px] text-slate-500 italic truncate max-w-[80px]">{item.note}</span>}
            </button>
          ))
        )}
      </div>

      {/* Edit modal */}
      {editing && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setEditing(null)}>
          <div className="bg-slate-900 border border-amber-500/40 rounded-xl p-4 max-w-sm w-full space-y-3"
            onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="text-xl">{config[editing]?.icon}</span>
                {config[editing]?.label || editing}
              </h3>
              <button onClick={() => setEditing(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[10px] text-slate-500 italic">{config[editing]?.desc}</p>

            <div className="space-y-2">
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Label *</label>
                <input data-testid="body-slot-label" type="text"
                  value={form.label} onChange={e => setForm({...form, label: e.target.value})}
                  placeholder="bv. Roadkill Cap"
                  className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white focus:outline-none focus:border-amber-500" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Icoon (emoji)</label>
                  <input data-testid="body-slot-icon" type="text"
                    value={form.icon} onChange={e => setForm({...form, icon: e.target.value})}
                    placeholder="🧢"
                    className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white focus:outline-none focus:border-amber-500" />
                </div>
                <div>
                  <label className="text-[10px] text-slate-400 block mb-1">Kleur</label>
                  <input data-testid="body-slot-color" type="color"
                    value={form.color || '#f59e0b'} onChange={e => setForm({...form, color: e.target.value})}
                    className="w-full h-8 bg-slate-800 border border-slate-700 rounded cursor-pointer" />
                </div>
              </div>
              <div>
                <label className="text-[10px] text-slate-400 block mb-1">Notitie</label>
                <textarea data-testid="body-slot-note"
                  value={form.note} onChange={e => setForm({...form, note: e.target.value})}
                  placeholder="Verhaal achter dit item..."
                  rows={2}
                  className="w-full px-2 py-1.5 bg-slate-800 border border-slate-700 rounded text-xs text-white focus:outline-none focus:border-amber-500 resize-none" />
              </div>
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-slate-800">
              {slots[editing] ? (
                <button data-testid="body-slot-clear" onClick={clearSlot}
                  className="flex items-center gap-1 text-[10px] text-red-400 hover:text-red-300">
                  <Trash2 className="w-3 h-3" /> Slot legen
                </button>
              ) : <span />}
              <button data-testid="body-slot-save" onClick={saveSlot}
                className="flex items-center gap-1 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs rounded-lg">
                <Save className="w-3 h-3" /> Opslaan
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
