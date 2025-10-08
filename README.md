SONAGED Chatbot Reporting - MVP

Pré-requis
- Python 3.10+
- PostgreSQL 13+

Installation backend
1. Créer et remplir la base:
   - Créer la base `sonaged`
   - Exécuter `database/schema.sql`
2. Variables d'environnement (exemple):
   - Option A (simple): `DATABASE_URL=postgresql://postgres:VOTRE_MDP@localhost:5432/sonaged_reporting`
   - Option B (séparées): `DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD`
   - Support `.env` dans `backend/` (copier `.env.example` en `.env`)
   - `TWILIO_ACCOUNT_SID=...` (optionnel en dev)
   - `TWILIO_AUTH_TOKEN=...` (optionnel en dev)
3. Installer dépendances et lancer:
   - `cd backend`
   - `python -m venv .venv && .venv\Scripts\activate`
   - `pip install -r requirements.txt`
   - `python app.py`

Endpoints principaux
- POST /rapport
- GET /rapports
- POST /rapport/photo
- POST /webhook/twilio
- GET /agents

Test rapide du parser
`POST http://localhost:5000/rapport/parse` body: `{ "text": "Situation 18/07/25 - Mobilier urbain Kaolack : nettoyage des bacs..." }`

Frontend (placeholder)
Ouvrir `frontend/src/pages/index.html` dans un navigateur et utiliser le formulaire.

Déploiement
Peut être hébergé sur Render/Railway. Configurer `DATABASE_URL` et exposer `webhook/twilio` publiquement.



