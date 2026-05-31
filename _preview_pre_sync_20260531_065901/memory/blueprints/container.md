# Blueprint — container

> Auto-gegenereerde stub door synapse v6_synapse_002.
> Pad: `backend/modules/container`
> Gegenereerd op: 2026-05-26T16:13:26

## 🎯 Doel
Container module (v6_container_001) — Universeel container-patroon Door Willem: "alles wordt een container met eigen meta + (later) eigen encryption — user, shop, asset, kb_card, card_deck, chat_thread, trade_bot.

## ✅ Wat werkt al
- _(vul aan)_

## 🔌 Auto-gedetecteerde endpoints
- `DELETE /container/{container_type}/{container_id}`
- `GET /container/{container_type}`
- `GET /container/{container_type}/{container_id}/meta`
- `PATCH /container/{container_type}/{container_id}/meta`
- `POST /container/{container_type}`
- `POST /container/{container_type}/{container_id}/tag-for-deletion`

## 📝 TODO / open items
- [ ] _(vul aan)_

## ⚠️ Splitting-trigger
> Als deze map > 4 sub-mappen krijgt of > 10 endpoints, overweeg splitsen.
> Huidig: 4 files, 0 subdirs, 6 endpoints.

## 🔐 Encryption-plan (F2F)
- Status nu: `⚪ slot leeg (klaar voor activatie)`
- Wanneer aan: `algorithm = AES-256-GCM`, `key_holder = <owner>`
- Beschermt: _(welke velden zijn privacy-gevoelig?)_

## 🧬 Relaties
- Hangt af van: _(welke modules?)_
- Wordt gebruikt door: _(welke modules?)_
