# backend/app/models.py

from datetime import datetime
from bson import ObjectId
import bcrypt
from . import extensions


class UserModel:
    COLLECTION = "users"

    @staticmethod
    def create(email, password, name):
        db = extensions.get_db()

        if db is None:
            raise Exception("Database not initialized")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        user = {
            "email": email.lower().strip(),
            "password": hashed,
            "name": name.strip(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = db[UserModel.COLLECTION].insert_one(user)
        user["_id"] = result.inserted_id
        return user

    @staticmethod
    def find_by_email(email):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        return db[UserModel.COLLECTION].find_one(
            {"email": email.lower().strip()}
        )

    @staticmethod
    def find_by_id(user_id):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        return db[UserModel.COLLECTION].find_one(
            {"_id": ObjectId(user_id)}
        )

    @staticmethod
    def check_password(user, password):
        return bcrypt.checkpw(password.encode("utf-8"), user["password"])
