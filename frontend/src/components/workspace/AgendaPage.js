import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  Calendar, Plus, ChevronLeft, ChevronRight,
  Bell, Trash2, Briefcase, Home, Clock
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

// v13d_agenda_scope_001 (sessie 56b) — Privé/Zakelijk + uren-registratie velden.
// Zakelijk-modus toont extra velden: opdrachtgever, onderwerp, pauze. Totaal-uren
// wordt server-side berekend uit (eind - start) - pauze.
const EMPTY_FORM = {
  scope: 'prive',
  titel: '',
  beschrijving: '',
  date: '',
  start_time: '09:00',
  end_time: '17:00',
  pauze_minuten: 30,
  opdrachtgever: '',
  onderwerp: '',
};

export function AgendaPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showNew, setShowNew] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);

  useEffect(() => {
    fetch(`${API}/api/agenda/events/${userId}?viewer_id=${userId}`)
      .then(r => r.json())
      .then(d => { setEvents(d.events || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [userId]);

  const computedUren = React.useMemo(() => {
    if (form.scope !== 'zakelijk' || !form.start_time || !form.end_time) return null;
    const [sh, sm] = form.start_time.split(':').map(Number);
    const [eh, em] = form.end_time.split(':').map(Number);
    let minuten = (eh * 60 + em) - (sh * 60 + sm) - (Number(form.pauze_minuten) || 0);
    if (minuten <= 0) return 0;
    return Math.round((minuten / 60) * 100) / 100;
  }, [form.scope, form.start_time, form.end_time, form.pauze_minuten]);

  const addEvent = async () => {
    if (!form.titel.trim() || !form.date) return;
    const startISO = `${form.date}T${form.start_time || '09:00'}:00`;
    const endISO = form.end_time ? `${form.date}T${form.end_time}:00` : null;
    const body = {
      titel: form.titel,
      beschrijving: form.beschrijving || null,
      date: startISO,
      end_date: endISO,
      scope: form.scope,
    };
    if (form.scope === 'zakelijk') {
      body.pauze_minuten = Number(form.pauze_minuten) || 0;
      body.opdrachtgever = form.opdrachtgever || null;
      body.onderwerp = form.onderwerp || null;
    }
    const res = await fetch(`${API}/api/agenda/events/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.success) {
      setEvents([...events, data.event]);
      setForm(EMPTY_FORM);
      setShowNew(false);
    }
  };

  const deleteEvent = async (id) => {
    const res = await fetch(`${API}/api/agenda/events/${userId}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) setEvents(events.filter(e => e.id !== id));
  };

  const daysOfWeek = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
  const months = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni', 'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December'];

  const getWeekDates = () => {
    const dates = [];
    const start = new Date(currentDate);
    start.setDate(start.getDate() - ((start.getDay() + 6) % 7));
    for (let i = 0; i < 7; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      dates.push(d);
    }
    return dates;
  };

  const fmt = (d) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  const todayStr = fmt(new Date());
  const weekDates = getWeekDates();
  const getEventsForDate = (ds) => events.filter(e => (e.date || '').startsWith(ds));
  const todayEvents = getEventsForDate(selectedDate);

  const prevWeek = () => { const d = new Date(currentDate); d.setDate(d.getDate() - 7); setCurrentDate(d); };
  const nextWeek = () => { const d = new Date(currentDate); d.setDate(d.getDate() + 7); setCurrentDate(d); };

  if (loading) return <MainLayout activePage="calendar" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 rounded-full animate-spin" style={{ borderColor: 'color-mix(in srgb, var(--glow-base) 30%, transparent)', borderTopColor: 'var(--glow-base)' }} /></div></MainLayout>;

  return (
    <MainLayout activePage="calendar" onNavigate={onNavigate}>
      <div data-testid="agenda-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'var(--glow-base)' }}>
              <Calendar className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Agenda</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{events.length} events</p>
            </div>
            <button data-testid="add-event-btn" onClick={() => setShowNew(!showNew)} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'var(--glow-base)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* New event form */}
            {showNew && (
              <div className="p-4 bg-slate-900/60 rounded-xl space-y-3" style={{ borderWidth: '1px', borderStyle: 'solid', borderColor: 'color-mix(in srgb, var(--glow-base) 20%, transparent)' }}>
                {/* Scope toggle */}
                <div className="flex gap-2">
                  <button
                    data-testid="scope-prive-btn"
                    onClick={() => setForm({...form, scope: 'prive'})}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition"
                    style={form.scope === 'prive' ? {
                      background: 'color-mix(in srgb, var(--glow-base) 20%, transparent)',
                      borderWidth: '1px', borderStyle: 'solid',
                      borderColor: 'color-mix(in srgb, var(--glow-base) 50%, transparent)',
                      color: 'var(--glow-base)',
                    } : { background: 'rgba(30,41,59,0.5)', borderWidth: '1px', borderStyle: 'solid', borderColor: 'rgba(51,65,85,0.5)', color: '#94a3b8' }}
                  >
                    <Home className="w-3.5 h-3.5" /> Privé
                  </button>
                  <button
                    data-testid="scope-zakelijk-btn"
                    onClick={() => setForm({...form, scope: 'zakelijk'})}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition ${form.scope === 'zakelijk' ? 'bg-amber-500/20 border border-amber-500/50 text-amber-300' : 'bg-slate-800/50 border border-slate-700/50 text-slate-400'}`}
                  >
                    <Briefcase className="w-3.5 h-3.5" /> Zakelijk
                  </button>
                </div>

                <input data-testid="event-titel" type="text" value={form.titel} onChange={e => setForm({...form, titel: e.target.value})} placeholder="Titel..."
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500" />
                <input type="text" value={form.beschrijving} onChange={e => setForm({...form, beschrijving: e.target.value})} placeholder="Beschrijving..."
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />

                {/* Zakelijk-only velden */}
                {form.scope === 'zakelijk' && (
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      data-testid="event-opdrachtgever"
                      type="text"
                      value={form.opdrachtgever}
                      onChange={e => setForm({...form, opdrachtgever: e.target.value})}
                      placeholder="Opdrachtgever..."
                      className="px-3 py-2 bg-slate-800/50 border border-amber-500/20 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                    />
                    <input
                      data-testid="event-onderwerp"
                      type="text"
                      value={form.onderwerp}
                      onChange={e => setForm({...form, onderwerp: e.target.value})}
                      placeholder="Onderwerp..."
                      className="px-3 py-2 bg-slate-800/50 border border-amber-500/20 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                )}

                {/* Datum + tijden */}
                <div className="grid grid-cols-4 gap-2">
                  <input data-testid="event-date" type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})}
                    className="col-span-2 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none" />
                  <input data-testid="event-start-time" type="time" value={form.start_time} onChange={e => setForm({...form, start_time: e.target.value})}
                    className="px-2 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none" title="Start" />
                  <input data-testid="event-end-time" type="time" value={form.end_time} onChange={e => setForm({...form, end_time: e.target.value})}
                    className="px-2 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none" title="Eind" />
                </div>

                {/* Pauze (alleen zakelijk) + berekende uren */}
                {form.scope === 'zakelijk' && (
                  <div className="flex items-center gap-2">
                    <label className="text-xs text-slate-400 whitespace-nowrap">Pauze (min)</label>
                    <input
                      data-testid="event-pauze"
                      type="number"
                      min="0"
                      value={form.pauze_minuten}
                      onChange={e => setForm({...form, pauze_minuten: e.target.value})}
                      className="w-20 px-2 py-1.5 bg-slate-800/50 border border-amber-500/20 rounded-lg text-sm text-white focus:outline-none"
                    />
                    <div data-testid="computed-uren" className="ml-auto flex items-center gap-1.5 text-xs text-amber-300 bg-amber-500/10 px-2 py-1 rounded-lg">
                      <Clock className="w-3 h-3" />
                      {computedUren !== null ? `${computedUren} uur netto` : '—'}
                    </div>
                  </div>
                )}

                <button data-testid="save-event-btn" onClick={addEvent} className="w-full px-4 py-2 text-white rounded-lg text-xs font-medium transition hover:brightness-110" style={{ background: 'var(--glow-base)' }}>Opslaan</button>
              </div>
            )}

            {/* Week navigation */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <button onClick={prevWeek} className="p-1.5 hover:bg-slate-800 rounded-lg"><ChevronLeft className="w-4 h-4 text-slate-400" /></button>
                <h2 className="text-sm font-semibold text-white">{months[currentDate.getMonth()]} {currentDate.getFullYear()}</h2>
                <button onClick={nextWeek} className="p-1.5 hover:bg-slate-800 rounded-lg"><ChevronRight className="w-4 h-4 text-slate-400" /></button>
              </div>
              <div className="grid grid-cols-7 gap-2">
                {weekDates.map((date, idx) => {
                  const ds = fmt(date);
                  const isSel = ds === selectedDate;
                  const isToday = ds === todayStr;
                  const dayEvents = getEventsForDate(ds);
                  return (
                    <button key={idx} onClick={() => setSelectedDate(ds)}
                      className="p-2.5 rounded-xl transition-all border"
                      style={isSel ? {
                        background: 'color-mix(in srgb, var(--glow-base) 20%, transparent)',
                        borderColor: 'color-mix(in srgb, var(--glow-base) 50%, transparent)',
                      } : { background: 'rgba(30,41,59,0.3)', borderColor: 'transparent' }}
                    >
                      <p className="text-[10px] text-slate-500">{daysOfWeek[idx]}</p>
                      <p className="text-base font-bold" style={{ color: isToday ? 'var(--glow-base)' : '#ffffff' }}>{date.getDate()}</p>
                      {dayEvents.length > 0 && <span className="block w-1.5 h-1.5 rounded-full mx-auto mt-1" style={{ background: 'var(--glow-base)' }} />}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Events for selected date */}
            <div className="space-y-2">
              <p className="text-xs text-slate-500 font-medium px-1">{selectedDate === todayStr ? 'Vandaag' : selectedDate} — {todayEvents.length} event{todayEvents.length !== 1 ? 's' : ''}</p>
              {todayEvents.map(ev => {
                const time = ev.date ? new Date(ev.date).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : '';
                const endTime = ev.end_date ? new Date(ev.end_date).toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' }) : null;
                const isZakelijk = ev.scope === 'zakelijk';
                return (
                  <div key={ev.id} data-testid={`event-${ev.id}`} className={`flex items-center gap-3 p-3 rounded-xl transition-colors border ${isZakelijk ? 'bg-amber-950/20 border-amber-500/20 hover:border-amber-500/40' : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'}`}>
                    <div className="w-14 text-center flex-shrink-0">
                      <p className="text-xs font-medium" style={{ color: isZakelijk ? '#fbbf24' : 'var(--glow-base)' }}>{time}</p>
                      {endTime && <p className="text-[10px] text-slate-500">tot {endTime}</p>}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium text-white truncate">{ev.titel}</p>
                        {isZakelijk && (
                          <span className="inline-flex items-center gap-1 text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 font-medium uppercase tracking-wider">
                            <Briefcase className="w-2.5 h-2.5" /> Zakelijk
                          </span>
                        )}
                      </div>
                      {isZakelijk && (ev.opdrachtgever || ev.onderwerp) && (
                        <p className="text-[11px] text-amber-300/80 truncate">
                          {ev.opdrachtgever ? `${ev.opdrachtgever}` : ''}
                          {ev.opdrachtgever && ev.onderwerp ? ' · ' : ''}
                          {ev.onderwerp || ''}
                        </p>
                      )}
                      {ev.beschrijving && <p className="text-[11px] text-slate-400 truncate">{ev.beschrijving}</p>}
                      {isZakelijk && ev.totaal_uren != null && (
                        <p className="text-[10px] text-amber-400/70 mt-0.5">
                          <Clock className="w-2.5 h-2.5 inline-block mr-0.5" />
                          {ev.totaal_uren} uur netto (pauze {ev.pauze_minuten || 0} min)
                        </p>
                      )}
                    </div>
                    <button onClick={() => deleteEvent(ev.id)} className="p-1.5 hover:bg-red-500/10 text-slate-600 hover:text-red-400 rounded-lg"><Trash2 className="w-3.5 h-3.5" /></button>
                  </div>
                );
              })}
              {todayEvents.length === 0 && (
                <div className="py-8 text-center border border-dashed border-slate-800 rounded-xl">
                  <Calendar className="w-8 h-8 text-slate-700 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">Geen events voor deze dag</p>
                </div>
              )}
            </div>

            {/* All upcoming */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Bell className="w-4 h-4" style={{ color: 'var(--glow-base)' }} /> Alle Events</h3>
              <div className="space-y-2">
                {events.sort((a,b) => (a.date||'').localeCompare(b.date||'')).map(ev => (
                  <div key={ev.id} className="flex items-center gap-3 p-2 bg-slate-800/30 rounded-lg">
                    <span className="text-[10px] text-slate-500 w-20 flex-shrink-0">{ev.date ? new Date(ev.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' }) : '?'}</span>
                    <span className="text-xs text-white flex-1 truncate">{ev.titel}</span>
                    {ev.scope === 'zakelijk' && (
                      <span className="text-[9px] text-amber-300">
                        {ev.totaal_uren != null ? `${ev.totaal_uren}u` : 'zakelijk'}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default AgendaPage;
