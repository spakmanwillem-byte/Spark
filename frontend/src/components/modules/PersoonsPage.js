import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  UsersRound, Plus, Search, User, Heart, Tag, Trash2, Edit3, X, Save,
  ChevronDown, ChevronRight, Link2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { UserAvatar } from '../common/UserAvatar';

const API = process.env.REACT_APP_BACKEND_URL;

const relatieTypes = ['familie', 'vriend', 'collega', 'kennis', 'dochter', 'zoon', 'partner', 'moeder', 'vader', 'broer', 'zus'];
const gradatieLabels = { 1: 'Beheerder', 2: 'Familie', 3: 'Vriend', 4: 'Kennis', 5: 'Onbekend' };
const gradatieColors = { 1: '#f59e0b', 2: '#ec4899', 3: '#22c55e', 4: '#3b82f6', 5: '#64748b' };

export function PersoonsPage({ onNavigate }) {
  const { user, isAdmin } = useAuth();
  const ownerUserId = user?.id || 'user-001';
  // Admin kan een andere user selecteren om zijn persoonskaarten te zien
  const [viewUserId, setViewUserId] = useState(() => {
    try {
      const stored = sessionStorage.getItem('persons_view_user');
      if (stored) {
        sessionStorage.removeItem('persons_view_user');
        return stored;
      }
    } catch {}
    return ownerUserId;
  });
  const [allUsers, setAllUsers] = useState([]);
  const userId = viewUserId;

  const [persons, setPersons] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showNew, setShowNew] = useState(false);
  const [newPerson, setNewPerson] = useState({ naam: '', relatie: '', gradatie: 5, tags: '' });
  const [expandedId, setExpandedId] = useState(null);

  // Laad users lijst voor admin dropdown
  useEffect(() => {
    if (!isAdmin) return;
    fetch(`${API}/api/auth/users`).then(r => r.json()).then(d => setAllUsers(d.users || [])).catch(() => {});
  }, [isAdmin]);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetch(`${API}/api/persons/cards/${userId}`).then(r => r.json()).catch(() => ({ persons: [] })),
      fetch(`${API}/api/persons/relationships/${userId}`).then(r => r.json()).catch(() => ({ relationships: [] })),
    ]).then(([pData, rData]) => {
      setPersons(pData.persons || []);
      setRelationships(rData.relationships || []);
      setLoading(false);
    });
  }, [userId]);

  const filtered = persons.filter(p => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (p.naam || '').toLowerCase().includes(q) || (p.relatie || '').toLowerCase().includes(q) || (p.tags || []).some(t => t.toLowerCase().includes(q));
  });

  const addPerson = async () => {
    if (!newPerson.naam.trim()) return;
    const tags = newPerson.tags ? newPerson.tags.split(',').map(t => t.trim()).filter(Boolean) : [];
    const res = await fetch(`${API}/api/persons/cards/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ naam: newPerson.naam, relatie: newPerson.relatie || null, gradatie: parseInt(newPerson.gradatie), tags }),
    });
    const data = await res.json();
    if (data.success) {
      setPersons([...persons, data.person]);
      setNewPerson({ naam: '', relatie: '', gradatie: 5, tags: '' });
      setShowNew(false);
    }
  };

  const deletePerson = async (id) => {
    const res = await fetch(`${API}/api/persons/cards/${userId}/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) setPersons(persons.filter(p => p.id !== id));
  };

  const byGradatie = {};
  filtered.forEach(p => {
    const g = p.gradatie || 5;
    if (!byGradatie[g]) byGradatie[g] = [];
    byGradatie[g].push(p);
  });

  if (loading) return <MainLayout activePage="persons" onNavigate={onNavigate}><div className="flex items-center justify-center h-full"><div className="w-8 h-8 border-2 border-pink-500/30 border-t-pink-500 rounded-full animate-spin" /></div></MainLayout>;

  return (
    <MainLayout activePage="persons" onNavigate={onNavigate}>
      <div data-testid="persoons-page" className="h-full flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
              <UsersRound className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Persoonskaarten</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{persons.length} personen | {relationships.length} relaties</p>
            </div>
            {/* Admin: user selector */}
            {isAdmin && allUsers.length > 0 && (
              <select
                data-testid="admin-user-selector"
                value={viewUserId}
                onChange={(e) => setViewUserId(e.target.value)}
                className="ml-4 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs text-white focus:outline-none focus:border-pink-500"
                title="Bekijk persoonskaarten van andere gebruiker (admin)"
              >
                {allUsers.map(u => (
                  <option key={u.id} value={u.id}>
                    {u.naam}{u.id === ownerUserId ? ' (jij)' : ''}
                  </option>
                ))}
              </select>
            )}
            <button data-testid="add-person-btn" onClick={() => setShowNew(!showNew)} className="ml-auto flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-white" style={{ background: 'linear-gradient(135deg, #ec4899, #a855f7)' }}>
              <Plus className="w-3.5 h-3.5" /> Nieuw
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            {/* New person form */}
            {showNew && (
              <div className="p-4 bg-slate-900/60 border border-pink-500/20 rounded-xl space-y-3">
                <input data-testid="person-naam" type="text" value={newPerson.naam} onChange={e => setNewPerson({...newPerson, naam: e.target.value})} placeholder="Naam..."
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-pink-500" />
                <div className="flex gap-2">
                  <select value={newPerson.relatie} onChange={e => setNewPerson({...newPerson, relatie: e.target.value})}
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                    <option value="">Relatie kiezen...</option>
                    {relatieTypes.map(r => <option key={r} value={r}>{r}</option>)}
                  </select>
                  <select value={newPerson.gradatie} onChange={e => setNewPerson({...newPerson, gradatie: e.target.value})}
                    className="px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-slate-300 focus:outline-none">
                    {Object.entries(gradatieLabels).map(([k, v]) => <option key={k} value={k}>G{k}: {v}</option>)}
                  </select>
                </div>
                <div className="flex gap-2">
                  <input type="text" value={newPerson.tags} onChange={e => setNewPerson({...newPerson, tags: e.target.value})} placeholder="Tags (komma gescheiden)..."
                    className="flex-1 px-3 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
                  <button data-testid="save-person-btn" onClick={addPerson} className="px-4 py-2 bg-pink-500 text-white rounded-lg text-xs font-medium">Opslaan</button>
                </div>
              </div>
            )}

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
              <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Zoek personen..."
                className="w-full pl-8 pr-3 py-2 bg-slate-900/60 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none" />
            </div>

            {/* Persons grouped by gradatie */}
            {Object.entries(byGradatie).sort(([a],[b]) => a - b).map(([grad, pList]) => (
              <div key={grad}>
                <p className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider px-1 mb-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ background: gradatieColors[grad] || '#64748b' }} />
                  Gradatie {grad}: {gradatieLabels[grad] || 'Onbekend'} ({pList.length})
                </p>
                <div className="space-y-2">
                  {pList.map(p => {
                    const isExpanded = expandedId === p.id;
                    const gColor = gradatieColors[p.gradatie] || '#64748b';
                    return (
                      <div key={p.id} data-testid={`person-${p.id}`} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
                        <button onClick={() => setExpandedId(isExpanded ? null : p.id)}
                          className="w-full flex items-center gap-3 p-3 text-left">
                          <UserAvatar
                            user={{ id: p.id, naam: p.naam, avatar: p.avatar || p.avatar_ref, gradatie: p.gradatie }}
                            size="md"
                            rounded="rounded-lg"
                          />
                          <div className="flex-1 min-w-0">
                            <h4 className="text-sm font-medium text-white">{p.naam}</h4>
                            <div className="flex items-center gap-2">
                              {p.relatie && <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ background: `${gColor}15`, color: gColor }}>{p.relatie}</span>}
                              {p.is_user && <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400">Gebruiker</span>}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {(p.tags || []).length > 0 && <span className="text-[10px] text-slate-600">{p.tags.length} tags</span>}
                            {isExpanded ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                          </div>
                        </button>
                        {isExpanded && (
                          <div className="px-3 pb-3 space-y-2 border-t border-slate-800/50">
                            <div className="grid grid-cols-2 gap-2 pt-2">
                              <div className="p-2 bg-slate-800/30 rounded-lg">
                                <p className="text-[10px] text-slate-500">Volledige naam</p>
                                <p className="text-xs text-white">{p.volledige_naam || p.naam}</p>
                              </div>
                              <div className="p-2 bg-slate-800/30 rounded-lg">
                                <p className="text-[10px] text-slate-500">Aangemaakt</p>
                                <p className="text-xs text-white">{p.created_at ? new Date(p.created_at).toLocaleDateString('nl-NL') : '?'}</p>
                              </div>
                            </div>
                            {(p.tags || []).length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {p.tags.map((t, i) => <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">#{t}</span>)}
                              </div>
                            )}
                            {p.notes && <p className="text-xs text-slate-400 p-2 bg-slate-800/20 rounded-lg">{p.notes}</p>}
                            <div className="flex justify-end">
                              <button onClick={() => deletePerson(p.id)} className="flex items-center gap-1 px-2 py-1 text-[10px] text-red-400 hover:bg-red-500/10 rounded-lg transition-colors">
                                <Trash2 className="w-3 h-3" /> Verwijderen
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}

            {filtered.length === 0 && (
              <div className="py-16 text-center">
                <UsersRound className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                <p className="text-slate-400 text-sm">Geen personen gevonden</p>
              </div>
            )}

            {/* Relationships overview */}
            {relationships.length > 0 && (
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <Link2 className="w-4 h-4 text-pink-400" /> Spark's Relatie Overzicht
                </h3>
                <div className="space-y-2">
                  {relationships.map((r, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 bg-slate-800/30 rounded-lg">
                      <div className="w-7 h-7 rounded-lg bg-pink-500/10 flex items-center justify-center">
                        <Heart className="w-3.5 h-3.5 text-pink-400" />
                      </div>
                      <div className="flex-1">
                        <p className="text-xs text-white font-medium">{r.person_name}</p>
                        <p className="text-[10px] text-slate-500">{r.relation_type}</p>
                      </div>
                      {r.notes && <span className="text-[10px] text-slate-600">{r.notes}</span>}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default PersoonsPage;
