from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
import logging

logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*", 
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25
)
jwt = JWTManager()
mongo_client = None
db = None

class MockCollection:
    def __init__(self, name):
        self.name = name
        self.data = []

    def insert_one(self, doc):
        from bson import ObjectId
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        # Create a copy to avoid external mutation issues in mock
        doc_copy = doc.copy()
        self.data.append(doc_copy)
        class InsertResult:
            def __init__(self, id): self.inserted_id = id
        return InsertResult(doc_copy["_id"])

    def find_one(self, filter, return_copy=True):
        from bson import ObjectId
        import copy
        for item in self.data:
            match = True
            for k, v in filter.items():
                target_val = item.get(k)
                if isinstance(v, ObjectId) or isinstance(target_val, ObjectId):
                    if str(target_val) != str(v):
                        match = False
                        break
                elif target_val != v:
                    match = False
                    break
            if match: 
                return copy.deepcopy(item) if return_copy else item
        return None

    def find(self, filter=None):
        from bson import ObjectId
        import copy
        res = self.data
        if filter:
            res = []
            for item in self.data:
                match = True
                for k, v in filter.items():
                    target_val = item.get(k)
                    if isinstance(v, ObjectId) or isinstance(target_val, ObjectId):
                        if str(target_val) != str(v):
                            match = False
                            break
                    elif target_val != v:
                        match = False
                        break
                if match: res.append(item)
        
        # Return copies of items
        res_copy = [copy.deepcopy(x) for x in res]
        
        class Cursor:
            def __init__(self, data): self.data = data
            def sort(self, key, direction): 
                self.data.sort(key=lambda x: x.get(key) or "", reverse=(direction == -1))
                return self
            def __iter__(self): return iter(self.data)
        return Cursor(res_copy)

    def update_one(self, filter, update):
        doc = self.find_one(filter, return_copy=False)
        class UpdateResult:
            def __init__(self, modified): self.modified_count = modified
        if doc:
            if "$set" in update:
                doc.update(update["$set"])
            if "$push" in update:
                for k, v in update["$push"].items():
                    if k not in doc: doc[k] = []
                    doc[k].append(v)
            return UpdateResult(1)
        return UpdateResult(0)

    def delete_one(self, filter):
        doc = self.find_one(filter, return_copy=False)
        if doc: 
            self.data.remove(doc)
            return True # delete_one doesn't usually return a Result with modified_count in simple mocks, but let's be consistent if needed
        return False

    def create_index(self, *args, **kwargs):
        pass

class MockDatabase:
    def __init__(self):
        self.collections = {}
    def __getitem__(self, name):
        if name not in self.collections:
            self.collections[name] = MockCollection(name)
        return self.collections[name]


def init_mongo(uri, db_name):
    """Initialize MongoDB connection with connection pooling."""
    global mongo_client, db
    try:
        mongo_client = MongoClient(
            uri,
            maxPoolSize=50,
            minPoolSize=10,
            connectTimeoutMS=2000,
            serverSelectionTimeoutMS=2000,
        )
        db = mongo_client[db_name]
        # Test connection
        db.command('ping')
        # Create indices
        db.users.create_index("email", unique=True)
        db.projects.create_index("user_id")
        db.projects.create_index("updated_at")
        print(f"SUCCESS: Connected to MongoDB: {db_name}")
    except Exception as e:
        logger.error(f"DATABASE: MongoDB initialization failed, enabled MockDB: {e}")
        print(f"CRITICAL: MongoDB initialization failed, enabled MockDB: {e}")
        db = MockDatabase()

def get_db():
    """Guardian DB Access: Attempts to recover real DB if currently in Mock mode."""
    global db, mongo_client
    if isinstance(db, MockDatabase) and mongo_client:
        try:
            # Try a quick ping to see if service is back
            mongo_client.admin.command('ping', serverSelectionTimeoutMS=1000)
            # If ping succeeds, restore the real DB object
            from app.config import Config
            db = mongo_client[Config.MONGODB_DB]
            logger.info("DATABASE GUARD: MongoDB service recovered. Switching back from MockDB.")
            print("INFO: MongoDB service recovered. Switching back from MockDB.")
        except:
            pass
    return db

