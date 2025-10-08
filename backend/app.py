from flask import Flask
from flask_cors import CORS
from flask import jsonify, request
from flask import send_from_directory
import os


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    from routes.rapport_routes import rapport_bp
    from routes.agent_routes import agent_bp
    from routes.twilio_routes import twilio_bp
    from routes.completion_routes import completion_bp
    from routes.photo_routes import photo_bp
    from routes.dashboard_routes import dashboard_bp

    app.register_blueprint(rapport_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(twilio_bp)
    app.register_blueprint(completion_bp)
    app.register_blueprint(photo_bp)
    app.register_blueprint(dashboard_bp)

    @app.get("/")
    def health():
        return {"status": "ok"}

    # Static frontend serving (Option 3)
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "pages"))

    @app.get("/app/")
    def app_index():
        # default entry
        return send_from_directory(FRONTEND_DIR, "daily.html")

    @app.get("/app/<path:filename>")
    def app_static(filename: str):
        return send_from_directory(FRONTEND_DIR, filename)

    @app.errorhandler(Exception)
    def handle_exception(e):
        # Return JSON error to help the frontend/debugging
        status = 500
        try:
            # Werkzeug HTTPExceptions have code
            status = getattr(e, 'code', 500) or 500
        except Exception:
            status = 500
        return jsonify({
            "error": "internal_error",
            "detail": str(e),
            "path": request.path,
        }), status

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



