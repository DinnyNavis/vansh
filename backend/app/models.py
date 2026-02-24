from datetime import datetime
from bson import ObjectId
import bcrypt
from . import extensions


class UserModel:
    """User account model."""

    COLLECTION = "users"

    @staticmethod
    def create(email, password, name):
        db = extensions.get_db()
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = {
            "email": email.lower().strip(),
            "password": hashed,
            "name": name.strip(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        if db is None:
            user["_id"] = ObjectId()
            return user
        result = db[UserModel.COLLECTION].insert_one(user)
        user["_id"] = result.inserted_id
        return user

    @staticmethod
    def find_by_email(email):
        db = extensions.get_db()
        if db is None: return None
        return db[UserModel.COLLECTION].find_one({"email": email.lower().strip()})

    @staticmethod
    def find_by_id(user_id):
        db = extensions.get_db()
        if db is None: return None
        return db[UserModel.COLLECTION].find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def check_password(user, password):
        return bcrypt.checkpw(password.encode("utf-8"), user["password"])


class ProjectModel:
    """Unguided project model."""

    COLLECTION = "projects"

    @staticmethod
    def create(user_id, title, input_type="audio"):
        db = extensions.get_db()
        project = {
            "user_id": ObjectId(user_id),
            "title": title.strip(),
            "input_type": input_type,  # audio, text, video, upload-audio
            "status": "created",  # created, transcribing, writing, generating_images, complete
            "transcript": "",
            "refined_text": "",
            "chapters": [],
            "cover_title": title.strip(),
            "cover_subtitle": "",
            "pdf_url": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        if db is None: return project
        result = db[ProjectModel.COLLECTION].insert_one(project)
        project["_id"] = result.inserted_id
        return project

    @staticmethod
    def find_by_user(user_id):
        db = extensions.get_db()
        if db is None: return []
        return list(
            db[ProjectModel.COLLECTION]
            .find({"user_id": ObjectId(user_id)})
            .sort("updated_at", -1)
        )

    @staticmethod
    def find_by_id(project_id):
        db = extensions.get_db()
        if db is None: return None
        return db[ProjectModel.COLLECTION].find_one({"_id": ObjectId(project_id)})

    @staticmethod
    def update(project_id, update_data):
        db = extensions.get_db()
        if db is None: return None
        update_data["updated_at"] = datetime.utcnow()
        return db[ProjectModel.COLLECTION].update_one(
            {"_id": ObjectId(project_id)}, {"$set": update_data}
        )

    @staticmethod
    def delete(project_id):
        db = extensions.get_db()
        if db is None: return None
        return db[ProjectModel.COLLECTION].delete_one({"_id": ObjectId(project_id)})

    @staticmethod
    def add_chapter(project_id, chapter):
        db = extensions.get_db()
        if db is None: return None
        chapter["id"] = str(ObjectId())
        chapter["locked"] = False
        chapter["image_url"] = None
        chapter["image_type"] = None  # "ai" or "manual"
        return db[ProjectModel.COLLECTION].update_one(
            {"_id": ObjectId(project_id)},
            {
                "$push": {"chapters": chapter},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

    @staticmethod
    def update_chapter(project_id, chapter_id, update_data):
        db = extensions.get_db()
        if db is None: return None
        set_dict = {}
        for key, value in update_data.items():
            set_dict[f"chapters.$.{key}"] = value
        set_dict["updated_at"] = datetime.utcnow()

        return db[ProjectModel.COLLECTION].update_one(
            {"_id": ObjectId(project_id), "chapters.id": chapter_id},
            {"$set": set_dict},
        )
