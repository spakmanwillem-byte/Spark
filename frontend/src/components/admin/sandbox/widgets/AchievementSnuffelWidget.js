/**
 * v12_snuffel_widget_001 — Achievement/XP/Rang inventaris.
 *
 * Doel: parkeerplaats voor de findings uit sessie 56d over wat er ECHT bestaat
 * rondom achievements, XP en rang. Voorkomt dat we straks een tweede manager
 * bouwen naast de eerste omdat we vergeten waar dingen wonen.
 *
 * Als Willem alles gelezen heeft en de gaps opgepakt zijn: dit widget kan weg.
 */
import React from 'react';
import { CheckCircle2, AlertTriangle, HelpCircle } from 'lucide-react';

export function AchievementSnuffelWidget() {
  const bestaat = [
    {
      wat: 'AchievementBlueprintPanel',
      waar: 'InstellingenPage.js r1195 (admin-only, achter isAdmin)',
      wat_kan_het: 'Toont alle blueprint-JSONs uit /app/backend/modules/achievements/blueprints/',
      endpoint: 'GET /api/achievements/admin/blueprints',
    },
    {
      wat: 'Admin edit-modal per achievement',
      waar: 'AchievementsPage.js r212 (data-testid: achievement-admin-edit-{id})',
      wat_kan_het: 'Titel + icon (emoji of upload) aanpassen',
      endpoint: 'PATCH /api/achievements/admin/{id}?by_user=...',
    },
    {
      wat: 'XP-motor (centraal)',
      waar: '/app/backend/modules/chat/xp_service.py → grant_xp(user_id, amount, reason)',
      wat_kan_het: '6 bronnen: chat berichten, RPS, contributions, achievements-unlock, badges, tag-curatie',
      endpoint: '(interne functie, geen HTTP-endpoint)',
    },
    {
      wat: '50 achievements met XP-rewards',
      waar: '/app/backend/data/achievements.json',
      wat_kan_het: 'words_10 (50 XP) tot words_2500 (15.000 XP) schaal',
      endpoint: 'GET /api/achievements/list',
    },
    {
      wat: 'Rang op karakter-kaart',
      waar: 'DnDCharacterSheet.js r521-524 én r2005',
      wat_kan_het: 'Toont char.rang_titel + Community Level + militaire streepjes (100 levels = 1 streepje)',
      endpoint: '(client-side, uit char.derived.level)',
    },
    {
      wat: 'Leaderboard',
      waar: 'AchievementsPage.js + /api/achievements/leaderboard',
      wat_kan_het: 'Sorteert users op total_xp desc, toont avatar/level',
      endpoint: 'GET /api/achievements/leaderboard?period=alltime&limit=25',
    },
    {
      wat: 'RPS-leaderboard (aparte spelrang)',
      waar: '/api/rps/leaderboard',
      wat_kan_het: 'Spel-specifieke rank, los van XP',
      endpoint: 'GET /api/rps/leaderboard?limit=50',
    },
  ];

  const gaps = [
    {
      wat: 'XP-veld ontbreekt(?) in edit-modal',
      details: 'AchievementsPage.js edit-modal past nu alleen titel+icon aan. XP-waarde en threshold zijn nog blueprint-alleen. Bevestigen bij Willem: wilt hij XP/threshold ook editable via GUI?',
    },
    {
      wat: 'Rang-drempels hardcoded(?)',
      details: 'Rang op karakter-kaart komt uit char.derived.level. Regelt Spark de mapping [level → rang_titel] al? Of is dat een gap? Willem noemde "Sergeant/Luitenant" — check of die namen ergens in code voorkomen als mapping-tabel.',
    },
    {
      wat: 'text_importer geeft geen XP',
      details: '/app/backend/modules/kb_v2/text_importer.py apply_cards_to_kb() roept nergens grant_xp() aan. Bewust (import is admin-taak) of onbedoeld (nieuwe kennis = groei)? Vragen aan Willem.',
    },
    {
      wat: 'admin_capable UI-toggle',
      details: 'Backend heeft AuthService.set_admin_capable(). Frontend heeft (nog) geen switch in UsersAdminPage om een gradatie-3 Vriend admin_capable te maken. Blocker voor Willem\'s "community-admin" model.',
    },
    {
      wat: 'Legerrang-schaal parallel aan gradatie',
      details: 'Emmy stelde voor: Rookie/Bronze/Silver/Gold/Master/Legend als neutrale start, of direct Sergeant/Luitenant. Geen mapping-tabel in codebase gevonden. Wacht op Willems keuze: neutrale labels eerst (advies) of direct leger-jargon (Emmy).',
    },
  ];

  const nu_gefixt = [
    'v12_admin_capable_unlock_001 — /api/auth/register accepteert nu admin_capable=True users (naast gradatie 1/2) voor override — gradatie-3 admins kunnen users aanmaken.',
  ];

  return (
    <div data-testid="widget-achievement-snuffel" className="p-4 space-y-4">
      <div>
        <p className="text-xs text-slate-500 mb-2">
          <strong className="text-slate-300">Doel:</strong> voorkomen dat we een tweede
          achievement-manager bouwen naast de bestaande. Als je alles gelezen hebt
          en de gaps besproken, kan dit widget weg.
        </p>
      </div>

      <div>
        <h3 className="text-xs uppercase tracking-wide text-emerald-400 mb-2 flex items-center gap-2">
          <CheckCircle2 className="w-3.5 h-3.5" /> Bestaat al (7)
        </h3>
        <div className="space-y-2">
          {bestaat.map((b, i) => (
            <div key={i} className="p-2 bg-slate-900/60 border border-slate-800 rounded text-[11px]">
              <p className="font-semibold text-slate-200">{b.wat}</p>
              <p className="text-slate-400"><span className="text-slate-500">waar:</span> {b.waar}</p>
              <p className="text-slate-400"><span className="text-slate-500">doel:</span> {b.wat_kan_het}</p>
              <p className="text-slate-500 font-mono text-[10px]">{b.endpoint}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs uppercase tracking-wide text-amber-400 mb-2 flex items-center gap-2">
          <HelpCircle className="w-3.5 h-3.5" /> Open vragen / gaps (5)
        </h3>
        <div className="space-y-2">
          {gaps.map((g, i) => (
            <div key={i} className="p-2 bg-amber-500/5 border border-amber-500/20 rounded text-[11px]">
              <p className="font-semibold text-amber-300">{g.wat}</p>
              <p className="text-slate-300">{g.details}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs uppercase tracking-wide text-cyan-400 mb-2 flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5" /> Nu gefixt in deze sessie
        </h3>
        <div className="space-y-2">
          {nu_gefixt.map((n, i) => (
            <div key={i} className="p-2 bg-cyan-500/5 border border-cyan-500/20 rounded text-[11px] text-slate-300">
              {n}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
