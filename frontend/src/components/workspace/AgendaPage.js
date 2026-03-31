import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  Calendar, Clock, Plus, ChevronLeft, ChevronRight,
  Check, Circle, AlertCircle, Tag, User, MapPin,
  Bell, Repeat, Trash2, Edit3, MoreHorizontal
} from 'lucide-react';

// Sample data
const initialTasks = [
  { id: 1, title: 'Knowledge Base uitbreiden', date: '2026-03-31', time: '10:00', priority: 'high', done: false, category: 'werk' },
  { id: 2, title: 'Triggers controleren', date: '2026-03-31', time: '14:00', priority: 'medium', done: true, category: 'spark' },
  { id: 3, title: 'Team meeting', date: '2026-04-01', time: '09:00', priority: 'high', done: false, category: 'meeting' },
  { id: 4, title: 'Emotie systeem testen', date: '2026-04-01', time: '11:00', priority: 'low', done: false, category: 'spark' },
  { id: 5, title: 'Documentatie bijwerken', date: '2026-04-02', time: '15:00', priority: 'medium', done: false, category: 'werk' },
];

const initialEvents = [
  { id: 1, title: 'Sprint Planning', date: '2026-03-31', startTime: '09:00', endTime: '10:00', color: 'amber' },
  { id: 2, title: 'Lunch met team', date: '2026-03-31', startTime: '12:00', endTime: '13:00', color: 'green' },
  { id: 3, title: 'Code Review', date: '2026-04-01', startTime: '14:00', endTime: '15:00', color: 'purple' },
  { id: 4, title: 'Workshop AI', date: '2026-04-02', startTime: '10:00', endTime: '12:00', color: 'cyan' },
];

