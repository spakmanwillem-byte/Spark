/**
 * EmotieRouteringPage (v6_emotion_routing_sidebar_001, 2026-05-28)
 * Eigen sidebar-item voor de 7-laags Emotie Pipeline.
 * Hergebruikt SparkBrainPage met initialSection='emotie_pipeline' — geen UI-duplicaat.
 *
 * Onderscheid Detectie vs Routering:
 * - Detectie  (/spark/emotions)  = "Wat voelt deze user?"  → blij/boos/bang/bedroefd
 * - Routering (/spark/routering) = "Hoe reageer ik daarop?" → 7-laags behavior-pipeline
 */
import React from 'react';
import { SparkBrainPage } from './SparkBrainPage';

export function EmotieRouteringPage({ onNavigate }) {
  return <SparkBrainPage onNavigate={onNavigate} initialSection="emotie_pipeline" />;
}

export default EmotieRouteringPage;
