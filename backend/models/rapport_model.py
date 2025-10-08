from typing import Any, Dict, List
from services.db import get_db


def insert_rapport(data: Dict[str, Any]) -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rapports (
                    agent_id, date_rapport, heure_rapport, zone, type_activite,
                    activites, photo_url, latitude, longitude, commentaire, status
                ) VALUES (
                    %(agent_id)s, %(date_rapport)s, %(heure_rapport)s, %(zone)s, %(type_activite)s,
                    %(activites)s, %(photo_url)s, %(latitude)s, %(longitude)s, %(commentaire)s, COALESCE(%(status)s, 'en_attente')
                ) RETURNING id
                """,
                data,
            )
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id


def list_rapports(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    where = []
    params = {}
    if filters.get("agent_id"):
        where.append("agent_id = %(agent_id)s")
        params["agent_id"] = filters["agent_id"]
    if filters.get("zone"):
        where.append("zone ILIKE %(zone)s")
        params["zone"] = f"%{filters['zone']}%"
    if filters.get("date_from"):
        where.append("date_rapport >= %(date_from)s")
        params["date_from"] = filters["date_from"]
    if filters.get("date_to"):
        where.append("date_rapport <= %(date_to)s")
        params["date_to"] = filters["date_to"]
    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, agent_id, date_rapport, heure_rapport, zone, type_activite, activites, photo_url, latitude, longitude, commentaire, status, created_at FROM rapports {where_clause} ORDER BY created_at DESC",
                params,
            )
            rows = cur.fetchall()
    cols = [
        "id",
        "agent_id",
        "date_rapport",
        "heure_rapport",
        "zone",
        "type_activite",
        "activites",
        "photo_url",
        "latitude",
        "longitude",
        "commentaire",
        "status",
        "created_at",
    ]
    return [dict(zip(cols, r)) for r in rows]



