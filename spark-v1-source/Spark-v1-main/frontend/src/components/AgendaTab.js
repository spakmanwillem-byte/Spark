import React, { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function AgendaTab({ userId }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newEvent, setNewEvent] = useState({
    titel: "",
    date: "",
    time: "",
    beschrijving: "",
    reminder: false
  });
  const [saving, setSaving] = useState(false);
  const [currentMonth, setCurrentMonth] = useState(new Date());

  useEffect(() => {
    fetchEvents();
  }, [userId]);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API}/personal/agenda/${userId}`);
      setEvents(response.data.events || []);
    } catch (error) {
      console.error("Error fetching agenda:", error);
    } finally {
      setLoading(false);
    }
  };

  const addEvent = async () => {
    if (!newEvent.titel.trim() || !newEvent.date) return;

    setSaving(true);
    try {
      const dateTime = newEvent.time 
        ? `${newEvent.date}T${newEvent.time}:00`
        : `${newEvent.date}T12:00:00`;

      await axios.post(`${API}/personal/agenda`, {
        user_id: userId,
        titel: newEvent.titel,
        date: dateTime,
        beschrijving: newEvent.beschrijving || null,
        reminder: newEvent.reminder
      });
      
      // Clear form
      setNewEvent({
        titel: "",
        date: "",
        time: "",
        beschrijving: "",
        reminder: false
      });
      
      // Reload events
      await fetchEvents();
    } catch (error) {
      console.error("Error adding event:", error);
      alert("Kon afspraak niet opslaan");
    } finally {
      setSaving(false);
    }
  };

  // Calendar helpers
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    return { daysInMonth, startingDayOfWeek, year, month };
  };

  const getEventsForDate = (date) => {
    const dateStr = date.toISOString().split('T')[0];
    return events.filter(e => e.date.startsWith(dateStr));
  };

  const { daysInMonth, startingDayOfWeek, year, month } = getDaysInMonth(currentMonth);
  
  const monthNames = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"];
  const dayNames = ["Zo", "Ma", "Di", "Wo", "Do", "Vr", "Za"];

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1));
  };

  const upcomingEvents = events
    .filter(e => new Date(e.date) >= new Date())
    .sort((a, b) => new Date(a.date) - new Date(b.date))
    .slice(0, 5);

  if (loading) {
    return <div className="text-purple-400">Agenda laden...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Add Event Form */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">➕ Nieuwe Afspraak</h3>
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            value={newEvent.titel}
            onChange={(e) => setNewEvent({...newEvent, titel: e.target.value})}
            placeholder="Titel"
            className="px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50"
          />
          <input
            type="date"
            value={newEvent.date}
            onChange={(e) => setNewEvent({...newEvent, date: e.target.value})}
            className="px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:border-purple-500/50"
          />
          <input
            type="time"
            value={newEvent.time}
            onChange={(e) => setNewEvent({...newEvent, time: e.target.value})}
            placeholder="Tijd (optioneel)"
            className="px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white focus:outline-none focus:border-purple-500/50"
          />
          <input
            type="text"
            value={newEvent.beschrijving}
            onChange={(e) => setNewEvent({...newEvent, beschrijving: e.target.value})}
            placeholder="Beschrijving (optioneel)"
            className="px-4 py-2 bg-slate-700/50 border border-slate-600/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500/50"
          />
        </div>
        <div className="flex items-center gap-3 mt-4">
          <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
            <input
              type="checkbox"
              checked={newEvent.reminder}
              onChange={(e) => setNewEvent({...newEvent, reminder: e.target.checked})}
              className="w-4 h-4"
            />
            <span className="text-sm">Herinnering</span>
          </label>
          <button
            onClick={addEvent}
            disabled={saving || !newEvent.titel.trim() || !newEvent.date}
            className="ml-auto px-6 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg font-medium hover:from-purple-600 hover:to-pink-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {saving ? "Opslaan..." : "Toevoegen"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2 bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-white">
              {monthNames[month]} {year}
            </h3>
            <div className="flex gap-2">
              <button
                onClick={prevMonth}
                className="px-3 py-1 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded transition-all"
              >
                ←
              </button>
              <button
                onClick={nextMonth}
                className="px-3 py-1 bg-slate-700/50 hover:bg-slate-600/50 text-white rounded transition-all"
              >
                →
              </button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 gap-2">
            {/* Day headers */}
            {dayNames.map(day => (
              <div key={day} className="text-center text-xs font-semibold text-gray-400 pb-2">
                {day}
              </div>
            ))}
            
            {/* Empty cells for days before month starts */}
            {Array.from({ length: startingDayOfWeek }).map((_, i) => (
              <div key={`empty-${i}`} className="aspect-square" />
            ))}
            
            {/* Calendar days */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const day = i + 1;
              const date = new Date(year, month, day);
              const dayEvents = getEventsForDate(date);
              const isToday = new Date().toDateString() === date.toDateString();
              
              return (
                <div
                  key={day}
                  className={`aspect-square p-2 rounded-lg border ${
                    isToday 
                      ? 'bg-purple-500/20 border-purple-500/50' 
                      : 'bg-slate-700/30 border-slate-600/30'
                  } hover:border-purple-500/50 transition-all cursor-pointer relative`}
                >
                  <div className="text-sm text-white font-medium">{day}</div>
                  {dayEvents.length > 0 && (
                    <div className="absolute bottom-1 right-1 w-2 h-2 bg-pink-500 rounded-full" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Upcoming Events */}
        <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">🔜 Aankomend</h3>
          <div className="space-y-3">
            {upcomingEvents.length > 0 ? (
              upcomingEvents.map(event => (
                <div key={event.id} className="bg-slate-700/30 p-3 rounded-lg border border-slate-600/50">
                  <div className="font-medium text-white text-sm">{event.titel}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {new Date(event.date).toLocaleDateString('nl-NL', {
                      day: 'numeric',
                      month: 'short',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </div>
                  {event.beschrijving && (
                    <div className="text-xs text-gray-500 mt-1">{event.beschrijving}</div>
                  )}
                  {event.reminder && (
                    <div className="text-xs text-purple-300 mt-1">🔔 Herinnering aan</div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-sm text-center py-4">Geen aankomende afspraken</p>
            )}
          </div>
        </div>
      </div>

      {/* All Events List */}
      <div className="bg-slate-800/50 backdrop-blur-lg border border-purple-500/20 p-6 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-4">📋 Alle Afspraken</h3>
        {events.length > 0 ? (
          <div className="space-y-2">
            {events.map(event => (
              <div key={event.id} className="bg-slate-700/30 p-4 rounded-lg border border-slate-600/50 hover:border-purple-500/50 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h4 className="font-medium text-white">{event.titel}</h4>
                    {event.beschrijving && (
                      <p className="text-sm text-gray-400 mt-1">{event.beschrijving}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                      <span>📅 {new Date(event.date).toLocaleDateString('nl-NL', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}</span>
                      {event.reminder && <span>🔔 Herinnering</span>}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded text-xs ${
                    event.status === 'upcoming' 
                      ? 'bg-blue-500/20 text-blue-300' 
                      : 'bg-gray-500/20 text-gray-300'
                  }`}>
                    {event.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">Nog geen afspraken. Voeg je eerste event toe! 📅</p>
        )}
      </div>
    </div>
  );
}

// Dagboek Tab Component

export default AgendaTab;
