import logging
import time
import functools
import threading
from typing import Callable, Any, Dict, Optional

logger = logging.getLogger(__name__)

class GuardianSupervisor:
    """
    The ultimate safety layer for AI-dependent tasks.
    Ensures that any execution attempt either succeeds or falls back to a 
    guaranteed local algorithm, preventing permanent system failure.
    """
    
    def __init__(self):
        self.health_registry: Dict[str, Dict] = {}
        self._lock = threading.Lock()

    def report_success(self, service_name: str):
        with self._lock:
            self.health_registry[service_name] = {
                "status": "ONLINE",
                "last_success": time.time(),
                "failures": 0
            }

    def report_failure(self, service_name: str, error: str):
        with self._lock:
            record = self.health_registry.get(service_name, {"failures": 0})
            record["status"] = "DEGRADED"
            record["last_failure"] = time.time()
            record["last_error"] = error
            record["failures"] += 1
            
            if record["failures"] > 3:
                record["status"] = "OFFLINE"
            
            self.health_registry[service_name] = record
            logger.error(f"Guardian: Service '{service_name}' reported failure ({record['failures']}): {error}")

    def safe_execute(self, 
                     service_name: str, 
                     primary_func: Callable, 
                     fallback_func: Optional[Callable] = None, 
                     default_value: Any = None) -> Any:
        """
        Executes a primary function with automatic monitoring and failover.
        """
        try:
            logger.info(f"Guardian: Executing primary task for '{service_name}'...")
            result = primary_func()
            self.report_success(service_name)
            return result
        except Exception as e:
            self.report_failure(service_name, str(e))
            
            if fallback_func:
                logger.warning(f"Guardian: Primary task failed for '{service_name}'. Deploying Fallback...")
                try:
                    return fallback_func()
                except Exception as fallback_err:
                    logger.critical(f"Guardian: Fallback also failed for '{service_name}': {fallback_err}")
                    return default_value
            
            return default_value

    def get_status_report(self) -> Dict:
        with self._lock:
            return {
                "system_status": "CRITICAL" if any(s["status"] == "OFFLINE" for s in self.health_registry.values()) else "STABLE",
                "services": self.health_registry.copy(),
                "timestamp": time.time()
            }

# Singleton instance for system-wide use
guardian = GuardianSupervisor()

def with_guardian(service_name: str, fallback: Callable = None, default: Any = None):
    """Decorator for wrapping functions with Guardian protection."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return guardian.safe_execute(
                service_name,
                lambda: func(*args, **kwargs),
                fallback_func=lambda: fallback(*args, **kwargs) if fallback else None,
                default_value=default
            )
        return wrapper
    return decorator
