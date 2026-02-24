import os
from flask import Flask
from flask_cors import CORS

from .config import config_map
from .extensions import socketio, jwt, init_mongo
from .utils.init_libraries import init_all


def create_app(config_name=None):
    """Application factory for VANSH backend."""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_map.get(config_name, config_map["development"]))

    # Ensure upload folder exists and initialize core libraries
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_all()

    # Initialize extensions
    origins = app.config.get("CORS_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"])
    CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)
    jwt.init_app(app)
    socketio.init_app(app, cors_allowed_origins=origins)
    init_mongo(app.config["MONGODB_URI"], app.config["MONGODB_DB"])

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.projects import projects_bp
    from .routes.unguided import unguided_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(projects_bp, url_prefix="/api/projects")
    app.register_blueprint(unguided_bp, url_prefix="/api/unguided")

    # Register WebSocket events
    from .routes import websocket_events  # noqa: F401

    # Root route to prevent 404 confusion
    @app.route("/")
    def index():
        return f"""
        <html>
            <body style="font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: #121212; color: #eee;">
                <h1>VANSH Backend is Running</h1>
                <p>To access the application, please visit the frontend at:</p>
                <a href="http://localhost:5173" style="color: #646cff; font-weight: bold; font-size: 1.2rem;">http://localhost:5173</a>
                <div style="margin-top: 2rem; color: #888;">
                    <p>API Status: <a href="/api/health" style="color: #888;">/api/health</a></p>
                </div>
            </body>
        </html>
        """

    # Enhanced Health Check using Infrastructure Sentinel
    @app.route("/api/health")
    def health():
        from .services.sentinel import InfrastructureSentinel
        sentinel = InfrastructureSentinel(
            mongo_uri=app.config.get("MONGODB_URI"),
            ollama_url="http://localhost:11434"
        )
        return sentinel.get_system_health()

    return app
