import os

from flask import Flask, jsonify

from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors, limiter
from app.utils.logger import configure_logger
from app.utils.responses import error


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    configure_logger(app)

    # --- Init extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    limiter.init_app(app)

    # --- Register models (so Alembic + create_all see everything) ---
    from app import models  # noqa: F401

    # --- Register blueprints ---
    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from app.routes.election_routes import election_bp
    app.register_blueprint(election_bp, url_prefix="/api/elections")

    from app.routes.candidate_routes import candidate_bp
    app.register_blueprint(candidate_bp, url_prefix="/api")

    from app.routes.voter_admin_routes import voter_admin_bp
    app.register_blueprint(voter_admin_bp, url_prefix="/api/admin/voters")

    from app.routes.face_routes import face_bp
    app.register_blueprint(face_bp, url_prefix="/api/face")

    from app.routes.vote_routes import vote_bp
    app.register_blueprint(vote_bp, url_prefix="/api")

    from app.routes.blockchain_routes import blockchain_bp
    app.register_blueprint(blockchain_bp, url_prefix="/api/blockchain")

    from app.routes.fraud_routes import fraud_bp
    app.register_blueprint(fraud_bp, url_prefix="/api/fraud")

    from app.routes.audit_routes import audit_bp
    app.register_blueprint(audit_bp, url_prefix="/api/audit")

    from app.routes.result_routes import result_bp
    app.register_blueprint(result_bp, url_prefix="/api")

    # Added incrementally in later parts:
    # PDF/Excel export, Docker, seed data (Part 9)

    # --- Centralized error handlers ---
    from app.middleware.error_handler import register_error_handlers
    register_error_handlers(app)

    # --- CLI commands (e.g. `flask create-super-admin`) ---
    from app.cli import register_cli
    register_cli(app)

    # --- JWT error callbacks: keep the same JSON shape as every other error ---
    @jwt.unauthorized_loader
    def _missing_token(reason):
        return error("Authentication required.", 401)

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return error("Invalid authentication token.", 401)

    @jwt.expired_token_loader
    def _expired_token(jwt_header, jwt_payload):
        token_type = jwt_payload.get("type", "token")
        return error(f"Your {token_type} has expired. Please log in again.", 401)

    @jwt.needs_fresh_token_loader
    def _needs_fresh(jwt_header, jwt_payload):
        return error("This action requires a fresh login.", 401)

    @jwt.revoked_token_loader
    def _revoked_token(jwt_header, jwt_payload):
        return error("This session has been revoked.", 401)

    # --- Security headers on every response ---
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if app.config["ENV"] == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", env=app.config["ENV"])

    # Dev-only: serves scripts/vote_test.html for testing the full
    # face-verification + voting flow with a real webcam. Never enabled
    # outside DEBUG/development.
    if app.config["DEBUG"]:
        @app.get("/dev/vote-test")
        def dev_vote_test():
            import os
            from flask import send_from_directory

            scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
            return send_from_directory(scripts_dir, "vote_test.html")

    # Warm up the InsightFace model NOW, at server startup, instead of
    # lazily on the first /api/face/* request. InsightFace's first load
    # takes several seconds (reading ONNX models from disk) — without
    # this, that delay lands on whichever voter happens to click
    # "Register Face" first, which feels like the app is broken. Loading
    # it in a background thread means `flask run` itself isn't blocked,
    # and by the time anyone actually reaches the face capture step
    # (which itself takes a few seconds), the model is usually ready.
    if not app.config.get("TESTING"):
        import threading

        def _warm_up_face_model():
            try:
                from app.face.embedder import _get_app as _get_face_model
                _get_face_model()
                app.logger.info("Face recognition model pre-loaded.")
            except Exception as exc:  # pragma: no cover - best-effort warm-up only
                app.logger.warning(f"Face model warm-up skipped/failed: {exc}")

        threading.Thread(target=_warm_up_face_model, daemon=True).start()

    return app
