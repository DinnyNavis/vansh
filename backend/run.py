# backend/run.py

import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from app.extensions import socketio

app = create_app()

# Required for Gunicorn
socketio.init_app(app, async_mode="threading")
