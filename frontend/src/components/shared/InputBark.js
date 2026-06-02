/**
 * v6_input_bark_001 — Invoer-bark voor "vul iets in" momenten.
 *
 * Gebruikt het BarkModal frame-variant als basis maar voegt input(s) toe.
 *
 * Velden-formaat (array):
 *   [{ name, type: 'text'|'password'|'select'|'textarea', label, placeholder, options? }]
 *
 * onSubmit krijgt object { fieldName: value, ... }
 */
import React, { useState, useEffect, useMemo } from 'react';
import { BarkModal } from './BarkModal';

export function InputBark({
  open, onClose, begrip, imageUrl, title, text, tone = 'info', variant = 'frame',
  fields = [], onSubmit, submitLabel = 'Versturen', cancelLabel = 'Annuleer',
}) {
  const initial = useMemo(
    () => Object.fromEntries(fields.map(f => [f.name, f.initial ?? ''])),
    [fields],
  );
  const [values, setValues] = useState(initial);

  // Reset on open
  useEffect(() => { if (open) setValues(initial); }, [open, initial]);

  const setField = (name, val) => setValues(v => ({ ...v, [name]: val }));

  const submit = () => {
    onSubmit?.(values);
  };

  // Genereer input-children
  const inputs = (
    <div className="space-y-2 mt-2 text-left">
      {fields.map(f => (
        <div key={f.name}>
          {f.label && (
            <label className="block text-[10px] text-amber-300/80 uppercase tracking-wider mb-1">{f.label}</label>
          )}
          {f.type === 'select' ? (
            <select
              data-testid={`input-bark-${f.name}`}
              value={values[f.name] || ''}
              onChange={e => setField(f.name, e.target.value)}
              className="w-full px-2.5 py-1.5 bg-slate-900/80 border border-amber-700/40 rounded text-xs text-amber-50 focus:border-amber-500/60 outline-none"
            >
              <option value="">{f.placeholder || '— kies —'}</option>
              {(f.options || []).map(o => (
                <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>
                  {typeof o === 'string' ? o : o.label}
                </option>
              ))}
            </select>
          ) : f.type === 'textarea' ? (
            <textarea
              data-testid={`input-bark-${f.name}`}
              value={values[f.name] || ''}
              onChange={e => setField(f.name, e.target.value)}
              placeholder={f.placeholder}
              rows={f.rows || 3}
              className="w-full px-2.5 py-1.5 bg-slate-900/80 border border-amber-700/40 rounded text-xs text-amber-50 focus:border-amber-500/60 outline-none resize-none"
            />
          ) : (
            <input
              data-testid={`input-bark-${f.name}`}
              type={f.type || 'text'}
              value={values[f.name] || ''}
              onChange={e => setField(f.name, e.target.value)}
              onKeyDown={e => e.key === 'Enter' && submit()}
              placeholder={f.placeholder}
              autoFocus={f.autoFocus}
              className="w-full px-2.5 py-1.5 bg-slate-900/80 border border-amber-700/40 rounded text-xs text-amber-50 focus:border-amber-500/60 outline-none"
            />
          )}
        </div>
      ))}
    </div>
  );

  return (
    <BarkModal
      open={open}
      onClose={onClose}
      begrip={begrip}
      imageUrl={imageUrl}
      title={title}
      text={text}
      tone={tone}
      variant={variant}
      primary={{ label: submitLabel, onClick: submit, testId: 'input-bark-submit' }}
      secondary={{ label: cancelLabel, onClick: onClose, testId: 'input-bark-cancel' }}
    >
      {inputs}
    </BarkModal>
  );
}

export default InputBark;
