from flask import Blueprint, request
from services.db import get_db

photo_bp = Blueprint("photo", __name__)


@photo_bp.post("/rapport_journalier/<int:rid>/photos")
def add_photo(rid: int):
    """Ajouter une photo à un rapport journalier"""
    payload = request.get_json(silent=True) or {}
    photo_url = payload.get("photo_url")
    
    if not photo_url:
        return {"error": "photo_url is required"}, 400
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Vérifier que le rapport existe
            cur.execute("SELECT id FROM rapport_journalier WHERE id = %s", (rid,))
            if not cur.fetchone():
                return {"error": "Rapport non trouvé"}, 404
            
            # Ajouter la photo
            cur.execute("""
                INSERT INTO rapport_photos (rapport_id, photo_url)
                VALUES (%s, %s)
            """, (rid, photo_url))
            conn.commit()
    
    return {"ok": True, "message": "Photo ajoutée avec succès"}


@photo_bp.delete("/rapport_journalier/<int:rid>/photos/<int:photo_index>")
def delete_photo(rid: int, photo_index: int):
    """Supprimer une photo d'un rapport journalier par index"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Vérifier que le rapport existe
            cur.execute("SELECT id FROM rapport_journalier WHERE id = %s", (rid,))
            if not cur.fetchone():
                return {"error": "Rapport non trouvé"}, 404
            
            # Récupérer toutes les photos pour trouver celle à supprimer
            cur.execute("SELECT id, photo_url FROM rapport_photos WHERE rapport_id = %s ORDER BY id", (rid,))
            photos = cur.fetchall()
            
            if photo_index >= len(photos):
                return {"error": "Index de photo invalide"}, 400
            
            # Supprimer la photo à l'index spécifié
            photo_id = photos[photo_index][0]
            cur.execute("DELETE FROM rapport_photos WHERE id = %s", (photo_id,))
            conn.commit()
    
    return {"ok": True, "message": "Photo supprimée avec succès"}
