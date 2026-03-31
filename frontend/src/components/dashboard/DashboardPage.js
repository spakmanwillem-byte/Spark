import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { MainLayout, getPageInfo } from '../layout/MainLayout';
import { 
  Activity, Brain, Zap, Plus, Network, GitBranch
} from 'lucide-react';

export function DashboardPage({ activePage = 'dashboard', onNavigate }) {
  const { user } = useAuth();

  // Get current page info
  const pageInfo = getPageInfo(activePage);
  const PageIcon = pageInfo?.icon || Activity;

  // Dashboard content - Only Spark Brain & Triggers
  const renderDashboardContent = () => (
    <>
      {/* Welcome Banner */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 mb-8">
        <p className="text-slate-300">
          Welkom terug, <span className="text-amber-400 font-semibold">{user?.naam}</span>!
        </p>
      </div>

      {/* Main Grid - Spark Brain & Triggers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Spark Brain - Knowledge Graph */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Brain className="w-5 h-5 text-amber-400" />
              Spark Brain
            </h3>
            <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded">CONNECTED</span>
          </div>
          <div className="p-6">
            {/* Knowledge Graph Placeholder */}
            <div className="aspect-video bg-slate-800/30 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
              <div className="text-center">
                <Network className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Knowledge Graph</p>
                <p className="text-slate-600 text-xs mt-1">Verbindingen tussen kennis</p>
              </div>
            </div>
          </div>
        </div>

        {/* Triggers */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Triggers
            </h3>
            <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded">156 ACTIVE</span>
          </div>
          <div className="p-6">
            {/* Triggers Placeholder */}
            <div className="aspect-video bg-slate-800/30 rounded-xl border-2 border-dashed border-slate-700 flex items-center justify-center">
              <div className="text-center">
                <GitBranch className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">Trigger Zinnen</p>
                <p className="text-slate-600 text-xs mt-1">NLP herkenning patronen</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </>
  );

  // Empty placeholder content for other pages
  const renderPlaceholderContent = () => (
    <div className="flex-1 flex items-center justify-center min-h-[60vh]">
      <div className="text-center max-w-md">
        <div className="w-20 h-20 bg-slate-800/50 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-6">
          <PageIcon className="w-10 h-10 text-slate-500" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">{pageInfo?.label || 'Module'}</h2>
        <p className="text-slate-400 mb-6">
          Deze module is klaar om ingericht te worden.
        </p>
        <div className="p-6 border-2 border-dashed border-slate-700 rounded-2xl">
          <Plus className="w-8 h-8 text-slate-600 mx-auto mb-2" />
          <p className="text-sm text-slate-500">Inhoud komt hier</p>
        </div>
      </div>
    </div>
  );

  return (
    <MainLayout activePage={activePage} onNavigate={onNavigate}>
      <div className="p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-slate-800 rounded-xl flex items-center justify-center">
              <PageIcon className="w-5 h-5 text-amber-400" />
            </div>
            <h1 className="text-2xl font-bold text-white">
              {activePage === 'dashboard' ? 'Dashboard' : pageInfo?.label || 'Module'}
            </h1>
          </div>
          <p className="text-slate-400">
            {activePage === 'dashboard' 
              ? 'Spark Brain & Triggers overzicht' 
              : `${pageInfo?.section || ''} → ${pageInfo?.label || ''}`
            }
          </p>
        </div>

        {/* Content */}
        {activePage === 'dashboard' ? renderDashboardContent() : renderPlaceholderContent()}
      </div>
    </MainLayout>
  );
}

export default DashboardPage;
