# Spark Core 2.0 — Roadmap

> **Deze file is opgesplitst op 4 aug 2026 (sessie 56d).** Origineel bewaard in `/app/_backups/ROADMAP_pre_split_20260806_132036.md` (3181 regels).

## 📖 Waar zoek je wat?

- 🧭 **Wegwijzer**: [`ROADMAP_INDEX.md`](./ROADMAP_INDEX.md)
- 🌷 **Kernvisie + huidige sessie + P0 next + architectuur**: [`ROADMAP_CORE.md`](./ROADMAP_CORE.md) *(begin hier)*
- 📜 **Afgeronde sessies (van sessie 8 t/m 56)**: [`ROADMAP_HISTORY.md`](./ROADMAP_HISTORY.md)
- 💡 **Open items + Cluster A-J ideeën**: [`ROADMAP_BACKLOG.md`](./ROADMAP_BACKLOG.md)
- 🎓 **Bewezen lessen + fout-patterns**: [`LEARNINGS.md`](./LEARNINGS.md)
- ✅ **Wat gebouwd is per sessie**: [`CHANGELOG.md`](./CHANGELOG.md)
- 🏗️ **Modules, hooks, integraties**: [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- 🎯 **Product-visie + user-personas**: [`PRD.md`](./PRD.md)

## ⚙️ Onderhouds-regels

- **CORE blijft <500 regels.** Als het groeit → oudste sessie naar HISTORY, done items naar CHANGELOG.
- **Nieuwe sessie voegt max 30 regels toe** aan CORE + CHANGELOG samen. Meer? Dan aan het praten i.p.v. bouwen.
- **`[x] DONE` items** verhuizen direct van BACKLOG naar CHANGELOG.
- **HISTORY** mag groeien maar comprimeer sessies >3 maanden oud tot 3-5 regels.

Spark's `spark_index` leest deze bestanden automatisch mee. Nieuwe `.md`-toevoegingen worden bij backend-restart geïndexeerd (of `POST /api/spark-index/rebuild`).
