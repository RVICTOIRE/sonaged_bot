from flask import Blueprint, request
from twilio.request_validator import RequestValidator
from config import config
from services.db import get_db
from services.parser import parse_message_text


twilio_bp = Blueprint("twilio", __name__)


def _is_valid_twilio_request(req) -> bool:
    if not config.TWILIO_AUTH_TOKEN:
        return True  # allow in dev
    validator = RequestValidator(config.TWILIO_AUTH_TOKEN)
    signature = req.headers.get("X-Twilio-Signature", "")
    url = request.url
    params = request.form.to_dict(flat=True)
    return validator.validate(url, params, signature)


@twilio_bp.post("/webhook/twilio")
def webhook_twilio():
    if not _is_valid_twilio_request(request):
        return ("Invalid signature", 403)

    from_number = request.form.get("From", "")
    body = request.form.get("Body", "")
    media_url = request.form.get("MediaUrl0")

    parsed = parse_message_text(body)

    agent_id = None
    if from_number:
        # very naive mapping: try to find agent by matricule equal to phone (to be adapted)
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM agents WHERE matricule = %s LIMIT 1", (from_number,))
                row = cur.fetchone()
                agent_id = row[0] if row else None

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO rapports (agent_id, date_rapport, zone, type_activite, activites, photo_url, commentaire)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    agent_id,
                    parsed.get("date"),
                    parsed.get("zone"),
                    parsed.get("type_activite"),
                    parsed.get("activites"),
                    media_url,
                    parsed.get("commentaire"),
                ),
            )
            rapport_id = cur.fetchone()[0]
            conn.commit()

    # Simple TwiML response
    return (
        f"<?xml version='1.0' encoding='UTF-8'?><Response><Message>Rapport reçu (ID {rapport_id}). Merci.</Message></Response>",
        200,
        {"Content-Type": "application/xml"},
    )



