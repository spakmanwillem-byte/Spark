import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Calendar, Clock, Plus, ChevronLeft, ChevronRight,
  Check, AlertCircle, Tag, Bell, Trash2, MoreHorizontal, X, Save
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const API = process.env.REACT_APP_BACKEND_URL;

export function AgendaPage({ onNavigate }) {
  const { user } = useAuth();
  const userId = user?.id || 'user-001';
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [showNew, setShowNew] = useState(false);
  const [newEvent, setNewEvent] = useState({ titel: '', beschrijving: '', date: '', time: '09:00' });

  useEffect(() => {
    fetch(`${API}/api/agenda/events/${userId}`)
      .then(r => r.json())
      .then(d => { setEvents(d.events || []); setLoading(false); })
      .catch(() => setLoading(false));
  }, [userId]);

  const addEvent = async () => {
    if (!newEvent.titel.trim() || !newEvent.date) return;
    const dateStr = `${newEvent.date}T${newEvent.time || '09:00'}:00`;
    const res = await fetch(`${API}/api/agenda/events/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ titel: newEvent.titel, beschrijving: newEvent.beschrijving || null, date: dateStr }),
    });
    const data = await res.json();
    if (data.success) {
      setEvents([...events, data.event]);
      setNewEvent({ titel: '', beschrijving: '', date: '', time: '09:00' });
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

  if (loading) return <MainLayout activePage="calendar" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="calendar" onNavigate={onNavigate}>
      <div data-testid="agenda-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
              <Calendar className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Agenda</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{events.length} events</p>
            </div>
            <button data-testid="add-event-btn" onClick={() => setShowNew(!showNew)} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* New event form */}
            {showNew && (
              <div className="p-4 bg-slate-900/60 border border-blue-500/20 rounded-xl space-y-3">
                <input data-testid="event-titel" type="text" value={newEvent.titel} onChange={e => setNewEvent({...newEvent, titel: e.target.value})} placeholder="Titel..."
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500" />
                <input type="text" value={newEvent.beschrijving} onChange={e => setNewEvent({...newEvent, beschrijving: e.target.value})} placeholder="Beschrijving..."
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none" />
                <div className="flex gap-2">
                  <input data-testid="event-date" type="date" value={newEvent.date} onChange={e => setNewEvent({...newEvent, date: e.target.value})}
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none" />
                  <input type="time" value={newEvent.time} onChange={e => setNewEvent({...newEvent, time: e.target.value})}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white focus:outline-none" />
                  <button data-testid="save-event-btn" onClick={addEvent} className="px-4 py-2 bg-blue-500 text-white rounded-lg text-xs font-medium">Opslaan</button>
                </div>
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
                      className={`p-2.5 rounded-xl transition-all ${isSel ? 'bg-blue-500/20 border border-blue-500/50' : 'bg-slate-800/30 border border-transparent hover:border-slate-700'}`}>
                      <p className="text-[10px] text-slate-500">{daysOfWeek[idx]}</p>
                      <p className={`text-base font-bold ${isToday ? 'text-blue-400' : 'text-white'}`}>{date.getDate()}</p>
                      {dayEvents.length > 0 && <span className="block w-1.5 h-1.5 bg-blue-500 rounded-full mx-auto mt-1" />}
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
                return (
                  <div key={ev.id} data-testid={`event-${ev.id}`} className="flex items-center gap-3 p-3 bg-slate-900/50 border border-slate-800 rounded-xl hover:border-slate-700 transition-colors">
                    <div className="w-10 text-center flex-shrink-0">
                      <p className="text-xs font-medium text-blue-400">{time}</p>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{ev.titel}</p>
                      {ev.beschrijving && <p className="text-[11px] text-slate-400 truncate">{ev.beschrijving}</p>}
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400">{ev.status || 'upcoming'}</span>
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
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2"><Bell className="w-4 h-4 text-blue-400" /> Alle Events</h3>
              <div className="space-y-2">
                {events.sort((a,b) => (a.date||'').localeCompare(b.date||'')).map(ev => (
                  <div key={ev.id} className="flex items-center gap-3 p-2 bg-slate-800/30 rounded-lg">
                    <span className="text-[10px] text-slate-500 w-20 flex-shrink-0">{ev.date ? new Date(ev.date).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short' }) : '?'}</span>
                    <span className="text-xs text-white flex-1 truncate">{ev.titel}</span>
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
