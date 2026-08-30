"""
personal_agent — Persoonlijke context-wrapper voor Spark's antwoordvorming.

Willem 15-feb 2026 (v13_personal_agent_skeleton_001):
Vandaag haalt de composer (chat/compose_routes.py) persoonlijke context
op via directe reads op meerdere plekken: personalia (naam, gradatie),
recente dagboek-tags, actieve potjes, laatst gestelde vragen. Dat leidt
tot copy-paste en verschillende "wat weet Spark van mij"-antwoorden per
route.

personal_agent bundelt dit tot één functie: `snapshot(user_id, depth)`
die een gestructureerde dict returnt. Composer + capability-handler +
recap-service kunnen dezelfde snapshot hergebruiken.

Belangrijk: dit is een READER, geen writer. Persoonlijke feiten worden
elders geschreven (personalia_extraction_service, dagboek-routes).

TODO:
- Depth-levels: "minimal" (naam+gradatie), "standard" (+recente-tags),
  "deep" (+active-potjes+laatste-vragen+gemoeds-samenvatting).
- Cache per user_id met TTL 30s (compose-route wordt vaak achter elkaar
  aangeroepen binnen één gesprek).
- Privacy-matrix respect: honor `data/config/privacy_matrix.json`
  wanneer die er komt (ROADMAP Attente Spark Fase 2).
"""

from __future__ import annotations

import logging
from typing import Dict, Literal, Optional

logger = logging.getLogger(__name__)

Depth = Literal["minimal", "standard", "deep"]


def snapshot(user_id: str, depth: Depth = "standard") -> Dict:
    """Return gestructureerde persoonlijke context voor Spark's compose-laag.

    Verwachte output-structuur (voor later):
        {
            "user_id": str,
            "naam": str,
            "gradatie": int,
            "recente_tags": [str],           # (standard+)
            "actieve_potjes": [dict],        # (deep)
            "laatste_vragen": [str],         # (deep)
            "gemoed": {"stemming": str, "energie": int},  # (deep)
        }

    TODO:
    - Depth "minimal": lees enkel personalia.json.
    - Depth "standard": + dagboek recente tags via tag-index.
    - Depth "deep": + trade/user_potjes.json + laatste 5 chat-turns.
    """
    logger.debug("[personal_agent] snapshot() nog niet geïmplementeerd — user=%s depth=%s", user_id, depth)
    return {"user_id": user_id, "depth": depth, "not_implemented": True}


def recent_topics(user_id: str, limit: int = 5) -> list:
    """Return de recent-actieve onderwerpen (dagboek-tags + open loops).

    TODO:
    - Merge dagboek-tags (laatste 7d) + open loops uit spark_planner.
    - Dedup op stam-vorm (fuzzy match ≥92 via snap_service).
    """
    return []


def get_privacy_flag(user_id: str, veld: str) -> Optional[str]:
    """Return privacy-niveau voor een specifiek veld (bv. 'financien').

    TODO: leest data/config/privacy_matrix.json (nog te bouwen, ROADMAP
    Attente Spark Fase 2). Voor nu placeholder.
    """
    return None
