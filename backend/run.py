import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import socketio

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    # Use socketio.run for WebSocket support
    print(f"Starting backend on port {port}...")
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=True,
        allow_unsafe_werkzeug=True,
        log_output=True,
    )
