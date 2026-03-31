# Relatie & Privacy Systeem

## Structuur:

### Per User:
- relationships.json: Wie deze user kent (personen + andere users)
- Eigen data (dagboek, agenda, geluiden, etc.)
- Privacy: Alleen deze user heeft toegang

### Spark (user-000):
- relationships.json: Spark's relatie met elke user
- emotions.json: Emotie state + geschiedenis
- normen_waarden.json: Spark's normen en waarden

## Hoe het werkt:

### Scenario: Willem's moeder
1. Moeder is persoon → in Willem's relationships.json
2. Moeder wordt user → user_id link toegevoegd
3. Spark ziet verband maar scheidt privacy

### Privacy:
- User A's data → alleen A ziet
- User B's data → alleen B ziet
- Spark ziet STRUCTUUR (relaties) maar niet INHOUD (privacy)
