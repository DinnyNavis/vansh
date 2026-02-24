import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import socketio

# Create Flask app
app = create_app()

# Initialize SocketIO in threading mode (NO eventlet)
socketio.init_app(app, async_mode="threading")

# IMPORTANT:
# Do NOT use socketio.run()
# Gunicorn will start the server using:
# gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --threads 2
