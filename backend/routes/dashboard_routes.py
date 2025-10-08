from flask import Blueprint, request, jsonify
from services.db import get_db

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.get("/dashboard/summary")
def dashboard_summary():
    """
    Retourne un résumé agrégé des rapports journaliers pour une date/unité.
    Query params:
      - date (YYYY-MM-DD) requis
      - unite (optionnel)
    """
    target_date = request.args.get("date")
    unite = request.args.get("unite")

    if not target_date:
        return {"error": "Paramètre 'date' requis (YYYY-MM-DD)"}, 400

    result = {
        "date": target_date,
        "unite": unite or None,
        "reports": []
    }

    with get_db() as conn:
        with conn.cursor() as cur:
            # Récupérer les rapports du jour (et unité si fournie)
            if unite:
                cur.execute(
                    """
                    SELECT rj.id, rj.date_rapport, rj.unite_commune, rj.status,
                           COALESCE(rj.completion_percentage, 0) AS completion_percentage,
                           rj.last_updated,
                           a.nom AS agent_nom
                    FROM rapport_journalier rj
                    LEFT JOIN agents a ON a.id = rj.agent_id
                    WHERE rj.date_rapport = %s AND rj.unite_commune = %s
                    ORDER BY rj.last_updated DESC
                    """,
                    [target_date, unite],
                )
            else:
                cur.execute(
                    """
                    SELECT rj.id, rj.date_rapport, rj.unite_commune, rj.status,
                           COALESCE(rj.completion_percentage, 0) AS completion_percentage,
                           rj.last_updated,
                           a.nom AS agent_nom
                    FROM rapport_journalier rj
                    LEFT JOIN agents a ON a.id = rj.agent_id
                    WHERE rj.date_rapport = %s
                    ORDER BY rj.last_updated DESC
                    """,
                    [target_date],
                )

            rows = cur.fetchall()

            for (rid, _date_r, unite_r, status, completion, last_updated, agent_nom) in rows:
                print(f"[DEBUG DASHBOARD] Traitement du rapport {rid} ({agent_nom})")
                try:
                    # --- COLLECTE ---
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(MAX(circuits_planifies), 0),
                            COALESCE(MAX(circuits_collectes), 0),
                            COALESCE(MAX(tonnage), 0),
                            COALESCE(MAX(depots_recurrents), 0),
                            COALESCE(MAX(depots_recurrents_leves), 0)
                        FROM collecte_indicateurs
                        WHERE rapport_id = %s
                        """,
                        [int(rid)],
                    )
                    row = cur.fetchone()
                    (col_plan, col_coll, col_ton, dep_rec, dep_rec_lev) = row or (0, 0, 0, 0, 0)

                    # --- CIRCUITS COLLECTE ---
                    cur.execute(
                        """
                        SELECT 
                            CASE 
                              WHEN LOWER(COALESCE(observation,'')) LIKE '%%termin%%' THEN 'Terminé'
                              WHEN LOWER(COALESCE(observation,'')) LIKE '%%panne%%' THEN 'Panne'
                              WHEN LOWER(COALESCE(observation,'')) LIKE '%%non%%' AND LOWER(observation) LIKE '%%termin%%' THEN 'Non terminé'
                              ELSE 'Autre'
                            END AS derive_statut,
                            COUNT(*)
                        FROM collecte_circuits
                        WHERE rapport_id = %s
                        GROUP BY derive_statut
                        """,
                        [int(rid)],
                    )
                    circ_rows = cur.fetchall() or []
                    circuits = {}
                    for r in circ_rows:
                        k = r[0] if len(r) > 0 else ''
                        v = r[1] if len(r) > 1 else 0
                        circuits[k or ""] = v or 0

                    # --- POLYBENNE ---
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(MAX(sites_caisse), 0),
                            COALESCE(MAX(nb_caisses), 0),
                            COALESCE(MAX(nb_caisses_levees), 0),
                            COALESCE(MAX(poids_collecte), 0)
                        FROM polybenne
                        WHERE rapport_id = %s
                        """,
                        [int(rid)],
                    )
                    poly_row = cur.fetchone()
                    (poly_sites, poly_caisses, poly_levees, poly_poids) = poly_row or (0, 0, 0, 0)

                    # --- NETTOIEMENT ---
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(MAX(NULLIF(km_planifie, '')), '0'),
                            COALESCE(MAX(NULLIF(km_balayes, '')), '0'),
                            COALESCE(MAX(km_desensables), 0)
                        FROM nettoiement
                        WHERE rapport_id = %s
                        """,
                        [int(rid)],
                    )
                    row = cur.fetchone() or ('0', '0', 0)
                    (km_plan_txt, km_balayes_txt, km_des) = row

                    def _to_num(txt):
                        try:
                            return float(txt)
                        except Exception:
                            return 0.0
                    km_plan = _to_num(km_plan_txt)
                    km_balayes = _to_num(km_balayes_txt)

                    # --- MOBILIER URBAIN ---
                    cur.execute(
                        """
                        SELECT libelle, 
                               COALESCE(SUM(sites), 0),
                               COALESCE(SUM(nb_bacs), 0),
                               COALESCE(SUM(nb_bacs_leves), 0)
                        FROM bacs_indicateurs
                        WHERE rapport_id = %s
                        GROUP BY libelle
                        """,
                        [int(rid)],
                    )
                    mobilier_rows = cur.fetchall() or []
                    mobilier = {}
                    for row_m in mobilier_rows:
                        lib = row_m[0] if len(row_m) > 0 else ''
                        s = row_m[1] if len(row_m) > 1 else 0
                        b = row_m[2] if len(row_m) > 2 else 0
                        l = row_m[3] if len(row_m) > 3 else 0
                        t = (lib or "").strip().lower()
                        key = 'rue'
                        if 'prn' in t:
                            key = 'prn'
                        elif t in ('pp', 'point de passage', 'points de passage'):
                            key = 'pp'
                        mobilier[key] = {"sites": s or 0, "bacs": b or 0, "leves": l or 0}

                    # --- INTERVENTIONS ---
                    cur.execute(
                        """
                        SELECT 
                            COALESCE(MAX(nb_agents), 0),
                            COALESCE(MAX(nb_pelles_mecaniques), 0),
                            COALESCE(MAX(nb_tasseuses), 0),
                            COALESCE(MAX(nb_camions_ouvert), 0)
                        FROM moyens_equipements
                        WHERE rapport_id = %s
                        """,
                        [int(rid)],
                    )
                    row = cur.fetchone() or (0, 0, 0, 0)
                    (int_agents, int_pelles, int_tasseuses, int_cam_ouvert) = row

                    cur.execute(
                        """
                        SELECT ARRAY_AGG(nom_site ORDER BY id)
                        FROM sites_intervention
                        WHERE rapport_id = %s
                        """,
                        [int(rid)],
                    )
                    sites_list_row = cur.fetchone()
                    sites_list = sites_list_row[0] if sites_list_row and sites_list_row[0] else []

                    # --- EFFECTIFS ---
                    cur.execute(
                        """
                        SELECT periode,
                               COALESCE(SUM(effectifs), 0),
                               COALESCE(SUM(presents), 0),
                               COALESCE(SUM(absents), 0),
                               COALESCE(SUM(malades), 0),
                               COALESCE(SUM(conges), 0),
                               COALESCE(SUM(remplacement), 0)
                        FROM effectifs_jour
                        WHERE rapport_id = %s
                        GROUP BY periode
                        """,
                        [int(rid)],
                    )
                    eff_rows = cur.fetchall() or []
                    eff = {
                        "matin": {"effectifs": 0, "presents": 0, "absents": 0, "malades": 0, "conges": 0, "renforts": 0},
                        "apresmidi": {"effectifs": 0, "presents": 0, "absents": 0, "malades": 0, "conges": 0, "renforts": 0},
                    }
                    for row_e in eff_rows:
                        per = row_e[0] if len(row_e) > 0 else ''
                        eff_tot = row_e[1] if len(row_e) > 1 else 0
                        pres = row_e[2] if len(row_e) > 2 else 0
                        abs = row_e[3] if len(row_e) > 3 else 0
                        mal = row_e[4] if len(row_e) > 4 else 0
                        cong = row_e[5] if len(row_e) > 5 else 0
                        renf = row_e[6] if len(row_e) > 6 else 0
                        p = (per or "").lower()
                        key = 'matin' if 'matin' in p else 'apresmidi'
                        eff[key] = {
                            "effectifs": eff_tot or 0,
                            "presents": pres or 0,
                            "absents": abs or 0,
                            "malades": mal or 0,
                            "conges": cong or 0,
                            "renforts": renf or 0,
                        }

                    result["reports"].append({
                        "rapport_id": rid,
                        "agent": agent_nom,
                        "status": status,
                        "completion": completion,
                        "collecte": {
                            "planifies": col_plan,
                            "collectes": col_coll,
                            "tonnage": col_ton,
                            "depots_recurrents": dep_rec,
                            "depots_recurrents_leves": dep_rec_lev,
                            "circuits": circuits,
                        },
                        "polybenne": {
                            "sites": poly_sites,
                            "caisses": poly_caisses,
                            "levees": poly_levees,
                            "poids": poly_poids,
                        },
                        "nettoiement": {
                            "km_planifies": km_plan,
                            "km_balayes": km_balayes,
                            "km_desensables": km_des,
                        },
                        "mobilier": mobilier,
                        "interventions": {
                            "agents": int_agents,
                            "pelles": int_pelles,
                            "tasseuses": int_tasseuses,
                            "camions_ouvert": int_cam_ouvert,
                            "sites": sites_list,
                        },
                        "effectifs": eff,
                        "last_updated": last_updated.isoformat() if last_updated else None,
                    })

                except Exception as e:
                    print(f"[ERREUR DASHBOARD] Rapport ID {rid} ({agent_nom}) — {type(e).__name__}: {e}")
                    result["reports"].append({
                        "rapport_id": rid,
                        "agent": agent_nom,
                        "status": status,
                        "completion": completion,
                        "collecte": {"planifies": 0, "collectes": 0, "tonnage": 0, "depots_recurrents": 0, "depots_recurrents_leves": 0, "circuits": {}},
                        "polybenne": {"sites": 0, "caisses": 0, "levees": 0, "poids": 0},
                        "nettoiement": {"km_planifies": 0, "km_balayes": 0, "km_desensables": 0},
                        "mobilier": {},
                        "interventions": {"agents": 0, "pelles": 0, "tasseuses": 0, "camions_ouvert": 0, "sites": []},
                        "effectifs": {"matin": {}, "apresmidi": {}},
                        "last_updated": last_updated.isoformat() if last_updated else None,
                        "_error": str(e),
                    })

    return jsonify(result)
