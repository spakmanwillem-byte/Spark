import React, { useState } from 'react';
import { MainLayout } from '../layout/MainLayout';
import {
  ShoppingBag, Star, Package, Tag, Gift, Sparkles,
  Lock, Clock
} from 'lucide-react';

const shopItems = [
  { id: 'custom-emoji', naam: 'Custom Emoji Slot', prijs: 500, type: 'tokens', categorie: 'Personalisatie', beschrijving: 'Voeg een eigen emoji toe aan Spark', icon: Sparkles, beschikbaar: true },
  { id: 'kleur-thema', naam: 'Kleur Thema Pakket', prijs: 750, type: 'tokens', categorie: 'Personalisatie', beschrijving: 'Unlock extra kleurthemas voor je dashboard', icon: Tag, beschikbaar: true },
  { id: 'priority-support', naam: 'Priority Support', prijs: 100, type: 'credits', categorie: 'Service', beschrijving: '1 maand priority support van Spark', icon: Star, beschikbaar: true },
  { id: 'extra-storage', naam: 'Extra Opslag (1GB)', prijs: 200, type: 'credits', categorie: 'Uitbreiding', beschrijving: 'Extra opslagruimte voor bestanden en data', icon: Package, beschikbaar: true },
  { id: 'ai-boost', naam: 'AI Boost Module', prijs: 2000, type: 'tokens', categorie: 'Modules', beschrijving: 'Geavanceerde AI functies voor 30 dagen', icon: Sparkles, beschikbaar: false },
  { id: 'gift-card', naam: 'Gift Card (50 Credits)', prijs: 5.00, type: 'eur', categorie: 'Cadeau', beschrijving: 'Geef credits cadeau aan een andere gebruiker', icon: Gift, beschikbaar: true },
];

const categories = ['Alles', 'Personalisatie', 'Service', 'Uitbreiding', 'Modules', 'Cadeau'];

export function WinkelPage({ onNavigate }) {
  const [filterCat, setFilterCat] = useState('Alles');

  const filtered = filterCat === 'Alles' ? shopItems : shopItems.filter(i => i.categorie === filterCat);

  return (
    <MainLayout activePage="winkel" onNavigate={onNavigate}>
      <div data-testid="winkel-page" className="h-[calc(100vh-4rem)] flex flex-col">
        <div className="flex-shrink-0 bg-slate-900/80 border-b border-slate-800 px-4 pt-3 pb-3">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #a855f7, #ec4899)' }}>
              <ShoppingBag className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">Winkel</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{shopItems.length} items beschikbaar</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-4">

            <div className="p-4 rounded-xl border border-purple-500/20" style={{ background: 'linear-gradient(135deg, rgba(168,85,247,0.06), rgba(236,72,153,0.04))' }}>
              <h2 className="text-lg font-bold text-white mb-1">Spark Winkel</h2>
              <p className="text-xs text-slate-400">Besteed je Spark Tokens en Credits aan upgrades, modules en personalisatie.</p>
            </div>

            {/* Category filter */}
            <div className="flex flex-wrap gap-2">
              {categories.map(c => (
                <button key={c} onClick={() => setFilterCat(c)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${filterCat === c ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30' : 'bg-slate-800/50 text-slate-400 border border-transparent hover:border-slate-700'}`}>
                  {c}
                </button>
              ))}
            </div>

            {/* Items grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {filtered.map(item => {
                const Icon = item.icon;
                return (
                  <div key={item.id} data-testid={`shop-item-${item.id}`}
                    className={`p-4 bg-slate-900/50 border rounded-xl transition-all ${item.beschikbaar ? 'border-slate-800 hover:border-purple-500/30' : 'border-slate-800/50 opacity-60'}`}>
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center flex-shrink-0">
                        <Icon className="w-5 h-5 text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-sm font-semibold text-white">{item.naam}</h3>
                          {!item.beschikbaar && <Lock className="w-3 h-3 text-slate-500" />}
                        </div>
                        <p className="text-[11px] text-slate-400 mb-3">{item.beschrijving}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-400">{item.categorie}</span>
                          <div className="flex items-center gap-1.5">
                            <span className="text-sm font-bold text-purple-400">{item.type === 'eur' ? `€${item.prijs.toFixed(2)}` : item.prijs}</span>
                            <span className="text-[10px] text-slate-500">{item.type === 'tokens' ? 'tokens' : item.type === 'credits' ? 'credits' : ''}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    {item.beschikbaar && (
                      <button className="mt-3 w-full py-2 rounded-lg text-xs font-medium text-white transition-colors" style={{ background: 'linear-gradient(135deg, #a855f7, #ec4899)' }}>
                        Kopen
                      </button>
                    )}
                    {!item.beschikbaar && (
                      <div className="mt-3 w-full py-2 rounded-lg text-xs font-medium text-center text-slate-500 bg-slate-800/30 flex items-center justify-center gap-1">
                        <Clock className="w-3 h-3" /> Binnenkort beschikbaar
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default WinkelPage;
