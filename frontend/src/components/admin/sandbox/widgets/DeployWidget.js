/**
 * v13d_deploy_kladblok_001 (sessie 56b) — Willem: "Deploy-tab uit notities mag
 * ook naar Widget Kladblok tot betere plek."
 *
 * Dunne wrapper rond bestaande DeployAnchorPanel component. Zelfstandig: haalt
 * viewer_id via window.__auth_user_id (fallback user-001).
 */
import React from 'react';
import { DeployAnchorPanel } from '../../../workspace/DeployAnchorPanel';

export function DeployWidget() {
  const viewerId = (typeof window !== 'undefined' && window.__auth_user_id) || 'user-001';
  return (
    <div data-testid="deploy-widget">
      <DeployAnchorPanel viewerId={viewerId} />
    </div>
  );
}
