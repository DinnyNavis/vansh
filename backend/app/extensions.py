# backend/app/extensions.py

from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from pymongo import MongoClient

socketio = SocketIO()
jwt = JWTManager()

_mongo_client = None
_mongo_db = None


def init_mongo(uri, db_name):
    global _mongo_client, _mongo_db

    _mongo_client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    _mongo_db = _mongo_client[db_name]


def get_db():
    return _mongo_db
