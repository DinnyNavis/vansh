# backend/app/__init__.py

import os
from flask import Flask
from flask_cors import CORS
from .config import config_map
from .extensions import socketio, jwt, init_mongo


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ✅ Production + Local Origins
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://vansh-1-ds78.onrender.com",  # your frontend
    ]

    # Enable CORS for API routes
    CORS(
        app,
        resources={r"/api/*": {"origins": origins}},
        supports_credentials=True,
    )

    # Initialize extensions
    jwt.init_app(app)

    socketio.init_app(
        app,
        cors_allowed_origins=origins,
    )

    # Mongo
    init_mongo(app.config["MONGODB_URI"], app.config["MONGODB_DB"])

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.unguided import unguided_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(unguided_bp, url_prefix="/api/unguided")

    @app.route("/")
    def index():
        return "VANSH Backend Running"

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app
