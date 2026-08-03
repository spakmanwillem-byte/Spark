# Blueprint — achievements

> **Refactor 2026-07-20**: Dispatcher/sub-agent architectuur (v7_agent_dispatcher_001)
> Pad: `backend/modules/achievements`

## 🎯 Doel
Achievement-systeem met **dispatcher-patroon**. `AchievementService` is een dun laagje dat unlock-checks delegeert naar sub-agents op basis van `achievement.type`. Elke sub-agent handelt één categorie af.

Blueprint-JSONs in `blueprints/` bevatten alle **runtime-config** (XP-waarden, texts, thresholds, banners). Deze zijn later admin-editable via UI zonder code-wijziging.

## 🏗️ Architectuur

```
modules/achievements/
├─ _meta.json                 (module-metadata)
├─ routes.py                  (dunne API-laag)
├─ service.py                 (DISPATCHER — routes per type)
├─ agents/                    (sub-agents)
│   ├─ base_agent.py             (abstract BaseAchievementAgent)
│   ├─ kb_agent.py               → 'words', 'letter_completion'
│   ├─ rps_agent.py              → 'rps'
│   └─ milestone_agent.py        → 'milestones', 'contributions'
└─ blueprints/                (runtime config JSONs — admin-editable)
    ├─ kb_achievements.json      (XP/text voor KB-agent)
    ├─ rps_achievements.json     (XP/text voor RPS-agent)
    └─ milestone_achievements.json
```

## 🤖 Sub-Agents

| Agent | Types | Blueprint | Verantwoordelijk voor |
|---|---|---|---|
| `KBAchievementAgent` | `words`, `letter_completion` | `kb_achievements.json` | Word-milestones (10/25/50/…) + 26 letter-achievements A-Z |
| `RPSAchievementAgent` | `rps` | `rps_achievements.json` | Steen-Papier-Schaar wins/losses/total |
| `MilestoneAchievementAgent` | `milestones`, `contributions` | `milestone_achievements.json` | Trigger-based (avatar, first token, first KB-bijdrage) |

## ✅ Wat werkt al
- Dispatcher-pattern in `service.py`
- 3 sub-agents met blueprint-koppeling
- Auto-unlock (retroactive) voor `words`, `letter_completion`, `rps`
- Manual unlock via `service.unlock_manual` (voor `milestones`)
- 26 letter-achievements (Ⓐ-Ⓩ) — unlockt als inbox 0 skeletons voor die letter heeft
- `GET /admin/blueprints` endpoint voor admin-UI toegang
- Progress-tracking per letter in UI (progress-balkje per achievement-kaart)

## 🔌 Auto-gedetecteerde endpoints
- `GET /achievements/all`
- `GET /achievements/admin/blueprints`  *(nieuw v7)*
- `GET /achievements/leaderboard`
- `GET /achievements/progress/{user_id}`
- `PATCH /achievements/admin/{achievement_id}` (admin edit titel/icon)
- `POST /achievements/admin/{achievement_id}/icon-upload` (admin upload icon)

## 📝 TODO / open items
- [ ] Admin UI: Instellingen → Features → Achievements-tab (placeholder-frame klaar)
- [ ] `PATCH /admin/blueprint/{name}` endpoint om blueprints te editen
- [ ] Contribution-agent uitbreiden met kb_card_count per user
- [ ] `unlock_manual` triggers registreren in andere modules (avatar/wallet callers)

## ⚠️ Splitting-trigger
> Als deze map > 4 sub-mappen krijgt of > 10 endpoints, overweeg splitsen.
> Huidig: 4 files, 2 subdirs (agents/, blueprints/), 6 endpoints.

## 🔐 Encryption-plan (F2F)
- Status nu: `⚪ slot leeg (klaar voor activatie)`
- Niet privacy-gevoelig — achievements zijn publiek in leaderboard

## 🧬 Relaties
- Hangt af van:
  - `modules.chat.xp_service` (grant_xp bij unlock)
  - `modules.core.storage` (JSON load/save)
  - Data: `data/achievements.json`, `data/system/users.json`, `data/knowledge/v2/`, `data/games/rps/stats.json`
- Wordt gebruikt door:
  - `modules.persons` (avatar → `unlock_milestone(user, 'avatar_first_upload')`)
  - `modules.wallet` (first token → `unlock_milestone(user, 'first_roar_token')`)
  - Frontend `AchievementsPage.js` + `LeaderboardPage.js`

## 📖 Voor toekomstige agents/developers
- **Nieuwe achievement-type toevoegen?**
  1. Maak `agents/{type}_agent.py` erf van `BaseAchievementAgent`
  2. Zet `handles_types` en `blueprint_name`
  3. Maak `blueprints/{type}_achievements.json` met XP/config
  4. Registreer in `service.AchievementService.__init__._agents` list
  5. Update deze blueprint-doc + `_meta.json`

- **XP-waarden wijzigen?** Alleen in `blueprints/*.json` — NIET in code.

- **Willem-regel**: *"Alles kunnen aanpassen behalve script zelf"* — houd deze regel voor alle nieuwe achievement-config.
