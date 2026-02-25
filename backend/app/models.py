# backend/app/models.py

from datetime import datetime
from bson import ObjectId
import bcrypt
from . import extensions


# =========================
# USER MODEL
# =========================

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


# =========================
# PROJECT MODEL
# =========================

class ProjectModel:
    COLLECTION = "projects"

    @staticmethod
    def create(user_id, title, input_type="audio"):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        project = {
            "user_id": ObjectId(user_id),
            "title": title.strip(),
            "input_type": input_type,
            "status": "created",
            "transcript": "",
            "refined_text": "",
            "chapters": [],
            "cover_title": title.strip(),
            "cover_subtitle": "",
            "pdf_url": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        result = db[ProjectModel.COLLECTION].insert_one(project)
        project["_id"] = result.inserted_id
        return project

    @staticmethod
    def find_by_user(user_id):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        return list(
            db[ProjectModel.COLLECTION]
            .find({"user_id": ObjectId(user_id)})
            .sort("updated_at", -1)
        )

    @staticmethod
    def find_by_id(project_id):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        return db[ProjectModel.COLLECTION].find_one(
            {"_id": ObjectId(project_id)}
        )

    @staticmethod
    def update(project_id, update_data):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        update_data["updated_at"] = datetime.utcnow()

        return db[ProjectModel.COLLECTION].update_one(
            {"_id": ObjectId(project_id)},
            {"$set": update_data},
        )

    @staticmethod
    def delete(project_id):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        return db[ProjectModel.COLLECTION].delete_one(
            {"_id": ObjectId(project_id)}
        )

    @staticmethod
    def add_chapter(project_id, chapter):
        db = extensions.get_db()
        if db is None:
            raise Exception("Database not initialized")

        chapter["id"] = str(ObjectId())
        chapter["locked"] = False
        chapter["image_url"] = None
        chapter["image_type"] = None

        return db[ProjectModel.COLLECTION].update_one(
            {"_id": ObjectId(project_id)},
            {
                "$push": {"chapters": chapter},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
