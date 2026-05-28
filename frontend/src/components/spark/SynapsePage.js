/**
 * SynapsePage (v6_synapse_sidebar_001, 2026-05-28)
 * Verhuisd van Beheer→Instellingen→Synapslaag naar SPARK AI sidebar.
 * Wraps bestaande SynapseTab (admin/SynapseTab.js) in MainLayout.
 */
import React from 'react';
import { MainLayout } from '../layout/MainLayout';
import { SynapseTab } from '../admin/SynapseTab';

export function SynapsePage({ onNavigate }) {
  return (
    <MainLayout activePage="synapse" onNavigate={onNavigate}>
      <div data-testid="synapse-page" className="h-full overflow-y-auto p-4">
        <SynapseTab />
      </div>
    </MainLayout>
  );
}

export default SynapsePage;
