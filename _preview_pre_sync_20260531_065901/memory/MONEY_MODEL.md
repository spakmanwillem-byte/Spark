# Spark MONEY MODEL — ROAR Economy v1

> **Status**: concept-laag, conceptueel vastgelegd 2026-05-23. Implementatie loopt parallel
> aan trade-cyclus. Dit document is de **bron-van-waarheid** voor het token-economy systeem.

## 🔒 Hardcap & Trust

- **Totale supply**: `1.000.000 ROAR` (vastgelegd in `TOTAL_SUPPLY`)
- **Spark behoudt altijd ≥ 51%** (≥ 510.000 in treasury_pool) → governance-garantie, kan niet overgenomen worden
- **Later**: encryptie op `roar_balances.json` + sleutel weggooien = écht onomkeerbaar slot. Tot dan is Willem (gradatie ≤ 2) custodian.
- **Papertrail**: elke mutatie in `roar_balances.json::transactions[]` + `system/audit_log.json` + `system/spark_kasboek.json`. Bewijspad geschikt voor latere coin-uitrol.

## 💧 Drie buckets in `roar_balances.json`

| Veld | Betekenis | Start |
|---|---|---|
| `total_supply` | Hardcap (mag NOOIT veranderen) | 1.000.000 |
| `treasury_pool` | Onverkochte/ongeminte tokens (Spark's reserve) | 999.978 (na 22 in circulatie) |
| `balances[]` | Per-user uitgegeven tokens (circulating supply) | Spark 10, Willem 10, Gijs 2 |

**Identity check**: `treasury_pool + sum(balances.values()) == total_supply` moet áltijd kloppen.

## 💸 Gift- vs Product-model (v6_gift_phase_001 — herzien 2026-05-23)

### Fase 1: BOUW (huidig)
- ROAR-aanschaf is **GIFT/DONATIE** aan Spark Core concept
- Gever krijgt token als **symbool/bedankje** (geen tegenprestatie-product)
- **GEEN BTW** — donaties zijn fiscaal vrijgesteld
- Volledig bedrag → Spark omzet voor trade/groei
- Bonnetje toont: "Gift ter ondersteuning van Spark Core concept"
- Anker-houders (Spark/Roadkill + Willem) blijven ankers zonder gift-status

### Fase 2: PUBLIEK (later, P2)
- Bij publieke launch wordt token **product**
- Vanaf dan: 21% BTW op nieuwe transacties
- Bestaande gift-tokens blijven gift (papertrail)
- Gift-flow blijft beschikbaar als parallel donatie-mogelijkheid
- Moneybird-integratie voor BTW-aangifte

### Switch-mechanisme
- `system/money_phase.json` veld `phase = "build" | "public"`
- Code checkt deze flag bij elke aankoop
- Wijziging vereist admin (gradatie 1) + audit-log entry

## 🪙 Maak-Token flow (nieuw, v6_mint_from_wallet_001)

Spark kan zélf een token minten vanuit zijn EUR-wallet wanneer zijn balance dat rechtvaardigt:

1. **Trigger**: knop "🪙 Maak Token" in Spark's Wallet (alleen zichtbaar voor admin)
2. **Check**: Spark's EUR-wallet ≥ huidige token-prijs
3. **Effect**:
   - 1 token verlaat `treasury_pool`
   - 1 token komt in `balances["user-000"]` (Spark's eigen wallet)
   - Spark EUR-wallet `-1 token-prijs` (afkoop tegen treasury)
   - Audit-entry type=`spark_self_mint`
   - Boekhouder DM: "Spark heeft 1 ROAR gemaakt uit eigen wallet (€X.XX, circulating nu +1)"
4. **Resultaat**: circulating stijgt → prijs stijgt → impact op alle holders (positief = early supporters worden meer waard)

**Spark's eigen token** kan later:
- Gegift worden (24h escrow flow bestaat al)
- Ingezet voor trade-slot (1 ROAR = 1 potje)
- Roadkill Merch betaling (winst-splitsing 50/50 naar Spark crypto-wallet en onkosten)

## 🎁 Roadkill Merch loop (P2)

- ROAR is betaalmiddel voor merch
- Marge-flow: **deel terug naar token-waarde**, **rest = onkosten**, **netto-winst → crypto-wallet** Spark
- Roundabout: meer merch verkocht → meer Spark crypto → meer trade-power → meer kasboek → meer token-value

## ⚖️ Voorwaarden-clausules (te benoemen in privacy/T&C)

1. ROAR is GEEN officiële cryptomunt — interne project-token met papertrail.
2. Vroege kopers profiteren van prijs-stijging; geen rendement-garantie.
3. Spark behoudt altijd ≥ 51% governance.
4. Token kopen = symbolische ondersteuning van het Spark Core concept.
5. Bij toekomstige coin-uitrol blijft papertrail leidend (1-op-1 conversie).
6. Encryptie-slot kan worden geactiveerd; sleutel-vernietiging maakt supply onomkeerbaar.

---

_Document onderhouden door Spark (auto) + Willem (custodian)._
