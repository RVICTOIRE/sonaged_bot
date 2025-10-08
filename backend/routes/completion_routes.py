from flask import Blueprint, request, jsonify
from services.db import get_db

completion_bp = Blueprint("completion", __name__)


@completion_bp.get("/test-completion")
def test_completion():
    """Endpoint de test pour vérifier que le blueprint fonctionne"""
    return {"status": "ok", "message": "Completion blueprint fonctionne"}


def _compute_completion(conn, rid: int):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM rapport_journalier WHERE id = %s", (rid,))
        if not cur.fetchone():
            return None, ("Rapport non trouvé", 404)

        sections = {
            'effectifs': 0,
            'collecte_indicateurs': 0,
            'collecte_circuits': 0,
            'polybenne': 0,
            'nettoiement': 0,
            'mobilier_urbain': 0,
            'interventions': 0,
            'difficultes': 0,
            'recommandations': 0,
            'photos': 0,
        }

        tables = [
            ("effectifs_jour", 'effectifs'),
            ("collecte_indicateurs", 'collecte_indicateurs'),
            ("collecte_circuits", 'collecte_circuits'),
            ("polybenne", 'polybenne'),
            ("nettoiement", 'nettoiement'),
            ("bacs_indicateurs", 'mobilier_urbain'),
            ("moyens_equipements", 'interventions'),
            ("difficultes", 'difficultes'),
            ("recommandations", 'recommandations'),
            ("rapport_photos", 'photos'),
        ]
        for table, key in tables:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE rapport_id = %s", (rid,))
            count_row = cur.fetchone()
            count_val = (count_row or [0])[0] if isinstance(count_row, (list, tuple)) else 0
            if count_val > 0:
                sections[key] = 1

        completed_sections = sum(sections.values())
        total_sections = len(sections)
        percentage = int((completed_sections / total_sections) * 100) if total_sections else 0

        if percentage == 0:
            status = 'brouillon'
        elif percentage < 50:
            status = 'partiel'
        elif percentage < 100:
            status = 'complet'
        else:
            status = 'finalise'

        return {
            "rapport_id": rid,
            "completion_percentage": percentage,
            "status": status,
            "sections": sections,
            "completed_sections": completed_sections,
            "total_sections": total_sections
        }, None


@completion_bp.get("/rapport_journalier/<int:rid>/completion")
def get_report_completion(rid: int):
    try:
        with get_db() as conn:
            data, err = _compute_completion(conn, rid)
            if err:
                msg, code = err
                return {"error": msg}, code

            # Mise à jour status/percentage si colonnes présentes
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name='rapport_journalier' AND column_name='status'
                    """)
                    if cur.fetchone():
                        cur.execute(
                            "UPDATE rapport_journalier SET status=%s, completion_percentage=%s, last_updated=NOW() WHERE id=%s",
                            (data["status"], data["completion_percentage"], rid)
                        )
                        conn.commit()
            except Exception:
                pass

            return jsonify(data)
    except Exception as e:
        return {"error": f"Erreur lors du calcul de complétion: {str(e)}"}, 500


@completion_bp.get("/rapports/incomplets")
def list_incomplete_reports():
    """Liste tous les rapports incomplets pour les superviseurs"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rj.id, rj.date_rapport, rj.unite_commune, rj.status, 
                       rj.completion_percentage, rj.last_updated, a.nom as agent_nom
                FROM rapport_journalier rj
                LEFT JOIN agents a ON rj.agent_id = a.id
                WHERE rj.status IN ('brouillon', 'partiel', 'complet')
                ORDER BY rj.date_rapport DESC, rj.last_updated DESC
            """)
            reports = cur.fetchall()
            
            result = []
            for report in reports:
                result.append({
                    "id": report[0],
                    "date_rapport": report[1].isoformat() if report[1] else None,
                    "unite_commune": report[2],
                    "status": report[3],
                    "completion_percentage": report[4],
                    "last_updated": report[5].isoformat() if report[5] else None,
                    "agent_nom": report[6]
                })
            
            return {"incomplete_reports": result, "count": len(result)}


@completion_bp.post("/rapport_journalier/<int:rid>/finaliser")
def finalize_report(rid: int):
    """Finalise un rapport journalier (marque comme terminé)"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Vérifier que le rapport existe
            cur.execute("SELECT id, status FROM rapport_journalier WHERE id = %s", (rid,))
            report = cur.fetchone()
            if not report:
                return {"error": "Rapport non trouvé"}, 404
            
            # Marquer comme finalisé
            cur.execute("""
                UPDATE rapport_journalier 
                SET status = 'finalise', last_updated = now()
                WHERE id = %s
            """, (rid,))
            conn.commit()
            
            return {"ok": True, "message": "Rapport finalisé avec succès"}
