/**
 * v10_sandbox_page_001 — Beheer → Sandbox (Willems verzoek sessie 47).
 *
 * FILOSOFIE: parkeer-plek voor front-end kaders zonder definitieve plek.
 * Elk kader = zelfstandige container-component in `./sandbox/widgets/`.
 * Registry in `./sandbox/registry.js`. Verplaatsen = 1 regel elders importeren.
 */
import React from 'react';
import { MainLayout } from '../layout/MainLayout';
import { Beaker, ArrowRight } from 'lucide-react';
import { SANDBOX_WIDGETS } from './sandbox/registry';

export default function SandboxPage({ onNavigate }) {
  return (
    <MainLayout activePage="sandbox" onNavigate={onNavigate}>
      <div data-testid="sandbox-page" className="p-6 max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <header className="flex items-start gap-3">
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/30">
            <Beaker className="w-6 h-6 text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Widget Kladblok</h1>
            <p className="text-sm text-slate-400 mt-1 max-w-xl">
              Tijdelijke parkeer-plek voor front-end kaders. Bouw je een widget en weet je nog niet
              waar hij hoort? Registreer &apos;m hier, verplaats later naar zijn definitieve module met
              &eacute;&eacute;n regel.
            </p>
            <p className="text-[10px] text-slate-600 mt-1.5">
              💡 Niet te verwarren met <span className="text-slate-500">Module Sandbox</span> (Integraties → tab) — die is voor Sparks Python-modules.
            </p>
          </div>
        </header>

        {/* Instructie voor volgende widget */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 text-[11px] text-slate-500 leading-relaxed">
          <span className="text-slate-300 font-medium">Nieuwe widget toevoegen:</span>{' '}
          <code className="text-amber-300">frontend/src/components/admin/sandbox/widgets/XxxWidget.js</code>
          {' '}→ registreer in{' '}
          <code className="text-amber-300">sandbox/registry.js</code>. Widget is zelfstandig
          (eigen state + fetch), zodat verplaatsen naar bv. Analytics simpel is:
          {' '}<code className="text-amber-300">import &#123; XxxWidget &#125; from &apos;./sandbox/widgets/XxxWidget&apos;;</code>
        </div>

        {/* Widgets grid */}
        {SANDBOX_WIDGETS.length === 0 ? (
          <div className="text-center py-16 text-slate-500 text-sm italic">
            Nog geen sandbox-widgets. Registreer je eerste in{' '}
            <code className="text-slate-400">sandbox/registry.js</code>.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SANDBOX_WIDGETS.map(({ id, naam, doel, waar_hoort_het, aangemaakt_op, reden, Component }) => (
              <div key={id} data-testid={`sandbox-item-${id}`}
                className="space-y-2">
                {/* Meta-info bovenaan */}
                <div className="px-3 py-2 rounded-xl bg-slate-900/30 border border-slate-800 text-[10px]">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-slate-300 font-medium">{naam}</span>
                    <span className="text-slate-600 tabular-nums">{aangemaakt_op}</span>
                  </div>
                  <p className="text-slate-500 mt-0.5">{doel}</p>
                  <p className="text-slate-600 mt-1 flex items-center gap-1">
                    <ArrowRight className="w-3 h-3" /> uiteindelijke plek: {waar_hoort_het}
                  </p>
                  {reden && <p className="text-slate-600 italic mt-0.5">— {reden}</p>}
                </div>

                {/* Widget zelf — zelfstandige component */}
                <Component />
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
