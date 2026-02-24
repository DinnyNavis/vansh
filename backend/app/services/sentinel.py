import requests
import logging
import time
from pymongo import MongoClient

logger = logging.getLogger(__name__)

class InfrastructureSentinel:
    """Monitors the health of the core infrastructure and handles failover states."""
    
    def __init__(self, mongo_uri="mongodb://localhost:27017/", ollama_url="http://localhost:11434"):
        self.mongo_uri = mongo_uri
        self.ollama_url = ollama_url
        self.last_check = {}
        
    def check_mongodb(self):
        """Verify MongoDB connectivity."""
        try:
            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB Sentinel: OFFLINE - {e}")
            return False

    def check_ollama(self):
        """Verify Ollama connectivity."""
        try:
            resp = requests.get(self.ollama_url, timeout=2)
            return resp.status_code == 200
        except Exception:
            return False

    def get_system_health(self):
        """Returns a snapshot of the infrastructure health."""
        mongo_ok = self.check_mongodb()
        ollama_ok = self.check_ollama()
        
        status = "HEALTHY"
        if not mongo_ok or not ollama_ok:
            status = "IMPAIRED"
        if not mongo_ok and not ollama_ok:
            status = "CRITICAL"
            
        return {
            "status": status,
            "mongodb": "online" if mongo_ok else "offline",
            "ollama": "online" if ollama_ok else "offline",
            "timestamp": time.time()
        }

if __name__ == "__main__":
    # Self-test
    sentinel = InfrastructureSentinel()
    print(sentinel.get_system_health())
