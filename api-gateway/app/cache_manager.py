"""Redis cache manager for user preferences and idempotency"""
import redis
import json
from typing import Optional, Dict, Any

from .utils.logging_config import setup_logging

logger = setup_logging("cache-manager")

class CacheManager:
    """Manages Redis caching operations"""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.client = None
    
    def connect(self):
        """Establish connection to Redis"""
        try:
            if self.client is None:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                self.client.ping()
                logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            self.connect()
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        try:
            self.connect()
            self.client.setex(key, ttl, json.dumps(value))
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
    
    def delete(self, key: str):
        """Delete key from cache"""
        try:
            self.connect()
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
    
    def check_idempotency(self, request_id: str) -> bool:
        """Check if request has already been processed (idempotency check)"""
        try:
            self.connect()
            key = f"idempotency:{request_id}"
            exists = self.client.exists(key)
            return exists > 0
        except Exception as e:
            logger.error(f"Error checking idempotency: {str(e)}")
            return False
    
    def set_idempotency(self, request_id: str, ttl: int = 86400):
        """Mark request as processed for idempotency"""
        try:
            self.connect()
            key = f"idempotency:{request_id}"
            self.client.setex(key, ttl, "1")
        except Exception as e:
            logger.error(f"Error setting idempotency: {str(e)}")
    
    def rate_limit_check(self, key: str, limit: int, window: int) -> bool:
        """Check rate limit using sliding window"""
        try:
            self.connect()
            current = self.client.incr(key)
            if current == 1:
                self.client.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return True  # Allow on error

# Global cache manager instance
cache_manager = None

def get_cache_manager(redis_url: str) -> CacheManager:
    """Get or create cache manager instance"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager(redis_url)
    return cache_manager
