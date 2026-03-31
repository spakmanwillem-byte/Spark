import React, { useState, useEffect } from 'react';
import { MainLayout } from '../layout/MainLayout';
import { 
  TrendingUp, TrendingDown, Activity, DollarSign, 
  Bitcoin, ArrowUpRight, ArrowDownRight, Clock,
  BarChart2, PieChart, Wallet, RefreshCw, Plus,
  Settings, Bell, Search, ChevronDown, GripVertical
} from 'lucide-react';

// Mock data for the trader dashboard
const mockCryptoData = [
  { id: 'btc', name: 'Bitcoin', symbol: 'BTC', price: 67234.52, change: 2.34, volume: '42.3B', icon: '₿', color: 'orange' },
  { id: 'eth', name: 'Ethereum', symbol: 'ETH', price: 3521.18, change: -1.23, volume: '18.7B', icon: 'Ξ', color: 'purple' },
  { id: 'sol', name: 'Solana', symbol: 'SOL', price: 142.67, change: 5.67, volume: '3.2B', icon: '◎', color: 'cyan' },
  { id: 'ada', name: 'Cardano', symbol: 'ADA', price: 0.4523, change: -0.87, volume: '890M', icon: '₳', color: 'blue' },
];

const mockPortfolio = {
  totalValue: 125432.67,
  dayChange: 2340.52,
  dayChangePercent: 1.89,
  assets: [
    { symbol: 'BTC', amount: 1.5, value: 100851.78, allocation: 80.4 },
    { symbol: 'ETH', amount: 5.2, value: 18310.14, allocation: 14.6 },
    { symbol: 'SOL', amount: 30, value: 4280.10, allocation: 3.4 },
    { symbol: 'ADA', amount: 4400, value: 1990.12, allocation: 1.6 },
  ]
};

const mockRecentTrades = [
  { id: 1, type: 'buy', symbol: 'BTC', amount: 0.05, price: 67100, time: '14:32', status: 'completed' },
  { id: 2, type: 'sell', symbol: 'ETH', amount: 1.2, price: 3540, time: '13:15', status: 'completed' },
  { id: 3, type: 'buy', symbol: 'SOL', amount: 10, price: 141.50, time: '11:45', status: 'pending' },
];