export function AgendaPage({ onNavigate }) {
  const [currentDate, setCurrentDate] = useState(new Date(2026, 2, 31)); // March 31, 2026
  const [tasks, setTasks] = useState(initialTasks);
  const [events] = useState(initialEvents);
  const [view, setView] = useState('week'); // 'day', 'week', 'month'
  const [selectedDate, setSelectedDate] = useState('2026-03-31');

  const daysOfWeek = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'];
  const months = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni', 'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December'];

  const toggleTask = (id) => {
    setTasks(tasks.map(task => 
      task.id === id ? { ...task, done: !task.done } : task
    ));
  };

  const getWeekDates = () => {
    const dates = [];
    const start = new Date(currentDate);
    start.setDate(start.getDate() - start.getDay() + 1); // Start from Monday
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(start);
      date.setDate(start.getDate() + i);
      dates.push(date);
    }
    return dates;
  };

  const weekDates = getWeekDates();

  const formatDateStr = (date) => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };

  const getTasksForDate = (dateStr) => tasks.filter(t => t.date === dateStr);
  const getEventsForDate = (dateStr) => events.filter(e => e.date === dateStr);

  const todayTasks = tasks.filter(t => t.date === selectedDate);
  const todayEvents = events.filter(e => e.date === selectedDate);

  const priorityColors = {
    high: 'text-red-400 bg-red-500/20',
    medium: 'text-amber-400 bg-amber-500/20',
    low: 'text-green-400 bg-green-500/20',
  };

  const categoryColors = {
    werk: 'bg-blue-500',
    spark: 'bg-amber-500',
    meeting: 'bg-purple-500',
    persoonlijk: 'bg-green-500',
  };

  return (
    <MainLayout activePage="calendar" onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <Calendar className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Agenda</h1>
              <p className="text-slate-400">WORKSPACE → Planning & Taken</p>
            </div>
          </div>
          <button className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-xl hover:bg-blue-500/30 transition-colors flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Nieuw Item
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Calendar & Week View */}
          <div className="lg:col-span-2 space-y-6">
            {/* Navigation */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => setCurrentDate(new Date(currentDate.setDate(currentDate.getDate() - 7)))}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <ChevronLeft className="w-5 h-5 text-slate-400" />
                  </button>
                  <h2 className="text-lg font-semibold text-white">
                    {months[currentDate.getMonth()]} {currentDate.getFullYear()}
                  </h2>
                  <button 
                    onClick={() => setCurrentDate(new Date(currentDate.setDate(currentDate.getDate() + 7)))}
                    className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  </button>
                </div>
                <div className="flex gap-1">
                  {['day', 'week', 'month'].map(v => (
                    <button
                      key={v}
                      onClick={() => setView(v)}
                      className={`px-3 py-1 rounded-lg text-sm capitalize ${
                        view === v 
                          ? 'bg-blue-500/20 text-blue-400' 
                          : 'text-slate-400 hover:bg-slate-800'
                      }`}
                    >
                      {v === 'day' ? 'Dag' : v === 'week' ? 'Week' : 'Maand'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Week View */}
              <div className="grid grid-cols-7 gap-2">
                {weekDates.map((date, idx) => {
                  const dateStr = formatDateStr(date);
                  const isSelected = dateStr === selectedDate;
                  const isToday = dateStr === '2026-03-31';
                  const dayTasks = getTasksForDate(dateStr);
                  const dayEvents = getEventsForDate(dateStr);

                  return (
                    <button
                      key={idx}
                      onClick={() => setSelectedDate(dateStr)}
                      className={`p-3 rounded-xl transition-all ${
                        isSelected 
                          ? 'bg-blue-500/20 border-2 border-blue-500/50' 
                          : 'bg-slate-800/50 border-2 border-transparent hover:border-slate-700'
                      }`}
                    >
                      <p className="text-xs text-slate-500 mb-1">{daysOfWeek[idx]}</p>
                      <p className={`text-lg font-bold ${
                        isToday ? 'text-blue-400' : 'text-white'
                      }`}>
                        {date.getDate()}
                      </p>
                      {(dayTasks.length > 0 || dayEvents.length > 0) && (
                        <div className="flex gap-1 mt-2 justify-center">
                          {dayEvents.length > 0 && (
                            <span className="w-2 h-2 bg-purple-500 rounded-full" />
                          )}
                          {dayTasks.length > 0 && (
                            <span className="w-2 h-2 bg-amber-500 rounded-full" />
                          )}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Day Timeline */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-400" />
                {selectedDate === '2026-03-31' ? 'Vandaag' : selectedDate}
              </h3>
              
              <div className="space-y-3">
                {/* Events */}
                {todayEvents.map(event => (
                  <div 
                    key={event.id}
                    className={`flex items-center gap-4 p-4 rounded-xl border-l-4 bg-slate-800/50 border-${event.color}-500`}
                  >
                    <div className="text-center">
                      <p className="text-sm font-medium text-white">{event.startTime}</p>
                      <p className="text-xs text-slate-500">{event.endTime}</p>
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-white">{event.title}</p>
                      <p className="text-xs text-slate-500">
                        {event.endTime.split(':')[0] - event.startTime.split(':')[0]} uur
                      </p>
                    </div>
                    <button className="p-2 hover:bg-slate-700 rounded-lg transition-colors">
                      <MoreHorizontal className="w-4 h-4 text-slate-400" />
                    </button>
                  </div>
                ))}

                {/* Empty state */}
                {todayEvents.length === 0 && (
                  <div className="text-center py-8 border-2 border-dashed border-slate-700 rounded-xl">
                    <Calendar className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                    <p className="text-slate-500 text-sm">Geen events gepland</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right: Tasks */}
          <div className="space-y-6">
            {/* Tasks Overview */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <Check className="w-4 h-4 text-blue-400" />
                  Taken
                </h3>
                <span className="text-xs text-slate-500">
                  {tasks.filter(t => t.done).length}/{tasks.length} klaar
                </span>
              </div>

              <div className="space-y-2">
                {todayTasks.map(task => (
                  <div 
                    key={task.id}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                      task.done ? 'bg-slate-800/30' : 'bg-slate-800/50'
                    }`}
                  >
                    <button
                      onClick={() => toggleTask(task.id)}
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                        task.done 
                          ? 'bg-green-500 border-green-500' 
                          : 'border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      {task.done && <Check className="w-3 h-3 text-white" />}
                    </button>
                    <div className="flex-1">
                      <p className={`text-sm ${task.done ? 'text-slate-500 line-through' : 'text-white'}`}>
                        {task.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`w-2 h-2 rounded-full ${categoryColors[task.category]}`} />
                        <span className="text-xs text-slate-500">{task.time}</span>
                      </div>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${priorityColors[task.priority]}`}>
                      {task.priority}
                    </span>
                  </div>
                ))}

                {todayTasks.length === 0 && (
                  <div className="text-center py-6 text-slate-500 text-sm">
                    Geen taken voor deze dag
                  </div>
                )}
              </div>

              {/* Add Task */}
              <button className="w-full mt-4 py-2 border-2 border-dashed border-slate-700 rounded-xl text-slate-500 hover:border-slate-600 hover:text-slate-400 transition-colors flex items-center justify-center gap-2">
                <Plus className="w-4 h-4" />
                Taak toevoegen
              </button>
            </div>

            {/* Upcoming */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Bell className="w-4 h-4 text-blue-400" />
                Binnenkort
              </h3>
              <div className="space-y-3">
                {tasks.filter(t => !t.done && t.date > selectedDate).slice(0, 3).map(task => (
                  <div key={task.id} className="flex items-center gap-3 p-3 bg-slate-800/30 rounded-xl">
                    <div className={`w-2 h-2 rounded-full ${categoryColors[task.category]}`} />
                    <div className="flex-1">
                      <p className="text-sm text-white">{task.title}</p>
                      <p className="text-xs text-slate-500">{task.date}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Categories */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                <Tag className="w-4 h-4 text-blue-400" />
                Categorieën
              </h3>
              <div className="space-y-2">
                {Object.entries(categoryColors).map(([cat, color]) => (
                  <div key={cat} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/50 transition-colors">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${color}`} />
                      <span className="text-sm text-slate-300 capitalize">{cat}</span>
                    </div>
                    <span className="text-xs text-slate-500">
                      {tasks.filter(t => t.category === cat).length}
                    </span>
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
