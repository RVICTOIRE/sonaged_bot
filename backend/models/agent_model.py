from typing import Optional, List, Dict, Any
from services.db import get_db


def get_all_agents() -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nom, matricule, zone_affectation FROM agents ORDER BY nom ASC")
            rows = cur.fetchall()
    return [
        {"id": r[0], "nom": r[1], "matricule": r[2], "zone_affectation": r[3]} for r in rows
    ]


def find_agent_by_matricule(matricule: str) -> Optional[int]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM agents WHERE matricule = %s LIMIT 1", (matricule,))
            row = cur.fetchone()
    return row[0] if row else None



