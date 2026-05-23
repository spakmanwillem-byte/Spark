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

## 💸 Prijs-model & BTW (v6_btw_pas_bij_winst_001 — herzien 2026-05-23)

- **Anker-houders** (`user-000` Spark/Roadkill + `user-001` Willem) = fundering van het concept → **GEEN BTW**. 10 tokens × €5.08 = €50.80 elk, 1-op-1 zonder marge.
- **Klanten** (alle andere users) → betalen **volle bedrag**, dat gaat **volledig naar Spark's omzet** (`omzet_in`) en EUR-wallet. Spark gebruikt dit om mee te traden.
- **BTW komt PAS bij winst-realisatie**: bij elke sell-trade met positieve PnL wordt **21% van de winst** gereserveerd in `btw_reserve` (kasboek). Dat is wat later via **Moneybird** naar de Belastingdienst gaat.
- **Reden**: BTW is fiscaal verschuldigd over **marge/winst**, niet over alle omzet. Direct afromen bij verkoop = boekhoudkundig onjuist.
- **Fixed prijs** zolang circulating < `FIXED_PRICE_LIMIT` (huidige drempel)
- **Daarna dynamisch**: prijs stijgt met groei van circulating (early-supporter effect)
- **Vroege kopers profiteren** van prijs-stijging (te benoemen in voorwaarden + privacy)

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
