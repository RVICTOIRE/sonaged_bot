from flask import Blueprint, request
from services.db import get_db


agent_bp = Blueprint("agent", __name__)


@agent_bp.get("/agents")
def list_agents():
    matricule = request.args.get("matricule")
    with get_db() as conn:
        with conn.cursor() as cur:
            if matricule:
                # Normalisation: suppression des espaces et mise en majuscules
                cur.execute(
                    """
                    SELECT id, nom, matricule, zone_affectation
                    FROM agents
                    WHERE replace(upper(matricule),' ','') = replace(upper(%s),' ','')
                    LIMIT 1
                    """,
                    (matricule,),
                )
                row = cur.fetchone()
                if not row:
                    return {"error": "Agent introuvable"}, 404
                return {
                    "items": [
                        {"id": row[0], "nom": row[1], "matricule": row[2], "zone_affectation": row[3]}
                    ]
                }
            cur.execute("SELECT id, nom, matricule, zone_affectation FROM agents ORDER BY nom ASC")
            rows = cur.fetchall()
    data = [
        {"id": r[0], "nom": r[1], "matricule": r[2], "zone_affectation": r[3]}
        for r in rows
    ]
    return {"items": data}


def _matricule_variants(m: str):
    m0 = (m or "").strip()
    variants = set([m0])
    # Add whatsapp: prefix if absent
    if not m0.lower().startswith("whatsapp:"):
        variants.add(f"whatsapp:{m0}")
    # Ensure plus for phone-like values
    if m0.isdigit():
        variants.add("+" + m0)
        variants.add(f"whatsapp:+{m0}")
    elif m0.startswith("+"):
        variants.add(m0.lstrip("+"))
        variants.add(f"whatsapp:{m0}")
    # Remove spaces
    variants.add(m0.replace(" ", ""))
    return list(variants)


@agent_bp.post("/agents/verify")
def verify_agent():
    payload = request.get_json(silent=True) or {}
    matricule = (payload.get("matricule") or "").strip()
    if not matricule:
        return {"error": "matricule requis"}, 400
    candidates = _matricule_variants(matricule)
    with get_db() as conn:
        with conn.cursor() as cur:
            for cand in candidates:
                cur.execute(
                    "SELECT id, nom, matricule, zone_affectation FROM agents WHERE matricule = %s LIMIT 1",
                    (cand,),
                )
                row = cur.fetchone()
                if row:
                    return {
                        "agent": {
                            "id": row[0],
                            "nom": row[1],
                            "matricule": row[2],
                            "zone_affectation": row[3],
                        }
                    }
    return {"error": "Agent introuvable"}, 404


@agent_bp.get("/health/db")
def health_db():
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"db": "ok"}
    except Exception as e:
        return {"db": "error", "detail": str(e)}, 500



