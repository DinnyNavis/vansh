# backend/app/extensions.py

from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

socketio = SocketIO()
jwt = JWTManager()

mongo_client = None
mongo_db = None


def init_mongo(uri, db_name):
    global mongo_client, mongo_db

    # IMPORTANT: Short timeout, no forced connection
    mongo_client = MongoClient(uri, serverSelectionTimeoutMS=3000)
    mongo_db = mongo_client[db_name]
