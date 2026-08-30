"""
modules.agents — Subject-Agent laag (ROADMAP Principe #8).

Elke Agent hier is een dunne wrapper rond een bestaand mechanisme (registry,
commando, KB-lade, systeemstate). Het doel:
- losse strings/commando's krijgen een Agent + KB-kaart zodat Spark
  introspectief kan uitleggen wat er onder de motorkap gebeurt;
- intent-matching (chat/routes) blijft gescheiden van uitvoering;
- self-awareness hooks (snap_agent, deprecation, drift-repair) hangen op
  één laag ipv verspreid door de codebase.

Deze module bevat GEEN route-registratie en GEEN volledige business-logica —
puur skeletons met signatures + TODO's. Wordt stapsgewijs ingevuld naarmate
elke agent geactiveerd wordt.
"""
