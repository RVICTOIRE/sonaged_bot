from flask import Blueprint, request
from services.db import get_db
from services.parser import parse_message_text


rapport_bp = Blueprint("rapport", __name__)


@rapport_bp.post("/rapport")
def create_rapport():
    payload = request.get_json(silent=True) or {}
    # Normalize and provide defaults for missing fields
    data = {
        "agent_id": payload.get("agent_id"),
        "date_rapport": payload.get("date_rapport"),
        "heure_rapport": payload.get("heure_rapport"),
        "zone": payload.get("zone"),
        "type_activite": payload.get("type_activite"),
        "activites": payload.get("activites"),
        "photo_url": payload.get("photo_url"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "commentaire": payload.get("commentaire"),
    }
    if data.get("agent_id") is None:
        return {"error": "agent_id is required"}, 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rapports (
                    agent_id, date_rapport, heure_rapport, zone, type_activite, activites, photo_url, latitude, longitude, commentaire
                ) VALUES (
                    %(agent_id)s, %(date_rapport)s, %(heure_rapport)s, %(zone)s, %(type_activite)s, %(activites)s, %(photo_url)s, %(latitude)s, %(longitude)s, %(commentaire)s
                ) RETURNING id
                """,
                data,
            )
            new_id = cur.fetchone()[0]
            conn.commit()
    return {"id": new_id}, 201


@rapport_bp.get("/rapports")
def list_rapports():
    agent_id = request.args.get("agent_id")
    zone = request.args.get("zone")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    filters = []
    params = {}
    if agent_id:
        filters.append("agent_id = %(agent_id)s")
        params["agent_id"] = agent_id
    if zone:
        filters.append("zone ILIKE %(zone)s")
        params["zone"] = f"%{zone}%"
    if date_from:
        filters.append("date_rapport >= %(date_from)s")
        params["date_from"] = date_from
    if date_to:
        filters.append("date_rapport <= %(date_to)s")
        params["date_to"] = date_to

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT id, agent_id, date_rapport, heure_rapport, zone, type_activite, activites, photo_url, latitude, longitude, commentaire, created_at FROM rapports {where_clause} ORDER BY created_at DESC",
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
        "created_at",
    ]
    items = []
    for r in rows:
        obj = dict(zip(cols, r))
        # Normalize JSON-serializable types
        if obj.get("date_rapport") is not None:
            obj["date_rapport"] = obj["date_rapport"].isoformat()
        if obj.get("heure_rapport") is not None:
            obj["heure_rapport"] = obj["heure_rapport"].isoformat()
        if obj.get("created_at") is not None:
            try:
                obj["created_at"] = obj["created_at"].isoformat()
            except Exception:
                obj["created_at"] = str(obj["created_at"])
        # Ensure activites is a list
        if obj.get("activites") is None:
            obj["activites"] = []
        items.append(obj)
    return {"items": items}


@rapport_bp.post("/rapport/photo")
def add_photo():
    data = request.get_json(silent=True) or {}
    rapport_id = data.get("rapport_id")
    photo_url = data.get("photo_url")
    if not rapport_id or not photo_url:
        return {"error": "rapport_id and photo_url are required"}, 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE rapports SET photo_url = %s WHERE id = %s", (photo_url, rapport_id))
            conn.commit()
    return {"ok": True}


@rapport_bp.post("/rapport/parse")
def parse_text():
    payload = request.get_json(silent=True) or {}
    text = payload.get("text", "")
    result = parse_message_text(text)
    return result


# Daily Report endpoints (MVP)
@rapport_bp.post("/rapport_journalier")
def create_daily_report():
    payload = request.get_json(silent=True) or {}
    date_rapport = payload.get("date_rapport")
    unite_commune = payload.get("unite_commune")
    agent_id = payload.get("agent_id")
    if not date_rapport:
        return {"error": "date_rapport required"}, 400
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rapport_journalier (date_rapport, unite_commune, agent_id, observation_rh)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (date_rapport, unite_commune, agent_id, payload.get("observation_rh")),
            )
            rid = cur.fetchone()[0]
            conn.commit()
    return {"id": rid}, 201


@rapport_bp.get("/rapport_journalier/<int:rid>")
def get_daily_report(rid: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, date_rapport, unite_commune, agent_id, observation_rh, created_at FROM rapport_journalier WHERE id = %s", (rid,))
            head = cur.fetchone()
            if not head:
                return {"error": "not found"}, 404

            cur.execute("SELECT periode, categorie, effectifs, presents, absents, malades, conges, remplacement FROM effectifs_jour WHERE rapport_id = %s ORDER BY id", (rid,))
            effectifs = cur.fetchall()

            cur.execute("SELECT circuits_planifies, circuits_collectes, tonnage, depots_recurrents, depots_recurrents_leves, depots_sauvages_identifies, depots_sauvages_traites FROM collecte_indicateurs WHERE rapport_id = %s", (rid,))
            coll_ind = cur.fetchone()

            cur.execute("SELECT nom, numero_porte, heure_debut, heure_fin, duree, poids, observation FROM collecte_circuits WHERE rapport_id = %s ORDER BY id", (rid,))
            circuits = cur.fetchall()

            cur.execute("SELECT sites_caisse, nb_caisses, nb_caisses_levees, poids_collecte FROM polybenne WHERE rapport_id = %s", (rid,))
            poly = cur.fetchone()

            cur.execute("SELECT circuits_planifies, circuits_balayes, km_planifie, km_balayes, km_desensables FROM nettoiement WHERE rapport_id = %s", (rid,))
            netto = cur.fetchone()

            cur.execute("SELECT libelle, sites, nb_bacs, nb_bacs_leves, observation FROM bacs_indicateurs WHERE rapport_id = %s ORDER BY id", (rid,))
            bacs = cur.fetchall()

            cur.execute("SELECT nb_agents, nb_pelles_mecaniques, nb_tasseuses, nb_camions_ouvert, sites_quartiers FROM moyens_equipements WHERE rapport_id = %s", (rid,))
            moyens = cur.fetchone()

            cur.execute("SELECT nom_site FROM sites_intervention WHERE rapport_id = %s ORDER BY id", (rid,))
            sites = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT contenu FROM difficultes WHERE rapport_id = %s ORDER BY id", (rid,))
            diff = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT contenu FROM recommandations WHERE rapport_id = %s ORDER BY id", (rid,))
            reco = [r[0] for r in cur.fetchall()]

            cur.execute("SELECT photo_url FROM rapport_photos WHERE rapport_id = %s ORDER BY id", (rid,))
            photos = [r[0] for r in cur.fetchall()]

    head_keys = ["id","date_rapport","unite_commune","agent_id","observation_rh","created_at"]
    result = {k:v for k,v in zip(head_keys, head)}
    # normalize dates/timestamps
    if result.get("date_rapport") is not None:
        result["date_rapport"] = result["date_rapport"].isoformat()
    if result.get("created_at") is not None:
        try:
            result["created_at"] = result["created_at"].isoformat()
        except Exception:
            result["created_at"] = str(result["created_at"]) 

    result["effectifs"] = [
        {
            "periode": r[0],
            "categorie": r[1],
            "effectifs": r[2],
            "presents": r[3],
            "absents": r[4],
            "malades": r[5],
            "conges": r[6],
            "remplacement": r[7],
        } for r in effectifs
    ]
    if coll_ind:
        result["collecte_indicateurs"] = {
            "circuits_planifies": coll_ind[0],
            "circuits_collectes": coll_ind[1],
            "tonnage": float(coll_ind[2]) if coll_ind[2] is not None else None,
            "depots_recurrents": coll_ind[3],
            "depots_recurrents_leves": coll_ind[4],
            "depots_sauvages_identifies": coll_ind[5],
            "depots_sauvages_traites": coll_ind[6],
        }
    result["collecte_circuits"] = [
        {
            "nom": r[0],
            "numero_porte": r[1],
            "heure_debut": r[2].isoformat() if r[2] else None,
            "heure_fin": r[3].isoformat() if r[3] else None,
            "duree": r[4],
            "poids": r[5],
            "observation": r[6],
        } for r in circuits
    ]
    if poly:
        result["polybenne"] = {
            "sites_caisse": poly[0],
            "nb_caisses": poly[1],
            "nb_caisses_levees": poly[2],
            "poids_collecte": float(poly[3]) if poly[3] is not None else None,
        }
    if netto:
        result["nettoiement"] = {
            "circuits_planifies": netto[0],
            "circuits_balayes": netto[1],
            "km_planifie": netto[2],
            "km_balayes": netto[3],
            "km_desensables": float(netto[4]) if netto[4] is not None else None,
        }
    result["bacs_indicateurs"] = [
        {"libelle": r[0], "sites": r[1], "nb_bacs": r[2], "nb_bacs_leves": r[3], "observation": r[4]} for r in bacs
    ]
    if moyens:
        result["moyens_equipements"] = {
            "nb_agents": moyens[0],
            "nb_pelles_mecaniques": moyens[1],
            "nb_tasseuses": moyens[2],
            "nb_camions_ouvert": moyens[3],
            "sites_quartiers": moyens[4],
        }
    result["sites_intervention"] = sites
    result["difficultes"] = diff
    result["recommandations"] = reco
    result["photos"] = photos

    return result


# ===== Collecte: Indicateurs =====
@rapport_bp.post("/rapport_journalier/<int:rid>/collecte/indicateurs")
def set_collecte_indicateurs(rid: int):
    payload = request.get_json(silent=True) or {}
    with get_db() as conn:
        with conn.cursor() as cur:
            # check exists
            cur.execute("SELECT id FROM collecte_indicateurs WHERE rapport_id = %s", (rid,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE collecte_indicateurs
                    SET circuits_planifies=%s, circuits_collectes=%s, tonnage=%s,
                        depots_recurrents=%s, depots_recurrents_leves=%s,
                        depots_sauvages_identifies=%s, depots_sauvages_traites=%s
                    WHERE rapport_id=%s
                    """,
                    (
                        payload.get("circuits_planifies"),
                        payload.get("circuits_collectes"),
                        payload.get("tonnage"),
                        payload.get("depots_recurrents"),
                        payload.get("depots_recurrents_leves"),
                        payload.get("depots_sauvages_identifies"),
                        payload.get("depots_sauvages_traites"),
                        rid,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO collecte_indicateurs (
                        rapport_id, circuits_planifies, circuits_collectes, tonnage,
                        depots_recurrents, depots_recurrents_leves,
                        depots_sauvages_identifies, depots_sauvages_traites
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        rid,
                        payload.get("circuits_planifies"),
                        payload.get("circuits_collectes"),
                        payload.get("tonnage"),
                        payload.get("depots_recurrents"),
                        payload.get("depots_recurrents_leves"),
                        payload.get("depots_sauvages_identifies"),
                        payload.get("depots_sauvages_traites"),
                    ),
                )
            conn.commit()
    return {"ok": True}


# ===== Collecte: Circuits CRUD =====
@rapport_bp.post("/rapport_journalier/<int:rid>/collecte/circuits")
def add_collecte_circuit(rid: int):
    payload = request.get_json(silent=True) or {}
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collecte_circuits (
                    rapport_id, nom, numero_porte, heure_debut, heure_fin, duree, poids, observation
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
                """,
                (
                    rid,
                    payload.get("nom"),
                    payload.get("numero_porte"),
                    payload.get("heure_debut"),
                    payload.get("heure_fin"),
                    payload.get("duree"),
                    payload.get("poids"),
                    payload.get("observation"),
                ),
            )
            line_id = cur.fetchone()[0]
            conn.commit()
    return {"ligne_id": line_id}, 201


@rapport_bp.patch("/rapport_journalier/<int:rid>/collecte/circuits/<int:ligne_id>")
def update_collecte_circuit(rid: int, ligne_id: int):
    payload = request.get_json(silent=True) or {}
    sets = []
    vals = []
    for field in [
        "nom",
        "numero_porte",
        "heure_debut",
        "heure_fin",
        "duree",
        "poids",
        "observation",
    ]:
        if field in payload:
            sets.append(f"{field} = %s")
            vals.append(payload.get(field))
    if not sets:
        return {"error": "no fields to update"}, 400
    vals.extend([ligne_id, rid])
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE collecte_circuits SET {', '.join(sets)} WHERE id = %s AND rapport_id = %s",
                tuple(vals),
            )
            conn.commit()
    return {"ok": True}


@rapport_bp.delete("/rapport_journalier/<int:rid>/collecte/circuits/<int:ligne_id>")
def delete_collecte_circuit(rid: int, ligne_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM collecte_circuits WHERE id = %s AND rapport_id = %s", (ligne_id, rid))
            conn.commit()
    return {"ok": True}


# ===== Polybenne (upsert) =====
@rapport_bp.post("/rapport_journalier/<int:rid>/polybenne")
def set_polybenne(rid: int):
    payload = request.get_json(silent=True) or {}
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM polybenne WHERE rapport_id = %s", (rid,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE polybenne
                    SET sites_caisse=%s, nb_caisses=%s, nb_caisses_levees=%s, poids_collecte=%s
                    WHERE rapport_id=%s
                    """,
                    (
                        payload.get("sites_caisse"),
                        payload.get("nb_caisses"),
                        payload.get("nb_caisses_levees"),
                        payload.get("poids_collecte"),
                        rid,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO polybenne (
                        rapport_id, sites_caisse, nb_caisses, nb_caisses_levees, poids_collecte
                    ) VALUES (%s,%s,%s,%s,%s)
                    """,
                    (
                        rid,
                        payload.get("sites_caisse"),
                        payload.get("nb_caisses"),
                        payload.get("nb_caisses_levees"),
                        payload.get("poids_collecte"),
                    ),
                )
            conn.commit()
    return {"ok": True}


# ===== Nettoiement (upsert) =====
@rapport_bp.post("/rapport_journalier/<int:rid>/nettoiement")
def set_nettoiement(rid: int):
    payload = request.get_json(silent=True) or {}
    # Accept both 'km_*' and 'kilometrage_*' keys
    km_plan = payload.get("km_planifie")
    if km_plan is None:
        km_plan = payload.get("kilometrage_planifie")
    km_bal = payload.get("km_balayes")
    if km_bal is None:
        km_bal = payload.get("kilometrage_balaye")
    km_des = payload.get("km_desensables")
    if km_des is None:
        km_des = payload.get("kilometrage_desensable")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM nettoiement WHERE rapport_id = %s", (rid,))
            row = cur.fetchone()
            if row:
                cur.execute(
                    """
                    UPDATE nettoiement
                    SET circuits_planifies=%s, circuits_balayes=%s,
                        km_planifie=%s, km_balayes=%s, km_desensables=%s
                    WHERE rapport_id=%s
                    """,
                    (
                        payload.get("circuits_planifies"),
                        payload.get("circuits_balayes"),
                        km_plan,
                        km_bal,
                        km_des,
                        rid,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO nettoiement (
                        rapport_id, circuits_planifies, circuits_balayes, km_planifie, km_balayes, km_desensables
                    ) VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        rid,
                        payload.get("circuits_planifies"),
                        payload.get("circuits_balayes"),
                        km_plan,
                        km_bal,
                        km_des,
                    ),
                )
            conn.commit()
    return {"ok": True}


# ===== Mobilier Urbain (PRN/PP/Bacs de rue) =====
@rapport_bp.post("/rapport_journalier/<int:rid>/mobilier_urbain")
def set_mobilier_urbain(rid: int):
    payload = request.get_json(silent=True) or {}
    blocks = {
        "PRN": payload.get("prn") or {},
        "PP": payload.get("pp") or {},
        "Bacs de rue": payload.get("bacs_rue") or {},
    }
    with get_db() as conn:
        with conn.cursor() as cur:
            for libelle, data in blocks.items():
                cur.execute(
                    "SELECT id FROM bacs_indicateurs WHERE rapport_id = %s AND libelle = %s",
                    (rid, libelle),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """
                        UPDATE bacs_indicateurs
                        SET sites=%s, nb_bacs=%s, nb_bacs_leves=%s, observation=%s
                        WHERE id=%s
                        """,
                        (
                            data.get("sites"),
                            data.get("bacs"),
                            data.get("bacs_leves"),
                            data.get("observations"),
                            row[0],
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO bacs_indicateurs (rapport_id, libelle, sites, nb_bacs, nb_bacs_leves, observation)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            rid,
                            libelle,
                            data.get("sites"),
                            data.get("bacs"),
                            data.get("bacs_leves"),
                            data.get("observations"),
                        ),
                    )
            conn.commit()
    return {"ok": True}


# ===== Interventions Ponctuelles (moyens + sites) =====
@rapport_bp.post("/rapport_journalier/<int:rid>/interventions_ponctuelles")
def set_interventions_ponctuelles(rid: int):
    payload = request.get_json(silent=True) or {}
    with get_db() as conn:
        with conn.cursor() as cur:
            # moyens_equipements upsert
            cur.execute("SELECT id FROM moyens_equipements WHERE rapport_id = %s", (rid,))
            row = cur.fetchone()
            fields = (
                payload.get("agents_mobilises"),
                payload.get("pelles_mecaniques"),
                payload.get("tasseuses"),
                payload.get("camions_ciel_ouvert"),
                payload.get("sites_intervention"),
            )
            if row:
                cur.execute(
                    """
                    UPDATE moyens_equipements
                    SET nb_agents=%s, nb_pelles_mecaniques=%s, nb_tasseuses=%s, nb_camions_ouvert=%s, sites_quartiers=%s
                    WHERE rapport_id=%s
                    """,
                    (*fields, rid),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO moyens_equipements (rapport_id, nb_agents, nb_pelles_mecaniques, nb_tasseuses, nb_camions_ouvert, sites_quartiers)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    (rid, *fields),
                )

            # optional: split sites_intervention into rows (normalize)
            if payload.get("sites_intervention"):
                # clear and insert
                cur.execute("DELETE FROM sites_intervention WHERE rapport_id = %s", (rid,))
                sites = [s.strip() for s in payload["sites_intervention"].split(",") if s.strip()]
                for s in sites:
                    cur.execute(
                        "INSERT INTO sites_intervention (rapport_id, nom_site) VALUES (%s,%s)",
                        (rid, s),
                    )

            conn.commit()
    return {"ok": True}


# ===== Difficultés & Recommandations =====
@rapport_bp.post("/rapport_journalier/<int:rid>/difficultes")
def set_difficultes(rid: int):
    payload = request.get_json(silent=True) or {}
    # Accept either {items: [..]} or {text: "a; b; c"}
    items = payload.get("items")
    if not items and payload.get("text"):
        items = [s.strip() for s in str(payload.get("text")).split(";") if s.strip()]
    if items is None:
        items = []
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM difficultes WHERE rapport_id = %s", (rid,))
            for d in items:
                cur.execute("INSERT INTO difficultes (rapport_id, contenu) VALUES (%s,%s)", (rid, d))
            conn.commit()
    return {"ok": True, "count": len(items)}


@rapport_bp.post("/rapport_journalier/<int:rid>/recommandations")
def set_recommandations(rid: int):
    payload = request.get_json(silent=True) or {}
    items = payload.get("items")
    if not items and payload.get("text"):
        items = [s.strip() for s in str(payload.get("text")).split(";") if s.strip()]
    if items is None:
        items = []
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM recommandations WHERE rapport_id = %s", (rid,))
            for d in items:
                cur.execute("INSERT INTO recommandations (rapport_id, contenu) VALUES (%s,%s)", (rid, d))
            conn.commit()
    return {"ok": True, "count": len(items)}


# ===== Effectifs (matin / apres_midi) =====
@rapport_bp.post("/rapport_journalier/<int:rid>/effectifs")
def set_effectifs(rid: int):
    payload = request.get_json(silent=True) or {}
    items = payload.get("items") or []
    # items: [{ periode: 'matin'|'apres_midi', categorie, effectifs, presents, absents, malades, conges, remplacement }]
    if not isinstance(items, list):
        return {"error": "items must be a list"}, 400
    with get_db() as conn:
        with conn.cursor() as cur:
            # Simple strategy: clear and reinsert
            cur.execute("DELETE FROM effectifs_jour WHERE rapport_id = %s", (rid,))
            for it in items:
                cur.execute(
                    """
                    INSERT INTO effectifs_jour (
                        rapport_id, periode, categorie, effectifs, presents, absents, malades, conges, remplacement
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        rid,
                        it.get("periode"),
                        it.get("categorie"),
                        it.get("effectifs"),
                        it.get("presents"),
                        it.get("absents"),
                        it.get("malades"),
                        it.get("conges"),
                        it.get("remplacement"),
                    ),
                )
            conn.commit()
    return {"ok": True, "count": len(items)}


