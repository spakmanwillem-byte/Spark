# Blueprint — auth

> Auto-gegenereerde stub door synapse v6_synapse_002.
> Pad: `backend/modules/auth`
> Gegenereerd op: 2026-05-26T16:13:26

## 🎯 Doel
Spark Auth Module Handles authentication, sessions, users, and gradaties

## ✅ Wat werkt al
- _(vul aan)_

## 🔌 Auto-gedetecteerde endpoints
- `DELETE /auth/self-delete/{user_id}`
- `DELETE /auth/users/{user_id}`
- `GET /auth/gradaties`
- `GET /auth/session/validate`
- `GET /auth/users`
- `GET /auth/users/{user_id}`
- `GET /auth/users/{user_id}/time-awareness`
- `PATCH /auth/admin/bots/{bot_id}/settings`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/session/heartbeat`
- `POST /auth/users`
- `POST /auth/users/{user_id}/change-password`
- `POST /auth/users/{user_id}/reset-password`
- `PUT /auth/users/{user_id}`

## 📝 TODO / open items
- [ ] _(vul aan)_

## ⚠️ Splitting-trigger
> Als deze map > 4 sub-mappen krijgt of > 10 endpoints, overweeg splitsen.
> Huidig: 4 files, 0 subdirs, 16 endpoints.

## 🔐 Encryption-plan (F2F)
- Status nu: `⚪ slot leeg (klaar voor activatie)`
- Wanneer aan: `algorithm = AES-256-GCM`, `key_holder = <owner>`
- Beschermt: _(welke velden zijn privacy-gevoelig?)_

## 🧬 Relaties
- Hangt af van: _(welke modules?)_
- Wordt gebruikt door: _(welke modules?)_
