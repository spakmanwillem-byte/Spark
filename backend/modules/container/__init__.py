"""
Container module (v6_container_001) — Universeel container-patroon
=====================================================================
Door Willem: "alles wordt een container met eigen meta + (later) eigen
encryption — user, shop, asset, kb_card, card_deck, chat_thread, trade_bot.
Bij delete: hele container weg + cross-refs anonimiseren. F2F-veilig."

Eerste implementatie: USER-CONTAINER.
Later: shop (Winkelstraat F7), asset, card-deck, chat-thread, trade-bot.

Bestanden:
  - service.py    : Container CRUD + helpers (create/touch/delete/migrate/get_path)
  - user_helper.py: User-specifieke helpers (get_user_dir, get_user_resource_path)
  - routes.py     : FastAPI endpoints (/api/container/*)

Schema (per container):
  data/{type_dir}/{container_id}/_meta.json   ← schema uit modules.synapse.schema
  data/{type_dir}/{container_id}/data.json    ← of sub-dirs per resource
"""
from .routes import router  # noqa: F401