export function TraderPage({ onNavigate }) {
  const [selectedCrypto, setSelectedCrypto] = useState('btc');
  const [cards, setCards] = useState([
    { id: 'portfolio', title: 'Portfolio Overzicht', size: 'large' },
    { id: 'chart', title: 'Prijs Grafiek', size: 'large' },
    { id: 'watchlist', title: 'Watchlist', size: 'medium' },
    { id: 'trades', title: 'Recente Trades', size: 'medium' },
    { id: 'stats', title: 'Statistieken', size: 'small' },
    { id: 'alerts', title: 'Alerts', size: 'small' },
  ]);
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);

  // Drag handlers
  const handleDragStart = (e, index) => {
    setDraggedCard(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragEnd = () => {
    setDraggedCard(null);
    setDragOverIndex(null);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedCard === null) return;
    setDragOverIndex(index);
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    if (draggedCard === null || draggedCard === dropIndex) return;

    const newCards = [...cards];
    const draggedItem = newCards[draggedCard];
    newCards.splice(draggedCard, 1);
    newCards.splice(dropIndex, 0, draggedItem);
    setCards(newCards);
    setDraggedCard(null);
    setDragOverIndex(null);
  };

  return (
    <MainLayout activePage="trader" onNavigate={onNavigate}>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Crypto Trader</h1>
              <p className="text-sm text-slate-400">MODULES → Trader</p>
            </div>
          </div>
          
          {/* Header Actions */}
          <div className="flex items-center gap-3">
            <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <RefreshCw className="w-5 h-5 text-slate-400" />
            </button>
            <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <Bell className="w-5 h-5 text-slate-400" />
            </button>
            <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <Settings className="w-5 h-5 text-slate-400" />
            </button>
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <QuickStat 
            label="Portfolio Waarde" 
            value={`$${mockPortfolio.totalValue.toLocaleString()}`}
            change={mockPortfolio.dayChangePercent}
            icon={Wallet}
          />
          <QuickStat 
            label="Dag Winst/Verlies" 
            value={`$${mockPortfolio.dayChange.toLocaleString()}`}
            change={mockPortfolio.dayChangePercent}
            icon={Activity}
          />
          <QuickStat 
            label="BTC Prijs" 
            value={`$${mockCryptoData[0].price.toLocaleString()}`}
            change={mockCryptoData[0].change}
            icon={Bitcoin}
          />
          <QuickStat 
            label="Actieve Orders" 
            value="3"
            subtext="2 pending"
            icon={Clock}
          />
        </div>

        {/* Main Grid - Draggable Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Portfolio Card */}
          <DraggableCard
            index={0}
            isDragging={draggedCard === 0}
            isDragOver={dragOverIndex === 0}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="lg:col-span-2"
          >
            <CardHeader title="Portfolio Verdeling" icon={PieChart} />
            <div className="p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Pie Chart Placeholder */}
                <div className="aspect-square max-w-[200px] mx-auto relative">
                  <div className="absolute inset-0 rounded-full border-[20px] border-amber-500" style={{clipPath: 'polygon(50% 50%, 100% 0, 100% 100%, 50% 100%)'}}></div>
                  <div className="absolute inset-0 rounded-full border-[20px] border-purple-500" style={{clipPath: 'polygon(50% 50%, 50% 0, 100% 0)'}}></div>
                  <div className="absolute inset-0 rounded-full border-[20px] border-cyan-500" style={{clipPath: 'polygon(50% 50%, 30% 0, 50% 0)'}}></div>
                  <div className="absolute inset-0 rounded-full border-[20px] border-blue-500" style={{clipPath: 'polygon(50% 50%, 20% 5%, 30% 0)'}}></div>
                  <div className="absolute inset-4 bg-slate-900 rounded-full flex items-center justify-center">
                    <div className="text-center">
                      <p className="text-2xl font-bold text-white">${(mockPortfolio.totalValue / 1000).toFixed(1)}K</p>
                      <p className="text-xs text-slate-400">Totaal</p>
                    </div>
                  </div>
                </div>
                
                {/* Asset List */}
                <div className="space-y-3">
                  {mockPortfolio.assets.map(asset => (
                    <div key={asset.symbol} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          asset.symbol === 'BTC' ? 'bg-amber-500/20 text-amber-400' :
                          asset.symbol === 'ETH' ? 'bg-purple-500/20 text-purple-400' :
                          asset.symbol === 'SOL' ? 'bg-cyan-500/20 text-cyan-400' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          <span className="text-sm font-bold">{asset.symbol[0]}</span>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{asset.symbol}</p>
                          <p className="text-xs text-slate-500">{asset.amount}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-white">${asset.value.toLocaleString()}</p>
                        <p className="text-xs text-slate-500">{asset.allocation}%</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </DraggableCard>

          {/* Watchlist Card */}
          <DraggableCard
            index={1}
            isDragging={draggedCard === 1}
            isDragOver={dragOverIndex === 1}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <CardHeader title="Watchlist" icon={Activity} action="+ Toevoegen" />
            <div className="p-4 space-y-2">
              {mockCryptoData.map(crypto => (
                <button 
                  key={crypto.id}
                  onClick={() => setSelectedCrypto(crypto.id)}
                  className={`w-full flex items-center justify-between p-3 rounded-xl transition-all ${
                    selectedCrypto === crypto.id 
                      ? 'bg-amber-500/10 border border-amber-500/30' 
                      : 'bg-slate-800/50 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-lg font-bold ${
                      crypto.color === 'orange' ? 'bg-amber-500/20 text-amber-400' :
                      crypto.color === 'purple' ? 'bg-purple-500/20 text-purple-400' :
                      crypto.color === 'cyan' ? 'bg-cyan-500/20 text-cyan-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {crypto.icon}
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium text-white">{crypto.name}</p>
                      <p className="text-xs text-slate-500">{crypto.symbol}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-white">${crypto.price.toLocaleString()}</p>
                    <p className={`text-xs flex items-center justify-end gap-1 ${crypto.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {crypto.change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {Math.abs(crypto.change)}%
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </DraggableCard>

          {/* Chart Card */}
          <DraggableCard
            index={2}
            isDragging={draggedCard === 2}
            isDragOver={dragOverIndex === 2}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="lg:col-span-2"
          >
            <CardHeader title="BTC/USD Grafiek" icon={BarChart2} action="1D 1W 1M 1Y" />
            <div className="p-4">
              {/* Placeholder Chart */}
              <div className="h-64 bg-slate-800/30 rounded-xl flex items-end justify-between p-4 gap-1">
                {[40, 55, 45, 60, 52, 70, 65, 75, 68, 80, 72, 85, 78, 90, 82, 88, 95, 87, 92, 98].map((height, i) => (
                  <div 
                    key={i} 
                    className="flex-1 bg-gradient-to-t from-amber-500/50 to-amber-500/10 rounded-t transition-all hover:from-amber-500/70 hover:to-amber-500/20"
                    style={{ height: `${height}%` }}
                  />
                ))}
              </div>
              <div className="flex items-center justify-between mt-4 text-sm text-slate-500">
                <span>00:00</span>
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
                <span>24:00</span>
              </div>
            </div>
          </DraggableCard>

          {/* Recent Trades Card */}
          <DraggableCard
            index={3}
            isDragging={draggedCard === 3}
            isDragOver={dragOverIndex === 3}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <CardHeader title="Recente Trades" icon={Clock} action="Alle bekijken" />
            <div className="p-4 space-y-3">
              {mockRecentTrades.map(trade => (
                <div key={trade.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-xl">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      trade.type === 'buy' ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                      {trade.type === 'buy' ? (
                        <ArrowUpRight className="w-4 h-4 text-green-400" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4 text-red-400" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">
                        {trade.type === 'buy' ? 'Koop' : 'Verkoop'} {trade.symbol}
                      </p>
                      <p className="text-xs text-slate-500">{trade.amount} @ ${trade.price}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-slate-400">{trade.time}</p>
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      trade.status === 'completed' ? 'bg-green-500/20 text-green-400' : 'bg-amber-500/20 text-amber-400'
                    }`}>
                      {trade.status === 'completed' ? 'Voltooid' : 'Pending'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </DraggableCard>
        </div>

        {/* Quick Trade Panel */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-amber-400" />
            Snel Handelen
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-slate-400 mb-2">Crypto</label>
              <select className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white focus:border-amber-500 focus:outline-none">
                <option>BTC - Bitcoin</option>
                <option>ETH - Ethereum</option>
                <option>SOL - Solana</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-2">Aantal</label>
              <input 
                type="number" 
                placeholder="0.00"
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:border-amber-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-2">Type</label>
              <div className="flex gap-2">
                <button className="flex-1 py-3 bg-green-500/20 text-green-400 rounded-xl font-medium hover:bg-green-500/30 transition-colors">
                  Koop
                </button>
                <button className="flex-1 py-3 bg-red-500/20 text-red-400 rounded-xl font-medium hover:bg-red-500/30 transition-colors">
                  Verkoop
                </button>
              </div>
            </div>
            <div>
              <label className="block text-xs text-slate-400 mb-2">Actie</label>
              <button className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-600 text-white font-semibold rounded-xl hover:from-amber-400 hover:to-orange-500 transition-all">
                Order Plaatsen
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// Quick Stat Component
function QuickStat({ label, value, change, subtext, icon: Icon }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-slate-500 uppercase tracking-wider">{label}</span>
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <p className="text-xl font-bold text-white">{value}</p>
      {change !== undefined && (
        <p className={`text-xs flex items-center gap-1 mt-1 ${change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {change >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          {Math.abs(change)}%
        </p>
      )}
      {subtext && <p className="text-xs text-slate-500 mt-1">{subtext}</p>}
    </div>
  );
}

// Card Header Component
function CardHeader({ title, icon: Icon, action }) {
  return (
    <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
      <h3 className="text-sm font-semibold text-white flex items-center gap-2">
        <Icon className="w-4 h-4 text-amber-400" />
        {title}
      </h3>
      {action && (
        <button className="text-xs text-slate-400 hover:text-amber-400 transition-colors">
          {action}
        </button>
      )}
    </div>
  );
}

// Draggable Card Wrapper
function DraggableCard({ children, index, isDragging, isDragOver, onDragStart, onDragEnd, onDragOver, onDrop, className = '' }) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, index)}
      onDragEnd={onDragEnd}
      onDragOver={(e) => onDragOver(e, index)}
      onDrop={(e) => onDrop(e, index)}
      className={`
        bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden cursor-move
        transition-all duration-200 group relative
        ${isDragging ? 'opacity-50 scale-95' : ''}
        ${isDragOver ? 'ring-2 ring-amber-500/50 scale-[1.02]' : ''}
        hover:border-slate-700
        ${className}
      `}
    >
      {/* Drag Handle Indicator */}
      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity z-10">
        <GripVertical className="w-4 h-4 text-slate-500" />
      </div>
      {children}
    </div>
  );
}

export default TraderPage;
